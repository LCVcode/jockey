# File: test_objects.py
import os
import random
from string import ascii_letters, digits

from orjson import loads as json_loads
import pytest

from jockey.objects import FullStatus, Object
from tests.test_util import SAMPLES_DIR


@pytest.mark.parametrize(
    "obj, want",
    [
        (Object.APPLICATION, "application"),
        (Object.UNIT, "unit"),
        (Object.MACHINE, "machine"),
    ],
)
def test_object_str(obj: Object, want: str):
    assert str(obj) == want


@pytest.mark.parametrize(
    "obj, want",
    [
        (Object.APPLICATION, "Object.APPLICATION"),
        (Object.UNIT, "Object.UNIT"),
        (Object.MACHINE, "Object.MACHINE"),
    ],
)
def test_object_repr(obj: Object, want: str):
    assert repr(obj) == want


@pytest.mark.parametrize(
    "obj1, obj2, want",
    [
        pytest.param(Object.APPLICATION, Object.APPLICATION, True, id="APPLICATION-APPLICATION"),
        pytest.param(Object.UNIT, Object.MACHINE, False, id="UNIT-MACHINE"),
        pytest.param(Object.MACHINE, Object.MACHINE, True, id="MACHINE-MACHINE"),
        pytest.param(Object.UNIT, Object.UNIT, True, id="UNIT-UNIT"),
        pytest.param(Object.APPLICATION, "some str", False, id="APPLICATION-str"),
        pytest.param(Object.UNIT, 213, False, id="UNIT-int"),
        pytest.param(Object.UNIT, True, False, id="UNIT-bool"),
    ],
)
def test_object_eq(obj1: Object, obj2: Object, want: bool):
    assert (obj1 == obj2) == want
    assert (obj1 != obj2) != want


def test_object_hash():
    assert isinstance(hash(Object.APPLICATION), int)


def test_object_tokens():
    got = Object.tokens()

    # assert the return characteristics
    assert isinstance(got, set)
    assert len(got) > 0

    # assert the existence of the fundamentals
    assert "applications" in got
    assert "units" in got
    assert "machines" in got


@pytest.mark.parametrize(
    "string, want",
    [
        ("app", Object.APPLICATION),
        ("a", Object.APPLICATION),
        ("unit", Object.UNIT),
        ("u", Object.UNIT),
        ("machine", Object.MACHINE),
        ("m", Object.MACHINE),
    ],
)
def test_object_from_str(string: str, want: Object):
    assert Object.from_str(string) == want


def test_object_from_str_bad_name():
    with pytest.raises(ValueError):
        Object.from_str("".join(random.sample(ascii_letters + digits, k=12)))


@pytest.mark.parametrize(
    "string, want_obj, want_field",
    [
        ("apps.field", Object.APPLICATION, "field"),
        ("units.field", Object.UNIT, "field"),
        ("machines.field", Object.MACHINE, "field"),
        ("a.field.sub", Object.APPLICATION, "field.sub"),
        ("u.field.sub", Object.UNIT, "field.sub"),
        ("m.field.sub", Object.MACHINE, "field.sub"),
        ("app", Object.APPLICATION, None),
        ("unit", Object.UNIT, None),
        ("machine", Object.MACHINE, None),
    ],
)
def test_object_parse(string: str, want_obj: Object, want_field: str):
    assert Object.parse(string) == (want_obj, want_field)


def test_object_parse_bad_name():
    with pytest.raises(ValueError):
        Object.parse("".join(random.sample(ascii_letters + digits, k=12)))


@pytest.mark.parametrize(
    "sample, obj, names",
    [
        (
            "k8s-core-juju-status.json",
            Object.APPLICATION,
            {"calico", "containerd", "easyrsa", "etcd", "kubernetes-control-plane", "kubernetes-worker"},
        ),
        (
            "k8s-core-juju-status.json",
            Object.UNIT,
            {
                "easyrsa/0",
                "etcd/0",
                "kubernetes-control-plane/0",
                "calico/1",
                "containerd/1",
                "kubernetes-worker/0",
                "calico/0",
                "containerd/0",
            },
        ),
        ("k8s-core-juju-status.json", Object.MACHINE, {"0", "1"}),
    ],
)
def test_object_collect(obj: Object, sample: str, names: set[str]):
    sample_path = os.path.join(SAMPLES_DIR, sample)
    with open(sample_path) as f:
        sample_status: FullStatus = json_loads(f.read())

    got = obj.collect(sample_status)
    assert isinstance(got, list)

    got_names = set(map(lambda item: item["name"], got))
    assert got_names == names


def test_object_collect_bad_collector():
    obj = Object.APPLICATION
    obj.value.from_juju_status = 2

    with pytest.raises(ValueError):
        Object.collect(
            Object.APPLICATION,
            {},
        )
