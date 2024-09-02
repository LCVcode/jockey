from datetime import datetime
import os
from typing import Any, Callable, NamedTuple, Optional, Union

from orjson import dumps as json_dumps
from orjson import loads as json_loads
from slugify import slugify
from xdgenvpy import XDGPedanticPackage


JOCKEY_XDG = XDGPedanticPackage("jockey")

DEFAULT_CACHE_BASE_PATH = JOCKEY_XDG.XDG_CACHE_HOME
DEFAULT_CACHE_MAX_AGE: float = 300


class Reference(NamedTuple):
    cloud: str
    controller: str
    model: str
    component: str

    def __str__(self) -> str:
        cloud = slugify(self.cloud)
        controller = slugify(self.controller)
        model = slugify(self.model)
        component = slugify(self.component)
        return f"{cloud}_{controller}_{model}_{component}"

    def __repr__(self) -> str:
        return f"Reference('{self.cloud}', '{self.controller}', '{self.model}', '{self.component}')"

    def to_file_name(self, ext="json") -> str:
        return self.__str__() + "." + ext


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
    def reference_for(cloud: str, controller: str, model: str, component: str) -> Reference:
        return Reference(cloud, controller, model, component)

    def file_path_for(self, ref: Reference) -> str:
        """Returns the path to the entry file for the specified `Reference`."""
        return os.path.join(self.base_path, ref.to_file_name())

    def has(self, ref: Reference) -> bool:
        """Checks whether an entry exists in the file system."""
        return os.path.exists(self.file_path_for(ref))

    def read(self, ref: Reference) -> Any:
        """Reads the content from a specific entry file."""
        with open(self.file_path_for(ref), "rb") as f:
            return json_loads(f.read())

    def write(self, ref: Reference, data: Any) -> None:
        """Writes a serialized JSON data entry to a file."""
        with open(self.file_path_for(ref), "wb") as f:
            f.write(json_dumps(data))

    def delete(self, ref: Reference) -> None:
        """Deletes an entry from the file system."""
        os.remove(self.file_path_for(ref))

    def entry_or(self, ref: Reference, cb: Callable[[], Any]) -> Any:
        """Retrieves data from a cache or computes and caches the data if it is not already present.

        - If the data is already present in the cache and is not expired, the method returns the cached data.
        - If the data is not present in the cache or is expired, the method calls the provided callable function
          `cb` to compute the data, caches the computed data, and returns the computed data.
        """
        if self.is_expired(ref):
            data = cb()
            self.write(ref, data)
            return data
        else:
            return self.read(ref)

    def last_modified(self, ref: Reference) -> float:
        """Get the last modified timestamp of a specific entry file in the file system."""
        return os.path.getmtime(self.file_path_for(ref))

    def age(self, ref: Reference) -> float:
        """Calculate the age of an entry by subtracting the last modified timestamp of the entry from the
        current timestamp."""
        return datetime.now().timestamp() - self.last_modified(ref)

    def is_expired(self, ref: Reference, max_age: Optional[float] = None) -> bool:
        """Check if an entry is expired based on its age."""
        return not self.has(ref) or self.age(ref) > (max_age or self.max_age or 300)
