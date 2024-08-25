from datetime import datetime
import os
from typing import Any, Callable, Optional, Union

from orjson import dumps as json_dumps
from orjson import loads as json_loads
from slugify import slugify
from xdgenvpy import XDGPedanticPackage


JOCKEY_XDG = XDGPedanticPackage("jockey")

DEFAULT_CACHE_BASE_PATH = JOCKEY_XDG.XDG_CACHE_HOME
DEFAULT_CACHE_MAX_AGE: float = 300


class FileCache:
    """A class representing a file cache."""

    base_path: str
    max_age: float

    def __init__(self, base_path: Optional[str] = None, max_age: Optional[float] = None):
        self.base_path = base_path if base_path else DEFAULT_CACHE_BASE_PATH
        self.max_age = max_age if max_age else DEFAULT_CACHE_MAX_AGE

    def __repr__(self) -> str:
        return f"FileCache({self.base_path}, max_age={self.max_age})"

    def clear(self):
        for entry in os.listdir(self.base_path):
            file_path = os.path.join(self.base_path, entry)
            if os.path.isfile(file_path):
                os.remove(file_path)

    @staticmethod
    def entry_file_name(cloud: str, controller: str, model: str, component: str) -> str:
        """A static method that generates a formatted entry file name."""
        cloud = slugify(cloud)
        controller = slugify(controller)
        model = slugify(model)
        component = slugify(component)

        return f"{cloud}_{controller}_{model}_{component}.json"

    def entry_file_path(self, cloud: str, controller: str, model: str, component: str) -> str:
        """Returns the path to the entry file for the specified cloud, controller, model, and component."""
        return os.path.join(self.base_path, self.entry_file_name(cloud, controller, model, component))

    def has_entry(self, cloud: str, controller: str, model: str, component: str) -> bool:
        """Checks whether an entry exists in the file system."""
        return os.path.exists(self.entry_file_path(cloud, controller, model, component))

    def read_entry(self, cloud: str, controller: str, model: str, component: str) -> Any:
        """Reads the content from a specific entry file."""
        with open(self.entry_file_path(cloud, controller, model, component), "rb") as f:
            return json_loads(f.read())

    def write_entry(self, cloud: str, controller: str, model: str, component: str, data: Any) -> None:
        """Writes a serialized JSON data entry to a file."""
        with open(self.entry_file_path(cloud, controller, model, component), "wb") as f:
            f.write(json_dumps(data))

    def delete_entry(self, cloud: str, controller: str, model: str, component: str) -> None:
        """Deletes an entry from the file system."""
        os.remove(self.entry_file_path(cloud, controller, model, component))

    def entry_or(self, cloud: str, controller: str, model: str, component: str, cb: Callable[[], Any]) -> Any:
        """Retrieves data from a cache or computes and caches the data if it is not already present.

        - If the data is already present in the cache and is not expired, the method returns the cached data.
        - If the data is not present in the cache or is expired, the method calls the provided callable function
          `cb` to compute the data, caches the computed data, and returns the computed data.
        """
        if self.entry_expired(cloud, controller, model, component):
            data = cb()
            self.write_entry(cloud, controller, model, component, data)
            return data
        else:
            return self.read_entry(cloud, controller, model, component)

    def entry_last_modified(self, cloud: str, controller: str, model: str, component: str) -> float:
        """Get the last modified timestamp of a specific entry file in the file system."""
        return os.path.getmtime(self.entry_file_path(cloud, controller, model, component))

    def entry_age(self, cloud: str, controller: str, model: str, component: str) -> float:
        """Calculate the age of an entry by subtracting the last modified timestamp of the entry from the
        current timestamp."""
        return datetime.now().timestamp() - self.entry_last_modified(cloud, controller, model, component)

    def entry_expired(
        self, cloud: str, controller: str, model: str, component: str, max_age: Optional[float] = None
    ) -> bool:
        """Check if an entry is expired based on its age."""
        return not self.has_entry(cloud, controller, model, component) or self.entry_age(
            cloud, controller, model, component
        ) > (max_age or self.max_age or 300)
