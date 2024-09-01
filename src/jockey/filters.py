from dataclasses import astuple, dataclass
from enum import Enum
from functools import wraps
from logging import getLogger
from typing import Any, Callable, Dict, Iterable, List, Tuple, Type

from dotty_dict import dotty
from regex import regex

from jockey.abstractions import C_C, E_C, NE_C, O_C, OE_C, C, T


logger = getLogger(__name__)

REGEX_TIMEOUT = 100
REGEX_FLAGS = regex.I | regex.U

FilterAction = Callable[[C, C], bool]


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
def not_equals_filter(value: NE_C, query: NE_C) -> bool:
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
def contains_filter(value: C_C, query: C_C) -> bool:
    return query in value


@log_filter_action
def not_contains_filter(value: C_C, query: C_C) -> bool:
    return query not in value


@dataclass
class FilterType:
    tokens: Tuple[str, ...]
    name: str
    should_parse: bool
    action: FilterAction


class FilterMode(Enum):
    EQUALS = FilterType(("=", "=="), "equals", True, equals_filter)
    NOT_EQUALS = FilterType(("^=", "!="), "not equals", True, not_equals_filter)
    REGEX = FilterType(("%",), "regex", False, regex_filter)
    NOT_REGEX = FilterType(("^%", "!%"), "not regex", False, not_regex_filter)
    GREATER_THAN = FilterType((">",), "greater than", True, greater_than_filter)
    GREATER_THAN_OR_EQUALS = FilterType((">=", "=>"), "greater than or equals", True, greater_than_or_equals_filter)
    LESS_THAN = FilterType(("<",), "less than", True, less_than_filter)
    LESS_THAN_OR_EQUALS = FilterType(("<=", "=<"), "less than or equals", True, less_than_or_equals_filter)
    CONTAINS = FilterType(("~",), "contains", False, contains_filter)
    NOT_CONTAINS = FilterType(("!~", "^~"), "not contains", False, not_contains_filter)

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


def bool_parser(value: str) -> bool:
    return value.lower() in {"true", "t", "1", "yes", "y"}


TYPE_PARSERS: Dict[Type[T], Callable[[str], T]] = {bool: bool_parser}


def get_type_parser(t: Type[T]) -> Callable[[str], T]:
    if parser := TYPE_PARSERS.get(t):
        return parser
    return t


def parse_filter_expression(expression: str) -> Callable[[Dict], bool]:
    for mode in FilterMode:
        (tokens, _, should_parse, action) = astuple(mode.value)
        for token in tokens:
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

                @wraps(action)
                def _filter_action(item: Dict) -> bool:
                    item_field = dotty(item)[field]

                    if should_parse:
                        field_parser = get_type_parser(type(item_field))
                        logger.debug("Using field parser %r on %r for [b][blue]%s[/][/]", field_parser, field, mode)
                        parsed_query = field_parser(query)
                    else:
                        logger.debug("No need to parse field %r for [b][blue]%s[/][/]", field, mode)
                        parsed_query = query

                    return action(item_field, parsed_query)

                return _filter_action

    raise ValueError(f"Invalid filter expression '{expression}'")


def parse_filter_expressions(expressions: Iterable[str]) -> List[Callable[[Dict], bool]]:
    return [parse_filter_expression(expression) for expression in expressions]
