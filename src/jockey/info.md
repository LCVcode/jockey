


## Objects
### Supported
_Jockey_ supports querying the following Juju objects:

- **Application:** An [application][juju-application] is a running abstraction of a charm in the Juju model. It is the sum of all units of a given charm with the same name.
- **Unit:** In Juju, a [unit][juju-unit] is a deployed [charm][juju-charm]. An **application's** units occupy [machines][juju-machine].
- **Machine:** In Juju, a [machine][juju-machine] is any instance requested explicitly (via `juju add-machine`) or implicitly (e.g., `juju bootstrap`, `juju deploy`, `juju add-unit`) from a [cloud][juju-cloud] environment.

### Aliases
When querying Juju objects, _Jockey_ provides numerous shorthand aliases to help make operations swifter.

The following aliases resolve to their respective Juju objects:

- **Application:** application, applications, app, apps, a
- **Unit:** unit, units, u
- **Machine:** machine, machines, m

## Filtering
### Expressions
**Filter expressions** have a three-part syntax:
```
<OBJECT>(.FIELD)<FILTER><QUERY>
```

The syntax elements are:
- `OBJECT`: any supported [Juju object type](#supported) or their [equivalent aliases](#aliases).
- `.FIELD`: specifies the field within the object to filter against.
- `FILTER`: specifies how Jockey should filter Juju objects relative to `QUERY`.
- `QUERY`: the value Jockey will compare with the value resolved by `OBJECT` and `.FIELD`.

### Filters
The `FILTER` part of the [filter expression](#expressions) is a token to select the filtering action. _Jockey_ supports an extensive suite of filtering actions:

| Token(s)  | Name       | Description |
|-----------|------------|-------------|
| `==`, `=` | Equals     | Check for equality between values |
| `^=`, `!=` | Not Equals | Check for inequality between values |
| `%` | Regular Expression | Match against a regular expression |
| `^%`, `!%` | Not Regular Expression | Ensure a value does not match a regular expression |
| `>` | Greater Than | Check if a value is greater than another |
| `>=`, `=>` | Greater Than or Equals | Check if a value is greater than or equal to another |
| `<` | Less Than | Check if a value is less than another |
| `<=`, `=<` | Less Than or Equals | Check if a value is less than or equal to another |
| `~` | Contains | Check if a value contains another. |
| `!~`, `^~` | Not Contains | Check if a value does not contain another |

For example, the following expression selects items where the hostname contains "juju":
```
'hostname~juju'
```

Alternatively, this expression uses a regular expression to find hostnames that contain either "juju" or "metal":
```
'hostname%juju|metal'
```

## Fields
Each Juju object contains one or more fields that you may use in a filter expression or the output.

_Jockey_ exposes these fields through "dot notation."
For  demonstration, assume we have a unit like this:

```python
unit = {
    'workload-status': {
        'current': 'active',
        'message': 'Certificate Authority connected.',
        'since': '23 Mar 2024 13:03:27-06:00'
    },
    'juju-status': {
        'current': 'idle',
        'since': '23 Mar 2024 13:29:59-06:00',
        'version': '3.1.5'
    },
    'leader': True,
    'machine': '0/lxd/0',
    'public-address': '10.192.62.201'
}
```

We can filter based on deeply nested values:
```bash
juju-jockey unit juju-status.current==idle
```

We can also output specific fields from the unit after filtering:
```bash
juju-jockey unit.machine juju-status.current==idle
```

By default, when specifying the application without a field expression, _Jockey_ will output the name of each object. You can output all fields by placing a single `.` after the name of the object:
```bash
juju-jockey unit. juju-status.current==idle
```

### Virtual fields
While querying fields on a single object is helpful, _Jockey_ takes it further. It resolves relationships between objects through **virtual fields**. These particular fields typically start with an "at" symbol (`@`).

Virtual fields are not included in the output due to the potential for infinite loops (e.g., unit to machine to units to machine).

As an example of virtual field traversal, you can filter upon values in the machine related to a unit:
```bash
juju-jockey units unit.@machine.hostname~juju
```

You can list the available virtual fields by accessing the `@` field:
```bash
juju-jockey unit.@
```



[juju-cloud]: https://juju.is/docs/juju/cloud
[juju-charm]: https://juju.is/docs/juju/charmed-operator
[juju-application]: https://juju.is/docs/juju/application
[juju-unit]: https://juju.is/docs/juju/unit
[juju-machine]: https://juju.is/docs/juju/machine
