from typing import List

from typing_extensions import Required

from jockey.juju_schema.full_status import ApplicationStatus, FullStatus, MachineStatus, UnitStatus


class JujuUnitStatus(UnitStatus):
    name: Required[str]
    host: MachineStatus


class JujuApplicationStatus(ApplicationStatus):
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
        host: MachineStatus = status["machines"][unit["machine"]]
        units.append(JujuUnitStatus(name=unit_name, host=host, **unit))
        units.extend(unit_subordinates(status, app_name, unit_name))

    return units


def application_unit_names(status: FullStatus, app_name: str) -> List[str]:
    return [unit["name"] for unit in application_units(status, app_name)]


def all_charm_names(status: FullStatus) -> List[str]:
    """
    Get all charms in the Juju status by name.

    Returns
    =======
    charm_names (Generator[str])
        All charms names, in no particular order, as a generator.
    """
    return [status["applications"][name]["charm"] for name in all_application_names(status)]


def unit_has_subordinates(status: FullStatus, app_name: str, unit_name: str) -> bool:
    return (
        "subordinates" in status["applications"][app_name]["units"][unit_name]
        and len(status["applications"][app_name]["units"][unit_name]["subordinates"]) > 0
    )


def unit_subordinate_names(status: FullStatus, app_name: str, unit_name: str) -> List[str]:
    if not unit_has_subordinates(status, app_name, unit_name):
        return []

    return [sub_name for sub_name in status["applications"][app_name]["units"][unit_name]["subordinates"].keys()]


def unit_subordinates(status: FullStatus, app_name: str, unit_name: str) -> List[JujuUnitStatus]:
    if not unit_has_subordinates(status, app_name, unit_name):
        return []

    subs = []
    for sub_name, sub in status["applications"][app_name]["units"][unit_name]["subordinates"].items():
        host: MachineStatus = status["machines"][sub["machine"]]
        subs.append(JujuUnitStatus(name=sub_name, host=host, **sub))

    return subs


def all_units(status: FullStatus) -> List[JujuUnitStatus]:
    units = []
    for app_name in all_application_names(status):
        units.extend(application_units(status, app_name))

    return units


def all_unit_names(status: FullStatus) -> List[str]:
    unit_names = []
    for app_name in all_application_names(status):
        unit_names.extend(application_unit_names(status, app_name))

    return unit_names


def machine_has_containers(status: FullStatus, machine_id: str) -> bool:
    return "containers" in status["machines"][machine_id]


def machine_container_ids(status: FullStatus, machine_id: str) -> List[str]:
    if not machine_has_containers(status, machine_id):
        return []

    return [container for container in status["machines"][machine_id]["containers"].keys()]
