#!/usr/bin/env python3
"""Jockey: a Juju query language to put all of your Juju objects at your fingertips."""
import logging
import os
from pkgutil import get_data
import sys
from typing import Dict, List, Optional, Sequence

from dotty_dictionary import Dotty  # type: ignore[import-untyped]
from orjson import loads as json_loads
from rich import print
from rich.console import Console
from rich.logging import RichHandler
from rich.markdown import Markdown
from rich.panel import Panel
from rich.traceback import install as install_traceback

from jockey.__args__ import parse_args
from jockey.cache import FileCache
from jockey.cloud import Cloud, CloudCredentialsException
from jockey.filters import parse_filter_expressions
from jockey.juju import Application, Machine, Unit
from jockey.objects import Object


logger = logging.getLogger(__name__)

DEBUG_ENV_VAR = "JOCKEY_DEBUG"
if "SNAP" in os.environ:
    os.environ["PATH"] += ":" + os.path.join(os.environ["SNAP"], "usr", "juju", "bin")


def configure_logging(verbosity: int) -> None:
    levels = {
        0: logging.ERROR,
        1: logging.WARN,
        2: logging.INFO,
        3: logging.DEBUG,
    }

    level = levels[verbosity % len(levels)]
    level_name = logging.getLevelName(level)
    handler = RichHandler(
        console=Console(stderr=True, markup=True),
        rich_tracebacks=(DEBUG_ENV_VAR in os.environ),
        tracebacks_show_locals=(DEBUG_ENV_VAR in os.environ),
        tracebacks_suppress=["paramiko", "invoke", "fabric"],
        locals_max_length=4,
        markup=True,
    )

    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[handler],
    )
    logger.debug(
        "Logger configured with level %s",
        level_name,
    )

    install_traceback(show_locals=True)
    logger.debug("Traceback handler installed.")


def info() -> Markdown:
    info_data = get_data("jockey", "info.md")
    info_data = info_data.decode("utf-8") if info_data else ""
    return Markdown(info_data)


def print_info(console: Optional[Console] = None) -> None:
    if not console:
        console = Console(width=120)

    console.print(info())


def main(argv: Optional[Sequence[str]] = None) -> int:
    # parse command-line arguments and configure logging
    if argv is None:
        argv = sys.argv[1:]

    args = parse_args(argv)
    verbosity = args.verbose if "verbose" in args else 0
    configure_logging(verbosity)
    logger.debug("Parsed command-line arguments:\n%r", args)

    # obtain OBJECT expression
    obj_expression = args.object

    # check if OBJECT is requesting the informational message
    if obj_expression == "info":
        print_info()
        return 0

    # try parsing the OBJECT expression into its components (object, field)
    try:
        obj, obj_fields = Object.parse(args.object)
        logger.debug("Parsed object expression %r into %r with fields %r", obj_expression, obj, obj_fields)
    except ValueError as e:
        logger.error("Unable to parse object expression: %s\nValid options: %s", e, Object.names())
        return 2  # usage error

    # obtain the Juju status
    if "file" in args:  # obtain the Juju status from the provided file
        status_file = args.file
        status = json_loads(status_file.read())
        status_file.close()
    else:  # obtain the Juju status from the cloud
        # configure the file cache
        cache_dir = args.cache if "cache" in args else None
        cache_age = args.cache_age if "cache_age" in args else None
        cache_refresh = args.refresh
        cache = FileCache(cache_dir, cache_age)
        if cache_refresh:
            cache.clear()
            logger.info("Cleared file cache at %s", args.cache)

        # obtain cloud configuration
        cloud_host = args.host if "host" in args else None
        cloud_user = args.user if "user" in args else None
        cloud_doas = args.sudo if "sudo" in args else None
        cloud_timeout = args.timeout if "timeout" in args else None
        cloud_juju = args.juju if "juju" in args else None

        # connect to the cloud and get the Juju status
        cloud = Cloud(host=cloud_host, user=cloud_user, doas=cloud_doas, timeout=cloud_timeout, juju=cloud_juju)

        try:
            status = cloud.juju_status
        except CloudCredentialsException as e:
            print(Panel(e.advice_markup(), title="[red]" + e.message), file=sys.stderr)
            return 126
        finally:
            cloud.close()

    # select OBJECTs from the Juju status
    selection: List[Dict] = []
    if "filters" not in args:  # select all OBJECTs in the absence of filters
        selection = obj.collect(status)
    else:  # apply filtering to OBJECTs
        # parse the filters into actions
        actions = parse_filter_expressions(args.filters)

        # collect the OBJECTs
        collection = obj.collect(status)

        # iterate over each OBJECT in the collection,
        # check all filters against it,
        # and add it to our selection if they all pass
        for item in collection:
            if all([action(item) for action in actions]):
                selection.append(item)

    for item in selection:
        if obj_fields is None:
            print(item["name"])
        elif len(obj_fields) == 1:
            if obj_fields[0] == "":
                print(item)
            else:
                print(Dotty(item, mapping_types=(dict, Application, Unit, Machine))[obj_fields[0]])
        else:
            print(
                [Dotty(item, mapping_types=(dict, Application, Unit, Machine))[obj_field] for obj_field in obj_fields]
            )

    return 0


if __name__ == "__main__":
    exit(main(sys.argv[1:]))
