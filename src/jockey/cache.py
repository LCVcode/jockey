"""
This module provides a simple caching solutin of Juju statuses in JSON format.
"""

from dataclasses import dataclass
import json
import os
from typing import Any, Dict


DEFAULT_DIR = os.path.expanduser("~/.local/share/jockey")
DEFAULT_MAX_AGE = 300  # Default cache max age is five minutes


@dataclass(frozen=True)
class CacheContext:
    """
    This data class caputes information to identify unique caches.
    """

    cache_dir: str  # Path to cache directory
    juju_model: str  # Juju model name
    max_age: int  # Max age, in seconds

    @property
    def cache_path(self) -> str:
        """
        The fully qualified path to the Jockey cache.
        """
        return os.path.join(self.cache_dir, f"cache_{self.juju_model}.json")

    @property
    def valid(self) -> bool:
        """
        Check if the cache exists and is current.  Returns False if the cache
        needs to be refreshed.
        """
        if not os.path.exists(self.cache_path):
            return False

        return os.path.getmtime(self.cache_path) < self.max_age


def new_cache_context(model: str, dir_name: str = "", max_age: int = 0) -> CacheContext:
    """
    Factory function for CacheContexts.  Has default values for the cache directory and max age.

    Arguments
    ---------
    model    (str)
        Juju model name.
    dir_name (str) [optional]
        The cache directory.  Must be used if `path` is not provided.
    max_age  (int) [optional]
        The maximum age of the cache, in seconds.  Uses a default when not
        provided.

    Returns
    -------
    context (CacheContext)
        CacheContext object for this Jockey cache.
    """
    return CacheContext(cache_dir=dir_name or DEFAULT_DIR, juju_model=model, max_age=max_age or DEFAULT_MAX_AGE)


def update_cache(context: CacheContext, data: Dict[str, Any]) -> None:
    """
    Write new data to a Jockey cache.

    Arguments
    ---------
    context (CacheContext)
        The Jockey cache context to use.
    data    (Dict[str, Any])
        Any JSON-like data to write to the cache.
    """
    # Create any required directories
    os.makedirs(os.path.dirname(context.cache_path), exist_ok=True)

    # Write data to the cache file
    with open(context.cache_path, "w") as f:
        json.dump(data, f)


def load_cache(context: CacheContext) -> Dict[str, Any]:
    """
    Loads a Jockey cache, regardless of its age.

    Raises and AssertionError if the cache is not found.

    Arguments
    ---------
    context (CacheContext)
        The Jockey cache context to use.

    Returns
    -------
    data    (Dict[str, Any])
        The loaded Jockey cache.
    """
    assert os.path.exists(context.cache_path)

    with open(context.cache_path, "r") as f:
        return json.load(f)
