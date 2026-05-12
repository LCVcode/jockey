"""Juju object types and object-name abbreviation utilities."""

from enum import Enum
from typing import Optional


class ObjectType(Enum):
    """Supported object types and their accepted abbreviations."""

    CHARM = ("charms", "charm", "c")
    APP = ("applications", "app", "apps", "application", "a")
    UNIT = ("units", "unit", "u")
    MACHINE = ("machines", "machine", "m")
    IP = ("ips", "address", "addresses", "ip", "i")
    HOSTNAME = ("hostnames", "hostname", "host", "hosts", "h")
    AVAILABILITY_ZONE = ("availability-zone", "availability_zone", "az", "zone")


def list_abbreviations() -> str:
    """
    Build a display table of object types and their short names.

    Returns
    =======
    abbreviations (str)
        A formatted table containing object names and abbreviations.
    """
    pad = 15

    header = "OBJECT TYPE".ljust(pad, " ") + "SHORT NAMES"
    lines = [obj_type.value[0].ljust(pad, " ") + ", ".join(obj_type.value[1:]) for obj_type in ObjectType]
    return "\n".join([header, *lines])


def convert_object_abbreviation(abbrev: str) -> Optional[ObjectType]:
    """
    Convert an object type abbreviation into an ObjectType.  If the abbreviation
    is not a valid Juju object, None will be returned.

    Arguments
    =========
    abbrev (str)
        A possibly abbreviated object name.

    Returns
    =======
    object_type (ObjectType) [optional]
        The ObjectType corresponding with the given abbreviation, if any.
    """
    normalized = abbrev.lower()
    return next((obj_type for obj_type in ObjectType if normalized in obj_type.value), None)
