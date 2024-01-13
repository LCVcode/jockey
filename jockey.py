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


class Unit(NamedTuple):
    name: str
    app: str
    machine: str
    charm: str
    principal: bool


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
    """Test if a given application is principal."""
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


def get_unit_data(status: JujuStatus, unit_name: str) -> Unit:
    """
    Given a unit name, get a populated Unit object matching that unit.
    """
    app = unit_name.split("/")[0]
    charm = status["applications"][app]["charm"]
    principal = is_app_principal(status, app)

    # Determine machine number
    if principal:
        machine = status["applications"][app]["units"][unit_name]["machine"]
    else:
        p_unit = get_principal_unit_for_subordinate(status, unit_name)
        p_app = p_unit.split("/")[0]
        machine = status["applications"][p_app]["units"][p_unit]["machine"]

    return Unit(
        name=unit_name,
        app=app,
        machine=machine,
        charm=charm,
        principal=principal,
    )


def get_all_units(status: JujuStatus) -> Generator[Unit, None, None]:
    """
    Get all units as a generator.
    """
    for app in status["applications"]:

        # Skip subordinate applicaitons
        if not is_app_principal(status, app):
            continue

        for unit_name, data in status["applications"][app]["units"].items():
            # Generate principal unit
            yield get_unit_data(status, unit_name)

            # Check if subordinate units exist
            if "subordinates" not in data:
                continue

            # Generate subordinate units
            for s_unit_name in data["subordinates"]:
                yield get_unit_data(status, s_unit_name)


def get_filtered_units(
    status: JujuStatus, filters: List[Tuple[str, str, str]]
) -> Generator[Unit, None, None]:
    """
    Get all units that satisfy a set of filters.
    """
    unit_filter_map = {
        "charm": None,
        "application": None,
        "machine": None,
        "ip": None,
        "hostname": None,
    }
    for unit in get_all_units(status):
        for key, operator, value in filters:
            print(key, operator, value)


GET_MAP = {"unit": get_filtered_units}


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
