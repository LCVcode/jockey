import json
import pytest
from jockey import get_machines


@pytest.fixture
def k8s_core_juju_status():
    """A simple Kubernetes core Juju status."""
    with open("tests/k8s-core-juju-status.json") as f:
        status = json.loads(f.read())
    return status


def test_get_machines(k8s_core_juju_status):
    """Test that get_machines correctly returns all machines."""
    assert sorted(get_machines(k8s_core_juju_status)) == ["0", "0/lxd/0", "1"]
