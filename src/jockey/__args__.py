from argparse import SUPPRESS, ArgumentParser, FileType, Namespace
from logging import getLogger
from typing import Optional, Sequence


logger = getLogger(__name__)

from rich_argparse import ArgumentDefaultsRichHelpFormatter as ArgumentDefaultsHelpFormatter

from jockey import __issues__, __repository__, __version__


epilog = (
    f"[grey50]Version {__version__}[/] | "
    f"[dark_cyan][link={__repository__}]{__repository__}[/][/] | "
    f"[dark_cyan][link={__issues__}]{__issues__}[/][/]"
)


# TODO: ORIGINALLY PART OF INFO
# examples = """
# Examples:
#   %(prog)s units                            get all units
#   %(prog)s units application=nova-compute   get all `nova-compute` units
#   %(prog)s u a=hw-health host~e01           get all `hw-health` units on hostname like "e01"
#   %(prog)s m m^~lxd                         get all non-LXD machines
#
# """


def get_parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog="jockey", description=__doc__, epilog=epilog, formatter_class=ArgumentDefaultsHelpFormatter
    )

    parser.add_argument("-v", "--verbose", default=0, action="count", help="increase logging verbosity")

    # Filtering
    group_filtering = parser.add_argument_group("Filtering Arguments")
    group_filtering.add_argument(
        "object",
        metavar="OBJECT",
        help="object type to query from Juju (use 'info' to see options)",
    )
    group_filtering.add_argument(
        "filters",
        metavar="EXPRESSION",
        type=str,
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
    group_remote.add_argument(
        "-S", "--sudo", metavar="USERNAME", default=None, help="username of sudoer to run commands"
    )
    group_remote.add_argument(
        "-T", "--timeout", metavar="SEC", default=SUPPRESS, help="timeout for commands and connections"
    )
    group_remote.add_argument("-J", "--juju", metavar="COMMAND", default=SUPPRESS, help="name of the Juju command")

    # Cache Options
    group_cache = parser.add_argument_group("Cache Options", "Management of the local Juju object cache")
    group_cache.add_argument(
        "-c",
        "--cache",
        metavar="DIR",
        type=str,
        default=SUPPRESS,
        help="storage location of the local Juju object cache",
    )
    group_cache.add_argument(
        "-C",
        "--cache-age",
        metavar="SEC",
        type=float,
        default=SUPPRESS,
        help="maximum cache age in seconds",
    )
    group_cache.add_argument("--refresh", action="store_true", help="clean and refresh the cache")

    return parser


def parse_args(argv: Optional[Sequence[str]]) -> Namespace:
    return get_parser().parse_args(argv)
