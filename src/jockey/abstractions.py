"""
This module defines a set of protocols and type abstractions for working with different Python types based on the
compatibility of different comparison operations. The protocols are used to annotate types that support specific
operations, such as ordering comparisons, equality comparisons, and containment checks.

Utility Methods
---------------
Each protocol includes a static method `is_valid` to check if a given object conforms to the protocol.

Versions
--------
- 0.1.1: Initial version with protocol definitions and validation methods.
- 0.2.0: Full normalization and documentation.
"""

from abc import ABC, abstractmethod
import inspect
from typing import Any, Callable, Protocol, TypeVar, Union, get_type_hints


class OrderingComparable(Protocol):
    """
    A protocol for annotating types that support ordering comparisons.

    Classes implementing this protocol must provide implementations for the following methods:

    - `__lt__` (less than)
    - `__gt__` (greater than)
    - `__le__` (less than or equal to)
    - `__ge__` (greater than or equal to)
    """

    @abstractmethod
    def __lt__(self, other: "O_C") -> bool:
        pass

    @abstractmethod
    def __gt__(self, other: "O_C") -> bool:
        pass

    @abstractmethod
    def __le__(self, other: "O_C") -> bool:
        pass

    @abstractmethod
    def __ge__(self, other: "O_C") -> bool:
        pass

    @staticmethod
    def is_valid(obj: object) -> bool:
        """
        Check if the given object is valid for the :class:`OrderingComparable` protocol.

        :param object obj: The object to be checked.
        :return: ``True`` if the object is a valid for the :class:`OrderingComparable` protocol,
            otherwise ``False``.

        .. versionadded:: 0.2.0
        """
        return hasattr(obj, "__lt__") and hasattr(obj, "__gt__") and callable(obj.__lt__) and callable(obj.__gt__)


class EqualityComparable(Protocol):
    """
    A protocol for annotating types that support equality comparisons.

    Classes implementing this protocol must provide implementations for the following methods:

    - `__eq__` (equals)
    - `__ne__` (not equals)
    """

    @abstractmethod
    def __eq__(self, other: "E_C") -> bool:
        pass

    @abstractmethod
    def __ne__(self, other: "E_C") -> bool:
        pass

    @staticmethod
    def is_valid(obj: object) -> bool:
        """
        Check if the given object is valid for the :class:`EqualityComparable` protocol.

        :param obj: The object to be checked.
        :return: ``True`` if the object is a valid for the :class:`EqualityComparable` protocol,
            otherwise ``False``.

        .. versionadded:: 0.2.0
        """
        return hasattr(obj, "__eq__") and hasattr(obj, "__ne__") and callable(obj.__eq__) and callable(obj.__ne__)


class OrderingEqualityComparable(OrderingComparable, EqualityComparable, ABC):
    """
    A protocol for annotating types that support both ordering and equality comparisons.

    This protocol combines the functionalities of :class:`OrderingComparable` and :class:`EqualityComparable`.

    Classes implementing this protocol must provide implementations for the following methods:

    - `__lt__` (less than)
    - `__gt__` (greater than)
    - `__le__` (less than or equal to)
    - `__ge__` (greater than or equal to)
    - `__eq__` (equals)
    - `__ne__` (not equals)
    """

    @staticmethod
    def is_valid(obj: object) -> bool:
        """
        Check if the given object is valid for the :class:`OrderingEqualityComparable` protocol.

        :param obj: The object to be checked.
        :returns: ``True`` if the object is a valid for the :class:`OrderingEqualityComparable` protocol,
            otherwise ``False``.

        .. versionadded:: 0.2.0
        """
        return OrderingComparable.is_valid(obj) and EqualityComparable.is_valid(obj)


class ContainsComparable(Protocol):
    """
    A protocol for annotating types that support containment comparisons.

    Classes implementing this protocol must provide implementations for the following methods:

    - `__contains__` (containment check)
    """

    @abstractmethod
    def __contains__(self, other: "C_C") -> bool:
        pass

    @staticmethod
    def is_valid(obj: object) -> bool:
        """
        Check if the given object is valid for the :class:`ContainsComparable` protocol.

        :param obj: The object to be checked.
        :returns: ``True`` if the object is a valid for the :class:`ContainsComparable` protocol,
            otherwise ``False``.

        .. versionadded:: 0.2.0
        """
        return hasattr(obj, "__contains__") and callable(obj.__contains__)


O_C = TypeVar("O_C", bound=OrderingComparable)
"""
A :class:`typing.TypeVar` bound to the :class:`OrderingComparable` protocol,
representing any type that supports ordering comparisons.
"""

E_C = TypeVar("E_C", bound=EqualityComparable)
"""
A :class:`typing.TypeVar` bound to the :class:`EqualityComparable` protocol,
representing any type that supports equality comparisons.
"""

OE_C = TypeVar("OE_C", bound=OrderingEqualityComparable)
"""
A :class:`typing.TypeVar` bound to the :class:`OrderingEqualityComparable` protocol,
representing any type that supports both ordering and equality comparisons.
"""

C_C = TypeVar("C_C", bound=ContainsComparable)
"""
A :class:`typing.TypeVar` bound to the :class:`ContainsComparable` protocol,
representing any type that supports containment checks.
"""

C = Union[O_C, E_C, OE_C, C_C]
"""
A :obj:`Union` type of :obj:`O_C`, :obj:`E_C`, :obj:`OE_C`, and :obj:`C_C`,
representing any type that supports one or more of the defined comparability protocols.
"""

T = TypeVar("T")
"""A generic :class:`typing.TypeVar` representing any type."""


def uses_typevar_params(func: Callable[..., Any]) -> bool:
    """
    Check if all parameters of the given *func* are annotated with :class:`typing.TypeVar` s.

    :param func: The function to be checked.
    :return: ``True`` if all arguments of the given *func* are annotated with :class:`typing.TypeVar` s,
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
