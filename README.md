# Juju Jockey 

## Overview

Jockey is a CLI tool designed to facilitate quick and easy retrieval of Juju objects using filters.  It uses automatic caching of Juju's status in json format to enable faster parsing.  

Jockey relies on this model of Juju objects and how they are related:
```
+-------+
| Charm |
+-------+
    |
+-------------+
| Application |
+-------------+
    |
+------+
| Unit |
+------+
    |
+---------+
| Machine |------\
+---------+      |
    |            |
+----------+   +----+
| Hostname |   | IP |
+----------+   +----+
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

`$ ./jockey.py units`
`$ ./jockey.py units charm=ceph-osd`
`$ ./jockey.py charms machine=1`
`$ ./jockey.py app charm=charm-nrpe machine=4/lxd/2`
`$ ./jockey.py units app^=nova principal=true hostname~blrt`

## Wishlist:

* Allow comma-delimited selection of multiple object types:
    `$ ./jockey.py get unit,app`
* Filter by leadership
* Filter by principal
* Filter by lxd
