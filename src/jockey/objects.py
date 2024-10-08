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

from enum import Enum
from typing import Any, Callable, Iterable, Optional

from jockey.juju import Application, Machine, Unit
from jockey.juju_schema.full_status import FullStatus


ObjectCollector = Callable[[FullStatus], Iterable[Any]]
"""A type alias representing a function that collects objects from the Juju :class:`full_status.FullStatus`."""


class Object(Enum):
    """An enumeration of different Juju object types, such as applications, units, and machines."""

    APPLICATION = Application
    """Represents Juju applications and their associated collector."""

    UNIT = Unit
    """Represents Juju units and their associated collector."""

    MACHINE = Machine
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

        return {token for obj in Object for token in obj.value.tokens}

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
            for name in obj.value.tokens:
                if name == obj_name:
                    return obj

        raise ValueError(f"Unknown object name '{obj_name}'")

    @staticmethod
    def parse(obj_expression: str) -> tuple["Object", Optional[list[str]]]:
        """
        Parses an object expression into its corresponding :class:`Object` and an optional field reference.

        :param obj_expression: The string object expression (e.g., `"application.name"`).
        :return: A :type:`tuple` containing the :class:`Object` and an optional field reference.
        :raises ValueError: If the string does not match any known :class:`Object`, from :func:`from_str`.
        """
        if "." in obj_expression:
            # split on the first dot
            obj_name, obj_fields_expression = obj_expression.split(".", 1)
        else:
            # split on the first comma
            parts = obj_expression.split(",", 1)
            obj_name = parts[0]
            obj_fields_expression = parts[1] if len(parts) > 1 else None

        # if fields are specified, split them on the comma boundary into a set
        if obj_fields_expression:
            obj_fields = obj_fields_expression.split(",")
        else:
            obj_fields = None

        return Object.from_str(obj_name), obj_fields

    def collect(self, status: FullStatus) -> list[dict]:
        """
        Collects objects of the specified type from the given :class:`full_status.FullStatus` object.

        :param status: The :class:`full_status.FullStatus` data structure.
        :return: A :type:`list` of collected objects as :type:`dict`.
        :raises ValueError: If the :class:`ObjectType` collector is not callable.
        """
        if not hasattr(self.value, "from_juju_status") or not callable(self.value.from_juju_status):
            raise ValueError("Object 'from_juju_status' is not callable")

        return list(self.value.from_juju_status(status))
