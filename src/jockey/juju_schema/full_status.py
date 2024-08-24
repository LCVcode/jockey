from typing import Any, Dict, List, TypedDict
from typing_extensions import Required


# | ApplicationOfferStatus.
ApplicationOfferStatus = TypedDict('ApplicationOfferStatus', {
    # | Required property
    'active-connected-count': Required[int],
    # | Required property
    'application-name': Required[str],
    # | Required property
    'charm': Required[str],
    # | Required property
    'endpoints': Required[Dict[str, "RemoteEndpoint"]],
    # | Error.
    'err': "Error",
    # | Required property
    'offer-name': Required[str],
    # | Required property
    'total-connected-count': Required[int],
}, total=False)


# | ApplicationStatus.
ApplicationStatus = TypedDict('ApplicationStatus', {
    # | Required property
    'can-upgrade-to': Required[str],
    # | Required property
    'charm': Required[str],
    'charm-channel': str,
    # | Required property
    'charm-profile': Required[str],
    # | Required property
    'charm-version': Required[str],
    # | Required property
    'endpoint-bindings': Required[Dict[str, str]],
    # | Error.
    'err': "Error",
    # | Required property
    'exposed': Required[bool],
    'exposed-endpoints': Dict[str, "ExposedEndpoint"],
    'int': int,
    # | Value.
    # | 
    # | Required property
    'life': Required["Value"],
    # | Required property
    'meter-statuses': Required[Dict[str, "MeterStatus"]],
    'provider-id': str,
    # | Required property
    'public-address': Required[str],
    # | Required property
    'relations': Required[Dict[str, List[str]]],
    # | Required property
    'series': Required[str],
    # | DetailedStatus.
    # | 
    # | Required property
    'status': Required["DetailedStatus"],
    # | Required property
    'subordinate-to': Required[List[str]],
    # | Required property
    'units': Required[Dict[str, "UnitStatus"]],
    # | Required property
    'workload-version': Required[str],
}, total=False)


# | BranchStatus.
BranchStatus = TypedDict('BranchStatus', {
    # | Required property
    'assigned-units': Required[Dict[str, List[str]]],
    # | Required property
    'created': Required[int],
    # | Required property
    'created-by': Required[str],
}, total=False)


class DetailedStatus(TypedDict, total=False):
    """ DetailedStatus. """

    data: Required[Dict[str, Dict[str, Any]]]
    """ Required property """

    err: "Error"
    """ Error. """

    info: Required[str]
    """ Required property """

    kind: Required[str]
    """ Required property """

    life: Required["Value"]
    """
    Value.

    Required property
    """

    since: Required[str]
    """
    format: date-time

    Required property
    """

    status: Required[str]
    """ Required property """

    version: Required[str]
    """ Required property """



class EndpointStatus(TypedDict, total=False):
    """ EndpointStatus. """

    application: Required[str]
    """ Required property """

    name: Required[str]
    """ Required property """

    role: Required[str]
    """ Required property """

    subordinate: Required[bool]
    """ Required property """



class Error(TypedDict, total=False):
    """ Error. """

    code: Required[str]
    """ Required property """

    info: Dict[str, Dict[str, Any]]
    message: Required[str]
    """ Required property """



# | ExposedEndpoint.
ExposedEndpoint = TypedDict('ExposedEndpoint', {
    'expose-to-cidrs': List[str],
    'expose-to-spaces': List[str],
}, total=False)


# | FullStatus.
FullStatus = TypedDict('FullStatus', {
    # | Required property
    'applications': Required[Dict[str, "ApplicationStatus"]],
    # | Required property
    'branches': Required[Dict[str, "BranchStatus"]],
    # | format: date-time
    # | 
    # | Required property
    'controller-timestamp': Required[str],
    # | Required property
    'machines': Required[Dict[str, "MachineStatus"]],
    # | ModelStatusInfo.
    # | 
    # | Required property
    'model': Required["ModelStatusInfo"],
    # | Required property
    'offers': Required[Dict[str, "ApplicationOfferStatus"]],
    # | Required property
    'relations': Required[List["RelationStatus"]],
    # | Required property
    'remote-applications': Required[Dict[str, "RemoteApplicationStatus"]],
}, total=False)


class LXDProfile(TypedDict, total=False):
    """ LXDProfile. """

    config: Required[Dict[str, str]]
    """ Required property """

    description: Required[str]
    """ Required property """

    devices: Required[Dict[str, Dict[str, str]]]
    """ Required property """



# | MachineStatus.
MachineStatus = TypedDict('MachineStatus', {
    # | DetailedStatus.
    # | 
    # | Required property
    'agent-status': Required["DetailedStatus"],
    # | Required property
    'constraints': Required[str],
    # | Required property
    'containers': Required[Dict[str, "MachineStatus"]],
    # | Required property
    'display-name': Required[str],
    # | Required property
    'dns-name': Required[str],
    # | Required property
    'hardware': Required[str],
    # | Required property
    'has-vote': Required[bool],
    'hostname': str,
    # | Required property
    'id': Required[str],
    # | Required property
    'instance-id': Required[str],
    # | DetailedStatus.
    # | 
    # | Required property
    'instance-status': Required["DetailedStatus"],
    'ip-addresses': List[str],
    # | Required property
    'jobs': Required[List[str]],
    'lxd-profiles': Dict[str, "LXDProfile"],
    # | DetailedStatus.
    # | 
    # | Required property
    'modification-status': Required["DetailedStatus"],
    'network-interfaces': Dict[str, "NetworkInterface"],
    'primary-controller-machine': bool,
    # | Required property
    'series': Required[str],
    # | Required property
    'wants-vote': Required[bool],
}, total=False)


class MeterStatus(TypedDict, total=False):
    """ MeterStatus. """

    color: Required[str]
    """ Required property """

    message: Required[str]
    """ Required property """



# | ModelStatusInfo.
ModelStatusInfo = TypedDict('ModelStatusInfo', {
    # | Required property
    'available-version': Required[str],
    # | Required property
    'cloud-tag': Required[str],
    # | MeterStatus.
    # | 
    # | Required property
    'meter-status': Required["MeterStatus"],
    # | DetailedStatus.
    # | 
    # | Required property
    'model-status': Required["DetailedStatus"],
    # | Required property
    'name': Required[str],
    'region': str,
    # | Required property
    'sla': Required[str],
    # | Required property
    'type': Required[str],
    # | Required property
    'version': Required[str],
}, total=False)


# | NetworkInterface.
NetworkInterface = TypedDict('NetworkInterface', {
    'dns-nameservers': List[str],
    'gateway': str,
    # | Required property
    'ip-addresses': Required[List[str]],
    # | Required property
    'is-up': Required[bool],
    # | Required property
    'mac-address': Required[str],
    'space': str,
}, total=False)


class RelationStatus(TypedDict, total=False):
    """ RelationStatus. """

    endpoints: Required[List["EndpointStatus"]]
    """ Required property """

    id: Required[int]
    """ Required property """

    interface: Required[str]
    """ Required property """

    key: Required[str]
    """ Required property """

    scope: Required[str]
    """ Required property """

    status: Required["DetailedStatus"]
    """
    DetailedStatus.

    Required property
    """



# | RemoteApplicationStatus.
RemoteApplicationStatus = TypedDict('RemoteApplicationStatus', {
    # | Required property
    'endpoints': Required[List["RemoteEndpoint"]],
    # | Error.
    'err': "Error",
    # | Value.
    # | 
    # | Required property
    'life': Required["Value"],
    # | Required property
    'offer-name': Required[str],
    # | Required property
    'offer-url': Required[str],
    # | Required property
    'relations': Required[Dict[str, List[str]]],
    # | DetailedStatus.
    # | 
    # | Required property
    'status': Required["DetailedStatus"],
}, total=False)


class RemoteEndpoint(TypedDict, total=False):
    """ RemoteEndpoint. """

    interface: Required[str]
    """ Required property """

    limit: Required[int]
    """ Required property """

    name: Required[str]
    """ Required property """

    role: Required[str]
    """ Required property """



# | UnitStatus.
UnitStatus = TypedDict('UnitStatus', {
    'address': str,
    # | DetailedStatus.
    # | 
    # | Required property
    'agent-status': Required["DetailedStatus"],
    # | Required property
    'charm': Required[str],
    'leader': bool,
    # | Required property
    'machine': Required[str],
    # | Required property
    'opened-ports': Required[List[str]],
    'provider-id': str,
    # | Required property
    'public-address': Required[str],
    # | Required property
    'subordinates': Required[Dict[str, "UnitStatus"]],
    # | DetailedStatus.
    # | 
    # | Required property
    'workload-status': Required["DetailedStatus"],
    # | Required property
    'workload-version': Required[str],
}, total=False)


# | Value.
Value = TypedDict('Value', {
    'allocate-public-ip': bool,
    'arch': str,
    'container': str,
    'cores': int,
    'cpu-power': int,
    'instance-role': str,
    'instance-type': str,
    'mem': int,
    'root-disk': int,
    'root-disk-source': str,
    'spaces': List[str],
    'tags': List[str],
    'virt-type': str,
    'zones': List[str],
}, total=False)
