from datetime import datetime
import os
from typing import Any, Callable, NamedTuple, Optional

from orjson import dumps as json_dumps
from orjson import loads as json_loads
from slugify import slugify
from xdgenvpy import XDGPedanticPackage


JOCKEY_XDG = XDGPedanticPackage("jockey")
"""An instance of :mod:`xdgenvpy.XDGPedanticPackage` used to manage XDG directories for Jockey."""

DEFAULT_CACHE_BASE_PATH = JOCKEY_XDG.XDG_CACHE_HOME
"""The default base path for cache files, derived using :obj:`JOCKEY_XDG`."""

DEFAULT_CACHE_MAX_AGE: float = 300
"""The default maximum age, in seconds, for cache entries before they are considered expired."""


class Reference(NamedTuple):
    """
    Represents a unique identifier for a cache entry,
    based on the *cloud*, *controller*, *model*, and *component*.
    """

    cloud: str
    """The cloud environment (e.g., bastion host, or `"localhost"`)."""

    controller: str
    """The Juju controller identifier."""

    model: str
    """The Juju model identifier."""

    component: str
    """The Juju component (e.g., "status")."""

    def __str__(self) -> str:
        cloud = slugify(self.cloud)
        controller = slugify(self.controller)
        model = slugify(self.model)
        component = slugify(self.component)
        return f"{cloud}_{controller}_{model}_{component}"

    def __repr__(self) -> str:
        return f"Reference('{self.cloud}', '{self.controller}', '{self.model}', '{self.component}')"

    def to_file_name(self, extension="json") -> str:
        """
        Generates a file name for the reference with the given *extension*.

        :param extension: The file extension appended to the file name.
        :return: A file name for the reference.
        """
        return self.__str__() + "." + extension


class FileCache:
    """Represents an interactive cache using JSON files for Juju objects."""

    base_path: str
    """The base directory where cache files are stored."""

    max_age: float
    """The maximum age, in seconds, for cache entries before they are considered expired."""

    def __init__(self, base_path: Optional[str] = None, max_age: Optional[float] = None):
        self.base_path = base_path if base_path else DEFAULT_CACHE_BASE_PATH
        self.max_age = max_age if max_age else DEFAULT_CACHE_MAX_AGE

    def __repr__(self) -> str:
        return f"FileCache({self.base_path}, max_age={self.max_age})"

    def clear(self):
        """Clears all cache entries from the base directory."""
        for entry in os.listdir(self.base_path):
            file_path = os.path.join(self.base_path, entry)
            if os.path.isfile(file_path):
                os.remove(file_path)

    @staticmethod
    def reference_for(cloud: str, controller: str, model: str, component: str) -> Reference:
        """
        Creates a :class:`Reference` object for the specified *cloud*, *controller*, *model*, *component*.

        :param cloud: The cloud environment (e.g., bastion host, or `"localhost"`).
        :param controller: The Juju controller identifier.
        :param model: The Juju model identifier.
        :param component: The Juju component (e.g., "status").
        :return: A :class:`Reference` object.
        """
        return Reference(cloud, controller, model, component)

    def file_path_for(self, ref: Reference) -> str:
        """
        Returns the path to the entry file for the specified :class:`Reference`.

        :param ref: The :class:`Reference` object to generate the file path for.
        :return: The full path to the file corresponding to the given :class:`Reference` *ref*.
        """
        return os.path.join(self.base_path, ref.to_file_name())

    def has(self, ref: Reference) -> bool:
        """
        Checks whether an entry exists in the file system.

        :param ref: The :class:`Reference` object to check.
        :return: Whether the entry exists in the file system.
        """
        return os.path.exists(self.file_path_for(ref))

    def read(self, ref: Reference) -> Any:
        """
        Reads the deserialized JSON content from a specific entry file.

        :param ref: The :class:`Reference` object to read the data for.
        :return: The content of the specified :class:`Reference` *ref*.
        """
        with open(self.file_path_for(ref), "rb") as f:
            return json_loads(f.read())

    def write(self, ref: Reference, data: Any) -> None:
        """
        Writes a serialized JSON data entry to a file.

        :param ref: The :class:`Reference` object to write the data for.
        :param data: The JSON data as a Python object.
        """
        with open(self.file_path_for(ref), "wb") as f:
            f.write(json_dumps(data))

    def delete(self, ref: Reference) -> None:
        """
        Deletes an entry from the file system.

        :param ref: The :class:`Reference` object to delete the data for.
        """
        os.remove(self.file_path_for(ref))

    def entry_or(self, ref: Reference, cb: Callable[[], Any]) -> Any:
        """
        Retrieves data from a cache or computes and caches the data if it is not already present.

        - If the data is already present in the cache and is not expired, the method returns the cached data.
        - If the data is not present in the cache or is expired, the method calls the provided callable function
          *cb* to compute the data, caches the computed data, and returns the computed data.

        :param ref: The :class:`Reference` object to retrieve or compute the data for.
        :param cb: The callable function to compute the data.
        :return: The cached or newly computed data.
        """
        if self.is_expired(ref):
            data = cb()
            self.write(ref, data)
            return data
        else:
            return self.read(ref)

    def last_modified(self, ref: Reference) -> float:
        """
        Get the last modified timestamp of a specific entry file in the file system.

        :param ref: The :class:`Reference` object to get the last modified timestamp for.
        :return: The last modified timestamp in seconds since the epoch.
        """
        return os.path.getmtime(self.file_path_for(ref))

    def age(self, ref: Reference) -> float:
        """
        Calculate the age of an entry by subtracting the last modified timestamp of the entry from
        the current timestamp.

        :param ref: The :class:`Reference` object to calculate the age for.
        :return: The age of the entry in seconds.
        """
        return datetime.now().timestamp() - self.last_modified(ref)

    def is_expired(self, ref: Reference, max_age: Optional[float] = None) -> bool:
        """
        Check if an entry is expired based on its age.

        :param ref: The :class:`Reference` object to check.
        :param max_age: The maximum age, in seconds. If not provided, the instance's :attr:`max_age` will be used.
        :return: Whether the entry is expired or doesn't exist.
        """
        return not self.has(ref) or self.age(ref) > (max_age or self.max_age or 300)
