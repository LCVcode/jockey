from dataclasses import astuple, dataclass
from enum import Enum
from functools import wraps
from logging import getLogger
from typing import Any, Callable, Dict, Iterable, List, Type

from dotty_dict import dotty
from regex import regex

from jockey.abstractions import C_C, E_C, O_C, OE_C, C, T, uses_typevar_params


logger = getLogger(__name__)

REGEX_TIMEOUT = 100
REGEX_FLAGS = regex.I | regex.U

FilterAction = Callable[[C, C], bool]
WrappedFilterAction = Callable[[Dict], bool]


def log_filter_action(action: FilterAction) -> Callable:
    @wraps(action)
    def wrapper(value: Any, query: Any) -> Any:
        action_name = str(action.__name__).removesuffix("_filter")
        result = action(value, query)
        logger.debug("%r [b][blue]%s[/][/] %r ? %r", value, action_name, query, result)
        return result

    return wrapper


@log_filter_action
def equals_filter(value: E_C, query: E_C) -> bool:
    return value == query


@log_filter_action
def not_equals_filter(value: E_C, query: E_C) -> bool:
    return value != query


@log_filter_action
def regex_filter(value: str, query: str) -> bool:
    return regex.search(str(query), str(value), flags=REGEX_FLAGS, timeout=REGEX_TIMEOUT) is not None


@log_filter_action
def not_regex_filter(value: str, query: str) -> bool:
    return regex.search(str(query), str(value), flags=REGEX_FLAGS, timeout=REGEX_TIMEOUT) is None


@log_filter_action
def greater_than_filter(value: O_C, query: O_C) -> bool:
    return value > query


@log_filter_action
def greater_than_or_equals_filter(value: OE_C, query: OE_C) -> bool:
    return value >= query


@log_filter_action
def less_than_filter(value: O_C, query: O_C) -> bool:
    return value < query


@log_filter_action
def less_than_or_equals_filter(value: OE_C, query: OE_C) -> bool:
    return value <= query


@log_filter_action
def contains_filter(value: C_C, query: Any) -> bool:
    return query in value


@log_filter_action
def not_contains_filter(value: C_C, query: Any) -> bool:
    return query not in value


@dataclass
class FilterType:
    tokens: set[str]
    name: str
    action: FilterAction


class FilterMode(Enum):
    EQUALS = FilterType({"==", "="}, "equals", equals_filter)
    NOT_EQUALS = FilterType({"^=", "!="}, "not equals", not_equals_filter)
    REGEX = FilterType({"%"}, "regex", regex_filter)
    NOT_REGEX = FilterType({"^%", "!%"}, "not regex", not_regex_filter)
    GREATER_THAN = FilterType({">"}, "greater than", greater_than_filter)
    GREATER_THAN_OR_EQUALS = FilterType({">=", "=>"}, "greater than or equals", greater_than_or_equals_filter)
    LESS_THAN = FilterType({"<"}, "less than", less_than_filter)
    LESS_THAN_OR_EQUALS = FilterType({"<=", "=<"}, "less than or equals", less_than_or_equals_filter)
    CONTAINS = FilterType({"~"}, "contains", contains_filter)
    NOT_CONTAINS = FilterType({"!~", "^~"}, "not contains", not_contains_filter)

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
        return set(token for mode in FilterMode for token in mode.value.tokens)


def bool_type_parser(value: str) -> bool:
    return value.lower() in {"true", "t", "1", "yes", "y"}


TYPE_PARSERS: Dict[Type[T], Callable[[str], T]] = {bool: bool_type_parser}
"""An override map between types and their corresponding parser functions."""


def type_parser_for(t: Type[T]) -> Callable[[str], T]:
    if parser := TYPE_PARSERS.get(t):
        return parser
    return t


def wrap_filter_action(mode: FilterMode, field: str, query: str) -> WrappedFilterAction:
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


def parse_filter_expression(expression: str) -> Callable[[Dict], bool]:
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


def parse_filter_expressions(expressions: Iterable[str]) -> List[Callable[[Dict], bool]]:
    return [parse_filter_expression(expression) for expression in expressions]
