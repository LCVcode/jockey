"""Juju object listing and relationship conversion helpers."""

from typing import Generator, Optional

from jockey.types import JujuStatus


def is_app_principal(status: JujuStatus, app_name: str) -> bool:
    """
    Test if a given application is principal.  True indicates principal and
    False indicates subordinate.

    Arguments
    =========
    status (JujuStatus)
        The current Juju status in json format.
    app_name (str)
        The name of the application to check.

    Returns
    =======
    is_principal (bool)
        Whether the indicated application is principal.
    """
    return "subordinate-to" not in status["applications"][app_name]


def get_principal_unit_for_subordinate(status: JujuStatus, unit_name: str) -> str:
    """
    Get a principal unit name for the given subordinate unit.

    Arguments
    =========
    status (JujuStatus)
        The current Juju status in json format.
    unit_name (str)
        The subordinate unit name.

    Returns
    =======
    principal_unit (str)
        The corresponding principal unit name, if found.
    """
    for app, data in status["applications"].items():
        if not is_app_principal(status, app):
            continue

        for unit, unit_data in data["units"].items():
            if unit_name in unit_data["subordinates"]:
                return unit

    return ""


def get_applications(status: JujuStatus) -> Generator[str, None, None]:
    """
    Get all applications in the Juju status by name.

    Arguments
    =========
    status (JujuStatus)
        The current Juju status in json format.

    Returns
    =======
    application_names (Generator[str])
        All application names, in no particular order, as a generator.
    """
    for app in status["applications"]:
        yield app


def get_charms(status: JujuStatus) -> Generator[str, None, None]:
    """
    Get all charms in the Juju status by name.

    Arguments
    =========
    status (JujuStatus)
        The current Juju status in json format.

    Returns
    =======
    charm_names (Generator[str])
        All charms names, in no particular order, as a generator.
    """
    for app in get_applications(status):
        yield status["applications"][app]["charm"]


def get_units(status: JujuStatus) -> Generator[str, None, None]:
    """
    Get all units in the Juju status by name.

    Arguments
    =========
    status (JujuStatus)
        The current Juju status in json format.

    Returns
    =======
    unit_names (Generator[str])
        All unit names, in no particular order, as a generator.
    """
    for app in get_applications(status):
        if not is_app_principal(status, app):
            continue

        if "units" not in status["applications"][app]:
            continue

        for unit_name, data in status["applications"][app]["units"].items():
            yield unit_name

            if "subordinates" not in data:
                continue

            for subordinate_unit_name in data["subordinates"]:
                yield subordinate_unit_name


def get_machines(status: JujuStatus) -> Generator[str, None, None]:
    """
    Get all machines in the Juju model, including containers.

    Arguments
    =========
    status (JujuStatus)
        The current Juju status in json format.

    Returns
    =======
    machine_ids (Generator[str])
        All machines, in no particular order, as a generator.
    """
    for machine_id in status["machines"].keys():
        yield machine_id

        if "containers" not in status["machines"][machine_id]:
            continue

        for container in status["machines"][machine_id]["containers"]:
            yield container


def get_hostnames(status: JujuStatus) -> Generator[str, None, None]:
    """
    Get all machine hostnames in the Juju model.

    Arguments
    =========
    status (JujuStatus)
        The current Juju status in json format.

    Returns
    =======
    hostnames (Generator[str])
        All hostnames, in no particular order, as a generator.
    """
    for machine in get_machines(status):
        yield machine_to_hostname(status, machine)


def get_ips(status: JujuStatus) -> Generator[str, None, None]:
    """
    Get all machine IPs in the Juju model.

    Arguments
    =========
    status (JujuStatus)
        The current Juju status in json format.

    Returns
    =======
    ips (Generator[str])
        All IPs, in no particular order, as a generator.
    """
    for machine in get_machines(status):
        for address in machine_to_ips(status, machine):
            yield address


def charm_to_applications(status: JujuStatus, charm_name: str) -> Generator[str, None, None]:
    """
    Given a charm name, get all applications using it, as a generator. If no
    matching charm is found, the generator will be empty.

    Arguments
    =========
    status (JujuStatus)
        The current Juju status in json format.
    charm_name (str)
        The name of the charm to find applications for.


    Returns
    =======
    applications (Generator[str])
        All applications that match the given charm name.
    """
    for application, data in status["applications"].items():
        if data["charm"] == charm_name:
            yield application


def application_to_charm(status: JujuStatus, app_name: str) -> Optional[str]:
    """
    Given an application name, get the charm it is using, if any.

    Arguments
    =========
    status (JujuStatus)
        The current Juju status in json format.
    app_name (str)
        The name of the application to find a charm for.

    Returns
    =======
    charm (str) [optional]
        The name of the charm, if the indicated application exists.
    """
    try:
        return status["applications"][app_name]["charm"]
    except KeyError:
        return None


def application_to_units(status: JujuStatus, app_name: str) -> Generator[str, None, None]:
    """
    Given an application name, get all of its units, as a generator.  If no
    matching application is found, the generator will be empty.

    Arguments
    =========
    status (JujuStatus)
        The current Juju status in json format.
    app_name (str)
        The name of the application to find units for.

    Returns
    =======
    units (Generator[str])
        All units of the given application.
    """
    for application, data in status["applications"].items():
        if application != app_name:
            continue

        for unit_name in data["units"].keys():
            yield unit_name


def unit_to_application(status: JujuStatus, unit_name: str) -> Optional[str]:
    """
    Given a unit name, get its application name.

    Arguments
    =========
    status (JujuStatus)
        The current Juju status in json format.
    unit_name (str)
        The name of the unit to find an application for.

    Returns
    =======
    application (str) [optional]
        The name of the corresponding application.
    """
    app_name = unit_name.split("/")[0]

    if app_name in status["applications"]:
        return app_name

    return None


def subordinate_unit_to_principal_unit(status: JujuStatus, unit_name: str) -> str:
    """
    Given a unit name, get its principal unit.  If the given unit is principal,
    it will be returned as-is.

    Arguments
    =========
    status (JujuStatus)
        The current Juju status in json format.

    Returns
    =======
    unit_name (str)
        The name of the unit to check.
    """
    app = unit_to_application(status, unit_name)
    assert app, f"No application found for unit {unit_name}"
    app_data = status["applications"]

    if is_app_principal(status, app):
        return unit_name

    for principal_app in app_data[app]["subordinate-to"]:
        if not is_app_principal(status, principal_app):
            continue

        for principal_unit in app_data[principal_app]["units"]:
            if unit_name in app_data[principal_app]["units"][principal_unit]["subordinates"]:
                return principal_unit

    raise Exception(f"No principal unit detected for unit {unit_name}")


def unit_to_machine(status: JujuStatus, unit_name: str) -> Optional[str]:
    """
    Given a unit name, get the ID of the machine it is running on, if any.
    Currently only works on units from principal applications.

    Arguments
    =========
    status (JujuStatus)
        The current Juju status in json format.
    unit_name (str)
        The name of the unit.

    Returns
    =======
    machine_id (str) [optional]
        The ID of the corresponding machine.
    """
    principal_unit_name = subordinate_unit_to_principal_unit(status, unit_name)
    app = unit_to_application(status, principal_unit_name)
    assert app

    return status["applications"][app]["units"][principal_unit_name]["machine"]


def machine_to_units(status: JujuStatus, machine: str) -> Generator[str, None, None]:
    """
    Given a machine id, get all of its units, as a generator.  If no matching
    units are found, the generator will be empty.

    Arguments
    =========
    status (JujuStatus)
        The current Juju status in json format.
    machine (str)
        The ID of the machine to use.

    Returns
    =======
    units (Generator[str])
        All units on the given machine.
    """
    for unit in get_units(status):
        app = unit_to_application(status, unit)
        assert app
        if not is_app_principal(status, app):
            continue

        if unit_to_machine(status, unit) == machine:
            yield unit

            if "subordinates" not in status["applications"][app]["units"][unit]:
                continue

            for subordinate_unit in status["applications"][app]["units"][unit]["subordinates"]:
                yield subordinate_unit


def machine_to_ips(status: JujuStatus, machine: str) -> Generator[str, None, None]:
    """
    Given a machine id, get each of its IP addresses as a generator.

    Arguments
    =========
    status (JujuStatus)
        The current Juju status in json format.
    machine (str)
        The ID of the machine to use.

    Returns
    =======
    addresses (Generator[str])
        The IP addresses of the machine.
    """
    if "lxd" in machine.lower():
        base_machine = status["machines"][machine.split("/")[0]]
        for ip in base_machine["containers"][machine]["ip-addresses"]:
            yield ip
    else:
        for ip in status["machines"][machine]["ip-addresses"]:
            yield ip


def ip_to_machine(status: JujuStatus, ip: str) -> str:
    """
    Given an ip, get the ID of the machine that owns it.

    Arguments
    =========
    status (JujuStatus)
        The current Juju status in json format.
    address (str)
        The IP address in question.

    Returns
    =======
    machine ID (str)
        ID of the machine owning the given IP.
    """
    for machine in get_machines(status):
        if ip in machine_to_ips(status, machine):
            return machine

    raise Exception(f"No machine found with IP {ip}")


def machine_to_availability_zone(status: JujuStatus, machine: str) -> str:
    """
    Given a machine id, get its availability zone.

    Arguments
    =========
    status (JujuStatus)
        The current Juju status in json format.
    machine (str)
        The ID of the machine to use.

    Returns
    =======
    availability_zone (str)
        The machine's availability zone.
    """
    if "lxd" in machine:
        machine, _, _ = machine.split("/")
    hardware = status["machines"][machine]["hardware"]
    for entry in hardware.split():
        key, value = entry.split("=")
        if key == "availability-zone":
            return value
    return ""


def machine_to_hostname(status: JujuStatus, machine: str) -> str:
    """
    Given a machine id, get its hostname.

    Arguments
    =========
    status (JujuStatus)
        The current Juju status in json format.
    machine (str)
        The ID of the machine to use.

    Returns
    =======
    hostname (str)
        The machine's hostname.
    """
    if "lxd" in machine:
        physical_machine = machine.split("/")[0]
        return status["machines"][physical_machine]["containers"][machine]["hostname"]
    return status["machines"][machine]["hostname"]


def hostname_to_machine(status: JujuStatus, hostname: str) -> str:
    """
    Given a hostname, get that machine's ID.

    Arguments
    =========
    status (JujuStatus)
        The current Juju status in json format.
    hostname (str)
        The machine's hostname.

    Returns
    =======
    machine (str)
        The ID of the machine with the given hostname.
    """
    for machine in get_machines(status):
        if machine_to_hostname(status, machine) == hostname:
            return machine

    raise Exception(f"No machine found for hostname {hostname}")
