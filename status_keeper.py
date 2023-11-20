import datetime
import json
import os
import subprocess
from typing import Any, Dict


JOCKEY_PATH = os.path.expanduser("~/.jockey/")
CACHE_PATH = f"{JOCKEY_PATH}cache.json"
CONFIG_PATH = f"{JOCKEY_PATH}jockey.conf"


def get_current_juju_status_json() -> str:
    """
    Use the Juju CLI to get the current Juju status.
    """
    cmd = ["juju", "status", "--format", "json"]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        return result.stdout
    else:
        raise Exception("Juju status command failed.")
    return ""


def cache_juju_status() -> None:
    """
    Cache the current Juju status in json format.
    """
    if not os.path.exists(JOCKEY_PATH):
        os.makedirs(JOCKEY_PATH)

    status = get_current_juju_status_json()
    with open(CACHE_PATH, 'w') as file:
        file.write(status)


def cache_regeneration_needed() -> bool:
    """
    Check if the Juju cache needs to be generated or regenerated.
    """
    if not os.path.exists(CACHE_PATH):
        return True

    current_time = datetime.datetime.now().timestamp()
    last_modified_time = os.path.getmtime(CACHE_PATH)
    if current_time - last_modified_time > 300:
        return True

    return False


def retrieve_juju_cache() -> Dict[str, Any]:
    """
    Get the cached juju status.  Will regenerate cache if needed.
    """
    if cache_regeneration_needed():
        cache_juju_status()

    with open(CACHE_PATH, "r") as file:
        status = json.loads(file.read())

    return status

