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


class EqualityComparable(Protocol):
    """Protocol for annotating equality comparable types."""

    @abstractmethod
    def __eq__(self, other: "E_C") -> bool:
        pass


class NonEqualityComparable(Protocol):
    """Protocol for annotating non-equality comparable types."""

    @abstractmethod
    def __ne__(self, other: "NE_C") -> bool:
        pass


class OrderingEqualityComparable(OrderingComparable, EqualityComparable, ABC):
    """Protocol for annotating ordering and equality comparable types."""


class ContainsComparable(Protocol):
    """Protocol for annotating containment comparable types."""

    @abstractmethod
    def __contains__(self, other: "C_C") -> bool:
        pass


O_C = TypeVar("O_C", bound=OrderingComparable)
E_C = TypeVar("E_C", bound=EqualityComparable)
NE_C = TypeVar("NE_C", bound=NonEqualityComparable)
OE_C = TypeVar("OE_C", bound=OrderingEqualityComparable)
C_C = TypeVar("C_C", bound=ContainsComparable)

C = Union[O_C, E_C, NE_C, OE_C, C_C]

T = TypeVar("T")
