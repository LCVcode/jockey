from typing import List

from typing_extensions import Required

from jockey.juju_schema.full_status import ApplicationStatus, FullStatus, MachineStatus, UnitStatus


class JujuUnitStatus(UnitStatus):
    name: Required[str]
    host: MachineStatus


class JujuApplicationStatus(ApplicationStatus):
    name: Required[str]


class JujuMachineStatus(MachineStatus):
    name: Required[str]


def all_applications(status: FullStatus) -> List[JujuApplicationStatus]:
    return [JujuApplicationStatus(name=name, **app) for name, app in status["applications"].items()]


def all_application_names(status: FullStatus) -> List[str]:
    """
    Get all applications in the Juju status by name.

    Returns
    =======
    application_names (Generator[str])
        All application names, in no particular order, as a generator.
    """
    return [app for app in status["applications"].keys()]


def is_subordinate_application(status: FullStatus, app_name: str) -> bool:
    return "subordinate-to" in status["applications"][app_name]


def is_principal_application(status: FullStatus, app_name: str) -> bool:
    """
    Test if a given application is principal.  True indicates principal and
    False indicates subordinate.

    Arguments
    =========
    app_name (str)
        The name of the application to check.

    Returns
    =======
    is_principal (bool)
        Whether the indicated application is principal.
    """
    return not is_subordinate_application(status, app_name)


def application_has_units(status: FullStatus, app_name: str) -> bool:
    return "units" in status["applications"][app_name] and len(status["applications"][app_name]["units"]) > 0


def application_units(status: FullStatus, app_name: str) -> List[JujuUnitStatus]:
    if not application_has_units(status, app_name):
        return []

    units = []
    for unit_name, unit in status["applications"][app_name]["units"].items():
        host: MachineStatus = lookup_machine(status, unit["machine"])
        units.append(JujuUnitStatus(name=unit_name, host=host, **unit))
        units.extend(unit_subordinates(status, app_name, unit_name))

    return units


def application_unit_names(status: FullStatus, app_name: str) -> List[str]:
    return [unit["name"] for unit in application_units(status, app_name)]


def unit_has_subordinates(status: FullStatus, app_name: str, unit_name: str) -> bool:
    return (
        "subordinates" in status["applications"][app_name]["units"][unit_name]
        and len(status["applications"][app_name]["units"][unit_name]["subordinates"]) > 0
    )


def unit_subordinates(status: FullStatus, app_name: str, unit_name: str) -> List[JujuUnitStatus]:
    if not unit_has_subordinates(status, app_name, unit_name):
        return []

    subs = []
    host: MachineStatus = lookup_machine(status, status["applications"][app_name]["units"][unit_name]["machine"])
    for sub_name, sub in status["applications"][app_name]["units"][unit_name]["subordinates"].items():
        subs.append(JujuUnitStatus(name=sub_name, host=host, **sub))

    return subs


def all_units(status: FullStatus) -> List[JujuUnitStatus]:
    units = []
    for app_name in all_application_names(status):
        units.extend(application_units(status, app_name))

    return units


def all_machines(status: FullStatus) -> List[MachineStatus]:
    return [JujuMachineStatus(name=name, **machine) for name, machine in status["machines"].items()]


def is_container(machine_id: str) -> bool:
    return "/lxd/" in machine_id


def lookup_machine(status: FullStatus, machine_id: str) -> MachineStatus:
    if is_container(machine_id):
        root_machine_id = machine_id.split("/")[0]
        return status["machines"][root_machine_id]["containers"][machine_id]
    else:
        return status["machines"][machine_id]
