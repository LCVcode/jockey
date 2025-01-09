import logging
import os

from rich.console import Console
from rich.logging import RichHandler
from rich.traceback import install as install_traceback


DEBUG_ENV_VAR = "JOCKEY_DEBUG"


logger = logging.getLogger(__name__)


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
