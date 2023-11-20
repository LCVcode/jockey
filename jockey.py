#!/bin/python3
import argparse
import json
from status_keeper import retrieve_juju_cache, cache_juju_status
from typing import Any, Dict, NamedTuple, Generator


JUJU_OBJECTS = ("charm", "application", "unit", "machine", "ip", "hostname")


JujuStatus = Dict[str, Any]


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


def main(args: argparse.Namespace):
    # First, perform any requested cache refresh
    if args.refresh:
        cache_juju_status()
    status = retrieve_juju_cache()

    print(tuple(get_all_units(status)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Jockey - All your Juju objects at your fingertips."
    )

    parser.add_argument(
        "--refresh", action="store_true", help="Force a cache update"
    )
    verbparser = parser.add_mutually_exclusive_group(required=True)
    verbparser.add_argument(
        "action", choices=["get", "show"], nargs="?", help="Choose an action"
    )

    objectparser = parser.add_mutually_exclusive_group(required=True)
    objectparser.add_argument(
        "object",
        choices=JUJU_OBJECTS,
        nargs="?",
        help="Choose an object type to seek",
    )
    args = parser.parse_args()
    main(args)
