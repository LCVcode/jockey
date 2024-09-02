import datetime
import json
import os
import subprocess
from typing import Any, Dict, TextIO

from xdgenvpy import XDGPedanticPackage


JOCKEY_XDG = XDGPedanticPackage('jockey')
CACHE_PATH = os.path.join(JOCKEY_XDG.XDG_CACHE_HOME, 'cache.json')
CONFIG_PATH = os.path.join(JOCKEY_XDG.XDG_CONFIG_HOME, 'config.json')


def get_current_juju_status_json() -> str:
    """
    Use the Juju CLI to get the current Juju status.
    """
    cmd = ['juju', 'status', '--format', 'json']
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        return result.stdout
    else:
        raise Exception('Juju status command failed.')


def cache_juju_status() -> None:
    """
    Cache the current Juju status in json format.  Creates the jockey directory
    if it does not already exist.
    """
    status = get_current_juju_status_json()
    with open(CACHE_PATH, 'w') as file:
        file.write(status)


def is_cache_update_needed() -> bool:
    """
    Check if the Juju cache needs to be generated or regenerated.  Returns True
    if the cache file does not exist or if it has not been altered in more than
    300 seconds.
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
    Retrieve the cached Juju status.  This will create or refresh the cash, if
    needed.
    """
    if is_cache_update_needed():
        cache_juju_status()

    with open(CACHE_PATH, 'r') as file:
        status = json.loads(file.read())

    return status


def read_local_juju_status_file(file: TextIO) -> Dict[str, Any]:
    """
    Import Juju status from a local JSON file.
    """
    filepath = os.path.abspath(file.name)
    with open(filepath, 'r') as file:
        status = json.loads(file.read())

    return status
