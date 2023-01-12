# Python Ember Mug

[![pypi](https://img.shields.io/pypi/v/python-ember-mug.svg)](https://pypi.org/project/python-ember-mug/)
[![python](https://img.shields.io/pypi/pyversions/python-ember-mug.svg)](https://pypi.org/project/python-ember-mug/)
[![Build Status](https://github.com/sopelj/python-ember-mug/actions/workflows/dev.yml/badge.svg)](https://github.com/sopelj/python-ember-mug/actions/workflows/dev.yml)
[![codecov](https://codecov.io/gh/sopelj/python-ember-mug/branch/main/graphs/badge.svg)](https://codecov.io/github/sopelj/python-ember-mug)
![Project Maintenance](https://img.shields.io/maintenance/yes/2023.svg?style=for-the-badge)

Python Library for Ember Mugs

* Documentation: <https://sopelj.github.io/python-ember-mug>
* GitHub: <https://github.com/sopelj/python-ember-mug>
* PyPI: <https://pypi.org/project/python-ember-mug/>
* Free software: MIT

## Summary

Library to attempt to interact with Ember Mugs via Bluetooth using the bleak library.
This was created for use with my [Home Assistant integration](https://github.com/sopelj/hass-ember-mug-component),
but could be useful separately and has a simple CLI interface too.

**Note**: I have only tested with my Ember Mug 2, but others should work. (Please let me know)

## Features

* Finding mugs
* Connecting to Mugs
* Reading Information (Colour, temp, liquid level, etc.)
* Writing (Desired temp, colour, temperature unit)*
* Polling for changes

*** Writing only works if the mug has been set up in the app previously

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
async with mug.connection() as con:
    print('Connected.\nFetching Info')
    await con.update_all()
    print(mug.formatted_data)
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

| Command     | Use                                                                            |
|-------------|--------------------------------------------------------------------------------|
| `discover`  | Find/List all detected unpaired mugs in pairing mode                           |
| `find`      | Find *one* already paired mugs                                                 |
| `info`      | Connect to *one* mug and print its current state                               |
| `poll`      | Connect to *one* mug and print its current state and keep watching for changes |
| `get`       | Get the value(s) of one or more attribute(s) by name                           |
| `set`       | Set one or more values on the mug                                              |


![CLI Example](./docs/images/cli-example.png)

## Caveats

- Since this api is not public, a lot of guesswork and reverse engineering is involved, so it's not perfect.
- If the mug has not been set up in the app since it was reset, writing is not allowed. I don't know what they set in the app, but it changes something, and it doesn't work without it.
- Once that mug has been set up in the app, you should ideally forget the device or at least turn off bluetooth whilst using it here, or you will probably get disconnected often
- I haven't figured out some attributes like udsk, dsk, location and timezone.

## Troubleshooting

### 'Operation failed with ATT error: 0x0e' or another connection error
This seems to be caused by the bluetooth adaptor being in some sort of passive mode. I have not yet figured out how to wake it programmatically so sadly, you need to manually open `bluetoothctl` to do so.
Please ensure the mug is in pairing mode (ie the light is flashing blue) and run the `bluetoothctl` command. You don,t need to type anything. run it and wait until the mug connects.

## Todo
- Test with other devices. Please let me know if you have tried it with others.

## Credits

This package was created with [Cookiecutter](https://github.com/audreyr/cookiecutter) and the [waynerv/cookiecutter-pypackage](https://github.com/waynerv/cookiecutter-pypackage) project template.
