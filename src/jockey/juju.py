"""
This module provides a set of classes and functions for interacting with and extracting information
from Juju's :class:`full_status.FullStatus` data structure.

It offers utilities to retrieve information about applications, units, and machines within a Juju environment,
extending Juju's native status objects with additional functionality.
"""

from abc import abstractmethod
from collections.abc import Mapping
import logging
from typing import Any, ClassVar, Generator, Iterable, Optional

from jockey.juju_schema.full_status import ApplicationStatus
from jockey.juju_schema.full_status import FullStatus as JujuStatus
from jockey.juju_schema.full_status import MachineStatus, UnitStatus


logger = logging.getLogger(__name__)


class Wrapper(Mapping):
    tokens: ClassVar[set[str]] = {"wrapper"}
    """The tokens used to identify the wrapped object."""

    virtual_fields: ClassVar[set[str]] = {"name", "@name", "@tokens", "@status"}

    juju_status: JujuStatus
    """The Juju status containing the wrapped object."""

    name: str
    """The name of the wrapped object."""

    def __init__(self, juju_status: JujuStatus, name: str):
        self.juju_status = juju_status
        self.name = name

    def __getitem__(self, key) -> object:
        if key == "@":
            return self.virtual_fields

        if key == "name" or key == "@name" or key in self.tokens:
            return self.name

        if key == "@tokens":
            return self.tokens

        if key == "@status":
            return self.juju_status

        return self.status[key]

    def __setitem__(self, key, value):
        if key == "name" or key == "@name" or key in self.tokens:
            self.name = value

        self.status[key] = value

    def __eq__(self, other):
        return self.status == other.status

    def __ne__(self, other):
        return self.status != other.status

    def __iter__(self):
        return iter(self.status)

    def __len__(self):
        return len(self.status)

    def __dict__(self):
        return self.status

    def __str__(self):
        return str(self.status)

    @staticmethod
    @abstractmethod
    def from_juju_status(juju_status: JujuStatus) -> Iterable["Wrapper"]:
        yield Wrapper(juju_status, "")

    @property
    def status(self) -> Any:
        return self.juju_status


class Application(Wrapper):
    """Represents the status of a Juju application, extending the :class:`full_status.ApplicationStatus` schema."""

    tokens: ClassVar[set[str]] = {"applications", "app", "apps", "application", "a"}
    virtual_fields: ClassVar[set[str]] = {
        "name",
        "@name",
        "@tokens",
        "@status",
        "@is-subordinate",
        "@is-principal",
        "@has-units",
        "@units",
    }

    def __init__(self, juju_status: JujuStatus, name: str):
        super().__init__(juju_status, name)

    def __getitem__(self, key) -> object:
        if key == "@is-subordinate":
            return self.is_subordinate

        if key == "@is-principal":
            return self.is_principal

        if key == "@has-units":
            return self.has_units

        if key == "@units":
            return self.units

        return super().__getitem__(key)

    def __eq__(self, other):
        return isinstance(other, Application) and super().__eq__(other)

    def __ne__(self, other):
        return not isinstance(other, Application) or super().__ne__(other)

    @staticmethod
    def from_juju_status(juju_status: JujuStatus) -> Generator["Application", None, None]:
        """
        Retrieve all applications from the Juju status.

        :param juju_status: The :class:`full_status.FullStatus` data structure.
        :return: A generator of :class:`Application` objects representing each application.
        """
        if "applications" in juju_status:
            for name in juju_status["applications"].keys():
                logger.debug("Found application: %r", name)
                yield Application(juju_status, name)

    @staticmethod
    def name_from_unit_name(unit_name: str) -> str:
        """
        Parse the application name from a given unit name.

        :param unit_name: The unit name.
        :return: The application name.
        """
        return unit_name.split("/")[0]

    @property
    def status(self) -> ApplicationStatus:
        return self.juju_status["applications"][self.name]

    @property
    def is_subordinate(self) -> bool:
        """
        Check if the application is subordinate to another.

        :return: ``True`` if the application is subordinate, ``False`` otherwise.
        """
        return "subordinate-to" in self.status

    @property
    def is_principal(self) -> bool:
        """
        Check if the application is principal to another.

        :return: ``True`` if the application is principal, ``False`` otherwise.
        """
        return not self.is_subordinate

    @property
    def has_units(self) -> bool:
        """
        Check if the application has any active units.

        :return: ``True`` if the application has any active units, ``False`` otherwise.
        """
        return "units" in self.status and len(self.status["units"]) > 0

    @property
    def units(self) -> Generator["Unit", None, None]:
        """
        Retrieve the units associated with the Juju application.

        :return: A generator of :class:`Unit` objects representing each unit.
        """
        if "units" in self.status:
            for unit_name in self.status["units"].keys():
                yield Unit(self.juju_status, unit_name, self.name)


class Unit(Wrapper):
    """Represents the status of a Juju unit, extending the :class:`full_status.UnitStatus` schema."""

    tokens: ClassVar[set[str]] = {"units", "unit", "u"}

    virtual_fields: ClassVar[set[str]] = {
        "name",
        "@name",
        "@tokens",
        "@status",
        "@application",
        "@application-name",
        "@has-subordinates",
        "@subordinates",
        "@machine",
    }

    principal_unit: Optional["Unit"] = None

    application_name: str
    """The name of the Juju application associated with this unit."""

    def __init__(
        self, juju_status: JujuStatus, name: str, application_name: str, principal_unit: Optional["Unit"] = None
    ):
        super().__init__(juju_status, name)
        self.application_name = application_name
        self.principal_unit = principal_unit

    def __getitem__(self, key) -> object:
        if key == "@application":
            return self.application

        if key == "@application-name":
            return self.application_name

        if key == "@has-subordinates" or key == "@has_subordinates":
            return self.has_subordinates

        if key == "@subordinates":
            return self.subordinates

        if key == "@machine":
            return self.machine

        return super().__getitem__(key)

    def __eq__(self, other):
        return isinstance(other, Unit) and super().__eq__(other)

    def __ne__(self, other):
        return not isinstance(other, Unit) or super().__ne__(other)

    @staticmethod
    def from_juju_status(juju_status: JujuStatus) -> Generator["Unit", None, None]:
        """
        Retrieve all units from the Juju status.

        :param juju_status: The :class:`full_status.FullStatus` data structure.
        :return: A generator of :class:`JujuUnitStatus` objects representing each unit.
        """
        for application in Application.from_juju_status(juju_status):
            for unit in application.units:
                yield unit
                yield from unit.subordinates

    @property
    def status(self) -> UnitStatus:
        if self.principal_unit:
            return self.principal_unit.status["subordinates"][self.name]
        else:
            return self.juju_status["applications"][self.application_name]["units"][self.name]

    @property
    def application(self) -> Application:
        return Application(self.juju_status, self.application_name)

    @property
    def has_subordinates(self) -> bool:
        """
        Check if the unit has subordinates.

        :return: ``True`` if the unit has subordinates, ``False`` otherwise.
        """
        return "subordinates" in self.status and len(self.status["subordinates"]) > 0

    @property
    def subordinates(self) -> Generator["Unit", None, None]:
        """
        Retrieve the subordinate units associated with this unit.

        :return: A generator of :class:`Unit` objects representing each subordinate unit associated with this unit.
        """
        if self.has_subordinates:
            for subordinate_name in self.status["subordinates"].keys():
                application_name = Application.name_from_unit_name(subordinate_name)
                yield Unit(self.juju_status, subordinate_name, application_name, self)

    @property
    def machine(self) -> "Machine":
        return self.principal_unit.machine if self.principal_unit else Machine(self.juju_status, self.status["machine"])


class Machine(Wrapper):
    """Represents the status of a Juju machine, extending the :class:`full_status.MachineStatus` schema."""

    tokens: ClassVar[set[str]] = {"machines", "machine", "m"}

    virtual_fields = {
        "@name",
        "name",
        "@tokens",
        "@status",
        "@id",
        "@machine-id",
        "@parent-id",
        "@parent-name",
        "@parent",
        "@has-containers",
        "@containers",
        "@is-container",
    }

    def __getitem__(self, key) -> object:
        if key == "@id" or key == "@machine-id":
            return self.name

        if key == "@parent-id" or key == "@parent-name":
            return self.parent_name

        if key == "@parent":
            return self.parent

        if key == "@has-containers":
            return self.has_containers

        if key == "@containers":
            return self.containers

        if key == "@is-container":
            return self.is_container

        return super().__getitem__(key)

    def __eq__(self, other):
        return isinstance(other, Machine) and super().__eq__(other)

    def __ne__(self, other):
        return not isinstance(other, Machine) or super().__ne__(other)

    @staticmethod
    def from_juju_status(juju_status: JujuStatus) -> Generator["Machine", None, None]:
        """
        Retrieve all machines from the Juju status.

        :param juju_status: The :class:`full_status.FullStatus` data structure.
        :return: A generator of :class:`JujuMachineStatus` objects representing each machine.
        """
        if "machines" in juju_status:
            for name in juju_status["machines"]:
                yield Machine(juju_status, name)

    @staticmethod
    def id_is_container(machine_name: str) -> bool:
        """
        Check if a machine is a container.

        :param machine_name: The machine ID.
        :return: ``True`` if the machine is a container, ``False`` otherwise.
        """
        return "/lxd/" in machine_name

    @property
    def status(self) -> MachineStatus:
        if self.is_container:
            return self.juju_status["machines"][self.parent_name]["containers"][self.name]
        else:
            return self.juju_status["machines"][self.name]

    @property
    def has_containers(self) -> bool:
        return not self.is_container and "containers" in self.status and len(self.status["containers"]) > 0

    @property
    def containers(self) -> Generator["Machine", None, None]:
        if self.has_containers:
            for container_name in self.status["containers"]:
                yield Machine(self.juju_status, container_name)

    @property
    def parent_name(self) -> str:
        return self.name.split("/")[0] if self.is_container else self.name

    @property
    def parent(self) -> "Machine":
        return Machine(self.juju_status, self.name.split("/")[0]) if self.is_container else self

    @property
    def is_container(self) -> bool:
        """
        Check if this machine is a container.

        :return: ``True`` if the machine is a container, ``False`` otherwise.
        """
        return Machine.id_is_container(self.name)
