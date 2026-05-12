"""Juju status loading from file, cache, or Juju CLI."""

import json
import logging
import os
import subprocess

from jockey.cache import load_cache, new_cache_context, update_cache
from jockey.types import JujuStatus


logger = logging.getLogger(__name__)


def get_juju_status(file: str = "", model_name: str = "", cache_age: int = 300) -> JujuStatus:
    """
    Loads a Juju status from a file, a Jockey cache, or the juju CLI.
    Providing a file ignores all caching.
    Loading a cache that is older than cache_age will trigger a re-caching of an
    updated Juju status.
    If model_name is not provided, it will be loaded from the JUJU_MODEL
    environment variable.

    Arguments
    =========
    file (str) [optional]
        A local file to read from.
    model_name (str) [optional]
        The name of a Juju model.
    cache_age (int) [optional]
        The maximum allowable age of a Jockey cache.
    """
    if file:
        logger.debug("Loading local Juju status from %r", file)
        with open(file, "r") as status_file:
            return json.loads(status_file.read())

    model_name = model_name or os.environ.get("JUJU_MODEL", "")
    assert model_name, "You must provide a Juju model name or have the `JUJU_MODEL` environment variable set."
    cache_context = new_cache_context(model=model_name, max_age=cache_age)

    if cache_context.valid:
        return load_cache(cache_context)

    logger.debug("Running a juju command to get status")
    status = json.loads(subprocess.run(["juju", "status", "--format", "json"], capture_output=True, text=True).stdout)
    update_cache(cache_context, status)

    return status
