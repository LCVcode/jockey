"""
This module defines a framework for collecting and working with different types of Juju objects, such as applications,
units, and machines. It leverages the Juju :class:`full_status.FullStatus` data structure to extract and manage these
objects through enumerated types and associated collectors.

Examples
--------
.. code-block:: python
    :linenos:

    from jockey.objects import Object

    # parse an object expression
    obj_type, obj_field = Object.parse("application.name")

    # collect all applications from the Juju status
    status = { "applications": { "a": {}, "b": {} } }
    applications = obj_type.collect(status)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Iterable, Optional

from jockey.juju import all_applications, all_machines, all_units
from jockey.juju_schema.full_status import FullStatus


ObjectCollector = Callable[[FullStatus], Iterable[Any]]
"""A type alias representing a function that collects objects from the Juju :class:`full_status.FullStatus`."""


@dataclass
class ObjectType:
    """Represents a Juju object type with its associated collector function and possible names."""

    names: set[str]
    """A set of strings representing the possible names or aliases of the Juju object."""

    collector: ObjectCollector
    """An :type:`ObjectCollector` that collects the objects of this type from a :class:`full_status.FullStatus`."""


class Object(Enum):
    """An enumeration of different Juju object types, such as applications, units, and machines."""

    APPLICATION = ObjectType({"applications", "app", "apps", "application", "a"}, all_applications)
    """Represents Juju applications and their associated collector."""

    UNIT = ObjectType({"units", "unit", "u"}, all_units)
    """Represents Juju units and their associated collector."""

    MACHINE = ObjectType({"machines", "machine", "m"}, all_machines)
    """Represents Juju machines and their associated collector."""

    def __str__(self) -> str:
        return self.name.lower()

    def __repr__(self) -> str:
        return f"Object.{self.name}"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Object):
            return self.name == other.name
        return False

    def __ne__(self, other: object) -> bool:
        if isinstance(other, Object):
            return self.name != other.name
        return True

    def __hash__(self) -> int:
        return hash(self.name)

    @staticmethod
    def tokens() -> set[str]:
        """
        Retrieves all possible tokens (names / aliases) associated with the defined Juju object types.

        :return: A set of all tokens corresponding to the Juju object types.
        """

        return {token for obj in Object for token in obj.value.names}

    @staticmethod
    def names() -> set[str]:
        """
        Retrieves all names associated with the defined Juju object types.

        :return: A set of all names associated with the Juju object types.
        """
        return {str(obj) for obj in Object}

    @staticmethod
    def from_str(obj_name: str) -> "Object":
        """
        Converts a string representation of a Juju object type into its corresponding :class:`Object`.

        :param obj_name: The string representation of a Juju object type.
        :return: The corresponding :class:`Object`.
        :raises ValueError: If the string does not match any known :class:`Object`.
        """
        obj_name = obj_name.lower()

        for obj in Object:
            for name in obj.value.names:
                if name == obj_name:
                    return obj

        raise ValueError(f"Unknown object name '{obj_name}'")

    @staticmethod
    def parse(obj_expression: str) -> tuple["Object", Optional[str]]:
        """
        Parses an object expression into its corresponding :class:`Object` and an optional field reference.

        :param obj_expression: The string object expression (e.g., `"application.name"`).
        :return: A :type:`tuple` containing the :class:`Object` and an optional field reference.
        :raises ValueError: If the string does not match any known :class:`Object`, from :func:`from_str`.
        """
        if "." in obj_expression:
            obj_name, obj_field = obj_expression.split(".", 1)
        else:
            obj_name = obj_expression
            obj_field = None

        return Object.from_str(obj_name), obj_field

    def collect(self, status: FullStatus) -> list[dict]:
        """
        Collects objects of the specified type from the given :class:`full_status.FullStatus` object.

        :param status: The :class:`full_status.FullStatus` data structure.
        :return: A :type:`list` of collected objects as :type:`dict`.
        :raises ValueError: If the :class:`ObjectType` collector is not callable.
        """
        if not callable(self.value.collector):
            raise ValueError("Object collector is not callable")

        return list(self.value.collector(status))
