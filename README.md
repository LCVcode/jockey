Goal:

To quickly and easily retrieve any Juju objects using filters.

Example `get` commands:

`$ jockey get units`
`$ jockey get units where charm=ceph-osd`
`$ jockey get charms where machine=1`
`$ jockey get app where charm=nrpe`
`$ jockey get unit where charm=rabbitmq-server and machine=5`

Example `show` commands:

`$ jockey unit show <unit-name>`
`$ jockey app show <app-name>`
`$ jockey machine show <machine-name>`
`$ jockey charm show <charm-name>`

