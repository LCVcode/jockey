from dataclasses import astuple, dataclass
from enum import Enum
from functools import wraps
from logging import getLogger
from typing import Any, Callable, Dict, Iterable, Type

from dotty_dict import dotty
from regex import regex

from jockey.abstractions import C_C, E_C, O_C, OE_C, C, T, uses_typevar_params


logger = getLogger(__name__)
"""The logger for the :mod:`jockey.filters` module."""

REGEX_TIMEOUT = 100
"""
Module-wide timeout for user-provided regular expressions.

.. note:: This is necessary measure to prevent occurrences of ReDoS_.

.. _ReDoS: https://en.wikipedia.org/wiki/ReDoS
"""

REGEX_FLAGS = regex.I | regex.U
"""Module-wide flags for user-provided regular expressions."""

FilterAction = Callable[[C, C], bool]
"""A type defining functions capable of performing comparisons for filtering."""

WrappedFilterAction = Callable[[Dict], bool]
"""
A type defining a wrapped instance of a :type:`FilterAction` that internally performs filtering when
given an :class:`~.object.Object`.
"""


def log_filter_action(action: FilterAction) -> FilterAction:
    """
    A decorator that wraps the given *action* function and logs the details of the filtering action being performed.

    :param action: The :type:`FilterAction` function that is being logged.
        It should be a callable that takes two arguments:
            - `value` (the value being filtered)
            - `query` (the filter query).
    :return: A wrapped function that logs the action and returns the result.
    """

    @wraps(action)
    def wrapper(value: Any, query: Any) -> Any:
        action_name = str(action.__name__).removesuffix("_filter")
        result = action(value, query)
        logger.debug("%r [b][blue]%s[/][/] %r ? %r", value, action_name, query, result)
        return result

    return wrapper


@log_filter_action
def equals_filter(value: E_C, query: E_C) -> bool:
    """
    Checks if the value equals the query.

    :param value: The value to compare.
    :param query: The query to compare against.
    :return: True if the value equals the query, otherwise False.
    """
    return value == query


@log_filter_action
def not_equals_filter(value: E_C, query: E_C) -> bool:
    """
    Checks if the value does not equal the query.

    :param value: The value to compare.
    :param query: The query to compare against.
    :return: True if the value does not equal the query, otherwise False.
    """
    return value != query


@log_filter_action
def regex_filter(value: str, query: str) -> bool:
    """
    Checks if the value matches the regular expression query.

    :param value: The value to compare.
    :param query: The regular expression query to match against.
    :return: True if the value matches the query, otherwise False.
    :raises TimeoutError: If :obj:`REGEX_TIMEOUT` is exceeded.
    """
    try:
        return regex.search(str(query), str(value), flags=REGEX_FLAGS, timeout=REGEX_TIMEOUT) is not None
    except TimeoutError as e:
        logger.warning("Encountered timeout on %r regex %r: %s", value, query, e)
        raise e


@log_filter_action
def not_regex_filter(value: str, query: str) -> bool:
    """
    Checks if the value does not match the regular expression query.

    :param value: The value to compare.
    :param query: The regular expression query to match against.
    :return: True if the value does not match the query, otherwise False.
    :raises TimeoutError: If :obj:`REGEX_TIMEOUT` is exceeded.
    """
    try:
        return regex.search(str(query), str(value), flags=REGEX_FLAGS, timeout=REGEX_TIMEOUT) is None
    except TimeoutError as e:
        logger.warning("Encountered timeout on %r not_regex %r: %s", value, query, e)
        raise e


@log_filter_action
def greater_than_filter(value: O_C, query: O_C) -> bool:
    """
    Checks if the value is greater than the query.

    :param value: The value to compare.
    :param query: The query to compare against.
    :return: True if the value is greater than the query, otherwise False.
    """
    return value > query


@log_filter_action
def greater_than_or_equals_filter(value: OE_C, query: OE_C) -> bool:
    """
    Checks if the value is greater than or equal to the query.

    :param value: The value to compare.
    :param query: The query to compare against.
    :return: True if the value is greater than or equal to the query, otherwise False.
    """
    return value >= query


@log_filter_action
def less_than_filter(value: O_C, query: O_C) -> bool:
    """
    Checks if the value is less than the query.

    :param value: The value to compare.
    :param query: The query to compare against.
    :return: True if the value is less than the query, otherwise False.
    """
    return value < query


@log_filter_action
def less_than_or_equals_filter(value: OE_C, query: OE_C) -> bool:
    """
    Checks if the value is less than or equal to the query.

    :param value: The value to compare.
    :param query: The query to compare against.
    :return: True if the value is less than or equal to the query, otherwise False.
    """
    return value <= query


@log_filter_action
def contains_filter(value: C_C, query: Any) -> bool:
    """
    Checks if the query is contained within the value.

    :param value: The value to check.
    :param query: The query to look for.
    :return: True if the query is contained within the value, otherwise False.
    """
    return query in value


@log_filter_action
def not_contains_filter(value: C_C, query: Any) -> bool:
    """
    Checks if the query is not contained within the value.

    :param value: The value to check.
    :param query: The query to look for.
    :return: True if the query is not contained within the value, otherwise False.
    """
    return query not in value


@dataclass
class FilterType:
    """Represents a filter type consisting of tokens, name, and the associated action."""

    tokens: set[str]
    """A set of strings representing the tokens that can trigger this filter."""

    name: str
    """The name of the filter."""

    action: FilterAction
    """The action to be performed when this filter is applied."""


class FilterMode(Enum):
    """
    An enumeration of filter types, each with a specific filtering action.
    """

    EQUALS = FilterType({"==", "="}, "equals", equals_filter)
    """Checks that checks for equality between values."""

    NOT_EQUALS = FilterType({"^=", "!="}, "not equals", not_equals_filter)
    """Checks for inequality between values."""

    REGEX = FilterType({"%"}, "regex", regex_filter)
    """Matches a value against a regular expression."""

    NOT_REGEX = FilterType({"^%", "!%"}, "not regex", not_regex_filter)
    """Ensures a value does not match a regular expression."""

    GREATER_THAN = FilterType({">"}, "greater than", greater_than_filter)
    """Checks if a value is greater than another."""

    GREATER_THAN_OR_EQUALS = FilterType({">=", "=>"}, "greater than or equals", greater_than_or_equals_filter)
    """Checks if a value is greater than or equal to another."""

    LESS_THAN = FilterType({"<"}, "less than", less_than_filter)
    """Checks if a value is less than another."""

    LESS_THAN_OR_EQUALS = FilterType({"<=", "=<"}, "less than or equals", less_than_or_equals_filter)
    """Checks if a value is less than or equal to another."""

    CONTAINS = FilterType({"~"}, "contains", contains_filter)
    """Checks if a value contains another."""

    NOT_CONTAINS = FilterType({"!~", "^~"}, "not contains", not_contains_filter)
    """Checks if a value does not contain another."""

    def __str__(self) -> str:
        return self.value.name

    def __eq__(self, other: object) -> bool:
        if isinstance(other, FilterMode):
            return self.name == other.name
        return False

    def __ne__(self, other: object) -> bool:
        if isinstance(other, FilterMode):
            return self.name != other.name
        return True

    def __hash__(self) -> int:
        return hash(self.name)

    @staticmethod
    def tokens() -> set[str]:
        """
        Retrieves all tokens used across all filter modes.

        :return: A set of tokens.
        """
        return set(token for mode in FilterMode for token in mode.value.tokens)


def bool_type_parser(value: str) -> bool:
    """
    Parses a string into a boolean value.

    :param value: The string value to parse.
    :return: `True` if the value represents a truthy value, otherwise `False`.
    """
    return value.lower() in {"true", "t", "1", "yes", "y"}


TYPE_PARSERS: Dict[Type[T], Callable[[str], T]] = {bool: bool_type_parser}
"""An override map between types and their corresponding parser functions."""


def type_parser_for(t: Type[T]) -> Callable[[str], T]:
    """
    Returns the appropriate parser function for the given type.

    :param t: The type to locate a parser for.
    :return: The parser function that converts a string into the given type.

    .. seealso::
        This function uses :obj:`TYPE_PARSERS` for overrides to the base Python type functions.
    """

    if parser := TYPE_PARSERS.get(t):
        return parser
    return t


def wrap_filter_action(mode: FilterMode, field: str, query: str) -> WrappedFilterAction:
    """
    Wraps a filter action with additional parsing and logging functionality.

    The resulting :type:`WrappedFilterAction` function will accept one argument, being the `item` object to be
    examined by the filter. It will:

    - traverse `item` to the *field* using :func:`dotty_dict.dotty_dict.dotty` to obtain the `value`, then
    - compare the `value` against the *query* using the wrapped :type:`FilterAction`.

    :param mode: The filter mode to use.
    :param field: The field to filter on.
    :param query: The filter query to apply.
    :return: A wrapped filter action function.
    """
    action = mode.value.action

    @wraps(action)
    def wrapped_filter_action(item: Dict) -> bool:
        try:
            value = dotty(item)[field]
        except KeyError:
            logger.debug("Could not find field '%s', fast-failing filter", field)
            return False

        if uses_typevar_params(action):
            field_parser = type_parser_for(type(value))
            logger.debug("Using field parser %r on %r for [b][blue]%s[/][/]", field_parser, field, mode)
            parsed_query = field_parser(query)
        else:
            logger.debug("No need to parse field %r for [b][blue]%s[/][/]", field, mode)
            parsed_query = query

        return action(value, parsed_query)

    return wrapped_filter_action


def parse_filter_expression(expression: str) -> WrappedFilterAction:
    """
    Parses a filter expression string into a callable :type:`WrappedFilterAction`.

    The resulting :type:`WrappedFilterAction` checks a provided :class:`~.objects.Object` against the result
    of the :class:`FilterMode` :type:`FilterAction` and `query` parsed from the `expression`.

    :param expression: The filter expression to parse.
    :return: A callable that applies the parsed filter to an :class:`~.objects.Object`.
    :raises ValueError: If the expression is invalid (e.g., fails to match any :class:`FilterMode`).
    """
    tokens: set[str]
    action: FilterAction

    for mode in FilterMode:
        (tokens, _, action) = astuple(mode.value)
        for token in sorted(tokens, key=len, reverse=True):
            if token in expression:
                field, query = expression.split(token)
                logger.debug(
                    "Parsed filter [i]'%s %s %s'[/] with token '%s' on expression %r",
                    field,
                    mode,
                    query,
                    token,
                    expression,
                )

                return wrap_filter_action(mode, field, query)

    raise ValueError(f"Invalid filter expression '{expression}'")


def parse_filter_expressions(expressions: Iterable[str]) -> Iterable[WrappedFilterAction]:
    """
    Parses multiple filter expressions into a list of :type:`WrappedFilterAction`.

    :param expressions: An iterable containing filter expression strings.
    :return: A list of :type:`WrappedFilterAction` that apply the parsed filters to an :class:`~.objects.Object`.

    .. seealso:: This is a thin wrapper for :func:`parse_filter_expression`.
    """

    return [parse_filter_expression(expression) for expression in expressions]
