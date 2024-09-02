from typing import Any, Callable, List, Tuple

import pytest

from jockey.abstractions import (
    E_C,
    O_C,
    OE_C,
    ContainsComparable,
    EqualityComparable,
    OrderingComparable,
    OrderingEqualityComparable,
    uses_typevar_params,
)


class TestOrderingComparable:
    class DummyOrderingComparable(OrderingComparable):
        def __lt__(self, other: O_C) -> bool:
            return True

        def __gt__(self: O_C, other) -> bool:
            return True

    @pytest.fixture
    def ordering_comparable(self):
        return self.DummyOrderingComparable()

    def test_lt_method(self, ordering_comparable):
        assert ordering_comparable.__lt__(1) == True

    def test_gt_method(self, ordering_comparable):
        assert ordering_comparable.__gt__(2) == True


class TestEqualityComparable:
    class DummyEqualityComparable(EqualityComparable):
        def __eq__(self, other: E_C) -> bool:
            return True

        def __ne__(self, other: E_C) -> bool:
            return True

    @pytest.fixture
    def equality_comparable(self):
        return self.DummyEqualityComparable()

    def test_eq_method(self, equality_comparable):
        assert equality_comparable.__eq__(1) == True

    def test_ne_method(self, equality_comparable):
        assert equality_comparable.__ne__(1) == True


class TestOrderingEqualityComparable:
    class DummyOrderingEqualityComparable(OrderingEqualityComparable):
        def __lt__(self, other: O_C) -> bool:
            return True

        def __gt__(self, other: O_C) -> bool:
            return True

        def __eq__(self, other: E_C) -> bool:
            return True

    @pytest.fixture
    def ordering_equality_comparable(self):
        return self.DummyOrderingEqualityComparable()

    def test_lt_method(self, ordering_equality_comparable):
        assert ordering_equality_comparable.__lt__(1) == True

    def test_gt_method(self, ordering_equality_comparable):
        assert ordering_equality_comparable.__gt__(2) == True

    def test_eq_method(self, ordering_equality_comparable):
        assert ordering_equality_comparable.__eq__(1) == True


@pytest.mark.parametrize("t", [int(1), float(1.2), str("1"), bool(True), None, list(), dict()])
def test_type_for_ordering_comparable(t: object):
    assert OrderingComparable.is_valid(t) == True


@pytest.mark.parametrize("t", [int(1), float(1.2), str("1"), bool(True), None, list(), dict()])
def test_type_for_equality_comparable(t: object):
    assert EqualityComparable.is_valid(t) == True


@pytest.mark.parametrize("t", [int(1), float(1.2), str("1"), bool(True), None, list(), dict()])
def test_type_for_ordering_equality_comparable(t: object):
    assert OrderingEqualityComparable.is_valid(t) == True


@pytest.mark.parametrize("t", [str("1"), list(), dict()])
def test_type_for_contains_comparable(t: object):
    assert ContainsComparable.is_valid(t) == True


def uses_typevar_params_cases() -> List[Tuple[Callable[..., Any], bool]]:

    def all_typevar_func(a: O_C, b: E_C, c: OE_C) -> bool:
        print(a, b, c)
        return True

    def some_typevar_func_1(a: O_C, b: E_C, c: OE_C, d: str) -> bool:
        print(a, b, c, d)
        return True

    def some_typevar_func_2(a: O_C, b: E_C, c: int, d: OE_C) -> bool:
        print(a, b, c, d)
        return True

    def no_typevar_func(a: int, b: str, c: bool, d: None) -> bool:
        print(a, b, c, d)
        return True

    def no_param_func() -> bool:
        return True

    return [
        (all_typevar_func, True),
        (some_typevar_func_1, False),
        (some_typevar_func_2, False),
        (no_typevar_func, False),
        (no_param_func, False),
    ]


@pytest.mark.parametrize("func, want", uses_typevar_params_cases())
def test_uses_typevar_params(func: Callable[..., Any], want: bool):
    assert uses_typevar_params(func) == want, (
        f"uses_typevar_params({func}) returned {not want}, " f"but expected {want}."
    )
