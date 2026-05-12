"""Juju status loading and projection for active query paths."""

import json
import logging
import os
import subprocess
from typing import Any, Dict

from jockey.cache import load_cache, new_cache_context, update_cache
from jockey.types import JujuStatus


logger = logging.getLogger(__name__)


def _project_unit_status(unit_data: Dict[str, Any]) -> Dict[str, Any]:
    projected_unit: Dict[str, Any] = {}

    if "machine" in unit_data:
        projected_unit["machine"] = unit_data["machine"]

    raw_subordinates = unit_data.get("subordinates", {})
    projected_unit["subordinates"] = {
        subordinate_name: {} for subordinate_name in raw_subordinates
    }

    return projected_unit


def _project_status(raw_status: Dict[str, Any]) -> JujuStatus:
    projected_applications: Dict[str, Dict[str, Any]] = {}
    for app_name, app_data in raw_status.get("applications", {}).items():
        projected_app: Dict[str, Any] = {}

        if "charm" in app_data:
            projected_app["charm"] = app_data["charm"]
        if "subordinate-to" in app_data:
            projected_app["subordinate-to"] = app_data["subordinate-to"]
        if "units" in app_data:
            projected_app["units"] = {
                unit_name: _project_unit_status(unit_data)
                for unit_name, unit_data in app_data["units"].items()
            }

        projected_applications[app_name] = projected_app

    projected_machines: Dict[str, Dict[str, Any]] = {}
    for machine_name, machine_data in raw_status.get("machines", {}).items():
        projected_machine: Dict[str, Any] = {}

        if "hostname" in machine_data:
            projected_machine["hostname"] = machine_data["hostname"]
        if "ip-addresses" in machine_data:
            projected_machine["ip-addresses"] = machine_data["ip-addresses"]
        if "hardware" in machine_data:
            projected_machine["hardware"] = machine_data["hardware"]
        if "containers" in machine_data:
            projected_machine["containers"] = {
                container_name: {
                    key: container_data[key]
                    for key in ("hostname", "ip-addresses")
                    if key in container_data
                }
                for container_name, container_data in machine_data["containers"].items()
            }

        projected_machines[machine_name] = projected_machine

    return {
        "applications": projected_applications,
        "machines": projected_machines,
    }


def get_juju_status(file: str = "", model_name: str = "", cache_age: int = 300) -> JujuStatus:
    """
    Load Juju status from a file, cache, or the juju CLI.
    The returned status is projected to only the fields required by currently
    supported query filters.

    Providing a file ignores all caching.
    A cache that fails the cache validity check will trigger a refreshed status.
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
            return _project_status(json.loads(status_file.read()))

    model_name = model_name or os.environ.get("JUJU_MODEL", "")
    assert model_name, "You must provide a Juju model name or have the `JUJU_MODEL` environment variable set."
    cache_context = new_cache_context(model=model_name, max_age=cache_age)

    if cache_context.valid:
        return _project_status(load_cache(cache_context))

    logger.debug("Running a juju command to get status")
    status = _project_status(
        json.loads(
            subprocess.run(
                ["juju", "status", "--format", "json"],
                capture_output=True,
                text=True,
            ).stdout
        )
    )
    update_cache(cache_context, status)

    return status
