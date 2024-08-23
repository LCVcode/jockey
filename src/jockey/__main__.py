#!/usr/bin/env python3
"""Jockey: a Juju query language to put all of your Juju objects at your fingertips."""
from argparse import SUPPRESS, ArgumentParser, FileType, Namespace
import logging
import sys
from typing import Optional, Sequence, Union

from orjson import loads as json_loads
from rich.console import Console
from rich.logging import RichHandler
from rich.traceback import install as install_traceback
from rich_argparse import ArgumentDefaultsRichHelpFormatter

from jockey.__init__ import __issues__ as issues
from jockey.__init__ import __repository__ as repository
from jockey.__init__ import __version__ as version
from jockey.cache import DEFAULT_CACHE_BASE_PATH, FileCache
from jockey.core import (
    FilterMode,
    ObjectType,
    convert_object_abbreviation,
    filter_machines,
    filter_units,
    list_abbreviations,
    parse_filter_string,
)
from jockey.juju import Cloud


logger = logging.getLogger(__name__)

LOGGING_LEVELS = {
    0: logging.ERROR,
    1: logging.WARN,
    2: logging.INFO,
    3: logging.DEBUG,
}

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


def configure_logging(logging_level: Union[int, str, None]) -> None:
    logging.basicConfig(
        level=logging_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                console=Console(stderr=True, markup=True),
                rich_tracebacks=True,
                tracebacks_show_locals=True,
                locals_max_length=4,
                markup=True,
            )
        ],
    )
    logger.debug(
        "Logger configured with level %s",
        logging.getLevelName(logging_level or logging.NOTSET),
    )

    install_traceback(show_locals=True)
    logger.debug("Traceback handler installed.")


def parse_args(argv: Optional[Sequence[str]]) -> Namespace:
    epilog = (
        f"[grey50]Version {version}[/] | "
        f"[dark_cyan][link={repository}]{repository}[/][/] | "
        f"[dark_cyan][link={issues}]{issues}[/][/]"
    )
    parser = ArgumentParser(
        prog="jockey", description=__doc__, epilog=epilog, formatter_class=ArgumentDefaultsRichHelpFormatter
    )

    parser.add_argument("-v", "--verbose", default=0, action="count", help="increase logging verbosity")

    # Filtering
    group_filtering = parser.add_argument_group("Filtering Arguments")
    group_filtering.add_argument(
        "object",
        help="object type to query from Juju (use 'info' to see options)",
    )
    group_filtering.add_argument(
        "filters",
        type=parse_filter_string,
        nargs="*",
        default=SUPPRESS,
        help="filters to query for objects",
    )
    group_filtering.add_argument(
        "-f",
        "--file",
        type=FileType("r"),
        default=SUPPRESS,
        help="use a local Juju status JSON file",
    )

    # Remote Juju Options
    group_remote = parser.add_argument_group(
        title="Remote Juju Options", description="SSH connections to remote systems with Juju"
    )
    group_remote.add_argument(
        "-H", "--host", metavar="HOSTNAME", default=SUPPRESS, help="hostname or IP for Juju over SSH"
    )
    group_remote.add_argument("-U", "--user", metavar="USERNAME", default=SUPPRESS, help="username for Juju over SSH")

    # Cache Options
    group_cache = parser.add_argument_group("Cache Options", "Management of the local Juju object cache")
    group_cache.add_argument(
        "-c",
        "--cache",
        metavar="DIR",
        default=DEFAULT_CACHE_BASE_PATH,
        help="storage location of the local Juju object cache",
    )
    group_cache.add_argument("--refresh", action="store_true", help="clean and refresh the cache")

    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None):
    if argv is None:
        argv = sys.argv[1:]

    args = parse_args(argv)
    configure_logging(LOGGING_LEVELS[(args.verbose if "verbose" in args else 0) % len(LOGGING_LEVELS)])

    # Check if 'help' was requested
    if args.object == "info":
        print(INFO_MESSAGE)
        return

    cache = FileCache(args.cache)
    if "refresh" in args and args.refresh:
        cache.clear()
        logger.info("Cleared file cache at %s", args.cache)

    # Get status
    if "file" in args:
        status = json_loads(args.file.read())
        args.file.close()
    else:
        status = Cloud("localhost", cache=cache).juju_status()

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
    filters = args.filters if "filters" in args else []
    assert action, f"Parsing {obj_type} is not implemented."
    print(" ".join(action(status, filters)))


if __name__ == "__main__":
    main(sys.argv[1:])
