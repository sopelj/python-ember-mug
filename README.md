# Python Ember Mug

[![pypi](https://img.shields.io/pypi/v/python-ember-mug.svg)](https://pypi.org/project/python-ember-mug/)
[![python](https://img.shields.io/pypi/pyversions/python-ember-mug.svg)](https://pypi.org/project/python-ember-mug/)
[![Build Status](https://github.com/sopelj/python-ember-mug/actions/workflows/dev.yml/badge.svg)](https://github.com/sopelj/python-ember-mug/actions/workflows/dev.yml)
[![codecov](https://codecov.io/gh/sopelj/python-ember-mug/branch/main/graphs/badge.svg)](https://codecov.io/github/sopelj/python-ember-mug)

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
* Polling for changes

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
```

Basic options:

| Command    | Use                                                                            |
|------------|--------------------------------------------------------------------------------|
| `discover` | Find/List all detected unpaired mugs in pairing mode                           |
| `find`     | Find *one* already paired mugs                                                 |
| `info`     | Connect to *one* mug and print its current state                               |
| `poll`     | Connect to *one* mug and print its current state and keep watching for changes |

![CLI Example](./docs/images/cli-example.png)

## Caveats

- Since this api is not public, a lot of guesswork and reverse engineering is involved, so it's not perfect.
- Only works with one mug at a time
- These mugs do not broadcast data unless paired. So you can only have one device connected to it. You need to reset them to change to another device and make sure the previous device doesn't try to reconnect.
- Reading data from the mug seems to work pretty well, but I have been unable to write to it so far... I always get NotPermitted errors.
- I haven't figured out some attributes like udsk, dsk, location,

## Credits

This package was created with [Cookiecutter](https://github.com/audreyr/cookiecutter) and the [waynerv/cookiecutter-pypackage](https://github.com/waynerv/cookiecutter-pypackage) project template.
