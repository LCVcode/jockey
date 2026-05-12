#!/usr/bin/env python3
# Jockey is a CLI utility that facilitates quick retrieval of Juju objects that
# match given filters.
# Author: Connor Chamberlain

"""Compatibility facade for Jockey query and filtering utilities."""

import logging
from typing import Generator, List

from jockey.filtering import (
    FilterMode,
    JockeyFilter,
    check_filter_batch_match,
    check_filter_match,
    negative_filters,
    parse_filter_string,
    positive_filters,
)
from jockey.juju_conversions import (
    application_to_charm,
    application_to_units,
    charm_to_applications,
    get_applications,
    get_charms,
    get_hostnames,
    get_ips,
    get_machines,
    get_principal_unit_for_subordinate,
    get_units,
    hostname_to_machine,
    ip_to_machine,
    is_app_principal,
    machine_to_availability_zone,
    machine_to_hostname,
    machine_to_ips,
    machine_to_units,
    subordinate_unit_to_principal_unit,
    unit_to_application,
    unit_to_machine,
)
from jockey.log import configure_logging
from jockey.object_types import ObjectType, convert_object_abbreviation, list_abbreviations
from jockey.query_runtime import RETRIEVAL_MAP, filter_machines, filter_units
from jockey.status_loader import get_juju_status
from jockey.types import JujuStatus


logger = logging.getLogger(__name__)


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


def query(
    object_type: str,
    filter_strings: List[str],
    model: str = "",
    file: str = "",
    verbosity: int = 0,
) -> Generator[str, None, None]:
    """
    Perform a Jockey query.  Use this function as an entry point.

    Arguments
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
    query_result (Generator[str, None, None])
        A generator of objects matching the query. May be empty.
    """
    logger.debug("Starting Jockey query with: object=%r filter_strings=%r", object_type, filter_strings)
    configure_logging(verbosity)

    juju_object = convert_object_abbreviation(object_type)
    assert juju_object, f"Object type '{object_type}' not recognized."

    filter_function = RETRIEVAL_MAP.get(juju_object, None)
    assert filter_function, f"Querying of '{object_type}' is not yet supported."

    filters = [parse_filter_string(filter_str) for filter_str in filter_strings]
    status = get_juju_status(file=file, model_name=model)

    return filter_function(status, filters)


__all__ = [
    "JujuStatus",
    "FilterMode",
    "ObjectType",
    "JockeyFilter",
    "INFO_MESSAGE",
    "RETRIEVAL_MAP",
    "application_to_charm",
    "application_to_units",
    "check_filter_batch_match",
    "check_filter_match",
    "charm_to_applications",
    "convert_object_abbreviation",
    "filter_machines",
    "filter_units",
    "get_applications",
    "get_charms",
    "get_hostnames",
    "get_ips",
    "get_juju_status",
    "get_machines",
    "get_principal_unit_for_subordinate",
    "get_units",
    "hostname_to_machine",
    "ip_to_machine",
    "is_app_principal",
    "list_abbreviations",
    "machine_to_availability_zone",
    "machine_to_hostname",
    "machine_to_ips",
    "machine_to_units",
    "negative_filters",
    "parse_filter_string",
    "positive_filters",
    "query",
    "subordinate_unit_to_principal_unit",
    "unit_to_application",
    "unit_to_machine",
]
