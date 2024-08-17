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

## Getting Started
### Installing Dependencies
First, make sure you have Poetry installed. If not, please refer to the
[Poetry installation guide](https://python-poetry.org/docs/#installation).
Then, install all the required dependencies for Jockey:
```bash
poetry install
```

This command will create the virtual environment and install all the necessary packages as defined in
[`pyproject.toml`](pyproject.toml).

### Using Jockey
Once installed, you can interact with the Jockey directly:

```bash
poetry run python jockey.py --help
```

### Hacking with Jockey
#### Entering the Virtual Environment
To work within the virtual environment created by Poetry:
```bash
poetry shell
```

This will activate the virtual environment.
You will need to do this each time you start a new session.

#### Performing checks locally
```bash
# Lint import order with isort
poetry run isort . --check

# Fix import order with isort
poetry run isort .

# Lint with flake8
poetry run flake8 .

# Lint with mypy
poetry run mypy .

# Lint code format with black
poetry run black . --check

# Fix code format with black
poetry run black .

# Execute unit tests
poetry run pytest -s
```

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
