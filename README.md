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

## Examples:

`$ ./jockey.py units`
`$ ./jockey.py units charm=ceph-osd`
`$ ./jockey.py charms machine=1`
`$ ./jockey.py app charm=charm-nrpe machine=4/lxd/2`
`$ ./jockey.py units app!=nova principal=true hostname~blrt`

## Wishlist:

* Allow comma-delimited selection of multiple object types:
    `$ ./jockey.py get unit,app`
