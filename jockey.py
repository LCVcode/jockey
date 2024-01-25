#!/bin/python3
# Jockey is a CLI utility that facilitates quick retrieval of Juju objects that
# match given filters.
# Author: Connor Chamberlain

import argparse
import json
import re
from typing import Any, Dict, NamedTuple, Generator, Optional, List, Tuple

from status_keeper import retrieve_juju_cache, cache_juju_status


JujuStatus = Dict[str, Any]


OBJECTS = {
    "charm": ("charms", "c"),
    "application": ("app", "apps", "applications", "a"),
    "unit": ("units", "u"),
    "machine": ("machines", "m"),
    "ip": ("address", "addresses", "ips", "i"),
    "hostname": ("hostnames", "host", "hosts", "h"),
}


def pretty_print_keys(data: JujuStatus, depth: int = 0) -> None:
    """Print a dictionary's keys in a heirarchy."""
    if depth > 3:
        return

    for key, value in data.items():
        print(" |" * depth + key)

        if isinstance(value, dict):
            pretty_print_keys(data[key], depth=depth + 1)


def convert_object_abbreviation(abbrev: str) -> Optional[str]:
    """
    Convert an object type abbreviation into its full name.  If the object type
    is not a valid Juju object, None will be returned.

    Arguments
    =========
    abbrev (str)
        A possibly abbreviated object name.

    Returns
    =======
    object_name (str) [optional]
        The decoded object abbrevation, if one exists.  May be the same as the
        abbrev argument.  Is None if abbrev is not a valid object type.
    """
    abbrev = abbrev.lower()
    if abbrev in OBJECTS:
        return abbrev

    for obj_name, alternatives in OBJECTS.items():
        if abbrev in alternatives:
            return obj_name


def parse_filter_string(filter_str: str) -> Tuple[str, str, str]:
    """
    Split a filter string into its three parts: object-type, filter-code, and
    contents.

    Arguments
    =========
    filter_str (str)
        A raw filter string as given to the CLI.

    Returns
    =======
    object_type (str)
        The object type portion of the filter, comprising everything prior to
        the filter code.
    filter_code (str)
        The one or two character filter code (=, ~, !=, or !~).
    content (str)
        The content portion of the filter, comprising everything after the
        filter code.
    """
    filter_pattern = re.compile(r'(\w+)\s*([=~]|!=)\s*("[^"]+"|[\w\/.-]+)')
    match = filter_pattern.match(filter_str)
    if match:
        object_type, filter_code, content = match.groups()
        object_type = convert_object_abbreviation(object_type)
        assert object_type is not None
        content = value.strip('"')
        return object_type, filter_code, content
    else:
        raise argparse.ArgumentTypeError(f"Invalid filter: '{filter_str}'")


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


def get_principal_unit_for_subordinate(
    status: JujuStatus, unit_name: str
) -> str:
    """Get the name of a princpal unit for a given subordinate unit."""
    for app, data in status["applications"].items():

        # Skip other subordinate applications
        if not is_app_principal(status, app):
            continue

        # Check if given unit is a subordinate of any of these units
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

        # Skip subordinate applicaitons
        if not is_app_principal(status, app):
            continue

        for unit_name, data in status["applications"][app]["units"].items():
            # Generate principal unit
            yield unit_name

            # Check if subordinate units exist
            if "subordinates" not in data:
                continue

            # Generate subordinate units
            for subordinate_unit_name in data["subordinates"]:
                yield subordinate_unit_name


def get_machines(status: JujuStatus) -> Generator[str, None, None]:
    """
    Get all machines in the Juju model by index.

    Arguments
    =========
    status (JujuStatus)
        The current Juju status in json format.

    Returns
    =======
    machine_ids (Generator[str])
        All machine indices, in no particular order, as a generator.
    """
    for id in status["machines"].keys():
        yield id


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
    for machine in status["machines"]:
        yield machine["hostname"]


def get_ips(status: JujuStatus) -> Generator[str, None, None]:
    """
    Get all machine ips in the Juju model.

    Arguments
    =========
    status (JujuStatus)
        The current Juju status in json format.

    Returns
    =======
    ips (Generator[str])
        All ips, in no particular order, as a generator.
    """
    for machine in status["machines"]:
        for address in machine["ip-addresses"]:
            yield address


def charm_to_applications(
    status: JujuStatus, charm_name: str
) -> Generator[str, None, None]:
    """
    Given a charm name, get all applications using it, as a generator.

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
    for application in status["applications"]:
        if application["charm"] == charm_name:
            yield application


def application_to_charm(status: JujuStatus, app_name: str) -> Optional[str]:
    """
    Given an application name, get the charm it is using, if any.

    Arguments
    =========
    status (JujuStatus)
        The current Juju status in json format.
    app_name (str)
        The name of the applicaiton to find a charm for.

    Returns
    =======
    charm (str) [optional]
        The name of the charm, if the indicated application exists.
    """
    try:
        return status["applications"][app_name]["charm"]
    except KeyError:
        return


def application_to_units(
    status: JujuStatus, app_name: str
) -> Generator[str, None, None]:
    """
    Given an application name, get all of its untis, as a generator.

    Arguments
    =========
    status (JujuStatus)
        The current Juju status in json format.
    app_name (str)
        The name of the applicaiton to find a units for.

    Returns
    =======
    units (Generator[str])
        All units of the given application.
    """
    for application, data in status["applications"].items():

        if application != app_name:
            continue

        for unit_name in application["units"].keys():
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


def main(args: argparse.Namespace):
    # Perform any requested cache refresh
    if args.refresh:
        cache_juju_status()

    # Get status
    status = retrieve_juju_cache()

    # 'show' is not implemented yet
    if args.action == "show":
        raise NotImplementedError()

    assert args.object in OBJECTS

    # Get item generation function
    action = GET_MAP.get(args.object, None)
    if not action:
        raise NotImplementedError()

    # Get items of interest
    items = action(status, args.filters)
    return
    for item in items:
        print(item)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Jockey - All your Juju objects at your fingertips."
    )

    # Add cache refresh flag
    parser.add_argument(
        "--refresh", action="store_true", help="Force a cache update"
    )

    # Add object type argument
    objectparser = parser.add_mutually_exclusive_group(required=True)
    objectparser.add_argument(
        "object",
        choices=OBJECTS.keys(),
        nargs="?",
        help="Choose an object type to seek",
    )

    # Add filters as positional arguments
    filters_help = (
        "Specify filters for the query. Each filter should be in the format"
        "`key operator value`. Supported operators: = != ~."
        "For example:"
        '  app="nova-compute" principal=true hostname~ubun'
    )
    parser.add_argument(
        "filters", type=parse_filter_string, nargs="*", help=filters_help
    )

    args = parser.parse_args()
    main(args)
