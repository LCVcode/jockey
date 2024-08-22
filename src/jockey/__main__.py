#!/usr/bin/env python3
"""Jockey: a Juju query language to put all of your Juju objects at your fingertips."""
from argparse import ArgumentParser, FileType, Namespace
import sys
from typing import Optional, Sequence

from jockey.__init__ import __version__ as version
from jockey.core import (
    FilterMode,
    ObjectType,
    convert_object_abbreviation,
    filter_machines,
    filter_units,
    list_abbreviations,
    parse_filter_string,
)
from jockey.status_keeper import cache_juju_status, read_local_juju_status_file, retrieve_juju_cache

from jockey.juju import Cloud

INFO_MESSAGE = f"""
+----+
|NOTE|
+----+
Jockey is a work-in-progress currently only supports querying:
    units
    machines


+-------+
|FILTERS|
+-------+
Filters have a three-part syntax:
    <object type><filter code><content>

<object type> can be any supported Juju object types or their equivalent
abbreviations (see "SHORT NAMES", below).  These values are identical to the
`object` argument in the Jockey CLI.

<filter code> specifies how objects should be filtered relative to <content>
There are four possible values for <filter code>:
    {FilterMode.EQUALS.value.ljust(3)}: matches
    {FilterMode.NOT_EQUALS.value.ljust(3)}: does not match
    {FilterMode.CONTAINS.value.ljust(3)}: contains
    {FilterMode.NOT_CONTAINS.value.ljust(3)}: does not contain
Exactly one <filter code> must be given per filter.

<content> is a given string that will be used to filter Juju object names.


+-----------+
|SHORT NAMES|
+-----------+
Jockey object name abbreviations:

{list_abbreviations()}


+---------------+
|EXAMPLE QUERIES|
+---------------+
 Get all units:
     jockey units

 Get all nova-compute units:
     jockey units application=nova-compute

 Get the hw-health unit on a machine with a partial hostname "e01":
    jockey u a=hw-health host~e01

 Get all non-lxd machines:
     jockey m m^~lxd


+-------------------+
|OPERATIONS EXAMPLES|
+-------------------+
 Run a 'show-sel' action a machine with a partial host name 'ts1363co':
     juju run-action --wait $(jockey u a~hw-hea m~ts1363co) show-sel
"""


def parse_args(argv: Optional[Sequence[str]]) -> Namespace:
    parser = ArgumentParser(prog="jockey", description=__doc__, epilog=f"Version {version}")

    # Add cache refresh flag
    parser.add_argument("--refresh", action="store_true", help="Force a cache update")

    # Add object type argument
    parser.add_argument(
        "object",
        help="Choose an object type to query or 'info'",
    )

    # Add filters as positional arguments
    parser.add_argument(
        "filters",
        type=parse_filter_string,
        nargs="*",
        help="Specify filters for your query.",
    )

    # Optional import from a json file
    parser.add_argument(
        "-f",
        "--file",
        type=FileType("r"),
        help="Use a local Juju status JSON file",
    )

    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None):
    if argv is None:
        argv = sys.argv[1:]

    args = parse_args(argv)

    # Check if 'help' was requested
    if args.object == "info":
        print(INFO_MESSAGE)
        return

    # Perform any requested cache refresh
    if args.refresh:
        cache_juju_status()

    # Get status
    status = Cloud("localhost").juju_status()

        # TODO: replicate:
        # read_local_juju_status_file(args.file))

    RETRIEVAL_MAP = {
        ObjectType.CHARM: None,
        ObjectType.APP: None,
        ObjectType.UNIT: filter_units,
        ObjectType.MACHINE: filter_machines,
        ObjectType.IP: None,
        ObjectType.HOSTNAME: None,
    }

    obj_type = convert_object_abbreviation(args.object)
    assert obj_type, f"'{args.object}' is not a valid object type."

    action = RETRIEVAL_MAP[obj_type]
    assert action, f"Parsing {obj_type} is not implemented."
    print(" ".join(action(status, args.filters)))


if __name__ == "__main__":
    main(sys.argv[1:])
