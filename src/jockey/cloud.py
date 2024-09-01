from functools import cached_property
from ipaddress import ip_address
import logging
import os
from shlex import quote as shell_quote
from textwrap import dedent
from typing import Any, Dict, Generator, List, NamedTuple, Optional, Union

from fabric import Config as FabricConfig
from fabric import Connection
from fabric import Result as FabricResult
from invoke import Config as InvokeConfig
from invoke import Context
from invoke import Result as InvokeResult
from orjson import loads as json_loads
from paramiko.ssh_exception import PasswordRequiredException

from jockey.cache import FileCache, Reference
from jockey.juju_schema.full_status import FullStatus


JUJU_CONTROLLER_ENV_VAR = "JUJU_CONTROLLER"
JUJU_MODEL_ENV_VAR = "JUJU_MODEL"

SSH_PASSWORD_ENV_VAR = "JOCKEY_SSH_PASSWORD"
SSH_PASSPHRASE_ENV_VAR = "JOCKEY_SSH_PASSPHRASE"


SSH_DISABLED_ALGORITHMS = {"pubkeys": ["rsa-sha2-512", "rsa-sha2-256"], "keys": ["rsa-sha2-512", "rsa-sha2-256"]}


# TODO: A stub in place of full types.
class WhoAmI(NamedTuple):
    controller: str
    model: str


logger = logging.getLogger(__name__)


class CloudCredentialsException(Exception):
    message: str

    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self):
        return self.message + CloudCredentialsException.advice()

    @staticmethod
    def advice() -> str:
        return dedent(
            """
        There was an error connecting to the cloud with the provided credentials.
        Consider using the following environment variables:

            - JOCKEY_SSH_PASSWORD:   specify a password for the SSH server
            - JOCKEY_SSH_PASSPHRASE: specify a passphrase to unlock the SSH key
        """
        )

    @staticmethod
    def advice_markup() -> str:
        return dedent(
            """
        There was an error connecting to the cloud with the provided credentials.
        Consider using the following environment variables:

            - [cyan]JOCKEY_SSH_PASSWORD[/]:   specify a password for the SSH server
            - [cyan]JOCKEY_SSH_PASSPHRASE[/]: specify a passphrase to unlock the SSH key
        """
        )


class CloudInvokeConfig(InvokeConfig):
    """Override class for invoke.Config to prevent configuration file loading."""

    def _load_file(self, prefix: str, absolute: bool = False, merge: bool = True) -> None:
        pass

    def _merge_file(self, name: str, desc: str) -> None:
        pass

    def load_user(self, merge: bool = True) -> None:
        pass

    def load_system(self, merge: bool = True) -> None:
        pass


class CloudFabricConfig(FabricConfig):
    """Override class for fabric.Config to prevent configuration file loading."""

    def _load_file(self, prefix: str, absolute: bool = False, merge: bool = True) -> None:
        pass

    def _merge_file(self, name: str, desc: str) -> None:
        pass

    def load_user(self, merge: bool = True) -> None:
        pass

    def load_system(self, merge: bool = True) -> None:
        pass


class Cloud(Connection, Context):
    doas: Optional[str] = None
    juju: str
    cache: FileCache
    command_timeout: Optional[int]
    localhost: bool = False

    def __init__(
        self,
        host: Optional[str] = None,
        doas: Optional[str] = None,
        juju: str = "juju",
        cache: Optional[FileCache] = None,
        timeout: Optional[int] = None,
        *args,
        **kwargs,
    ):

        self.doas = doas
        self.juju = juju or "juju"
        self.cache = cache or FileCache()
        self.command_timeout = timeout
        self.original_host = host

        if Cloud.is_localhost_address(host):
            config = CloudInvokeConfig()
            config.update(timeouts={"command": timeout})
            Context.__init__(self, config)
            self.host = host
            self.localhost = True
            logger.debug("Cloud initialized on loopback")
        else:
            config = CloudFabricConfig()

            password = os.environ[SSH_PASSWORD_ENV_VAR] if SSH_PASSWORD_ENV_VAR in os.environ else None
            passphrase = os.environ[SSH_PASSPHRASE_ENV_VAR] if SSH_PASSPHRASE_ENV_VAR in os.environ else None

            config.update(
                timeouts={"command": timeout},
                connect_kwargs={
                    "passphrase": passphrase,
                    "password": password,
                    "look_for_keys": False,
                    "allow_agent": True,
                    "disabled_algorithms": SSH_DISABLED_ALGORITHMS,
                },
            )
            Connection.__init__(self, host, *args, config=config, connect_timeout=timeout, **kwargs)
            logger.debug("Cloud initialized on remote host %s", host)

    def __setattr__(self, name, value):
        if name in self.__annotations__:
            # Handle attributes defined in Cloud class
            self.__dict__[name] = value
        else:
            # Delegate to the base class
            super().__setattr__(name, value)

    def __getattr__(self, name):
        # Check if the attribute is in the instance dictionary
        if name in self.__dict__:
            return self.__dict__[name]

        # Check if the attribute is a class attribute, method, or property
        if hasattr(self.__class__, name):
            attr = getattr(self.__class__, name)

            # If it's a property, call its getter
            if isinstance(attr, property) or isinstance(attr, cached_property):
                return attr.__get__(self)

            return attr

        # Otherwise, delegate to the base class
        return super().__getattr__(name)

    def _patch_run_kwargs(self, kwargs: dict) -> dict:
        if "hide" not in kwargs:
            kwargs["hide"] = True

        if "warn" not in kwargs:
            kwargs["warn"] = False

        if "timeout" not in kwargs:
            kwargs["timeout"] = self.command_timeout

        return kwargs

    def __str__(self) -> str:
        return "localhost" if self.localhost else self.host

    @staticmethod
    def model_reference(controller: str, model: str) -> str:
        return f"{controller}:{model}"

    @staticmethod
    def is_localhost_address(address: Optional[str]) -> bool:
        return (
            not address
            or address in ("local", "localhost", "localhost.localdomain", "127.0.0.1", "::1", "loopback")
            or ip_address(address).is_loopback
        )

    def open(self) -> None:
        if not self.localhost:
            try:
                logger.debug("Opening connection on %s", self)
                Connection.open(self)
            except PasswordRequiredException as e:
                raise CloudCredentialsException(str(e)) from e

    @cached_property
    def environ(self) -> Dict[str, str]:
        result = self.run("env")
        environ = {}
        for line in result.stdout.splitlines():
            key, value = line.split("=", 1)
            environ[key] = value

        logger.debug("Read %i environment variables", len(environ))
        return environ

    def sudo(self, command, **kwargs) -> Union[FabricResult, InvokeResult]:
        kwargs = self._patch_run_kwargs(kwargs)

        if self.localhost:
            logger.debug("Running command with sudo as %s on loopback: '%s'", self.doas, command)
            return Context.sudo(self, command, user=self.doas, **kwargs)
        else:
            logger.debug("Running command with sudo as %s on %s: '%s'", self.doas, self.host, command)
            return Connection.sudo(self, command, user=self.doas, **kwargs)

    def run(self, command: str, **kwargs) -> Union[FabricResult, InvokeResult]:
        if self.doas is not None and self.doas != self.user:
            logger.debug("run() invoked on cloud requiring sudo, passing to sudo()")
            return self.sudo(command, **kwargs)

        kwargs = self._patch_run_kwargs(kwargs)

        if self.localhost:
            logger.debug("Running non-sudo command on loopback: '%s'", command)
            return Context.run(self, command, **kwargs)
        else:
            logger.debug("Running non-sudo command on %s: '%s'", self.host, command)
            return Connection.run(self, command, **kwargs)

    @cached_property
    def has_juju(self) -> bool:
        return self.run("which juju", hide=True, warn=True).return_code == 0

    def run_juju(self, command: str, **kwargs) -> Union[FabricResult, InvokeResult]:
        command = "juju " + command
        return self.run(command, **kwargs)

    def run_juju_json(self, command: str, **kwargs) -> Any:
        if "json" not in command:
            logger.warning("run_juju_json called without --format=json")

        result = self.run_juju(command, **kwargs)
        return json_loads(result.stdout)

    @cached_property
    def juju_whoami(self) -> WhoAmI:
        if JUJU_CONTROLLER_ENV_VAR in self.environ.keys() and JUJU_MODEL_ENV_VAR in self.environ.keys():
            whoami = WhoAmI(self.environ[JUJU_CONTROLLER_ENV_VAR], self.environ[JUJU_MODEL_ENV_VAR])
            logger.debug(
                "Found whoami in environment ('%s', '%s') = %s", JUJU_CONTROLLER_ENV_VAR, JUJU_MODEL_ENV_VAR, whoami
            )
            return whoami

        json_whoami = self.run_juju_json("whoami --format=json")
        return WhoAmI(json_whoami["controller"], json_whoami["model"])

    @cached_property
    def juju_status(self) -> FullStatus:
        whoami = self.juju_whoami
        controller = whoami.controller
        model = whoami.model
        model_reference = Cloud.model_reference(controller, model)
        logger.debug("Getting status for '%s'", model_reference)

        cache_ref = Reference(str(self), controller, model, "status")
        return self.cache.entry_or(
            cache_ref,
            lambda: self.run_juju_json(f"status --format=json --model {shell_quote(model_reference)}"),
        )
