import logging
from ipaddress import ip_address
from shlex import quote as shell_quote
from typing import Optional, Any, NamedTuple, Union, Dict

from fabric import Connection, Config, Result as FabricResult
from invoke import Context, Result as InvokeResult
from orjson import loads as json_loads

from jockey.cache import memory_cache_property, FileCache

SSH_DISABLED_ALGORITHMS = {
    "pubkeys": ["rsa-sha2-512", "rsa-sha2-256"], "keys": ["rsa-sha2-512", "rsa-sha2-256"]
}

# TODO: A stub in place of full types.
# See PR #39 -> https://github.com/LCVcode/jockey/pull/39
FullStatus = Any


# TODO: A stub in place of full types.
class WhoAmI(NamedTuple):
    controller: str
    model: str


JUJU_CONTROLLER_ENV_VAR = "JUJU_CONTROLLER"
JUJU_MODEL_ENV_VAR = "JUJU_MODEL"


class JujuRunError(Exception):
    def __init__(self, message: str, return_code: Optional[int] = None, output: Optional[str] = None):
        super().__init__(message)
        self.return_code = return_code
        self.output = output

    def __str__(self):
        return f"{super(Exception, self).__str__()}, return code: {self.return_code}, output:\n{self.output}"


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Cloud(Connection, Context):
    doas: Optional[str] = None
    juju: str
    cache: FileCache
    command_timeout: Optional[int]
    localhost: bool = False

    def __init__(self, host: Optional[str] = None, doas: Optional[str] = None, juju: str = "juju",
                 cache: Optional[FileCache] = None, command_timeout: Optional[int] = None, *args, **kwargs):
        if Cloud.is_localhost_address(host):
            Context.__init__(self)
            self.host = host
            self.localhost = True
            logger.debug("Cloud initialized on loopback")
        else:
            config = Config()
            config.update(connect_kwargs={"look_for_keys": False, "allow_agent": True,
                                          "disabled_algorithms": SSH_DISABLED_ALGORITHMS})

            Connection.__init__(self, host, *args, config=config, **kwargs)
            logger.debug("Cloud initialized on %s", host)

        self.doas = doas
        self.juju = juju or "juju"
        self.cache = cache or FileCache()
        self.command_timeout = command_timeout
        self.original_host = host

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
            not address or
            address in ("local", "localhost", "localhost.localdomain", "127.0.0.1", "::1", "loopback") or
            ip_address(address).is_loopback)

    def open(self) -> None:
        if not self.localhost:
            logger.debug("Opening connection on %s", self)
            Connection.open(self)

    @memory_cache_property
    def environ(self) -> Dict[str, str]:
        result = self.run("env")
        environ = {}
        for line in result.stdout.splitlines():
            key, value = line.split("=", 1)
            environ[key] = value

        return environ

    def sudo(self, command, **kwargs) -> Union[FabricResult, InvokeResult]:
        kwargs = self._patch_run_kwargs(kwargs)

        if self.localhost:
            logger.debug("Running command with sudo as %s on loopback: %s", self.doas, command)
            return Context.sudo(self, command, user=self.doas, **kwargs)
        else:
            logger.debug("Running command with sudo as %s on %s: %s", self.doas, self.host, command)
            return Connection.sudo(self, command, user=self.doas, **kwargs)

    def run(self, command: str, **kwargs) -> Union[FabricResult, InvokeResult]:
        if self.doas is not None or self.doas != self.user:
            logger.debug("run() invoked on cloud requiring sudo, passing to sudo()")
            return self.sudo(command, **kwargs)

        kwargs = self._patch_run_kwargs(kwargs)

        if self.localhost:
            logger.debug("Running non-sudo command on loopback: %s", command)
            return Context.run(self, command, **kwargs)
        else:
            logger.debug("Running non-sudo command on %s: %s", self.host, command)
            return Connection.run(self, command, **kwargs)

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

    def juju_whoami(self) -> WhoAmI:
        json_whoami = self.run_juju_json("whoami --format=json")
        return WhoAmI(json_whoami["controller"], json_whoami["model"])

    def juju_status(self) -> FullStatus:
        (controller, model) = self.juju_whoami()
        model_reference = Cloud.model_reference(controller, model)
        logger.debug("Getting status for %s", model_reference)

        return self.cache.entry_or(
            str(self), controller, model, "status",
            lambda: self.run_juju_json(f"status --format=json --model {shell_quote(model_reference)}"))

