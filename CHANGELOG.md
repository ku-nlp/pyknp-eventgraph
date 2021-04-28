# Change Log
All notable changes to this project will be documented in this file.

## [6.1.4]
- Reduce debug printing.
- Fix a bug in the process to add special marks to events' text.
- Use poetry for package management.

## [6.1.3]

### Changed
- Renamed Token to BasePhrase.

### Fixed
- Fixed the logic to merge modifier events.

## [6.1.2]

### Fixed
- Fixed a bug in the logic to normalize event strings.
- Fixed a bug in the logic to add "|" marks.

## [6.1.1]

### Fixed
- Fixed a bug in head_reps assignment.

## [6.1.0]

### Changed
- Introduce PAS class, which manages a predicate and its arguments.

## [6.0.1]

### Changed
- Introduced a cache for computationally heavy properties.

## [6.0.0]

### Changed
- Drastically refactored the construction logic.
- Added a number of properties for the use as a high-level interface built on pyknp.

## [0.5.3]

### Fixed
- Fixed a bug related to complex particle handling

## [0.5.2]

### Fixed
- Fixed a bug related to shallow copy of basic phrases.

## [0.5.0]

### Changed
- Represented arguments by a dictionary of **list** of argument information.

### Removed
- Removed the attribute `event_head` from `Argument`. 
- Removed the parameters `logging_level` and `logger` to `EventGraph.build()`, `EventGraph.load()`, and `EventGraphVisualizer.make_image()`.

## Fixed
- Fixed a bug in normalizing event strings.
- Fixed a bug in handling parallel phrases.

## [0.4.2]

### Changed
- Improved efficiency and readability of codes.

## [0.4.1]

### Added
- Introduced `__iter__()` into the class `Event`. This function yields constituent basic phrases in order.

### Changed
- Removed the attribute `omitted_case` from `BasicPhrase`. Instead, introduced the attributes `case` and `is_omitted`.

## [0.4.0]

### Added
- Introduced the class `BasicPhrase`, which is a wrapper of `pyknp.Tag`. With this change, removed the class `Content`.
- Introduced the parameters `logging_level` and `logger` to `EventGraph.build()`, `EventGraph.load()`, and `EventGraphVisualizer.make_image()`. According to this change, removed the attribute `verbose` from them.
- Introduced a function to save EventGraph as a binary file. According to this change, removed `EventGraph.output_json()`.

### Changed
- Improved normalization rules for an event surface
- Quarried `Features` class from `event.py`.
- Revised the naming of the following functions:
  - `EventGraph.output_json()` -> `EventGraph.save()`
- Revised the naming of the following attributes:
  - rep -> reps
  - rep_with_mark -> reps_with_mark
  - normalized_rep -> normalized_reps
  - normalized_rep_with_mark -> normalized_reps_with_mark
  - standard_rep -> standard_reps
  - content_reps -> content_rep_list
  - clausal_modifier_event_ids -> adnominal_event_ids
  - complementizer_event_ids -> sentential_complement_event_ids
  - feature -> features
