import pytest
from jockey.jockey import parse_filter_string, FilterMode


def test_filter_mode_retrieval():
    """Test that FilterModes are retrieved correctly."""

    assert (
        next(mode for mode in FilterMode if mode.value == "~")
        == FilterMode.CONTAINS
    )


def test_valid_filters():
    """Test that valid filter strings work."""

    valid_filters = (
        ("u~hw-health", "unit", FilterMode.CONTAINS, "hw-health"),
        (
            "app!=nrpe-host",
            "application",
            FilterMode.NOT_EQUALS,
            "nrpe-host",
        ),
        ("charm!~nova", "charm", FilterMode.NOT_CONTAINS, "nova"),
        ("ip=127.0.0.1", "ip", FilterMode.EQUALS, "127.0.0.1"),
    )
    for filter_str, object_type, mode, content in valid_filters:
        assert parse_filter_string(filter_str) == (
            object_type,
            mode,
            content,
        )


def test_invalid_object_types():
    """Test filter strings that have bad object types."""

    bad_filters = ("unite=unit-name", "appp!~cool-app")
    with pytest.raises(AssertionError):
        for filter_str in bad_filters:
            parse_filter_string(filter_str)


def test_blacklisted_characters():
    """Test that filters detect blacklisted characters."""

    blacklist_filters = (
        "unit!=nova_compute",
        "charm=glance,cinder",
        "ip=192.168,1,1",
        "unit~:test",
        "u!~test;",
    )
    with pytest.raises(AssertionError):
        for filter_str in blacklist_filters:
            parse_filter_string(filter_str)


def test_invalid_filter_modes():
    """Test that filters detect invalid filter modes."""

    invalid_feature_modes = (
        "u===unit",
        "app~!app",
        "charm!charm",
        "hostname=-=nodename",
        "ip127.0.0.1",
        "machine!!=14/lxd/0",
    )
    with pytest.raises(AssertionError):
        for filter_str in invalid_feature_modes:
            parse_filter_string(filter_str)


def test_empty_content():
    """Test that empty content is detected."""

    empty_content = (
        "charm~",
        "application!~",
        "unit=",
        "m!=",
        "ip=",
        "hostname~",
    )
    with pytest.raises(AssertionError):
        for filter_str in empty_content:
            parse_filter_string(filter_str)
