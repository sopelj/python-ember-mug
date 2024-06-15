Once this library is installed in your active python environment you can also use the `ember-mug` to interact with your device.
If you clone this project you may also run the commands via `hatch` in the project root. Simply use `hatch run ember-mug` with your desired options

## Command Overview

| Command     | Use                                                                               |
|-------------|-----------------------------------------------------------------------------------|
| `discover`  | Find/List all detected unpaired devices in pairing mode                           |
| `find`      | Find *one* already paired devices                                                 |
| `info`      | Connect to *one* device and print its current state                               |
| `poll`      | Connect to *one* device and print its current state and keep watching for changes |
| `get`       | Get the value(s) of one or more attribute(s) by name                              |
| `set`       | Set one or more values on the device                                              |

A few useful common arguments:
- `--mac your:mac:address` (or `-m`) to restrict to that address (useful if you have multiple devices)
- `--raw` (or `-r`) flag to restrict to very basic and parsable output (useful if you want to use the output in a script.)
- `--debug` (or `-d`) flag to enable very verbose output

Some commands have extra options. You can see them by using the `--help` flag after specifying a command. ex.
```bash
ember-mug set --help
```

## Examples

### Find a device in pairing mode (for the first time)
<!-- termynal -->
```bash
$ ember-mug discover
Found Mug: C9:0F:59:D6:33:F9
Name: EMBER MUG
Model: Ember Mug 2 [CM19/CM21M]
Colour: Black
Capacity: 295ml
```

### Find a previously paired device
<!-- termynal -->
```bash
$ ember-mug discover
Found device: C9:0F:59:D6:33:F9: Ember Ceramic Mug
```

### Fetch info and keep listening for changes
<!-- termynal -->
```bash
$ ember-mug poll
Found mug: C9:0F:59:D6:33:F9: Ember Ceramic Mug
```

### Get the value(s) of specific attribute(s)
<!-- termynal -->
```bash
$ ember-mug get name target-temp
```

### Set the value(s) of specific attribute(s)
<!-- termynal -->
```bash
$ ember-mug set --name "My mug" --target-temp 56.8
```
