#!/bin/python3
import argparse
import json
from status_keeper import retrieve_juju_cache, cache_juju_status
from typing import Any, Dict, NamedTuple, Generator


JUJU_OBJECTS = ("charm", "application", "unit", "machine", "ip", "hostname")


def pretty_print_keys(data: Dict[str, Any], depth: int = 0) -> None:
    """
    Print a dictionary's keys in a heirarchy
    """
    if depth > 3:
        return

    for key, value in data.items():
        print(" |" * depth + key)

        if isinstance(value, dict):
            pretty_print_keys(data[key], depth=depth+1)


class Unit(NamedTuple):
    name: str
    app: str
    machine: str
    charm: str


def get_unit_data(status: Dict[str, Any], unit_name: str) -> Unit:
    """
    Given a unit name, get a populated Unit object matching that unit.
    """
    # TODO: Make this handle subordinates
    app = unit_name.split("/")[0]
    machine = status["applications"][app]["units"][unit_name]["machine"]
    charm = status["applications"][app]["charm"]
    return Unit(name=unit_name, app=app, machine=machine, charm=charm)


def get_all_units(status: Dict[str, Any]) -> Generator[str, None, None]:
    """
    Get all units as a generator.
    """
    # TODO: Make this handle subordinates
    for app in status["applications"]:
        try:
            for unit_name in status["applications"][app]["units"]:
                yield get_unit_data(status, unit_name)
        except KeyError:
            continue


def main(args: argparse.Namespace):
    # First, perform any requested cache refresh
    # print(args)

    if args.refresh:
        cache_juju_status()

    status = retrieve_juju_cache()

    print(tuple(get_all_units(status)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Jockey - All your Juju objects at your fingertips.")

    parser.add_argument("--refresh", action="store_true", help="Force a cache update")

    verbparser = parser.add_mutually_exclusive_group(required=True)
    verbparser.add_argument("action", choices=["get", "show"], nargs="?", help="Choose an action")

    objectparser = parser.add_mutually_exclusive_group(required=True)
    objectparser.add_argument("object", choices=JUJU_OBJECTS, nargs="?", help="Choose an object type to seek")

    args = parser.parse_args()
    main(args)
