"""
This module defines a set of protocols and type abstractions for working with different Python types based on the
compatibility of different comparison operations. The protocols are used to annotate types that support specific
operations, such as ordering comparisons, equality comparisons, and containment checks.

Protocols
---------
- `OrderingComparable`:
    A protocol for annotating types that support ordering comparisons using the
    `__lt__` (less than) and `__gt__` (greater than) methods.

- `EqualityComparable`:
    A protocol for annotating types that support equality comparisons using the `__eq__` (equals) method.

- `NonEqualityComparable`:
    A protocol for annotating types that support non-equality comparisons using the `__ne__` (not equals) method.

- `OrderingEqualityComparable`:
    A protocol for annotating types that support both ordering and equality comparisons.
    It combines the functionality of `OrderingComparable` and `EqualityComparable`.

- `ContainsComparable`:
    A protocol for annotating types that support containment checks using the `__contains__` method.

TypeVars
--------
- `O_C`:
    A `TypeVar` bound to the `OrderingComparable` protocol,
    representing any type that supports ordering comparisons.

- `E_C`:
    A `TypeVar` bound to the `EqualityComparable` protocol,
    representing any type that supports equality comparisons.

- `NE_C`:
    A `TypeVar` bound to the `NonEqualityComparable` protocol,
    representing any type that supports non-equality comparisons.

- `OE_C`:
    A `TypeVar` bound to the `OrderingEqualityComparable` protocol,
    representing any type that supports both ordering and equality comparisons.

- `C_C`:
    A `TypeVar` bound to the `ContainsComparable` protocol,
    representing any type that supports containment checks.

- `C`:
    A union type of `O_C`, `E_C`, `NE_C`, `OE_C`, and `C_C`,
    representing any type that supports one or more of the defined comparability protocols.

- `T`:
    A generic `TypeVar` representing any type.

Utility Methods
---------------
Each protocol includes a static method `is_valid` to check if a given object conforms to the protocol.

Versions
--------
- 0.1.1: Initial version with protocol definitions and validation methods.
"""

from abc import ABC, abstractmethod
import inspect
from typing import Any, Callable, Protocol, TypeVar, Union, get_type_hints


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
        Check if the given object is valid for the `OrderingComparable` protocol.

        :param object obj:
            The object to be checked.

        :returns: ``True`` if the object is a valid for the `OrderingComparable` protocol,
            otherwise ``False``.

        .. versionadded:: 0.1.1
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
        Check if the given object is valid for the `EqualityComparable` protocol.

        :param object obj:
            The object to be checked.

        :returns: ``True`` if the object is a valid for the `EqualityComparable` protocol,
            otherwise ``False``.

        .. versionadded:: 0.1.1
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
        Check if the given object is valid for the `NonEqualityComparable` protocol.

        :param object obj:
            The object to be checked.

        :returns: ``True`` if the object is a valid for the `ContainsComparable` protocol,
            otherwise ``False``.

        .. versionadded:: 0.1.1
        """
        return hasattr(obj, "__ne__") and callable(obj.__ne__)


class OrderingEqualityComparable(OrderingComparable, EqualityComparable, ABC):
    """Protocol for annotating ordering and equality comparable types."""

    @staticmethod
    def is_valid(obj: object) -> bool:
        """
        Check if the given object is valid for the `OrderingEqualityComparable` protocol.

        :param object obj:
            The object to be checked.

        :returns: ``True`` if the object is a valid for the `OrderingEqualityComparable` protocol,
            otherwise ``False``.

        .. versionadded:: 0.1.1
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
        Check if the given object is valid for the `ContainsComparable` protocol.

        :param object obj:
            The object to be checked.

        :returns: ``True`` if the object is a valid for the `ContainsComparable` protocol,
            otherwise ``False``.

        .. versionadded:: 0.1.1
        """
        return hasattr(obj, "__contains__") and callable(obj.__contains__)


O_C = TypeVar("O_C", bound=OrderingComparable)
"""Ordering comparable type abstraction."""

E_C = TypeVar("E_C", bound=EqualityComparable)
"""Equality comparable type abstraction."""

NE_C = TypeVar("NE_C", bound=NonEqualityComparable)
"""Non-equality comparable type abstraction."""

OE_C = TypeVar("OE_C", bound=OrderingEqualityComparable)
"""Ordering and equality comparable type abstraction."""

C_C = TypeVar("C_C", bound=ContainsComparable)
"""Contains comparable type abstraction."""

C = Union[O_C, E_C, NE_C, OE_C, C_C]
"""Any comparable type abstraction."""

T = TypeVar("T")
"""Any type abstraction."""


def uses_typevar_params(func: Callable[..., Any]) -> bool:
    """
    Check if all parameters of the given `func` are annotated with `TypeVar`s.

    :param Callable[..., Any] func: The function to be checked.
    :return: ``True`` if all arguments of the given `func` are annotated with `TypeVar`s,
        otherwise ``False``.
    """
    # raise if we aren't even given a function >:(
    if not callable(func):
        raise TypeError("'func' must be a callable object.")

    # grab the function's signature
    signature = inspect.signature(func)

    # when there are zero parameters, fail
    if len(signature.parameters) == 0:
        return False

    # get the type hints for the function
    hints = get_type_hints(func)

    # check each parameter in the function's signature
    for param in signature.parameters.values():
        param_name = param.name

        # when lacking a type hint in a parameter,
        # we can fast-fail knowing not all parameters are TypeVars
        if param_name not in hints:
            return False

        # when we encounter a non-TypeVar parameter, fast-fail
        if not isinstance(hints[param_name], TypeVar):
            return False

    return True
