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


# ============================================================================
# Tests for basic queryable objects (units and machines)
# ============================================================================


def test_query_all_units():
    """Test querying all units without filters."""
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


def test_query_all_machines():
    """Test querying all machines without filters."""
    assert list(query(object_type="m", filter_strings=[], file=K8S_SAMPLE_PATH)) == [
        "0",
        "0/lxd/0",
        "1",
    ]


def test_query_units_alias_variations():
    """Test that unit alias variations work."""
    units_long = list(query(object_type="units", filter_strings=[], file=K8S_SAMPLE_PATH))
    units_short = list(query(object_type="u", filter_strings=[], file=K8S_SAMPLE_PATH))
    assert units_long == units_short


def test_query_machines_alias_variations():
    """Test that machine alias variations work."""
    machines_long = list(query(object_type="machines", filter_strings=[], file=K8S_SAMPLE_PATH))
    machines_short = list(query(object_type="m", filter_strings=[], file=K8S_SAMPLE_PATH))
    assert machines_long == machines_short


# ============================================================================
# Tests for filtering by charm (queryable objects: units)
# ============================================================================


def test_filter_units_by_charm_exact_match():
    """Test filtering units by exact charm name."""
    result = list(query(object_type="u", filter_strings=["charm=etcd"], file=K8S_SAMPLE_PATH))
    assert result == ["etcd/0"]


def test_filter_units_by_charm_contains():
    """Test filtering units by charm name substring."""
    result = list(query(object_type="u", filter_strings=["charm~control"], file=K8S_SAMPLE_PATH))
    assert result == ["kubernetes-control-plane/0"]


def test_filter_units_by_charm_multiple_matches():
    """Test filtering units by charm with multiple matches."""
    result = list(query(object_type="u", filter_strings=["charm=calico"], file=K8S_SAMPLE_PATH))
    assert sorted(result) == ["calico/0", "calico/1"]


def test_filter_units_by_charm_negation():
    """Test filtering units by negated charm name."""
    result = list(query(object_type="u", filter_strings=["charm^=etcd"], file=K8S_SAMPLE_PATH))
    assert "etcd/0" not in result
    assert "kubernetes-worker/0" in result


def test_filter_units_by_charm_negation_contains():
    """Test filtering units by negated charm substring."""
    result = list(query(object_type="u", filter_strings=["charm^~kube"], file=K8S_SAMPLE_PATH))
    assert "kubernetes-control-plane/0" not in result
    assert "kubernetes-worker/0" not in result
    assert "etcd/0" in result


# ============================================================================
# Tests for filtering by application (queryable objects: units)
# ============================================================================


def test_filter_units_by_application_exact_match():
    """Test filtering units by application name."""
    result = list(query(object_type="u", filter_strings=["app=etcd"], file=K8S_SAMPLE_PATH))
    assert result == ["etcd/0"]


def test_filter_units_by_application_alias():
    """Test filtering units using application alias 'a'."""
    result_full = list(query(object_type="u", filter_strings=["app=etcd"], file=K8S_SAMPLE_PATH))
    result_short = list(query(object_type="u", filter_strings=["a=etcd"], file=K8S_SAMPLE_PATH))
    assert result_full == result_short


def test_filter_units_by_application_contains():
    """Test filtering units by application substring."""
    result = list(query(object_type="u", filter_strings=["app~kube"], file=K8S_SAMPLE_PATH))
    assert sorted(result) == ["kubernetes-control-plane/0", "kubernetes-worker/0"]


def test_filter_units_by_application_negation():
    """Test filtering units by negated application."""
    result = list(query(object_type="u", filter_strings=["application^=etcd"], file=K8S_SAMPLE_PATH))
    assert "etcd/0" not in result
    assert len(result) == 7  # all except etcd/0


# ============================================================================
# Tests for filtering by unit name (queryable objects: units)
# ============================================================================


def test_filter_units_by_unit_name_exact_match():
    """Test filtering units by exact unit name."""
    result = list(query(object_type="u", filter_strings=["unit=etcd/0"], file=K8S_SAMPLE_PATH))
    assert result == ["etcd/0"]


def test_filter_units_by_unit_name_contains():
    """Test filtering units by unit name substring."""
    result = list(query(object_type="u", filter_strings=["u~calico"], file=K8S_SAMPLE_PATH))
    assert sorted(result) == ["calico/0", "calico/1"]


def test_filter_units_by_unit_number():
    """Test filtering units by unit suffix."""
    result = list(query(object_type="u", filter_strings=["unit~/0"], file=K8S_SAMPLE_PATH))
    # All units ending in /0
    assert all("/0" in u for u in result)
    # easyrsa/0, etcd/0, kubernetes-control-plane/0, kubernetes-worker/0, calico/0, containerd/0
    assert len(result) == 6


# ============================================================================
# Tests for filtering by machine (queryable objects: units)
# ============================================================================


def test_filter_units_by_machine_exact_match():
    """Test filtering units by machine number."""
    result = list(query(object_type="u", filter_strings=["machine=0"], file=K8S_SAMPLE_PATH))
    # Units on machine 0: etcd/0, kubernetes-control-plane/0, and their subordinates calico/1, containerd/1
    assert sorted(result) == ["calico/1", "containerd/1", "etcd/0", "kubernetes-control-plane/0"]


def test_filter_units_by_machine_container():
    """Test filtering units by container machine."""
    result = list(query(object_type="u", filter_strings=["machine=0/lxd/0"], file=K8S_SAMPLE_PATH))
    assert result == ["easyrsa/0"]


def test_filter_units_by_machine_negation():
    """Test filtering units by negated machine."""
    result = list(query(object_type="u", filter_strings=["machine^=0"], file=K8S_SAMPLE_PATH))
    assert "etcd/0" not in result
    assert "kubernetes-worker/0" in result


def test_filter_units_by_machine_contains():
    """Test filtering units by machine substring (contains lxd)."""
    result = list(query(object_type="u", filter_strings=["machine~lxd"], file=K8S_SAMPLE_PATH))
    assert result == ["easyrsa/0"]


# ============================================================================
# Tests for filtering by hostname (queryable objects: units)
# ============================================================================


def test_filter_units_by_hostname_exact_match():
    """Test filtering units by exact hostname."""
    result = list(query(object_type="u", filter_strings=["host=juju-36490e-0"], file=K8S_SAMPLE_PATH))
    # Units on machine 0 (juju-36490e-0 hostname)
    assert sorted(result) == ["calico/1", "containerd/1", "etcd/0", "kubernetes-control-plane/0"]


def test_filter_units_by_hostname_contains():
    """Test filtering units by hostname substring."""
    result = list(query(object_type="u", filter_strings=["hostname~36490e-1"], file=K8S_SAMPLE_PATH))
    # Units on machine 1 have hostname containing juju-36490e-1
    assert sorted(result) == ["calico/0", "containerd/0", "kubernetes-worker/0"]


def test_filter_units_by_hostname_negation():
    """Test filtering units by negated hostname."""
    result = list(query(object_type="u", filter_strings=["hostname^~lxd"], file=K8S_SAMPLE_PATH))
    # Units on machines without "lxd" in hostname
    assert "easyrsa/0" not in result
    assert "kubernetes-worker/0" in result


# ============================================================================
# Tests for filtering by IP address (queryable objects: units)
# ============================================================================


def test_filter_units_by_ip_exact_match():
    """Test filtering units by exact IP address."""
    result = list(query(object_type="u", filter_strings=["ip=10.118.249.243"], file=K8S_SAMPLE_PATH))
    # Units on machine 0 (IP 10.118.249.243)
    assert sorted(result) == ["calico/1", "containerd/1", "etcd/0", "kubernetes-control-plane/0"]


def test_filter_units_by_ip_contains():
    """Test filtering units by IP substring."""
    result = list(query(object_type="u", filter_strings=["ip~10.118"], file=K8S_SAMPLE_PATH))
    # All units have IPs in the 10.118 range (except easyrsa/0 which might not be returned)
    assert len(result) == 7

    result_specific = list(query(object_type="u", filter_strings=["ip~10.118.249.243"], file=K8S_SAMPLE_PATH))
    assert len(result_specific) == 4  # Units on machine 0


def test_filter_units_by_ip_negation():
    """Test filtering units by negated IP."""
    result = list(query(object_type="u", filter_strings=["ip^=10.118.249.130"], file=K8S_SAMPLE_PATH))
    # Units NOT on machine with IP .130
    assert "kubernetes-worker/0" not in result
    assert "etcd/0" in result


# ============================================================================
# Tests for multi-part filters on units (combining multiple conditions)
# ============================================================================


def test_filter_units_by_app_and_machine():
    """Test filtering units by app AND machine together."""
    result = list(query(object_type="u", filter_strings=["app=etcd", "machine=0"], file=K8S_SAMPLE_PATH))
    assert result == ["etcd/0"]


def test_filter_units_by_app_and_hostname():
    """Test filtering units by app AND hostname together."""
    result = list(query(object_type="u", filter_strings=["app~kube", "host~36490e-0"], file=K8S_SAMPLE_PATH))
    assert result == ["kubernetes-control-plane/0"]


def test_filter_units_by_charm_and_ip():
    """Test filtering units by charm AND IP together."""
    result = list(query(object_type="u", filter_strings=["charm=calico", "ip=10.118.249.130"], file=K8S_SAMPLE_PATH))
    # calico/0 is on machine 1 (IP 10.118.249.130)
    assert result == ["calico/0"]

    result2 = list(query(object_type="u", filter_strings=["charm=calico", "ip=10.118.249.243"], file=K8S_SAMPLE_PATH))
    # calico/1 is on machine 0 (IP 10.118.249.243)
    assert result2 == ["calico/1"]


def test_filter_units_by_app_not_machine_and_charm():
    """Test filtering units with negation: app NOT on machine 0 AND charm=containerd."""
    result = list(query(object_type="u", filter_strings=["app=containerd", "machine^=0"], file=K8S_SAMPLE_PATH))
    # containerd/0 is on machine 1 (not machine 0)
    assert result == ["containerd/0"]

    # All containerd units
    result_all = list(query(object_type="u", filter_strings=["app=containerd"], file=K8S_SAMPLE_PATH))
    assert sorted(result_all) == ["containerd/0", "containerd/1"]


def test_filter_units_multiple_conditions_three_way():
    """Test filtering units with three conditions."""
    filters = ["app=kubernetes-worker", "host~36490e-1", "ip~10.118"]
    result = list(query(object_type="u", filter_strings=filters, file=K8S_SAMPLE_PATH))
    assert result == ["kubernetes-worker/0"]


# ============================================================================
# Tests for filtering by charm (queryable objects: machines)
# ============================================================================


def test_filter_machines_by_charm():
    """Test filtering machines by units of a given charm."""
    result = list(query(object_type="m", filter_strings=["charm=etcd"], file=K8S_SAMPLE_PATH))
    assert result == ["0"]


def test_filter_machines_by_charm_multiple_results():
    """Test filtering machines with multiple units of the charm."""
    result = list(query(object_type="m", filter_strings=["charm=calico"], file=K8S_SAMPLE_PATH))
    assert sorted(result) == ["0", "1"]


def test_filter_machines_by_charm_negation():
    """Test filtering machines that DON'T have units of a charm."""
    result = list(query(object_type="m", filter_strings=["charm^=etcd"], file=K8S_SAMPLE_PATH))
    assert "0" not in result
    assert "1" in result


# ============================================================================
# Tests for filtering by application (queryable objects: machines)
# ============================================================================


def test_filter_machines_by_application():
    """Test filtering machines by units of a given application."""
    result = list(query(object_type="m", filter_strings=["app=etcd"], file=K8S_SAMPLE_PATH))
    assert result == ["0"]


def test_filter_machines_by_application_multiple_results():
    """Test filtering machines with units of the application."""
    result = list(query(object_type="m", filter_strings=["application~kube"], file=K8S_SAMPLE_PATH))
    assert sorted(result) == ["0", "1"]


# ============================================================================
# Tests for filtering by unit (queryable objects: machines)
# ============================================================================


def test_filter_machines_by_unit_exact_match():
    """Test filtering machines by unit name."""
    result = list(query(object_type="m", filter_strings=["unit=etcd/0"], file=K8S_SAMPLE_PATH))
    assert result == ["0"]


def test_filter_machines_by_unit_contains():
    """Test filtering machines by unit substring."""
    result = list(query(object_type="m", filter_strings=["unit~control"], file=K8S_SAMPLE_PATH))
    assert result == ["0"]


# ============================================================================
# Tests for filtering by machine (queryable objects: machines)
# ============================================================================


def test_filter_machines_by_machine_self():
    """Test filtering machines by machine number."""
    result = list(query(object_type="m", filter_strings=["machine=0"], file=K8S_SAMPLE_PATH))
    assert result == ["0"]


def test_filter_machines_by_machine_negation():
    """Test filtering machines by negated machine (exclude specific machine)."""
    result = list(query(object_type="m", filter_strings=["machine^=0"], file=K8S_SAMPLE_PATH))
    # machine^=0 means "not equal to 0", which excludes exact match but containers are different
    assert "0" not in result
    # Containers of 0 are different machines, but this depends on filter behavior
    # Check actual results
    assert "1" in result


def test_filter_machines_by_machine_container_exact():
    """Test filtering machines by container machine exact match."""
    result = list(query(object_type="m", filter_strings=["machine=0/lxd/0"], file=K8S_SAMPLE_PATH))
    assert result == ["0/lxd/0"]


# ============================================================================
# Tests for filtering by hostname (queryable objects: machines)
# ============================================================================


def test_filter_machines_by_hostname_exact():
    """Test filtering machines by exact hostname."""
    result = list(query(object_type="m", filter_strings=["host=juju-36490e-0"], file=K8S_SAMPLE_PATH))
    assert result == ["0"]


def test_filter_machines_by_hostname_contains():
    """Test filtering machines by hostname substring."""
    result = list(query(object_type="m", filter_strings=["hostname~lxd"], file=K8S_SAMPLE_PATH))
    assert result == ["0/lxd/0"]


def test_filter_machines_by_hostname_negation():
    """Test filtering machines by negated hostname."""
    result = list(query(object_type="m", filter_strings=["hostname^~lxd"], file=K8S_SAMPLE_PATH))
    assert "0/lxd/0" not in result
    assert "0" in result
    assert "1" in result


# ============================================================================
# Tests for filtering by IP address (queryable objects: machines)
# ============================================================================


def test_filter_machines_by_ip_exact():
    """Test filtering machines by exact IP address."""
    result = list(query(object_type="m", filter_strings=["ip=10.118.249.243"], file=K8S_SAMPLE_PATH))
    assert result == ["0"]


def test_filter_machines_by_ip_contains():
    """Test filtering machines by IP substring."""
    result = list(query(object_type="m", filter_strings=["ip~10.118.249"], file=K8S_SAMPLE_PATH))
    # Machines 0 and 1 have IPs in the .243 and .130 range, containers inherit from parent
    assert sorted(result) == ["0", "1"]


def test_filter_machines_by_ip_negation():
    """Test filtering machines by negated IP address."""
    result = list(query(object_type="m", filter_strings=["ip^=10.118.249.130"], file=K8S_SAMPLE_PATH))
    assert "1" not in result
    assert "0" in result


# ============================================================================
# Tests for multi-part filters on machines (combining multiple conditions)
# ============================================================================


def test_filter_machines_by_hostname_and_ip():
    """Test filtering machines by hostname AND IP together."""
    filters = ["host=juju-36490e-0", "ip=10.118.249.243"]
    result = list(query(object_type="m", filter_strings=filters, file=K8S_SAMPLE_PATH))
    assert result == ["0"]


def test_filter_machines_by_app_and_hostname():
    """Test filtering machines by app AND hostname together."""
    result = list(query(object_type="m", filter_strings=["app=etcd", "host~36490e-0"], file=K8S_SAMPLE_PATH))
    assert result == ["0"]


def test_filter_machines_by_app_and_machine():
    """Test filtering machines by app and machine negation."""
    result = list(query(object_type="m", filter_strings=["app=containerd", "machine^~lxd"], file=K8S_SAMPLE_PATH))
    assert "0/lxd/0" not in result
    assert "1" in result


def test_filter_machines_by_machine_not_lxd_and_charm():
    """Test filtering machines that are NOT containers and have a charm."""
    result = list(query(object_type="m", filter_strings=["machine^~lxd", "charm=calico"], file=K8S_SAMPLE_PATH))
    assert "0/lxd/0" not in result
    assert sorted(result) == ["0", "1"]


def test_filter_machines_by_hostname_contains_and_unit_contains():
    """Test filtering machines by hostname AND unit name together."""
    result = list(query(object_type="m", filter_strings=["host~36490e-0", "unit~control"], file=K8S_SAMPLE_PATH))
    assert result == ["0"]


def test_filter_machines_multiple_conditions_complex():
    """Test filtering: exclude containers, filter by app, filter by hostname."""
    filters = ["machine^~lxd", "app~kube", "host~36490e"]
    result = list(query(object_type="m", filter_strings=filters, file=K8S_SAMPLE_PATH))
    assert sorted(result) == ["0", "1"]


# ============================================================================
# Tests for Juju conversion helpers and status projection
# ============================================================================


def test_juju_conversion_helpers_cover_containers():
    """Test that conversion helpers properly handle container machines."""
    status = load_status()

    assert sorted(get_hostnames(status)) == ["juju-36490e-0", "juju-36490e-0-lxd-0", "juju-36490e-1"]
    assert sorted(get_ips(status)) == ["10.118.249.130", "10.118.249.243", "10.192.62.201"]
    assert hostname_to_machine(status, "juju-36490e-0-lxd-0") == "0/lxd/0"


def test_charm_to_applications_maps_charms_correctly():
    """Test charm-to-application mapping."""
    status = load_status()
    assert list(charm_to_applications(status, "etcd")) == ["etcd"]
    assert list(charm_to_applications(status, "missing-charm")) == []


def test_charm_to_applications_subordinates():
    """Test charm-to-application mapping for subordinate charms."""
    status = load_status()
    # Calico and containerd are subordinates deployed to multiple machines
    calico_apps = list(charm_to_applications(status, "calico"))
    assert calico_apps == ["calico"]


def test_status_loader_projects_only_query_fields():
    """Test that status loader projects only the fields needed for queries."""
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
