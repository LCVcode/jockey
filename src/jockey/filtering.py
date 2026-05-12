"""Filter expression parsing and matching helpers."""

from dataclasses import dataclass
from enum import Enum
import re
from typing import Generator, Iterable

from jockey.object_types import ObjectType, convert_object_abbreviation


class FilterMode(Enum):
    """Supported filter operators for Jockey query expressions."""

    EQUALS = "="
    CONTAINS = "~"
    NOT_EQUALS = "^="
    NOT_CONTAINS = "^~"


POSITIVE_MODES = (
    FilterMode.EQUALS,
    FilterMode.CONTAINS,
)


NEGATIVE_MODES = (
    FilterMode.NOT_EQUALS,
    FilterMode.NOT_CONTAINS,
)


@dataclass
class JockeyFilter:
    """Parsed representation of a single Jockey filter expression."""

    obj_type: ObjectType
    mode: FilterMode
    content: str


def positive_filters(
    filters: Iterable[JockeyFilter],
) -> Generator[JockeyFilter, None, None]:
    """
    Extract positive filters from a group of parsed filters.

    Arguments
    =========
    filters (Iterable[JockeyFilter])
        Filters to inspect.

    Returns
    =======
    positive (Generator[JockeyFilter, None, None])
        A generator containing only positive filters.
    """
    for filter_ in filters:
        if filter_.mode in POSITIVE_MODES:
            yield filter_


def negative_filters(
    filters: Iterable[JockeyFilter],
) -> Generator[JockeyFilter, None, None]:
    """
    Extract negative filters from a group of parsed filters.

    Arguments
    =========
    filters (Iterable[JockeyFilter])
        Filters to inspect.

    Returns
    =======
    negative (Generator[JockeyFilter, None, None])
        A generator containing only negative filters.
    """
    for filter_ in filters:
        if filter_.mode in NEGATIVE_MODES:
            yield filter_


def parse_filter_string(
    filter_str: str,
) -> JockeyFilter:
    """
    Parse a filter string down into its object type, filter code, and content.

    Arguments
    =========
    filter_str (str)
        The raw filter string.

    Returns
    =======
    jockey_filter (JockeyFilter)
        A filter that matches the given filter string.
    """
    filter_code_pattern = re.compile(r"[=^~]+")

    filter_codes = filter_code_pattern.findall(filter_str)
    assert len(filter_codes) == 1, "Incorrect number of filter codes detected."

    match = filter_code_pattern.search(filter_str)
    assert match

    object_type = convert_object_abbreviation(filter_str[: match.start()])
    assert object_type, "Invalid object type detected in filter string."

    filter_mode = next((mode for mode in FilterMode if mode.value == match.group()), None)
    assert filter_mode, f"Invalid filter mode detected: {match.group()}."

    content = filter_str[match.end() :]
    assert content, "Empty content detected in filter string."

    char_blacklist = ("_", ":", ";", "\\", "\t", "\n", ",")
    assert not any(
        char in char_blacklist for char in content
    ), "Blacklisted characters detected in filter string content."

    return JockeyFilter(obj_type=object_type, mode=filter_mode, content=content)


FILTER_ACTION_MAP = {
    FilterMode.EQUALS: lambda content, value: content == value,
    FilterMode.NOT_EQUALS: lambda content, value: content != value,
    FilterMode.CONTAINS: lambda content, value: content in value,
    FilterMode.NOT_CONTAINS: lambda content, value: content not in value,
}


def check_filter_match(jockey_filter: JockeyFilter, value: str) -> bool:
    """
    Check if a value satisfied a Jockey filter.

    Arguments
    =========
    jockey_filter (JockeyFilter)
        A single Jockey filter
    value (str)
        A string to test against the filter

    Returns
    =======
    is_match (bool)
        True if value satisfies jockey_filter, else False
    """
    action = FILTER_ACTION_MAP[jockey_filter.mode]
    return action(jockey_filter.content, value)


def check_filter_batch_match(filter_list: Iterable[JockeyFilter], batch: Iterable[str]) -> bool:
    """
    Check if a batch of Juju objects (as strings) satisfies a set of filters.
    The batch must satisfy all positive filters and trigger no negative filters
    to return a True.

    This is used in cases where a single Juju object contains multiple children,
    such as an Application having many Units.

    Just like check_filter_match, this function ignores the Juju object type
    and simply performs the relevant string comparisons.

    Arguments
    =========
    filter_list (Iterable[JockeyFilter])
        A set of Jockey filters to apply.
    batch (Iterable[str])
        A set of object names to be tested.

    Returns
    =======
    match_success (bool)
        True if all of batch pass testing against filter_list, else False.
    """
    batch = tuple(batch)
    filter_list = tuple(filter_list)
    pos_filters = tuple(positive_filters(filter_list))
    neg_filters = tuple(negative_filters(filter_list))

    for filter_ in neg_filters:
        if not all(check_filter_match(filter_, item) for item in batch):
            return False

    for filter_ in pos_filters:
        if not any(check_filter_match(filter_, item) for item in batch):
            return False

    return True
