# Python Ember Mug

[![pypi](https://img.shields.io/pypi/v/python-ember-mug.svg)](https://pypi.org/project/python-ember-mug/)
[![python](https://img.shields.io/pypi/pyversions/python-ember-mug.svg)](https://pypi.org/project/python-ember-mug/)
[![Build Status](https://github.com/sopelj/python-ember-mug/actions/workflows/tests.yml/badge.svg)](https://github.com/sopelj/python-ember-mug/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/sopelj/python-ember-mug/branch/main/graphs/badge.svg)](https://codecov.io/github/sopelj/python-ember-mug)
![Project Maintenance](https://img.shields.io/maintenance/yes/2023.svg)
[![Maintainer](https://img.shields.io/badge/maintainer-%40sopelj-blue.svg)](https://github.com/sopelj)
[![License](https://img.shields.io/github/license/sopelj/python-ember-mug.svg)](LICENSE)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen)](https://github.com/pre-commit/pre-commit)

Python Library for interacting with Ember Mugs, Cups and Travel Mugs via Bluetooth

* Documentation: <https://sopelj.github.io/python-ember-mug>
* GitHub: <https://github.com/sopelj/python-ember-mug>
* PyPI: <https://pypi.org/project/python-ember-mug/>

## Summary

This is an *unofficial* library to attempt to interact with Ember Mugs via Bluetooth.
This was created for use with my [Home Assistant integration](https://github.com/sopelj/hass-ember-mug-component),
but could be useful separately and has a simple CLI interface too.

All known Ember Mugs, Cups and Travel Mugs have been tested and work.
The Tumbler has not yet been tested. If you have one and would like to help, please see [Issue #65]((https://github.com/sopelj/python-ember-mug/issues/56))
If I missed one, or you have new feature ideas/issues, please let me know.

| Device       | Tested                                                    |
|--------------|-----------------------------------------------------------|
| Mug          | ✓                                                         |
| Mug 2        | ✓                                                         |
| Cup          | ✓                                                         |
| Travel Mug   | ✓                                                         |
| Travel Mug 2 | ✓                                                         |
| Tumbler      | [?](https://github.com/sopelj/python-ember-mug/issues/56) |


## Features

* Finding devices
* Connecting to devices
* Reading/Writing most values
* Poll for changes

Attributes by device:

| Attribute           | Mug | Cup | Travel Mug | Description                                   |
|---------------------|-----|-----|------------|-----------------------------------------------|
| Name                | R/W | N/A | R          | Name to give device                           |
| LED Colour          | R/W | R/W | N/A        | Colour of front LED                           |
| Current Temperature | R   | R   | R          | Current temperature of the liquid in the mug  |
| Target Temperature  | R/W | R/W | R/W        | Desired temperature for the liquid            |
| Temperature Unit    | R/W | R/W | R/W        | Internal temperature unit for the app (C/F)   |
| Liquid Level        | R   | R   | R          | Approximate level of the liquid in the device |
| Volume level        | N/A | N/A | R/W        | Volume of the button press beep               |
| Battery Percent     | R   | R   | R          | Current battery level                         |
| On Charger          | R   | R   | R          | Device is on it's charger                     |

*** Writing may only work if the devices has been set up in the app previously

## Usage

### Python

```python
from ember_mug.scanner import find_mug, discover_mugs
from ember_mug.mug import EmberMug

# if first time with mug in pairing
mugs = await discover_mugs()
device = mugs[0]
# after paired you can simply use
device = await find_mug()
mug = EmberMug(device)
await mug.update_all()
print(mug.data.formatted)
await mug.disconnect()

# You can also use connection as a context manager
# if you want to ensure connection before starting and cleanup on exit
async with mug.connection():
    print('Connected.\nFetching Info')
    await mug.update_all()
    print(mug.data.formatted)
```

### CLI

It can also be run via command line either directly with `ember-mug --help` or as a module with `python -m ember_mug --help`
There are four options with different subsections. You can see them by specifying them before help. eg `ember-mug poll --help`

```bash
ember-mug discover  # Finds the mug in pairing mode for the first time
ember-mug poll  # fetches info and keeps listening for notifications
ember-mug get name target-temp  # Prints name and target temp of mug
ember-mug set --name "My mug" --target-temp 56.8  # Sets the name and target temp to specified values
```

Basic options:

| Command     | Use                                                                               |
|-------------|-----------------------------------------------------------------------------------|
| `discover`  | Find/List all detected unpaired devices in pairing mode                           |
| `find`      | Find *one* already paired devices                                                 |
| `info`      | Connect to *one* device and print its current state                               |
| `poll`      | Connect to *one* device and print its current state and keep watching for changes |
| `get`       | Get the value(s) of one or more attribute(s) by name                              |
| `set`       | Set one or more values on the device                                              |

![CLI Example](./docs/images/cli-example.png)

## Caveats

* Since this api is not public, a lot of guesswork and reverse engineering is involved, so it's not perfect.
* If the device has not been set up in the app since it was reset, writing is not allowed. I don't know what they set in the app, but it changes something, and it doesn't work without it.
* Once that device has been set up in the app, you should ideally forget the device or at least turn off bluetooth whilst using it here, or you will probably get disconnected often
* I haven't figured out some attributes like udsk, dsk, location and timezone, but they are not very useful anyway.

## Troubleshooting

##### Systematic timeouts or `le-connection-abort-by-local`

If your mug gets stuck in a state where it refuses to connect, you get constant reconnects, timeouts, and/or `le-connection-abort-by-local` messages in the debug logs, you may need to remove
your mug via `bluetoothctl remove my-mac-address` and factory reset your device. It should reconnect correctly afterward.
You may also need to re-add it to the app in order to make it writable again as well.

### 'Operation failed with ATT error: 0x0e' or another connection error

This seems to be caused by the bluetooth adaptor being in some sort of passive mode. I have not yet figured out how to wake it programmatically so sadly, you need to manually open `bluetoothctl` to do so.
Please ensure the device is in pairing mode (ie the light is flashing blue or says "PAIR") and run the `bluetoothctl` command. You don't need to type anything. run it and wait until the mug connects.


## Development

Install:
- [hatch](https://hatch.pypa.io/latest/install/)
- [pre-commit](https://pre-commit.com/)

```bash
pip install hatch
# Use CLI interface
hatch run ember-mug --help
# Run Tests
hatch run test:cov
# View docs
hatch docs:serve
# Lint code
pre-commit run --all-files
```

## Credits

This package was created with [Cookiecutter](https://github.com/audreyr/cookiecutter) and the [waynerv/cookiecutter-pypackage](https://github.com/waynerv/cookiecutter-pypackage) project template.

## Notice of Non-Affiliation and Disclaimer

This project is not affiliated, associated, authorized, endorsed by, or in any way officially connected with Ember.

The name Ember as well as related names, marks, emblems and images are registered trademarks of their respective owners.
