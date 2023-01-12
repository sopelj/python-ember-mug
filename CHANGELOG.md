# Changelog

## [0.5.0]

## Added
* More tests for cli interface
* Add tests for Python 3.11

## Removed
* Automatic tests on macOS and Windows. They should still work though.

## Changed
* Update bleak and bleak-retry-connector to get retry decorator and match home assistant 2023.1
* Update documentation
* Updated linting and CI tools

## [0.4.2]

### Changed
* Also catch NotImplementedError when trying to pair. (Affects Home Assistant ESPHome proxies)

## [0.4.1]

### Fixed
* Format Colour as hex when printed (for CLI)

## [0.4.0]

### Changed
* Improve documentation for setting values

### Added
* cli option to get specific attributes by name
* cli option to set attributes
* cli option to limit output

### Fixed
* Column number calculation

## [0.3.7]

### Fix
* Remove ensure_connection in update_initial and update_multiple because it causes timeouts and loops

## Changes
* Update docs to document procedure for writing attributes

## [0.3.6]

### Fix
* Remove retry_bluetooth_connection_error...

## [0.3.5]

### Fix
* Add fallback method for retry_bluetooth_connection_error to not break on patch.

## [0.3.4]

### Added
* Use retry_bluetooth_connection_error on update methods

## [0.3.3]

### Fix
* Try to fetch services on initial connection to wake device

## [0.3.2]

### Fix
* Try to fix, but also always catch encoding errors

## [0.3.1]

### Fix
* Catch error decoding UDSK and log warning to avoid error setting up

## [0.3.0]

### Added
* Also packaged as CLI command to be used directly
* Add register_callback
* Fire callbacks in notifications and all updates
* Add set_device and pass to establish_connection

### Changed
* Update bleak-retry-connector to 1.17.1
* Update bleak to 0.17.0
* Renamed connect to ensure_connection

## [0.2.5]

### Fixed
* Catch EOFError during pair, which is not caught in bleak/dbus-next currently

## [0.2.4]

### Added
* Lots of tests

### Fixed
* Typo in metric in print_changes
* Fix Name validation rules
* set_temperature_unit method name

## [0.2.3]

### Added
* Format information as table in CLI
* Print message with error instead of stack trace in cli if bleak error occurs in find/discover

### Fixed
* Incorrect name for imperial CLI flag

## [0.2.2]

### Fixed
* Only try to disconnect if client is present

## [0.2.1]

### Added
* Tests for data, scanner, mug
* CLI flag for imperial units

### Fixed
* meta_display was not property
* target_temp returned current_temp
* extra flag was not applied to polling

## [0.2.0]

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
