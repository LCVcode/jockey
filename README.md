<div align="center">

# Juju Jockey

*Juju objects at your fingertips 🫰*

[![License][shield-license]][url-license]
![Python Version][shield-python]
![Programming Language][shield-language]
[![Tests][shield-tests]][url-tests]
[![Contributors][shield-contributors]][url-contributors]
[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2FLCVcode%2Fjockey.svg?type=shield)](https://app.fossa.com/projects/git%2Bgithub.com%2FLCVcode%2Fjockey?ref=badge_shield)

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
<summary><code>jockey units</code></summary>
<pre>
ceph-osd/0 telegraf-ceph/2 ceph-osd/1 telegraf-ceph/1 ceph-osd/2 telegraf-ceph/0 mysql-innodb-cluster/0 telegraf-mysql/0
</pre>
</details>

<!-- jockey units charm=ceph-osd -->
<details>
<summary><code>jockey units charm=ceph-osd</code></summary>
<pre>
ceph-osd/0 ceph-osd/1 ceph-osd/2
</pre>
</details>

<!-- jockey charms machine=1 -->
<details>
<summary><code>jockey charms machine=1</code></summary>

> **Note**
> Sorry, the `machine` filter is not yet implemented; stay tuned!

</details>

<!-- jockey app charm=charm-nrpe machine=4/lxd/2 -->
<details>
<summary><code>jockey app charm=charm-nrpe machine=4/lxd/2</code></summary>

> **Note**
> Sorry, the `app` filter is not yet implemented; stay tuned!

</details>

<!-- jockey units app^=nova principal=true hostname~blrt -->
<details>
<summary><code>jockey units app^=nova principal=true hostname~blrt</code></summary>

> **Note**
> Sorry, the `app` filter is not yet implemented; stay tuned!

</details>

## Wishlist:

* Allow comma-delimited selection of multiple object types:
    `jockey get unit,app`
* Filter by leadership
* Filter by principal
* Filter by lxd


## License
[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2FLCVcode%2Fjockey.svg?type=large)](https://app.fossa.com/projects/git%2Bgithub.com%2FLCVcode%2Fjockey?ref=badge_large)