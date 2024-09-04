
## Objects
### Supported Objects
_Jockey_ allows querying of the following **Juju** objects:

- **Application:** An [application][juju-application] is a running abstraction of a charm in the Juju model. It represents the sum of all units of a given charm with the same name.
- **Unit:** A [unit][juju-unit] in Juju is a deployed instance of a [charm][juju-charm]. Units of an **application** reside on [machines][juju-machine].
- **Machine:** A [machine][juju-machine] in Juju is any instance requested explicitly (via `juju add-machine`) or implicitly (e.g., `juju bootstrap`, `juju deploy`, `juju add-unit`) from a [cloud][juju-cloud] environment.

### Aliases for Objects

To simplify operations, _Jockey_ supports shorthand aliases for Juju objects. These aliases can be used in place of the full object names:

- **Application:** `application`, `applications`, `app`, `apps`, `a`
- **Unit:** `unit`, `units`, `u`
- **Machine:** `machine`, `machines`, `m`

## Filters
### Filter Expressions
_Filter expressions_ follow a structured syntax:
```
<OBJECT>(.FIELD)<FILTER><QUERY>
```

Where:
- `OBJECT`: A supported [Juju object](#objects) or its [alias](#aliases-for-objects).
- `.FIELD`: Specifies the field within the object to filter against.
- `FILTER`: Determines how _Jockey_ should filter the objects relative to `QUERY`.
- `QUERY`: The value to compare with the resolved value of `OBJECT` and `.FIELD`.

### Supported Filters
The `FILTER` part of a [filter expression](#filter-expressions) determines the action to perform. _Jockey_ supports the following filtering actions:

| Token(s)   | Action                  | Description                                    |
|------------|-------------------------|------------------------------------------------|
| `==`, `=`  | Equals                  | Check if values are equal                      |
| `^=`, `!=` | Not Equals              | Check if values are not equal                  |
| `%`        | Regular Expression      | Match against a regular expression             |
| `^%`, `!%` | Not Regular Expression   | Ensure a value does not match a regular expression |
| `>`        | Greater Than            | Check if a value is greater than another       |
| `>=`, `=>` | Greater Than or Equals   | Check if a value is greater than or equal to another |
| `<`        | Less Than               | Check if a value is less than another          |
| `<=`, `=<` | Less Than or Equals      | Check if a value is less than or equal to another |
| `~`        | Contains                | Check if a value contains another              |
| `!~`, `^~` | Not Contains            | Check if a value does not contain another      |

#### Examples:
- **Contains filter**: Select items where the hostname contains "juju":
    ```bash
    juju-jockey machine 'hostname~juju'
    ```

- **Regular expression filter**: Match hostnames that contain either "juju" or "metal":
    ```bash
    juju-jockey machine 'hostname%juju|metal'
    ```

## Object Fields
Each Juju object has various fields that can be used in filter expressions or specified for output.

Fields are accessed through **dot notation**. Consider the following example unit:

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

### Filtering Based on Fields
You can filter objects based on deeply nested field values.
For example, to filter units whose `juju-status` is `idle`:
```bash
juju-jockey unit juju-status.current==idle
```

### Specifying Output Fields
To output specific fields after filtering, simply specify the field(s) you're interested in:
```bash
juju-jockey unit.machine juju-status.current==idle
```

By default, when querying an application without specifying a field, _Jockey_ outputs the name of the object.
To output **all fields** of an object, use a single `.` after the object name:


### Virtual Fields
_Virtual fields_ allow you to traverse relationships between objects.
These fields typically start with the `@` symbol and allow you to reference related objects.

For instance, you can filter units based on values from their associated machine:
```bash
juju-jockey units unit.@machine.hostname~juju
```

```{note}
Virtual fields are not included in output due to potential recursive loops
(e.g., unit → machine → unit → machine).
```

#### Listing Virtual Fields
To see all available virtual fields for an object, query the `@` field:
```bash
juju-jockey unit.@
```

[juju-cloud]: https://juju.is/docs/juju/cloud
[juju-charm]: https://juju.is/docs/juju/charmed-operator
[juju-application]: https://juju.is/docs/juju/application
[juju-unit]: https://juju.is/docs/juju/unit
[juju-machine]: https://juju.is/docs/juju/machine
