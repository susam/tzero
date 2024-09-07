Changelog
=========

0.3.0 (UNRELEASED)
------------------

### Added

- Configuration field `keep_timeboxes` to configure the maximum number
  of timeboxes to retain in state per user per channel.
- Configuration field `keep_duration` to configure the maximum
  duration for which timeboxes are retained in state.
- Configuration field `max_print_channel` to configure the maximum
  number of timeboxes to be listed in a channel in response to `list`
  or `mine` commands.
- Configuration field `max_print_private` to configure the maximum
  number of timeboxes to be listed in private message in response to
  `list` or `mine` commands.


0.2.0 (2024-08-03)
------------------

### Added

- Support for timeboxes started by users from Matrix rooms bridged to
  IRC channels using [NIMB][].
- Command `summary` to display summary of timeboxes run across all channels.
- Command `version` to display version, copyright, and license details.


### Changed

- Show abbreviated weekday in start times of timeboxes.


0.1.0 (2024-07-02)
------------------

### Added

- Command `begin` to start a timebox.
- Command `cancel` to cancel a timebox.
- Command `delete` to delete a timebox.
- Command `list` to list completed timeboxes in channel.
- Command `mine` to list completed timeboxes in channel.
- Command `running` to list running timeboxes.
- Command `time` to display current time.
- Command `help` to display usage message.
- Support for tracking timeboxes across multiple channels.
- Support for tracking timeboxes started over private message.


[NIMB]: https://github.com/susam/nimb
