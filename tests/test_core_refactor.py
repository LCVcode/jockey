import json
import os

from jockey.core import query
from jockey.juju_conversions import charm_to_applications, get_hostnames, get_ips, hostname_to_machine
from jockey.status_loader import get_juju_status

from tests.test_util import SAMPLES_DIR


K8S_SAMPLE_PATH = os.path.join(SAMPLES_DIR, "k8s-core-juju-status.json")


def load_status():
    with open(K8S_SAMPLE_PATH, "r") as sample_file:
        return json.loads(sample_file.read())


def test_query_keeps_expected_unit_and_machine_results():
    assert list(query(object_type="u", filter_strings=[], file=K8S_SAMPLE_PATH)) == [
        "easyrsa/0",
        "etcd/0",
        "kubernetes-control-plane/0",
        "calico/1",
        "containerd/1",
        "kubernetes-worker/0",
        "calico/0",
        "containerd/0",
    ]
    assert list(query(object_type="m", filter_strings=[], file=K8S_SAMPLE_PATH)) == [
        "0",
        "0/lxd/0",
        "1",
    ]


def test_juju_conversion_helpers_cover_containers():
    status = load_status()

    assert sorted(get_hostnames(status)) == ["juju-36490e-0", "juju-36490e-0-lxd-0", "juju-36490e-1"]
    assert sorted(get_ips(status)) == ["10.118.249.130", "10.118.249.243", "10.192.62.201"]
    assert hostname_to_machine(status, "juju-36490e-0-lxd-0") == "0/lxd/0"


def test_charm_to_applications_maps_charms_correctly():
    status = load_status()
    assert list(charm_to_applications(status, "etcd")) == ["etcd"]
    assert list(charm_to_applications(status, "missing-charm")) == []


def test_status_loader_projects_only_query_fields():
    status = get_juju_status(file=K8S_SAMPLE_PATH)

    assert sorted(status.keys()) == ["applications", "machines"]
    assert "model" not in status
    assert "offers" not in status

    easyrsa = status["applications"]["easyrsa"]
    assert sorted(easyrsa.keys()) == ["charm", "units"]
    unit = easyrsa["units"]["easyrsa/0"]
    assert sorted(unit.keys()) == ["machine", "subordinates"]

    machine = status["machines"]["0"]
    assert sorted(machine.keys()) == ["containers", "hardware", "hostname", "ip-addresses"]
    container = machine["containers"]["0/lxd/0"]
    assert sorted(container.keys()) == ["hostname", "ip-addresses"]
