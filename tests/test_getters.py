import json
import pytest
from jockey import get_machines, get_units


@pytest.fixture
def k8s_core_juju_status():
    """A simple Juju status for Kubernetes core. Nothin special here."""
    with open("tests/k8s-core-juju-status.json") as f:
        status = json.loads(f.read())
    return status


@pytest.fixture
def empty_application_status():
    """
    A Juju status for Kubernetes core that has empty principal and subordinate
    applications.  That is, applications with zero units.

    kubernetes-service-checks is a principal charm with no units.
    nrpe is a subordinate charm with no units.
    """
    with open("tests/juju-status-empty-applications.json") as f:
        status = json.loads(f.read())
    return status


def test_get_machines(k8s_core_juju_status):
    """Test that get_machines correctly returns all machines."""
    assert sorted(get_machines(k8s_core_juju_status)) == ["0", "0/lxd/0", "1"]


def test_get_units(k8s_core_juju_status, empty_application_status):
    assert sorted(get_units(k8s_core_juju_status)) == [
        "calico/0",
        "calico/1",
        "containerd/0",
        "containerd/1",
        "easyrsa/0",
        "etcd/0",
        "kubernetes-control-plane/0",
        "kubernetes-worker/0",
    ]

    assert sorted(get_units(empty_application_status)) == [
        "calico/0",
        "calico/1",
        "containerd/0",
        "containerd/1",
        "easyrsa/0",
        "etcd/0",
        "kubernetes-control-plane/0",
        "kubernetes-worker/0",
    ]
