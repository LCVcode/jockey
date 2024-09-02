"""
This module provides a set of classes and functions for interacting with and extracting information
from Juju's :class:`full_status.FullStatus` data structure.

It offers utilities to retrieve information about applications, units, and machines within a Juju environment,
extending Juju's native status objects with additional functionality.
"""

from typing import List

from typing_extensions import Required

from jockey.juju_schema.full_status import ApplicationStatus, FullStatus, MachineStatus, UnitStatus


class JujuUnitStatus(UnitStatus):
    """Represents the status of a Juju unit, extending the :class:`full_status.UnitStatus` schema."""

    name: Required[str]
    """The name of the Juju unit."""

    host: MachineStatus
    """The machine on which the unit is hosted."""


class JujuApplicationStatus(ApplicationStatus):
    """Represents the status of a Juju application, extending the :class:`full_status.ApplicationStatus` schema."""

    name: Required[str]
    """The name of the Juju application."""


class JujuMachineStatus(MachineStatus):
    """Represents the status of a Juju machine, extending the :class:`full_status.MachineStatus` schema."""

    name: Required[str]
    """The ID of the Juju machine."""


def all_applications(status: FullStatus) -> List[JujuApplicationStatus]:
    """
    Retrieves all applications from the Juju status.

    :param status: The :class:`full_status.FullStatus` data structure.
    :return: A list of :class:`JujuApplicationStatus` objects representing each application.
    """
    return [JujuApplicationStatus(name=name, **app) for name, app in status["applications"].items()]


def all_application_names(status: FullStatus) -> List[str]:
    """
    Retrieves all application names from the Juju status.

    :param status: The :class:`full_status.FullStatus` data structure.
    :return: A list of application names in no particular order.
    """
    return [app for app in status["applications"].keys()]


def is_subordinate_application(status: FullStatus, app_name: str) -> bool:
    """
    Checks if an application is subordinate to another.

    :param status: The :class:`full_status.FullStatus` data structure.
    :param app_name: The name of the application.
    :return: ``True`` if the application is subordinate, ``False`` otherwise.
    """
    return "subordinate-to" in status["applications"][app_name]


def is_principal_application(status: FullStatus, app_name: str) -> bool:
    """
    Checks if an application is principal to another.

    :param status: The :class:`full_status.FullStatus` data structure.
    :param app_name: The name of the application.
    :return: ``True`` if the application is principal, ``False`` otherwise.
    """
    return not is_subordinate_application(status, app_name)


def application_has_units(status: FullStatus, app_name: str) -> bool:
    """
    Checks if an application has any active units.

    :param status: The :class:`full_status.FullStatus` data structure.
    :param app_name: The name of the application.
    :return: ``True`` if the application has any active units, ``False`` otherwise.
    """
    return "units" in status["applications"][app_name] and len(status["applications"][app_name]["units"]) > 0


def application_units(status: FullStatus, app_name: str) -> List[JujuUnitStatus]:
    """
    Retrieves the units associated with a Juju application.

    :param status: The :class:`full_status.FullStatus` data structure.
    :param app_name: The name of the application.
    :return: A list of :class:`JujuUnitStatus` objects representing each unit.
    """
    if not application_has_units(status, app_name):
        return []

    units = []
    for unit_name, unit in status["applications"][app_name]["units"].items():
        host: MachineStatus = lookup_machine(status, unit["machine"])
        units.append(JujuUnitStatus(name=unit_name, host=host, **unit))
        units.extend(unit_subordinates(status, app_name, unit_name))

    return units


def application_unit_names(status: FullStatus, app_name: str) -> List[str]:
    """
    Retrieves the names of the units associated with a Juju application.

    :param status: The :class:`full_status.FullStatus` data structure.
    :param app_name: The name of the application.
    :return: A list of unit names in no particular order.
    """
    return [unit["name"] for unit in application_units(status, app_name)]


def unit_has_subordinates(status: FullStatus, app_name: str, unit_name: str) -> bool:
    """
    Checks if a unit has subordinates.

    :param status: The :class:`full_status.FullStatus` data structure.
    :param app_name: The name of the application.
    :param unit_name: The name of the unit.
    :return: ``True`` if the unit has subordinates, ``False`` otherwise.
    """
    return (
        "subordinates" in status["applications"][app_name]["units"][unit_name]
        and len(status["applications"][app_name]["units"][unit_name]["subordinates"]) > 0
    )


def unit_subordinates(status: FullStatus, app_name: str, unit_name: str) -> List[JujuUnitStatus]:
    """
    Retrieves the subordinate units associated with a Juju unit.

    :param status: The :class:`full_status.FullStatus` data structure.
    :param app_name: The name of the application.
    :param unit_name: The name of the unit.
    :return: A list of :class:`JujuUnitStatus` objects representing each subordinate unit associated with the unit.
    """
    if not unit_has_subordinates(status, app_name, unit_name):
        return []

    subs = []
    host: MachineStatus = lookup_machine(status, status["applications"][app_name]["units"][unit_name]["machine"])
    for sub_name, sub in status["applications"][app_name]["units"][unit_name]["subordinates"].items():
        subs.append(JujuUnitStatus(name=sub_name, host=host, **sub))

    return subs


def all_units(status: FullStatus) -> List[JujuUnitStatus]:
    """
    Retrieves all units from the Juju status.

    :param status: The :class:`full_status.FullStatus` data structure.
    :return: A list of :class:`JujuUnitStatus` objects representing each unit.
    """
    units = []
    for app_name in all_application_names(status):
        units.extend(application_units(status, app_name))

    return units


def all_machines(status: FullStatus) -> List[MachineStatus]:
    """
    Retrieves all machines from the Juju status.

    :param status: The :class:`full_status.FullStatus` data structure.
    :return: A list of :class:`JujuMachineStatus` objects representing each machine.
    """
    return [JujuMachineStatus(name=name, **machine) for name, machine in status["machines"].items()]


def is_container(machine_id: str) -> bool:
    """
    Checks if a machine is a container.

    :param machine_id: The machine ID.
    :return: ``True`` if the machine is a container, ``False`` otherwise.
    """
    return "/lxd/" in machine_id


def lookup_machine(status: FullStatus, machine_id: str) -> MachineStatus:
    """
    Looks up a machine or container in the Juju status.

    :param status: The :class:`full_status.FullStatus` data structure.
    :param machine_id: The ID of the machine or container to find.
    :return: The :class:`full_status.MachineStatus` object representing the machine or container.
    """
    if is_container(machine_id):
        root_machine_id = machine_id.split("/")[0]
        return status["machines"][root_machine_id]["containers"][machine_id]
    else:
        return status["machines"][machine_id]
