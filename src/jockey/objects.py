from dataclasses import dataclass
from enum import Enum
from typing import Callable, Dict, Iterable, List, Optional, Tuple

from jockey.juju import all_applications, all_machines, all_units
from jockey.juju_schema.full_status import FullStatus


ObjectCollector = Callable[[FullStatus], Iterable[Dict]]


@dataclass
class ObjectType:
    names: Tuple[str, ...]
    collector: ObjectCollector


class Object(Enum):
    APPLICATION = ObjectType(("applications", "app", "apps", "application", "a"), all_applications)
    UNIT = ObjectType(("units", "unit", "u"), all_units)
    MACHINE = ObjectType(("machines", "machine", "m"), all_machines)

    def __str__(self) -> str:
        return self.value.names[0] if len(self.value.names) != 0 else self.name

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
        return set(token for obj in Object for token in obj.value.names)

    @staticmethod
    def from_str(obj_name: str) -> "Object":
        obj_name = obj_name.lower()

        for obj in Object:
            for name in obj.value.names:
                if name == obj_name:
                    return obj

        raise ValueError(f"Unknown object name '{obj_name}'")

    @staticmethod
    def parse(obj_expression: str) -> Tuple["Object", Optional[str]]:
        if "." in obj_expression:
            obj_name, obj_field = obj_expression.split(".", 1)
        else:
            obj_name = obj_expression
            obj_field = None

        return Object.from_str(obj_name), obj_field

    def collect(self, status: FullStatus) -> List[Dict]:
        if not callable(self.value.collector):
            raise ValueError("Object collector is not callable")

        return list(self.value.collector(status))
