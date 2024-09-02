from datetime import datetime, timedelta
import os
from tempfile import TemporaryDirectory
from uuid import uuid4

import pytest

from jockey.cache import FileCache, Reference


@pytest.fixture
def temp_dir():
    """Creates a temporary directory for use in tests."""
    with TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def file_cache(temp_dir):
    """Provides a FileCache instance using the temporary directory."""
    return FileCache(base_path=temp_dir, max_age=300)


@pytest.fixture
def ref():
    return Reference("test.site.local", "main", "production", "status")


@pytest.fixture
def rand_ref():
    return Reference("test.site.local", "main", "random", uuid4().hex)


@pytest.fixture
def bad_ref():
    return Reference("test.site.local", "does", "not", "exist")


def expire(file_cache: FileCache, ref: Reference):
    """Mocks expiration for an entry by overriding the file times."""
    old_time = datetime.now() - timedelta(minutes=123)
    os.utime(file_cache.file_path_for(ref), (old_time.timestamp(), old_time.timestamp()))


@pytest.mark.parametrize(
    "cloud, controller, model, component, want",
    [
        ("localhost", "lxd", "openstack", "status", "localhost_lxd_openstack_status"),
        ("cluster.local", "maas", "ceph", "status", "cluster-local_maas_ceph_status"),
        (
            "admin.company.local",
            "company:cloud",
            "admin/admin:openstack",
            "status",
            "admin-company-local_company-cloud_admin-admin-openstack_status",
        ),
    ],
)
def test_reference_str(cloud: str, controller: str, model: str, component: str, want: str):
    ref = Reference(cloud, controller, model, component)
    assert str(ref) == want


@pytest.mark.parametrize(
    "cloud, controller, model, component, want",
    [
        ("localhost", "lxd", "openstack", "status", "Reference('localhost', 'lxd', 'openstack', 'status')"),
        ("cluster.local", "maas", "ceph", "status", "Reference('cluster.local', 'maas', 'ceph', 'status')"),
        (
            "admin.company.local",
            "company:cloud",
            "admin/admin:openstack",
            "status",
            "Reference('admin.company.local', 'company:cloud', 'admin/admin:openstack', 'status')",
        ),
    ],
)
def test_reference_repr(cloud: str, controller: str, model: str, component: str, want: str):
    ref = Reference(cloud, controller, model, component)
    assert repr(ref) == want


@pytest.mark.parametrize(
    "cloud, controller, model, component, ext, want",
    [
        ("localhost", "lxd", "openstack", "status", "json", "localhost_lxd_openstack_status.json"),
        ("cluster.local", "maas", "ceph", "status", "txt", "cluster-local_maas_ceph_status.txt"),
        (
            "admin.company.local",
            "company:cloud",
            "admin/admin:openstack",
            "status",
            "yml",
            "admin-company-local_company-cloud_admin-admin-openstack_status.yml",
        ),
    ],
)
def test_reference_to_file_name(cloud: str, controller: str, model: str, component: str, ext: str, want: str):
    ref = Reference(cloud, controller, model, component)
    assert ref.to_file_name(ext) == want


def test_file_cache_init(temp_dir):
    file_cache = FileCache(base_path=temp_dir, max_age=6000)
    assert file_cache.base_path == temp_dir
    assert file_cache.max_age == 6000


def test_file_cache_repr(file_cache):
    assert repr(file_cache) == f"FileCache({file_cache.base_path}, max_age=300)"


def test_file_cache_reference_for(file_cache):
    ref = file_cache.reference_for("localhost", "main", "production", "status")
    assert isinstance(ref, Reference)
    assert str(ref) == "localhost_main_production_status"


def test_file_cache_clear(file_cache, rand_ref):
    file_cache.write(rand_ref, {})
    assert os.path.exists(file_cache.file_path_for(rand_ref))
    assert len(os.listdir(file_cache.base_path)) > 0

    file_cache.clear()
    assert not os.path.exists(file_cache.file_path_for(rand_ref))
    assert len(os.listdir(file_cache.base_path)) == 0


def test_file_cache_write_read(file_cache, ref):
    data = {
        "string": "Hello world!",
        "int": 1,
        "float": 3.141592653589793,
        "bool": True,
        "none": None,
        "list": ["a", 2, 3.5],
        "obj": {"a": 1, "b": 2},
    }

    file_cache.write(ref, data)
    assert file_cache.read(ref) == data


def test_file_cache_read_not_found(file_cache, ref):
    with pytest.raises(FileNotFoundError):
        file_cache.read(ref)


def test_file_cache_has(file_cache, rand_ref):
    assert not file_cache.has(rand_ref)

    file_cache.write(rand_ref, {})
    assert file_cache.has(rand_ref)


def test_file_cache_delete(file_cache, rand_ref):
    file_cache.write(rand_ref, {})
    assert file_cache.has(rand_ref)

    file_cache.delete(rand_ref)
    assert not file_cache.has(rand_ref)


def test_file_cache_last_modified(file_cache, rand_ref):
    file_cache.write(rand_ref, {})
    last_modified = file_cache.last_modified(rand_ref)

    assert last_modified is not None
    assert abs(last_modified - datetime.now().timestamp()) < 1


def test_file_cache_age(file_cache, rand_ref):
    file_cache.write(rand_ref, {})

    # mock the last modified time to be 10 seconds ago
    old_time = datetime.now() - timedelta(seconds=10)
    os.utime(file_cache.file_path_for(rand_ref), (old_time.timestamp(), old_time.timestamp()))

    assert file_cache.age(rand_ref) >= 10


def test_file_cache_is_expired(file_cache, rand_ref):
    file_cache.write(rand_ref, {})
    expire(file_cache, rand_ref)
    assert file_cache.is_expired(rand_ref)


def test_file_cache_entry_or(file_cache, rand_ref):
    # simulate missing entry
    assert file_cache.entry_or(rand_ref, lambda: {"hello": "world"}) == {"hello": "world"}

    # simulate working entry
    file_cache.write(rand_ref, {"abc": 123})
    assert file_cache.entry_or(rand_ref, lambda: {"hello": "world"}) == {"abc": 123}

    # simulate expired entry
    expire(file_cache, rand_ref)
    assert file_cache.entry_or(rand_ref, lambda: {"hi": "there"}) == {"hi": "there"}
    assert file_cache.read(rand_ref) == {"hi": "there"}
