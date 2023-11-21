Goal:

To quickly and easily retrieve any Juju objects using filters.

Example `get` commands:

`$ jockey get units`
`$ jockey get units charm="ceph-osd"`
`$ jockey get charms machine=1`
`$ jockey get app charm="charm-nrpe" machine="4/lxd/2"`
`$ jockey get units app="nova" principal=true hostname~"blrt"`

Example `show` commands:

`$ jockey unit show <unit-name>`
`$ jockey app show <app-name>`
`$ jockey machine show <machine-name>`
`$ jockey charm show <charm-name>`

