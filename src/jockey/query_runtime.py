"""Filtering runtime for object queries."""

from typing import Callable, Dict, Generator, List, Optional

from jockey.filtering import JockeyFilter, check_filter_batch_match, check_filter_match
from jockey.juju_conversions import (
    application_to_charm,
    get_machines,
    get_units,
    machine_to_availability_zone,
    machine_to_hostname,
    machine_to_ips,
    machine_to_units,
    unit_to_application,
    unit_to_machine,
)
from jockey.object_types import ObjectType
from jockey.types import JujuStatus


def _group_filters_by_type(filters: List[JockeyFilter]) -> Dict[ObjectType, List[JockeyFilter]]:
    """Group filters by their object type."""
    grouped: Dict[ObjectType, List[JockeyFilter]] = {obj_type: [] for obj_type in ObjectType}
    for f in filters:
        grouped[f.obj_type].append(f)
    return grouped


def filter_units(status: JujuStatus, filters: List[JockeyFilter]) -> Generator[str, None, None]:
    """
    Get all units from a Juju status that match a list of filters.

    Arguments
    =========
    status (JujuStatus)
        The current Juju status in json format.
    filters (List[JockeyFilter])
        A list of parsed filters, provided to the CLI.

    Returns
    =======
    units (Generator[str])
        All matching units, as a generator.
    """
    grouped_filters = _group_filters_by_type(filters)

    for unit in get_units(status):
        if not all(check_filter_match(unit_filter, unit) for unit_filter in grouped_filters[ObjectType.UNIT]):
            continue

        app_filters = grouped_filters[ObjectType.APP]
        charm_filters = grouped_filters[ObjectType.CHARM]
        if app_filters or charm_filters:
            app = unit_to_application(status, unit)
            assert app
            if not all(check_filter_match(app_filter, app) for app_filter in app_filters):
                continue

            charm = application_to_charm(status, app)
            assert charm
            if not all(check_filter_match(charm_filter, charm) for charm_filter in charm_filters):
                continue

        machine_filters = grouped_filters[ObjectType.MACHINE]
        ip_filters = grouped_filters[ObjectType.IP]
        hostname_filters = grouped_filters[ObjectType.HOSTNAME]
        if not any((machine_filters, ip_filters, hostname_filters)):
            yield unit
            continue

        machine = unit_to_machine(status, unit)
        assert machine
        if not all(check_filter_match(machine_filter, machine) for machine_filter in machine_filters):
            continue

        hostname = machine_to_hostname(status, machine)
        assert hostname
        if not all(check_filter_match(hostname_filter, hostname) for hostname_filter in hostname_filters):
            continue

        ips = machine_to_ips(status, machine)
        assert ips
        if not all(any(check_filter_match(ip_filter, ip) for ip in ips) for ip_filter in ip_filters):
            continue

        availability_zone = machine_to_availability_zone(status, machine)
        if availability_zone:
            az_filters = grouped_filters[ObjectType.AVAILABILITY_ZONE]
            if not all(check_filter_match(az_filter, availability_zone) for az_filter in az_filters):
                continue

        yield unit


def filter_machines(status: JujuStatus, filters: List[JockeyFilter]) -> Generator[str, None, None]:
    """
    Get all machines from a Juju status that match a list of filters.

    Arguments
    =========
    status (JujuStatus)
        The current Juju status in json format.
    filters (List[JockeyFilter])
        A list of parsed filters, provided to the CLI.

    Returns
    =======
    machines (Generator[str])
        All matching machines, as a generator.
    """
    grouped_filters = _group_filters_by_type(filters)

    for machine in get_machines(status):
        machine_filters = grouped_filters[ObjectType.MACHINE]
        if not all(check_filter_match(machine_filter, machine) for machine_filter in machine_filters):
            continue

        hostname = machine_to_hostname(status, machine)
        assert hostname
        hostname_filters = grouped_filters[ObjectType.HOSTNAME]
        if not all(check_filter_match(hostname_filter, hostname) for hostname_filter in hostname_filters):
            continue

        ips = machine_to_ips(status, machine)
        assert ips
        if not check_filter_batch_match(grouped_filters[ObjectType.IP], ips):
            continue

        units = tuple(machine_to_units(status, machine))
        if not check_filter_batch_match(grouped_filters[ObjectType.UNIT], units):
            continue

        apps = tuple(unit_to_application(status, unit) for unit in units)
        assert all(apps)
        if not check_filter_batch_match(grouped_filters[ObjectType.APP], apps):  # type: ignore[arg-type]
            continue

        charms = tuple(application_to_charm(status, app) for app in apps)  # type: ignore[arg-type]
        if not check_filter_batch_match(grouped_filters[ObjectType.CHARM], charms):  # type: ignore[arg-type]
            continue

        availability_zone = machine_to_availability_zone(status, machine)
        if availability_zone:
            az_filters = grouped_filters[ObjectType.AVAILABILITY_ZONE]
            if not all(check_filter_match(az_filter, availability_zone) for az_filter in az_filters):
                continue

        yield machine


RETRIEVAL_MAP: Dict[
    ObjectType,
    Optional[Callable[[JujuStatus, List[JockeyFilter]], Generator[str, None, None]]],
] = {
    ObjectType.CHARM: None,
    ObjectType.APP: None,
    ObjectType.UNIT: filter_units,
    ObjectType.MACHINE: filter_machines,
    ObjectType.IP: None,
    ObjectType.HOSTNAME: None,
}
