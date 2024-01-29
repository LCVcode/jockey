#!/bin/python3
# Jockey is a CLI utility that facilitates quick retrieval of Juju objects that
# match given filters.
# Author: Connor Chamberlain

import argparse
import json
import re
from enum import Enum
from typing import Any, Dict, NamedTuple, Generator, Optional, List, Tuple

from status_keeper import (
    retrieve_juju_cache,
    cache_juju_status,
    read_local_juju_status_file,
)


JujuStatus = Dict[str, Any]


class FilterMode(Enum):
    EQUALS = "="
    NOT_EQUALS = "!="
    CONTAINS = "~"
    NOT_CONTAINS = "!~"


OBJECTS = {
    "charm": ("charms", "c"),
    "application": ("app", "apps", "applications", "a"),
    "unit": ("units", "u"),
    "machine": ("machines", "m"),
    "ip": ("address", "addresses", "ips", "i"),
    "hostname": ("hostnames", "host", "hosts", "h"),
}


def pretty_print_keys(data: JujuStatus, depth: int = 1) -> None:
    """Print a dictionary's keys in a heirarchy."""
    if depth < 1:
        return

    for key, value in data.items():
        print(" |" * depth + key)

        if isinstance(value, dict):
            pretty_print_keys(data[key], depth=depth - 1)


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


def parse_filter_string(
    filter_str: str,
) -> Tuple[str, FilterMode, str]:
    """
    Parse a filter string down into its object type, filter mode, and content.

    Arguments
    =========
    filter_str (str)
        The filter string.

    Returns
    =======
    object_type (str)
        The object type of the filter.  May be "charm", "application", "unit",
        "machine", "ip", or "hostname".
    mode (FilterMode)
        FilterMode of the filter.
    content (str)
        Content of the filter string, which may be any string that doesn't
        include blacklisted characters.
    """

    filter_code_pattern = re.compile(r"[=!~]+")

    filter_codes = filter_code_pattern.findall(filter_str)
    assert len(filter_codes) == 1, "Incorrect number of filter codes detected."

    match = filter_code_pattern.search(filter_str)

    object_type = convert_object_abbreviation(filter_str[: match.start()])
    assert object_type, "Invalid object type detected in filter string."

    filter_mode = next(
        (mode for mode in FilterMode if mode.value == match.group()), None
    )
    assert filter_mode, f"Invalid filter mode detected: {match.group()}."

    content = filter_str[match.end() :]
    assert content, "Empty content detected in filter string."

    char_blacklist = ("_", ":", ";", "\\", "\t", "\n", ",")
    assert not any(
        char in char_blacklist for char in content
    ), "Blacklisted characters detected in filter string content."

    return object_type, filter_mode, content


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
    Given an application name, get all of its untis, as a generator.  If no
    matching application is found, the generator will be empty.

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


def unit_to_machine(status: JujuStatus, unit_name: str) -> Optional[str]:
    """
    Given a unit name, get the ID of the machine it is running on, if any.

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


def main(args: argparse.Namespace):
    # Perform any requested cache refresh
    if args.refresh:
        cache_juju_status()

    # Get status
    status = (
        retrieve_juju_cache()
        if not args.file
        else read_local_juju_status_file(args.file)
    )

    pretty_print_keys(status)


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
        "  app=nova-compute hostname~ubun"
    )
    parser.add_argument(
        "filters", type=parse_filter_string, nargs="*", help=filters_help
    )

    # Optional import from a json file
    parser.add_argument(
        "-f",
        "--file",
        type=argparse.FileType("r"),
        help="Use a local Juju status JSON file",
    )

    args = parser.parse_args()
    main(args)
