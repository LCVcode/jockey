## Objects
### Supported Objects
_Jockey_ allows querying of the following **Juju** objects:

- Units
- Machines

### Aliases for Objects

To simplify operations, _Jockey_ supports shorthand aliases for Juju objects. These aliases can be used in place of the full object names:

- **Charm:** `charm`, `charms`, `c`
- **Application:** `application`, `applications`, `app`, `apps`, `a`
- **Unit:** `unit`, `units`, `u`
- **Machine:** `machine`, `machines`, `m`
- **IP:** `ips`, `address`, `addresses`, `ip`, `i`
- **Hostname:** `hostnames`, `hostname`, `host`, `hosts`, `h`

## Filters
### Filter Expressions
_Filter expressions_ follow a structured syntax:
```
<OBJECT><FILTER><QUERY>
```

Where:
- `OBJECT`: A supported [Juju object](#objects) or its [alias](#aliases-for-objects).
- `FILTER`: Determines how _Jockey_ should filter the objects relative to `QUERY`.
- `QUERY`: The value to compare with the resolved value of `OBJECT` and `.FIELD`.

### Supported Filters
The `FILTER` part of a [filter expression](#filter-expressions) determines the action to perform. _Jockey_ supports the following filtering actions:

| Token(s) | Action       | Description                               |
|----------|--------------|-------------------------------------------|
| `=`      | Equals       | Check if values are equal                 |
| `^=`     | Not Equals   | Check if values are not equal             |
| `~`      | Contains     | Check if a value contains another         |
| `^~`     | Not Contains | Check if a value does not contain another |

#### Examples:
- **Equals filter**: Selet units whose application name is "nrpe":
    ```bash
    juju-jockey unit a=nrpe
    ```
- **Not Equals filter**: Select all machines which lack a unit of the application named "nrpe":
    ```bash
    juju-jockey machine app^=nrpe
    ```
- **Contains filter**: Select items where the hostname contains "juju":
    ```bash
    juju-jockey machines hostname~juju
    ```
- **Not Containers filter**: Select all non-LXD machines:
    ```bash
    juju-jockey m m^~lxd
    ```

