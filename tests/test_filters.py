from typing import Callable, Type
from unittest import TestCase
from unittest.mock import Mock, patch

import pytest

from jockey.abstractions import T
from jockey.filters import (
    bool_type_parser,
    contains_filter,
    equals_filter,
    greater_than_filter,
    greater_than_or_equals_filter,
    less_than_filter,
    less_than_or_equals_filter,
    log_filter_action,
    not_contains_filter,
    not_equals_filter,
    not_regex_filter,
    regex_filter,
    type_parser_for,
)


class TestLogFilterActionDecorator(TestCase):

    def test_action_function_is_called(self):
        # create mock action function
        mock_action = Mock()
        mock_action.__name__ = "test_filter"

        # wrap the action function
        wrapped_action = log_filter_action(mock_action)

        # call the newly wrapped action
        wrapped_action("value", "query")

        # assert the mock action was called
        mock_action.assert_called_once_with("value", "query")

    @patch("jockey.filters.logger")
    def test_logging(self, mock_logger):
        # create mock action function
        mock_action = Mock(return_value=True)
        mock_action.__name__ = "test_filter"

        # wrap the action function
        wrapped_action = log_filter_action(mock_action)

        # call the wrapped action
        wrapped_action("value", "query")

        # assert the action was logged
        mock_logger.debug.assert_called_once_with("%r [b][blue]%s[/][/] %r ? %r", "value", "test", "query", True)

    def test_return_value(self):
        # create mock action function
        mock_action = Mock(return_value=True)
        mock_action.__name__ = "test_filter"

        # wrap the action function
        wrapped_action = log_filter_action(mock_action)

        # call the wrapped action
        got = wrapped_action("value", "query")

        # assert the result is as expected
        self.assertEqual(got, True)


@pytest.mark.parametrize(
    "value, query, want",
    [
        ("abc123", "abc123", True),
        (1, 1, True),
        (["a", 2], ["a", 2], True),
        (2.3, 2.3, True),
        ("qwerty123", "asdf123", False),
        (10, 5, False),
        (["b", 10], ["c", 23], False),
        (4.5, 21.4, False),
    ],
)
def test_equals_filter(value: object, query: object, want: bool):
    assert equals_filter(value, query) == want


@pytest.mark.parametrize(
    "value, query, want",
    [
        ("abc123", "abc123", False),
        (1, 1, False),
        (["a", 2], ["a", 2], False),
        (2.3, 2.3, False),
        ("qwerty123", "asdf123", True),
        (10, 5, True),
        (["b", 10], ["c", 23], True),
        (4.5, 21.4, True),
    ],
)
def test_not_equals_filter(value: object, query: object, want: bool):
    assert not_equals_filter(value, query) == want


@pytest.mark.parametrize(
    "value, query, want",
    [
        ("abc123", "abc123", True),
        ("hello world", "hello|hi", True),
        ("juju-controller/5", "5$", True),
        ("juju-controller/5", "6$", False),
        ("kubernetes-worker/13", "^kube", True),
        ("ceph-mon/4", "^kube", False),
    ],
)
def test_regex_filter(value: str, query: str, want: bool):
    assert regex_filter(value, query) == want


@pytest.mark.parametrize(
    "value, query, want",
    [
        ("abc123", "abc123", False),
        ("hello world", "hello|hi", False),
        ("juju-controller/5", "5$", False),
        ("juju-controller/5", "6$", True),
        ("kubernetes-worker/13", "^kube", False),
        ("ceph-mon/4", "^kube", True),
    ],
)
def test_not_regex_filter(value: str, query: str, want: bool):
    assert not_regex_filter(value, query) == want


@pytest.mark.parametrize(
    "value, query, want",
    [
        (1, 2, False),
        (2, 1, True),
        (2, 2, False),
        (1000, 500, True),
        (24.5, 21.3, True),
        (10.5, 63.53, False),
        (92.3, 92.3, False),
    ],
)
def test_greater_than_filter(value: object, query: object, want: bool):
    assert greater_than_filter(value, query) == want


@pytest.mark.parametrize(
    "value, query, want",
    [
        (1, 2, False),
        (2, 1, True),
        (2, 2, True),
        (1000, 500, True),
        (24.5, 21.3, True),
        (10.5, 63.53, False),
        (92.3, 92.3, True),
    ],
)
def test_greater_than_or_equals_filter(value: object, query: object, want: bool):
    assert greater_than_or_equals_filter(value, query) == want


@pytest.mark.parametrize(
    "value, query, want",
    [
        (1, 2, True),
        (2, 1, False),
        (2, 2, False),
        (1000, 500, False),
        (24.5, 21.3, False),
        (10.5, 63.53, True),
        (92.3, 92.3, False),
    ],
)
def test_less_than_filter(value: object, query: object, want: bool):
    assert less_than_filter(value, query) == want


@pytest.mark.parametrize(
    "value, query, want",
    [
        (1, 2, True),
        (2, 1, False),
        (2, 2, True),
        (1000, 500, False),
        (24.5, 21.3, False),
        (10.5, 63.53, True),
        (92.3, 92.3, True),
    ],
)
def test_less_than_or_equals_filter(value: object, query: object, want: bool):
    assert less_than_or_equals_filter(value, query) == want


@pytest.mark.parametrize(
    "value, query, want",
    [
        ("abc123", "abc123", True),
        ("hello world", "hello", True),
        (["a", 1, 2], "a", True),
        ({"a": 1, "b": 2}, "a", True),
        ("abc123", "4", False),
        ("hello world", "goodbye", False),
        (["a", 1, 2], "b", False),
        ({"a": 1, "b": 2}, "c", False),
    ],
)
def test_contains_filter(value: object, query: object, want: bool):
    assert contains_filter(value, query) == want


@pytest.mark.parametrize(
    "value, query, want",
    [
        ("abc123", "abc123", False),
        ("hello world", "hello", False),
        (["a", 1, 2], "a", False),
        ({"a": 1, "b": 2}, "a", False),
        ("abc123", "4", True),
        ("hello world", "goodbye", True),
        (["a", 1, 2], "b", True),
        ({"a": 1, "b": 2}, "c", True),
    ],
)
def test_not_contains_filter(value: object, query: object, want: bool):
    assert not_contains_filter(value, query) == want


@pytest.mark.parametrize(
    "value, want",
    [
        ("true", True),
        ("t", True),
        ("yes", True),
        ("y", True),
        ("YES", True),
        ("Y", True),
        ("1", True),
        ("false", False),
        ("f", False),
        ("no", False),
        ("n", False),
        ("NO", False),
        ("N", False),
        ("0", False),
    ],
)
def test_bool_type_parser(value: str, want: bool):
    assert bool_type_parser(value) == want


@pytest.mark.parametrize(
    "t, want",
    [
        (bool, bool_type_parser),
        (str, str),
        (int, int),
        (float, float),
    ],
)
def test_type_parser_for(t: Type[T], want: Callable[[str], T]):
    assert type_parser_for(t) == want
