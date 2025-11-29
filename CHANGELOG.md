# Changelog

## [1.3.0] - 2025-11-28

### Changed

* Change internal API for temperature conversion
* Remove rounding in temp conversion
* Use `bleak` >= 1.0.1

## [1.2.1] - 2025-11-28

### Fixed

* Add -59 to represent 14oz Mug 2 Stainless Steel for <https://github.com/sopelj/hass-ember-mug-component/issues/101>

## [1.2.0] - 2025-08-29

### Changed

* Remove `service_uuids` filtering for `find_mug` method

### Fixed

* Removed tests folder from packaging

## [1.1.1] - 2025-03-25

### Changed

* Change -51 to represent 14oz Ember Mug 2 (by [@Flight-Lab](https://github.com/Flight-Lab))

## [1.1.0] - 2024-11-02

### Changed

* Rename `find_mug` and `discover_mugs` to `find_device` and `discover_devices` respectively
* Improved documentation
* Bumped Bleak to 0.22.2

### Removed

* Dropped support for Python 3.10

## [1.0.1] - 2024-06-15

### Fixed
* discover method - `discovered_devices_and_advertisement_data` is a dict and not a list (#62)

## [1.0.0] - 2024-02-25

### Added

* Log statistics when debug is selected
* Min/Max temp (based on advertised values in manual)
* Add `as_dict` to allow for serialization

### Fixed

* Target temp will expect and handle Fahrenheit if `use_metric` is False

## [0.9.0] - 2024-01-25

### Added

* Detect model from advertiser data (Hopefully correctly)
* Colour, capacity and model numbers
* Handle Tumbler
* Rename "Unknown" state to "Standby"

### Changed

* Bumped minimum version of bleak to 0.21.0
* Discover method changed to use advertisement information
* `set_device` method replaced by `ble_event_callback` and it now also updated model info if not yet set.
* `model` renamed to `model_info`
* `include_extra` option removed. `debug` has a similar function now.

## [0.8.3] - 2023-10-31

### Fixed

* Set proper version and rebuild release

## [0.8.2] - 2023-10-31

### Added

* Tests for Python 3.12

### Changed

* Use debug level for connection timeout logger instead or error

## [0.8.1] - 2023-10-25

### Changed

* Use debug level for disconnect callback instead of warning

### Fixed

* Don't require adapter keyword for other backends

## [0.8.0] - 2023-10-25

### Added

* Added support for Travel Mug 2

### Changed

* Updated minimal dependencies

### Removed

* Dropped support for Python 3.9 as it is no longer supported by bleak-retry-connector and Home Assistant

## [0.7.0] - 2023-05-21

### Added

* Added support for Travel Mug
* Added debugger to dump characteristics and their values for debugging

### Changed

* Allow Travel Mug to be detected with shortened Bluetooth name
* Exclude led_colour attributes from the Travel Mug
* Add volume_level attribute for Travel Mug
* Make terms more generic as all devices are not Mugs

## [0.6.2] - 2023-04-14

### Added

* Added attributes to differentiate between device types
* Don't fetch name for the Ember "Cup" as it doesn't have it
* In theory the "Cup" should be supported

### Changed

* The model attribute of the data is now a Model class that provides attributes based on model

## [0.6.1] - 2023-04-13

### Added

* Discover Cups and Travel Mugs, but they are still not fully supported
* Debug option to print services and characteristics for debugging

## [0.6.0] - 2023-02-18

### Changed

* EmberMugConnection changed to EmberMug
* EmberMug changed to MugData
* Made ensure_connection private and call it automatically in most cases
* Log if disconnect was expected or not

### Added

* Lock for operations to ensure only one at a time
* _ensure_connection now called before every write and before bulk reads

### Fixed

* Changed condition that caused connections to be constantly reestablished because is_connected is not a bool.
* Don't call disconnect in disconnect callback

## [0.5.6] - 2023-02-08

### Fixed

* Set proper attribute for on charging base

### Changed

* Update pre-commit, pytest and add dependabot
* register callback stores a dict to avoid duplicate registrations

## [0.5.5] - 2023-02-03

### Changed

* Set values on mug immediately after setting them
* Only add/remove callback if not already done

## [0.5.4] - 2023-02-02

### Added

* More logging for different methods

### Changed

* Bump bleak to >=0.19.5 for Home Assistant 2023.2
* Catch exceptions on querying DSK and UDSK and return empty strings
* No longer query "extra" attributes unless `include_extra=True` was passed to mug

## [0.5.3] - 2023-01-18

### Changed

* Changed UUIDs, PushEvent IDs, LiquidState and TemperatureUnit to Enum
* TemperatureUnit changed to include degree symbol to match with Home Assistant

### Added

* Added _read and_write helper methods with logging

## [0.5.2] - 2023-01-17

### Fixed

* Fixed logging

## [0.5.1] - 2023-01-14

### Added

* as_dict() for dumping Mug info
* More tests

### Changed

* Allow unit with or without degree and handle Enum for Home Assistant in set_temperature_unit()
* Remove `metric` attribute, it was supposed to be `use_metric`

### Fixed

* Fixed `_device` attribute which would not be updated on callback

## [0.5.0] - 2023-01-11

### Added

* More tests for cli interface
* Add tests for Python 3.11

### Removed

* Automatic tests on macOS and Windows. They should still work though.

### Changed

* Update bleak and bleak-retry-connector to get retry decorator and match home assistant 2023.1
* Update documentation
* Updated linting and CI tools

## [0.4.2] - 2022-11-23

### Changed

* Also catch NotImplementedError when trying to pair. (Affects Home Assistant ESPHome proxies)

## [0.4.1] - 2022-11-04

### Fixed

* Format Colour as hex when printed (for CLI)

## [0.4.0] - 2022-11-03

### Changed

* Improve documentation for setting values

### Added

* cli option to get specific attributes by name
* cli option to set attributes
* cli option to limit output

### Fixed

* Column number calculation

## [0.3.7] - 2022-11-01

### Fix

* Remove ensure_connection in update_initial and update_multiple because it causes timeouts and loops

## Changes

* Update docs to document procedure for writing attributes

## [0.3.6] - 2022-10-19

### Fix

* Remove retry_bluetooth_connection_error...

## [0.3.5] - 2022-10-17

### Fix

* Add fallback method for retry_bluetooth_connection_error to not break on patch.

## [0.3.4] - 2022-10-17

### Added

* Use retry_bluetooth_connection_error on update methods

## [0.3.3] - 2022-10-17

### Fix

* Try to fetch services on initial connection to wake device

## [0.3.2] - 2022-10-12

### Fix

* Try to fix, but also always catch encoding errors

## [0.3.1] - 2022-10-10

### Fix

* Catch error decoding UDSK and log warning to avoid error setting up

## [0.3.0] - 2022-10-08

### Added

* Also packaged as CLI command to be used directly
* Add register_callback
* Fire callbacks in notifications and all updates
* Add set_device and pass to establish_connection

### Changed

* Update bleak-retry-connector to 1.17.1
* Update bleak to 0.17.0
* Renamed connect to ensure_connection

## [0.2.5] - 2022-09-18

### Fixed

* Catch EOFError during pair, which is not caught in bleak/dbus-next currently

## [0.2.4] - 2022-09-09

### Added

* Lots of tests

### Fixed

* Typo in metric in print_changes
* Fix Name validation rules
* set_temperature_unit method name

## [0.2.3] - 2022-09-09

### Added

* Format information as table in CLI
* Print message with error instead of stack trace in cli if bleak error occurs in find/discover

### Fixed

* Incorrect name for imperial CLI flag

## [0.2.2] - 2022-09-08

### Fixed

* Only try to disconnect if client is present

## [0.2.1] - 2022-09-08

### Added

* Tests for data, scanner, mug
* CLI flag for imperial units

### Fixed

* meta_display was not property
* target_temp returned current_temp
* extra flag was not applied to polling

## [0.2.0] - 2022-09-06

### Added

* bleak-retry-connector to help connect and maintain connection to mug
* Add option to show/hide less useful mug info
* Formatting for polled changes in CLI
* Add more tests

### Removed

* Support for python 3.8 - In order to use bleak-retry-connector

## [0.1.2] - 2022-09-03

### Added

* Add adapter param to EmberMugConnection and scanners (for BlueZ only)
* Add mac params to discover and find methods
* Decode udsk and mug id. Even if the values aren't super useful.

### Fixed

* Improve CLI interface and gracefully handle no options provided

## [0.1.1] - 2022-09-03

* Bump version because of issues with name conflicts
* Fix GitHub Actions issues with Poetry

## [0.1.0] - 2022-08-26

* First release on PyPI test.
