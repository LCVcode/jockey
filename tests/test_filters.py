import pytest

from jockey.core import FilterMode, JockeyFilter, ObjectType, check_filter_match, parse_filter_string


def test_filter_mode_retrieval():
    """Test that FilterModes are retrieved correctly."""

    assert next(mode for mode in FilterMode if mode.value == '~') == FilterMode.CONTAINS
    assert next(mode for mode in FilterMode if mode.value == '^~') == FilterMode.NOT_CONTAINS
    assert next(mode for mode in FilterMode if mode.value == '=') == FilterMode.EQUALS
    assert next(mode for mode in FilterMode if mode.value == '^=') == FilterMode.NOT_EQUALS


def test_valid_filters():
    """Test that valid filter strings work."""

    valid_filters = (
        ('u~hw-health', ObjectType.UNIT, FilterMode.CONTAINS, 'hw-health'),
        (
            'app^=nrpe-host',
            ObjectType.APP,
            FilterMode.NOT_EQUALS,
            'nrpe-host',
        ),
        ('charm^~nova', ObjectType.CHARM, FilterMode.NOT_CONTAINS, 'nova'),
        ('ip=127.0.0.1', ObjectType.IP, FilterMode.EQUALS, '127.0.0.1'),
    )
    valid_filters = (
        (
            'app^=nrpe-host',
            ObjectType.APP,
            FilterMode.NOT_EQUALS,
            'nrpe-host',
        ),
    )
    for filter_str, object_type, mode, content in valid_filters:
        assert parse_filter_string(filter_str) == JockeyFilter(
            object_type,
            mode,
            content,
        )


def test_invalid_object_types():
    """Test filter strings that have bad object types."""

    bad_filters = ('unite=unit-name', 'appp^~cool-app')
    with pytest.raises(AssertionError):
        for filter_str in bad_filters:
            parse_filter_string(filter_str)


def test_blacklisted_characters():
    """Test that filters detect blacklisted characters."""

    blacklist_filters = (
        'unit^=nova_compute',
        'charm=glance,cinder',
        'ip=192.168,1,1',
        'unit~:test',
        'u^~test;',
    )
    with pytest.raises(AssertionError):
        for filter_str in blacklist_filters:
            parse_filter_string(filter_str)


def test_invalid_filter_modes():
    """Test that filters detect invalid filter modes."""

    invalid_feature_modes = (
        'u===unit',
        'app~^app',
        'charm^charm',
        'hostname=-=nodename',
        'ip127.0.0.1',
        'machine^^=14/lxd/0',
    )
    with pytest.raises(AssertionError):
        for filter_str in invalid_feature_modes:
            parse_filter_string(filter_str)


def test_empty_content():
    """Test that empty content is detected."""

    empty_content = (
        'charm~',
        'application^~',
        'unit=',
        'm^=',
        'ip=',
        'hostname~',
    )
    with pytest.raises(AssertionError):
        for filter_str in empty_content:
            parse_filter_string(filter_str)


@pytest.fixture
def unit_equals_filter():
    return JockeyFilter(obj_type=ObjectType.UNIT, mode=FilterMode.EQUALS, content='test-content')


@pytest.fixture
def unit_not_equals_filter():
    return JockeyFilter(
        obj_type=ObjectType.UNIT,
        mode=FilterMode.NOT_EQUALS,
        content='test-content',
    )


@pytest.fixture
def unit_contains_filter():
    return JockeyFilter(
        obj_type=ObjectType.UNIT,
        mode=FilterMode.CONTAINS,
        content='test-content',
    )


@pytest.fixture
def unit_not_contains_filter():
    return JockeyFilter(
        obj_type=ObjectType.UNIT,
        mode=FilterMode.NOT_CONTAINS,
        content='test-content',
    )


def test_equals_filter_mode(unit_equals_filter):
    """Test that the equals (=) filters works."""
    assert check_filter_match(unit_equals_filter, 'test-content')
    assert not check_filter_match(unit_equals_filter, 'other-content')


def test_not_equals_filter_mode(unit_not_equals_filter):
    """Test that the not equals (^=) filters works."""
    assert not check_filter_match(unit_not_equals_filter, 'test-content')
    assert check_filter_match(unit_not_equals_filter, 'other-content')


def test_contains_filter_mode(unit_contains_filter):
    """Test that the contains (~) filters works."""
    assert check_filter_match(unit_contains_filter, 'test-content')
    assert check_filter_match(unit_contains_filter, 'test-content/0')
    assert check_filter_match(unit_contains_filter, 'test-content/1*')
    assert check_filter_match(unit_contains_filter, 'new-test-content/1*')
    assert not check_filter_match(unit_contains_filter, 'other-content')
    assert not check_filter_match(unit_contains_filter, 'test')
    assert not check_filter_match(unit_contains_filter, 'content')


def test_not_contains_filter_mode(unit_not_contains_filter):
    """Test that the not contains (^~) filters works."""
    assert not check_filter_match(unit_not_contains_filter, 'test-content')
    assert check_filter_match(unit_not_contains_filter, 'other-content')
