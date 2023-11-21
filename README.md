# Juju Jockey 

Jockey is a CLI tool designed to facilitate quick and easy retrieval of Juju objects using filters.  It uses automatic caching of Juju's status in json format to enable faster parsing.  

## Retrievable objects:

* Units
* Charms       (not implemented)
* Applications (not implemented)
* Machines     (not implemented)
* Hostnames    (not implemented)
* IPs          (not implemented)

## Example commands:

### Get commands:

Example `get` commands:

`$ ./jockey.py get units`
`$ ./jockey.py get units charm="ceph-osd"`
`$ ./jockey.py get charms machine=1`
`$ ./jockey.py get app charm="charm-nrpe" machine="4/lxd/2"`
`$ ./jockey.py get units app!="nova" principal=true hostname~"blrt"`

### Show commands (NOT IMPLEMENTED YET):

Example `show` commands:

`$ ./jockey.py unit show <unit-name>`
`$ ./jockey.py app show <app-name>`
`$ ./jockey.py machine show <machine-name>`
`$ ./jockey.py charm show <charm-name>`

## Wishlist:

* Implemented "does not contant" operator `!~`
* Allow comma-delimited selection of multiple object types:
    `$ ./jockey.py get unit,app`
