# Changelog

## [Unreleased]

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
