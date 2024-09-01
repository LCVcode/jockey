from abc import ABC, abstractmethod
from typing import Protocol, TypeVar, Union


class OrderingComparable(Protocol):
    """Protocol for annotating ordering comparable types."""

    @abstractmethod
    def __lt__(self, other: "O_C") -> bool:
        pass

    @abstractmethod
    def __gt__(self, other: "O_C") -> bool:
        pass

    @staticmethod
    def is_valid(obj: object) -> bool:
        """
        Check if the given object is valid for the OrderingComparable protocol.

        Parameters:
            obj (object): The object to be checked.

        Returns:
            bool: Returns True if the object is a valid for the OrderingComparable protocol, otherwise False.
        """
        return hasattr(obj, "__lt__") and hasattr(obj, "__gt__") and callable(obj.__lt__) and callable(obj.__gt__)


class EqualityComparable(Protocol):
    """Protocol for annotating equality comparable types."""

    @abstractmethod
    def __eq__(self, other: "E_C") -> bool:
        pass

    @staticmethod
    def is_valid(obj: object) -> bool:
        """
        Check if the given object is valid for the EqualityComparable protocol.

        Parameters:
            obj (object): The object to be checked.

        Returns:
            bool: Returns True if the object is a valid for the EqualityComparable protocol, otherwise False.
        """
        return hasattr(obj, "__eq__") and callable(obj.__eq__)


class NonEqualityComparable(Protocol):
    """Protocol for annotating non-equality comparable types."""

    @abstractmethod
    def __ne__(self, other: "NE_C") -> bool:
        pass

    @staticmethod
    def is_valid(obj: object) -> bool:
        """
        Check if the given object is valid for the NonEqualityComparable protocol.

        Parameters:
            obj (object): The object to be checked.

        Returns:
            bool: Returns True if the object is a valid for the NonEqualityComparable protocol, otherwise False.
        """
        return hasattr(obj, "__ne__") and callable(obj.__ne__)


class OrderingEqualityComparable(OrderingComparable, EqualityComparable, ABC):
    """Protocol for annotating ordering and equality comparable types."""

    @staticmethod
    def is_valid(obj: object) -> bool:
        """
        Check if the given object is valid for the OrderingEqualityComparable protocol.

        Parameters:
            obj (object): The object to be checked.

        Returns:
            bool: Returns True if the object is a valid for the OrderingEqualityComparable protocol, otherwise False.
        """
        return OrderingComparable.is_valid(obj) and EqualityComparable.is_valid(obj)


class ContainsComparable(Protocol):
    """Protocol for annotating containment comparable types."""

    @abstractmethod
    def __contains__(self, other: "C_C") -> bool:
        pass

    @staticmethod
    def is_valid(obj: object) -> bool:
        """
        Check if the given object is valid for the ContainsComparable protocol.

        Parameters:
            obj (object): The object to be checked.

        Returns:
            bool: Returns True if the object is a valid for the ContainsComparable protocol, otherwise False.
        """
        return hasattr(obj, "__contains__") and callable(obj.__contains__)


O_C = TypeVar("O_C", bound=OrderingComparable)
E_C = TypeVar("E_C", bound=EqualityComparable)
NE_C = TypeVar("NE_C", bound=NonEqualityComparable)
OE_C = TypeVar("OE_C", bound=OrderingEqualityComparable)
C_C = TypeVar("C_C", bound=ContainsComparable)

C = Union[O_C, E_C, NE_C, OE_C, C_C]

T = TypeVar("T")
