<div align="center">

# Juju Jockey

*Juju objects at your fingertips 🫰*

[![License][shield-license]][url-license]
![Python Version][shield-python]
![Programming Language][shield-language]
[![Tests][shield-tests]][url-tests]
[![Contributors][shield-contributors]][url-contributors]

[shield-license]: https://img.shields.io/github/license/LCVcode/jockey?style=for-the-badge
[shield-contributors]: https://img.shields.io/github/contributors/LCVcode/jockey?style=for-the-badge
[shield-python]: https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2FLCVcode%2Fjockey%2Fmaster%2Fpyproject.toml&style=for-the-badge
[shield-language]: https://img.shields.io/github/languages/top/LCVcode/jockey?style=for-the-badge&logo=python
[shield-tests]: https://img.shields.io/github/actions/workflow/status/LCVcode/jockey/ci.yml?style=for-the-badge&label=tests

[url-license]: LICENSE
[url-contributors]: https://github.com/LCVcode/jockey/graphs/contributors
[url-tests]: https://github.com/LCVcode/jockey/actions/workflows/ci.yml

</div>

## Overview

Jockey is a CLI tool for querying Juju model data with concise filter expressions.
It currently supports querying **units** and **machines** and can filter them
using related object values (applications, charms, hostnames, IPs, and
availability zones).

Jockey relies on this model of Juju objects and how they are related:
```mermaid
---
title: Juju object relationships
---
flowchart LR
    C([Charm]) --> A[Application]
    A -->|Instances of| U[Unit]
    U -->|Running on| M[Machine]
    M -->|Metadata| M_I(IP)
    M -->|Metadata| M_H(Hostname)
```

All filters are evaluated by traversing these relationships.

## Quick reference

### Queryable objects

Only these object types can be queried as the top-level `OBJECT`:

| Name | Aliases |
|---|---|
| Unit | `unit`, `units`, `u` |
| Machine | `machine`, `machines`, `m` |

### Filterable attributes

When filtering units or machines, you can reference these Juju objects:

| Attribute | Aliases |
|---|---|
| Charm | `charm`, `charms`, `c` |
| Application | `application`, `applications`, `app`, `apps`, `a` |
| Unit | `unit`, `units`, `u` |
| Machine | `machine`, `machines`, `m` |
| IP address | `ips`, `address`, `addresses`, `ip`, `i` |
| Hostname | `hostnames`, `hostname`, `host`, `hosts`, `h` |
| Availability Zone | `availability-zone`, `availability_zone`, `az`, `zone` |

### Filter operators

| Operator | Behavior |
|---|---|
| `=` | Value equals |
| `^=` | Value does not equal |
| `~` | Value contains substring |
| `^~` | Value does not contain substring |

## Usage

### Command structure

```
juju-jockey <OBJECT> [FILTER ...] [OPTIONS]
```

- `<OBJECT>`: A queryable object type (`u` or `m`) or alias
- `[FILTER ...]`: Zero or more filter expressions
- `[OPTIONS]`: `--file <path>` to query a Juju status JSON file

### Filter expression syntax

```
<ATTRIBUTE><OPERATOR><VALUE>
```

- `<ATTRIBUTE>`: A filterable attribute (e.g., `app`, `host`, `charm`)
- `<OPERATOR>`: One of `=`, `^=`, `~`, `^~`
- `<VALUE>`: The string to match

### Examples

#### Get all units
```bash
juju-jockey u
```

#### Get all machines
```bash
juju-jockey m
```

#### Filter units by application name
```bash
juju-jockey u app=etcd
```
Returns all units of the `etcd` application.

#### Filter units by charm name
```bash
juju-jockey u charm=nrpe
```
Returns all units running the `nrpe` charm.

#### Filter machines by hostname substring
```bash
juju-jockey m host~node
```
Returns machines whose hostname contains "node".

#### Filter units on specific machines
```bash
juju-jockey u machine=0
```
Returns units running on machine `0` (and its containers).

#### Combine multiple filters
```bash
juju-jockey u app=nova machine^=0
```
Returns units of the `nova` application that are NOT on machine `0`.

#### Exclude container machines
```bash
juju-jockey m m^~lxd
```
Returns all non-LXD machines (physical machines only).

#### Query a local Juju status file
```bash
juju-jockey u --file /tmp/status.json app=mysql
```
Returns `mysql` units from a local status file.

## Data sources and caching

- `--file /path/to/status.json` queries a local Juju status JSON file.
- Without `--file`, Jockey queries Juju CLI output and uses a local cache.
- The in-memory status used for filtering is intentionally narrowed to fields
  needed by the currently supported query/filter paths.
