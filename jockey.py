#!/bin/python3
import argparse
import json
import re
from status_keeper import retrieve_juju_cache, cache_juju_status
from typing import Any, Dict, NamedTuple, Generator, Optional


JujuStatus = Dict[str, Any]


JUJU_OBJECTS = {
    "charm": ("charms",),
    "application": ("app", "apps", "applications"),
    "unit": ("units",),
    "machine": ("machines",),
    "ip": ("address", "addresses", "ips"),
    "hostname": ("hostnames", "host", "hosts"),
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


def format_juju_object_name(name: str) -> Optional[str]:
    """
    Convert the name of an object type to a uniform format.  If the object type
    is not a valid Juju object, None will be returned.
    """
    name = name.lower()
    if name in JUJU_OBJECTS:
        return name

    for obj_name, alternatives in JUJU_OBJECTS.items():
        if name in alternatives:
            return obj_name


def parse_filter(filter_str):
    """Parse a single filter string into a tuple (key, operator, value)."""
    filter_pattern = re.compile(r'(\w+)\s*([=~]|!=)\s*("[^"]+"|[\w\/.-]+)')
    match = filter_pattern.match(filter_str)
    if match:
        key, operator, value = match.groups()
        key = format_juju_object_name(key)
        assert key is not None
        value = value.strip('"')
        return key, operator, value
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


def get_all_units(status: JujuStatus) -> Generator[str, None, None]:
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


GET_MAP = {"unit": get_all_units}


def main(args: argparse.Namespace):
    print(args.filters)
    # Perform any requested cache refresh
    if args.refresh:
        cache_juju_status()

    # Get status
    status = retrieve_juju_cache()

    # 'show' is not implemented yet
    if args.action == "show":
        raise NotImplementedError()

    assert args.object in JUJU_OBJECTS

    # Get item generation function
    action = GET_MAP.get(args.object, None)
    if not action:
        raise NotImplementedError()

    # Get items of interest
    items = action(status)
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

    # Add verb argument
    verbparser = parser.add_mutually_exclusive_group(required=True)
    verbparser.add_argument(
        "action", choices=["get", "show"], nargs="?", help="Choose an action"
    )

    # Add object type argument
    objectparser = parser.add_mutually_exclusive_group(required=True)
    objectparser.add_argument(
        "object",
        choices=JUJU_OBJECTS.keys(),
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
        "filters", type=parse_filter, nargs="*", help=filters_help
    )

    args = parser.parse_args()
    main(args)
