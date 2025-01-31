#!/usr/bin/env python3
# Jockey is a CLI utility that facilitates quick retrieval of Juju objects that
# match given filters.
# Author: Connor Chamberlain

from dataclasses import dataclass
from enum import Enum
import json
import logging
import os
import re
import subprocess
from typing import Any, Dict, Generator, Iterable, List, Optional

from jockey.cache import load_cache, new_cache_context, update_cache
from jockey.log import configure_logging


logger = logging.getLogger(__name__)


JujuStatus = Dict[str, Any]


class FilterMode(Enum):
    EQUALS = "="
    CONTAINS = "~"
    NOT_EQUALS = "^="
    NOT_CONTAINS = "^~"


POSITIVE_MODES = (
    FilterMode.EQUALS,
    FilterMode.CONTAINS,
)


NEGATIVE_MODES = (
    FilterMode.NOT_EQUALS,
    FilterMode.NOT_CONTAINS,
)


class ObjectType(Enum):
    CHARM = ("charms", "charm", "c")
    APP = ("applications", "app", "apps", "application", "a")
    UNIT = ("units", "unit", "u")
    MACHINE = ("machines", "machine", "m")
    IP = ("ips", "address", "addresses", "ip", "i")
    HOSTNAME = ("hostnames", "hostname", "host", "hosts", "h")
    AVAILABILITY_ZONE = ("availability-zone", "availability_zone", "az", "zone")


def list_abbreviations() -> str:
    pad = 15

    header = "OBJECT TYPE".ljust(pad, " ") + "SHORT NAMES"
    lines = [obj_type.value[0].ljust(pad, " ") + ", ".join(obj_type.value[1:]) for obj_type in ObjectType]
    return "\n".join([header, *lines])


INFO_MESSAGE = f"""
+----+
|NOTE|
+----+
Jockey is a work-in-progress currently only supports querying:
    units
    machines


+-------+
|FILTERS|
+-------+
Filters have a three-part syntax:
    <object type><filter code><content>

<object type> can be any supported Juju object types or their equivalent
abbreviations (see "SHORT NAMES", below).  These values are identical to the
`object` argument in the Jockey CLI.

<filter code> specifies how objects should be filtered relative to <content>
There are four possible values for <filter code>:
    {FilterMode.EQUALS.value.ljust(3)}: matches
    {FilterMode.NOT_EQUALS.value.ljust(3)}: does not match
    {FilterMode.CONTAINS.value.ljust(3)}: contains
    {FilterMode.NOT_CONTAINS.value.ljust(3)}: does not contain
Exactly one <filter code> must be given per filter.

<content> is a given string that will be used to filter Juju object names.


+-----------+
|SHORT NAMES|
+-----------+
Jockey object name abbreviations:

{list_abbreviations()}


+---------------+
|EXAMPLE QUERIES|
+---------------+
 Get all units:
     jockey units

 Get all nova-compute units:
     jockey units application=nova-compute

 Get the hw-health unit on a machine with a partial hostname "e01":
    jockey u a=hw-health host~e01

 Get all non-lxd machines:
     jockey m m^~lxd


+-------------------+
|OPERATIONS EXAMPLES|
+-------------------+
 Run a 'show-sel' action a machine with a partial host name 'ts1363co':
     juju run-action --wait $(jockey u a~hw-hea m~ts1363co) show-sel
"""


@dataclass
class JockeyFilter:
    obj_type: ObjectType
    mode: FilterMode
    content: str


def positive_filters(
    filters: Iterable[JockeyFilter],
) -> Generator[JockeyFilter, None, None]:
    """Extract the positive filters from a group of filters."""
    for f in filters:
        if f.mode in POSITIVE_MODES:
            yield f


def negative_filters(
    filters: Iterable[JockeyFilter],
) -> Generator[JockeyFilter, None, None]:
    """Extract the negative filters from a group of filters."""
    for f in filters:
        if f.mode in NEGATIVE_MODES:
            yield f


def convert_object_abbreviation(abbrev: str) -> Optional[ObjectType]:
    """
    Convert an object type abbreviation into an ObjectType.  If the abbreviation
    is not a valid Juju object, None will be returned.

    Arguments
    =========
    abbrev (str)
        A possibly abbreviated object name.

    Returns
    =======
    object_type (ObjectType) [optional]
        The ObjectType corresponding with the given abbrevation, if any.
    """
    abbrev = abbrev.lower()
    return next((obj_type for obj_type in ObjectType if abbrev in obj_type.value), None)


def parse_filter_string(
    filter_str: str,
) -> JockeyFilter:
    """
    Parse a filter string down into its object type, filter code, and content.

    :param filter_str str: The raw filter string.
    :return jockey_filter (JockeyFilter): A filter that matches the given filter string.
    """

    # Regex to extract characters in the filter code
    filter_code_pattern = re.compile(r"[=^~]+")

    # Check that exactly one filter code is used
    filter_codes = filter_code_pattern.findall(filter_str)
    assert len(filter_codes) == 1, "Incorrect number of filter codes detected."

    # Extract the filter code
    match = filter_code_pattern.search(filter_str)
    assert match

    # Extract object type
    object_type = convert_object_abbreviation(filter_str[: match.start()])
    assert object_type, "Invalid object type detected in filter string."

    # Verify the given filter code
    filter_mode = next((mode for mode in FilterMode if mode.value == match.group()), None)
    assert filter_mode, f"Invalid filter mode detected: {match.group()}."

    # Extract filter content, after the filter code
    content = filter_str[match.end() :]
    assert content, "Empty content detected in filter string."

    # Check for blacklisted characters in filter content
    char_blacklist = ("_", ":", ";", "\\", "\t", "\n", ",")
    assert not any(
        char in char_blacklist for char in content
    ), "Blacklisted characters detected in filter string content."

    return JockeyFilter(obj_type=object_type, mode=filter_mode, content=content)


FILTER_ACTION_MAP = {
    FilterMode.EQUALS: lambda c, v: c == v,
    FilterMode.NOT_EQUALS: lambda c, v: c != v,
    FilterMode.CONTAINS: lambda c, v: c in v,
    FilterMode.NOT_CONTAINS: lambda c, v: c not in v,
}


def check_filter_match(jockey_filter: JockeyFilter, value: str) -> bool:
    """
    Check if a value satisfied a Jockey filter.

    Arguments
    =========
    jockey_filter (JockeyFilter)
        A single Jockey filter
    value (str)
        A string to test against the filter

    Returns
    =======
    is_match (bool)
        True if value satisfies jockey_filter, else False
    """
    action = FILTER_ACTION_MAP[jockey_filter.mode]
    return action(jockey_filter.content, value)


def check_filter_batch_match(filter_list: Iterable[JockeyFilter], batch: Iterable[str]) -> bool:
    """
    Check if a batch of Juju objects (as strings) satisfies a set of filters.
    The batch must satisfy all positve filters and trigger no negative filters
    to return a True.

    This is used in cases where a single Juju object contains muliple children,
    such as an Application having many Units.

    Just like check_filter_match, this function ignores the Juju object type
    and simply performs the relevant string comparisons.

    Arguments
    =========
    filter_list (Iterable[JockeyFilter])
        A set of Jockey filters to apply.
    batch (Iterable[str])
        A set of object names to be tested.

    Returns
    =======
    match_success (bool)
        True if all of batch pass testings against filter_list, else False.
    """
    batch = tuple(batch)
    filter_list = tuple(filter_list)
    pos_filters = tuple(positive_filters(filter_list))
    neg_filters = tuple(negative_filters(filter_list))

    # First, check if any negative filters disqualify the batch
    for filt in neg_filters:
        if not all(check_filter_match(filt, item) for item in batch):
            return False

    # Finally, check that all positive filters are satisfied by batch
    for filt in pos_filters:
        if not any(check_filter_match(filt, item) for item in batch):
            return False

    return True


def is_app_principal(status: JujuStatus, app_name: str) -> bool:
    """
    Test if a given application is principal.  True indicates principal and
    False indicates subordinate.

    Arguments
    =========
    status (JujuStatus)
        The current Juju status in json format.
    app_name (str)
        The name of the application to check.

    Returns
    =======
    is_principal (bool)
        Whether the indicated application is principal.
    """
    return "subordinate-to" not in status["applications"][app_name]


def get_principal_unit_for_subordinate(status: JujuStatus, unit_name: str) -> str:
    """Get the name of a princpal unit for a given subordinate unit."""
    for app, data in status["applications"].items():

        # Skip other subordinate applications
        if not is_app_principal(status, app):
            continue

        # Check if given unit is a subordinate of any of these units
        for unit, unit_data in data["units"].items():
            if unit_name in unit_data["subordinates"]:
                return unit

    return ""


def get_applications(status: JujuStatus) -> Generator[str, None, None]:
    """
    Get all applications in the Juju status by name.

    Arguments
    =========
    status (JujuStatus)
        The current Juju status in json format.

    Returns
    =======
    application_names (Generator[str])
        All application names, in no particular order, as a generator.
    """
    for app in status["applications"]:
        yield app


def get_charms(status: JujuStatus) -> Generator[str, None, None]:
    """
    Get all charms in the Juju status by name.

    Arguments
    =========
    status (JujuStatus)
        The current Juju status in json format.

    Returns
    =======
    charm_names (Generator[str])
        All charms names, in no particular order, as a generator.
    """
    for app in get_applications(status):
        yield status["applications"][app]["charm"]


def get_units(status: JujuStatus) -> Generator[str, None, None]:
    """
    Get all units in the Juju status by name.

    Arguments
    =========
    status (JujuStatus)
        The current Juju status in json format.

    Returns
    =======
    unit_names (Generator[str])
        All unit names, in no particular order, as a generator.
    """
    for app in get_applications(status):

        # Skip subordinate applicaitons
        if not is_app_principal(status, app):
            continue

        # Skip applications that have no deployed units
        if "units" not in status["applications"][app]:
            continue

        for unit_name, data in status["applications"][app]["units"].items():
            # Generate principal unit
            yield unit_name

            # Check if subordinate units exist
            if "subordinates" not in data:
                continue

            # Generate subordinate units
            for subordinate_unit_name in data["subordinates"]:
                yield subordinate_unit_name


def get_machines(status: JujuStatus) -> Generator[str, None, None]:
    """
    Get all machines in the Juju model, including containers.

    Arguments
    =========
    status (JujuStatus)
        The current Juju status in json format.

    Returns
    =======
    machine_ids (Generator[str])
        All machines, in no particular order, as a generator.
    """
    for id in status["machines"].keys():
        yield id

        if "containers" not in status["machines"][id]:
            continue

        for container in status["machines"][id]["containers"]:
            yield container


def get_hostnames(status: JujuStatus) -> Generator[str, None, None]:
    """
    Get all machine hostnames in the Juju model.

    Arguments
    =========
    status (JujuStatus)
        The current Juju status in json format.

    Returns
    =======
    hostnames (Generator[str])
        All hostnames, in no particular order, as a generator.
    """
    for machine in status["machines"]:
        yield machine["hostname"]


def get_ips(status: JujuStatus) -> Generator[str, None, None]:
    """
    Get all machine ips in the Juju model.

    Arguments
    =========
    status (JujuStatus)
        The current Juju status in json format.

    Returns
    =======
    ips (Generator[str])
        All ips, in no particular order, as a generator.
    """
    for machine in status["machines"]:
        for address in machine["ip-addresses"]:
            yield address


def charm_to_applications(status: JujuStatus, charm_name: str) -> Generator[str, None, None]:
    """
    Given a charm name, get all applications using it, as a generator. If no
    matching charm is found, the generator will be empty.

    Arguments
    =========
    status (JujuStatus)
        The current Juju status in json format.
    charm_name (str)
        The name of the charm to find applications for.


    Returns
    =======
    applications (Generator[str])
        All applications that match the given charm name.
    """
    for application in status["applications"]:
        if application["charm"] == charm_name:
            yield application


def application_to_charm(status: JujuStatus, app_name: str) -> Optional[str]:
    """
    Given an application name, get the charm it is using, if any.

    Arguments
    =========
    status (JujuStatus)
        The current Juju status in json format.
    app_name (str)
        The name of the applicaiton to find a charm for.

    Returns
    =======
    charm (str) [optional]
        The name of the charm, if the indicated application exists.
    """
    try:
        return status["applications"][app_name]["charm"]
    except KeyError:
        return None


def application_to_units(status: JujuStatus, app_name: str) -> Generator[str, None, None]:
    """
    Given an application name, get all of its untis, as a generator.  If no
    matching application is found, the generator will be empty.

    Arguments
    =========
    status (JujuStatus)
        The current Juju status in json format.
    app_name (str)
        The name of the applicaiton to find a units for.

    Returns
    =======
    units (Generator[str])
        All units of the given application.
    """
    for application, data in status["applications"].items():

        if application != app_name:
            continue

        for unit_name in data["units"].keys():
            yield unit_name


def unit_to_application(status: JujuStatus, unit_name: str) -> Optional[str]:
    """
    Given a unit name, get its application name.


    Arguments
    =========
    status (JujuStatus)
        The current Juju status in json format.
    unit_name (str)
        The name of the unit to find an application for.

    Returns
    =======
    application (str) [optional]
        The name of the corresponding application.
    """
    app_name = unit_name.split("/")[0]

    if app_name in status["applications"]:
        return app_name

    return None


def subordinate_unit_to_principal_unit(status: JujuStatus, unit_name: str) -> str:
    """
    Given a unit name, get its principal unit.  If the given unit is principal,
    it will be returned as-is.

    Arguments
    =========
    status (JujuStatus)
        The current Juju status in json format.

    Returns
    =======
    unit_name (str)
        The name of the unit to check.
    """
    app = unit_to_application(status, unit_name)
    assert app, f"No application found for unit {unit_name}"
    app_data = status["applications"]

    if is_app_principal(status, app):
        return unit_name

    for p_app in app_data[app]["subordinate-to"]:

        if not is_app_principal(status, p_app):
            continue

        for p_unit in app_data[p_app]["units"]:
            if unit_name in app_data[p_app]["units"][p_unit]["subordinates"]:
                return p_unit

    raise Exception(f"No principal unit detected for unit {unit_name}")


def unit_to_machine(status: JujuStatus, unit_name: str) -> Optional[str]:
    """
    Given a unit name, get the ID of the machine it is running on, if any.
    Currently only works on units from principal applications.

    Arguments
    =========
    status (JujuStatus)
        The current Juju status in json format.
    unit_name (str)
        The name of the unit.

    Returns
    =======
    machine_id (str) [optional]
        The ID of the corresponding machine.
    """
    principal_unit_name = subordinate_unit_to_principal_unit(status, unit_name)
    app = unit_to_application(status, principal_unit_name)

    return status["applications"][app]["units"][principal_unit_name]["machine"]


def machine_to_units(status: JujuStatus, machine: str) -> Generator[str, None, None]:
    """
    Given an machine id, get all of its units, as a generator.  If no matching
    units are found, the generator will be empty.

    Arguments
    =========
    status (JujuStatus)
        The current Juju status in json format.
    machine (str)
        The ID of the machine to use.

    Returns
    =======
    units (Generator[str])
        All units on the given machine.
    """

    for unit in get_units(status):

        # Skip subordinate units
        app = unit_to_application(status, unit)
        assert app
        if not is_app_principal(status, app):
            continue

        if unit_to_machine(status, unit) == machine:
            yield unit

            if "subordinates" not in status["applications"][app]["units"][unit]:
                continue

            for subordinate_unit in status["applications"][app]["units"][unit]["subordinates"]:
                yield subordinate_unit


def machine_to_ips(status: JujuStatus, machine: str) -> Generator[str, None, None]:
    """
    Given an machine id, each of its IP addresses as a geneator.

    Arguments
    =========
    status (JujuStatus)
        The current Juju status in json format.
    machine (str)
        The ID of the machine to use.

    Returns
    =======
    addresses (Generator[str])
        The IP addresses of the machine.
    """
    if "lxd" in machine.lower():
        base_machine = status["machines"][machine.split("/")[0]]
        for ip in base_machine["containers"][machine]["ip-addresses"]:
            yield ip
    else:
        for ip in status["machines"][machine]["ip-addresses"]:
            yield ip


def ip_to_machine(status: JujuStatus, ip: str) -> str:
    """
    Given an ip, get the ID of the machine that owns it.

    Arguments
    =========
    status (JujuStatus)
        The current Juju status in json format.
    address (str)
        The IP address in question.

    Returns
    =======
    machine ID (str)
        ID of the machine owning the given IP.
    """
    for machine in status["machines"]:
        if ip in status["machines"][machine]["ip-addresses"]:
            return machine

    raise Exception(f"No machine found with IP {ip}")


def machine_to_availability_zone(status: JujuStatus, machine: str) -> Optional[str]:
    """
    Given an machine id, get its availability zone.

    Arguments
    =========
    status (JujuStatus)
        The current Juju status in json format.
    machine (str)
        The ID of the machine to use.

    Returns
    =======
    avaliability_zone (str)
        The machine's avilability zone.
    """
    if "lxd" in machine:
        # A container's availability zone is the same as its parent, so we grab that.
        machine, _, _ = machine.split("/")
    hardware = status["machines"][machine]["hardware"]
    for entry in hardware.split():
        key, value = entry.split("=")
        if key == "availability-zone":
            return value
    return None


def machine_to_hostname(status: JujuStatus, machine: str) -> str:
    """
    Given an machine id, get its hostname.

    Arguments
    =========
    status (JujuStatus)
        The current Juju status in json format.
    machine (str)
        The ID of the machine to use.

    Returns
    =======
    hostname (str)
        The machine's hostname.
    """
    if "lxd" in machine:
        physical_machine, _, container_id = machine.split("/")
        return status["machines"][physical_machine]["containers"][machine]["hostname"]
    return status["machines"][machine]["hostname"]


def hostname_to_machine(status: JujuStatus, hostname: str) -> str:
    """
    Given a hostname, get that machine's ID.

    Arguments
    =========
    status (JujuStatus)
        The current Juju status in json format.
    hostname (str)
        The machine's hostname.

    Returns
    =======
    machine (str)
        The ID of the machine with the given hostname.
    """
    for machine in get_machines(status):
        if status["machines"][machine]["hostname"] == hostname:
            return machine

    raise Exception(f"No machine found for hostname {hostname}")


def filter_units(status: JujuStatus, filters: List[JockeyFilter]) -> Generator[str, None, None]:
    """
    Get all units from a Juju status that match a list of filters.

    Arguments
    =========
    status (JujuStatus)
        The current Juju status in json format.
    filters (List[JockeyFilter])
        A list of parsed filters, provided to the CLI.

    Returns
    =======
    units (Generator[str])
        All matching units, as a generator.
    """

    charm_filters = [f for f in filters if f.obj_type == ObjectType.CHARM]
    app_filters = [f for f in filters if f.obj_type == ObjectType.APP]
    unit_filters = [f for f in filters if f.obj_type == ObjectType.UNIT]
    machine_filters = [f for f in filters if f.obj_type == ObjectType.MACHINE]
    ip_filters = [f for f in filters if f.obj_type == ObjectType.IP]
    hostname_filters = [f for f in filters if f.obj_type == ObjectType.HOSTNAME]
    az_filters = [f for f in filters if f.obj_type == ObjectType.AVAILABILITY_ZONE]

    for unit in get_units(status):
        # Check unit filters
        if not all(check_filter_match(u_filter, unit) for u_filter in unit_filters):
            continue

        if app_filters or charm_filters:
            # Check application filters
            app = unit_to_application(status, unit)
            assert app
            if not all(check_filter_match(a_filter, app) for a_filter in app_filters):
                continue

            # Check charm filters
            charm = application_to_charm(status, app)
            assert charm
            if not all(check_filter_match(c_filter, charm) for c_filter in charm_filters):
                continue

        # If there aren't any machine, IP, or hostname filters, just yield
        if not any((machine_filters, ip_filters, hostname_filters)):
            yield unit
            continue

        # Check machine filters
        machine = unit_to_machine(status, unit)
        assert machine
        if not all(check_filter_match(m_filter, machine) for m_filter in machine_filters):
            continue

        # Check hostname filters
        hostname = machine_to_hostname(status, machine)
        assert hostname
        if not all(check_filter_match(h_filter, hostname) for h_filter in hostname_filters):
            continue

        # Check IP filters
        ips = machine_to_ips(status, machine)
        assert ips
        if not all(any(check_filter_match(i_filter, ip) for ip in ips) for i_filter in ip_filters):
            continue

        # Check availability zone filter
        az = machine_to_availability_zone(status, machine)
        if not all(check_filter_match(az_filter, az) for az_filter in az_filters):
            continue

        yield unit


def filter_machines(status: JujuStatus, filters: List[JockeyFilter]) -> Generator[str, None, None]:
    """
    Get all machines from a Juju status that match a list of filters.

    Arguments
    =========
    status (JujuStatus)
        The current Juju status in json format.
    filters (List[JockeyFilter])
        A list of parsed filters, provided to the CLI.

    Returns
    =======
    machines (Generator[str])
        All matching machines, as a generator.
    """

    machine_filters = [f for f in filters if f.obj_type == ObjectType.MACHINE]
    hostname_filters = [f for f in filters if f.obj_type == ObjectType.HOSTNAME]
    ip_filters = [f for f in filters if f.obj_type == ObjectType.IP]
    az_filters = [f for f in filters if f.obj_type == ObjectType.AVAILABILITY_ZONE]

    unit_filters = [f for f in filters if f.obj_type == ObjectType.UNIT]
    app_filters = [f for f in filters if f.obj_type == ObjectType.APP]
    charm_filters = [f for f in filters if f.obj_type == ObjectType.CHARM]

    for machine in get_machines(status):
        # Check machine filters
        if not all(check_filter_match(m_filter, machine) for m_filter in machine_filters):
            continue

        # Check hostname filters
        hostname = machine_to_hostname(status, machine)
        assert hostname
        if not all(check_filter_match(h_filter, hostname) for h_filter in hostname_filters):
            continue

        # Check IP filters
        ips = machine_to_ips(status, machine)
        assert ips
        if not check_filter_batch_match(ip_filters, ips):
            continue

        # Check unit filters
        units = tuple(machine_to_units(status, machine))
        if not check_filter_batch_match(unit_filters, units):
            continue

        # Check application filters
        apps = tuple(unit_to_application(status, unit) for unit in units)
        assert all(apps)
        if not check_filter_batch_match(app_filters, apps):  # type: ignore
            continue

        # Check charm filters
        charms = tuple(application_to_charm(status, app) for app in apps)  # type: ignore
        if not check_filter_batch_match(charm_filters, charms):  # type: ignore
            continue

        # Check availability zone filter
        az = machine_to_availability_zone(status, machine)
        if not all(check_filter_match(az_filter, az) for az_filter in az_filters):
            continue

        yield machine


RETRIEVAL_MAP = {
    ObjectType.CHARM: None,
    ObjectType.APP: None,
    ObjectType.UNIT: filter_units,
    ObjectType.MACHINE: filter_machines,
    ObjectType.IP: None,
    ObjectType.HOSTNAME: None,
}


def get_juju_status(file: str = "", model_name: str = "", cache_age: float = 300) -> JujuStatus:
    """
    Loads a Juju status from a file, a Jockey cache, or the juju CLI.
    Providing a file ignores all caching.
    Loading a cache that is older than cache_age will trigger a re-caching of an
    updated Juju status.
    If model_name is not provided, it will be loaded from the JUJU_MODEL
    environment variable.

    Arguments
    ---------
    file (str) [optional]
        A local file to read from.
    model_name (str) [optional]
        The name of a Juju model.
    cache_age (float) [optional]
        The maximum allowable age of a Jockey cache.
    """
    # Prefer loading from a file, when provided
    if file:
        logger.debug("Loading local Juju status from %r", file)
        # print(dir(file))
        with open(file, "r") as f:
            return json.loads(f.read())

    # Get model name and build a CacheContext
    model_name = model_name or os.environ.get("JUJU_MODEL", None)
    assert model_name, "You must provide a Juju model name or have the `JUJU_MODEL` environment variable set."
    cache_context = new_cache_context(model=model_name, max_age=cache_age)

    # Load cache if it is still valid
    if cache_context.valid:
        return load_cache(cache_context)

    # Get Juju status from CLI and update cache
    logger.debug("Running a juju command to get status")
    status = json.loads(subprocess.run(["juju", "status", "--format", "json"], capture_output=True, text=True).stdout)
    update_cache(cache_context, status)

    return status
    """

    # Return cached status or ask Juju for a new status
    # configure the file cache
    cache_dir = cache if "cache" in args else None
    cache_age = cache_age if "cache_age" in args else None
    cache_refresh = refresh
    cache = FileCache(cache_dir, cache_age)
    if cache_refresh:
        cache.clear()
        logger.info("Cleared file cache at %s", args.cache)

    # obtain cloud configuration
    cloud_host = host if "host" in args else None
    cloud_user = user if "user" in args else None
    cloud_doas = sudo if "sudo" in args else None
    cloud_timeout = timeout if "timeout" in args else None
    cloud_juju = juju if "juju" in args else None

    # connect to the cloud and get the Juju status
    cloud = Cloud(host=cloud_host, user=cloud_user, doas=cloud_doas, timeout=cloud_timeout, juju=cloud_juju)

    try:
        status = cloud.juju_status
    except CloudCredentialsException as e:
        print(Panel(e.advice_markup(), title="[red]" + e.message), file=sys.stderr)
        return 126
    finally:
        cloud.close()
    """


def query(
    object_type: str, filter_strings: List[str], model: str = "", file: str = "", verbosity: int = 0
) -> Generator[str, None, None]:
    """
    Perform a Jockey query.  Use this fucntion as an entry point.

    Arugments
    =========
    object_type (str)
        The name of the object type being queried.
    filter_strings (List[str])
        A list of filters as strings.
    file (str) [optional]
        Local Juju status file to query.  Uses cached Juju status, if empty.
    verbosity (int) [optional]
        Verbosity setting from 0-3 (default=0).

    Returns
    =======
    query_result (List[str])
        A list of objects matching the query.  May be empty.
    """
    logger.debug("Starting Jockey query with: object=%r filter_strings=%r", object_type, filter_strings)
    configure_logging(verbosity)

    # Convert and validate object type to query
    juju_object = convert_object_abbreviation(object_type)
    assert juju_object, f"Object type '{object_type}' not recognized."

    # Get the approriate filtering function.  None indicates not supported.
    filter_function = RETRIEVAL_MAP.get(juju_object, None)
    assert filter_function, f"Querying of '{object_type}' is not yet supported."

    # Convert filter strings into JockeyFilter dataclasses
    filters = [parse_filter_string(filter_str) for filter_str in filter_strings]

    # Get the relevant Juju status
    status = get_juju_status(file=file, model_name=model)

    return filter_function(status, filters)
