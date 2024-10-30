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

Jockey is a CLI tool designed to facilitate quick and easy retrieval of Juju objects using filters.  It uses automatic caching of Juju's status in json format to enable faster parsing.

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

All filtering actions are performed by navigating this tree.

## Command Anatomy

The anatomy of a Jockey command is as follows:
```
jockey <object> <filters> <options>
```

`<object>` refers to any of the searchable Juju objects, such as applications and units.  `<filters>` is a space delimited list of filters (see below).

### Filters

Filters follow a specific syntax and allow the user to limit Jockey's output to meet certain criteria.  All filters have this structure:
```
<object><filter-code><content>
```
Just like in the origial `jockey` command anatomy, `<object>` is any of the searchable Juju objects.

## Examples:

<!-- jockey units -->
<details>
<summary><code>juju-jockey units</code></summary>
<pre>
ceph-osd/0 telegraf-ceph/2 ceph-osd/1 telegraf-ceph/1 ceph-osd/2 telegraf-ceph/0 mysql-innodb-cluster/0 telegraf-mysql/0
</pre>
</details>

<!-- jockey units charm=ceph-osd -->
<details>
<summary><code>juju-jockey units charm=ceph-osd</code></summary>
<pre>
ceph-osd/0 ceph-osd/1 ceph-osd/2
</pre>
</details>

<!-- jockey charms machine=1 -->
<details>
<summary><code>juju-jockey charms machine=1</code></summary>

> **Note**
> Sorry, the `machine` filter is not yet implemented; stay tuned!

</details>

<!-- jockey app charm=charm-nrpe machine=4/lxd/2 -->
<details>
<summary><code>juju-jockey app charm=charm-nrpe machine=4/lxd/2</code></summary>

> **Note**
> Sorry, the `app` filter is not yet implemented; stay tuned!

</details>

<!-- jockey units app^=nova principal=true hostname~blrt -->
<details>
<summary><code>juju-jockey units app^=nova principal=true hostname~blrt</code></summary>

> **Note**
> Sorry, the `app` filter is not yet implemented; stay tuned!

</details>

## Wishlist:

### Multi-object querying

Currently, Jockey only supports querying single object types.  This change would enable Jockey to return formatted object mappings, to see the relationship between various objects.

This proposed example shows a mapping of machines, which match the given filters, to their respective hostnames and IP addresses
```bash
$ juju-jockey m,hostname,ip c=nova-compute c=ceph-osd
+----+-------------+
|  8 | node5       |
|    | 10.210.3.11 |
+----+-------------+
| 83 | node6       |
|    | 10.210.3.12 |
+----+-------------+
| 97 | node11      |
|    | 10.210.3.17 |
+----+-------------+
| 99 | node13      |
|    | 10.210.3.19 |
+----+-------------+
...
```

### Filtering by leadership (on reasonable object types)

```bash
$ juju-jockey u leader=true
<list of all leader units>

$ juju-jockey a leader=true
<warning: leadership does not apply to applications>
```

### Filtering by principal

```bash
$ juju-jockey u principal=true
<list of all principal units>

$ juju-jockey c p=true
<list of all principal charms>

$ juju-jockey machine p=true
<warning: principal filter does not apply to machines>
```

### Option to return only first result

```bash
# Current functionality:
$ juju-jockey u c=hw-health h~node11
hw-health/20 hw-health/2

# Proposed:
$ juju-jockey u c=hw-health h~node11 --first
hw-health/20
```

### Remote Juju status caching

This feature is parially implemented in the `master` branch.

Creates a local cache of the remote Juju found at `infra.customer.address` as the user `jujuadmin`:
```
$ juju-jockey u -R infra.customer.address -U jujuadmin c=hw-health h~node8
```
