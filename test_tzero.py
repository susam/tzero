"""Tests for tzero module."""

import tzero

# ruff: noqa: S101, SLF001


def test_format_duration() -> None:
    """Test _format_duration()."""
    assert tzero._format_duration(0) == ""
    assert tzero._format_duration(1) == "1 second"
    assert tzero._format_duration(2) == "2 seconds"
    assert tzero._format_duration(59) == "59 seconds"
    assert tzero._format_duration(60) == "1 minute"
    assert tzero._format_duration(61) == "1 minute 1 second"
    assert tzero._format_duration(62) == "1 minute 2 seconds"
    assert tzero._format_duration(3599) == "59 minutes 59 seconds"
    assert tzero._format_duration(3600) == "1 hour"
    assert tzero._format_duration(3601) == "1 hour 1 second"
    assert tzero._format_duration(3602) == "1 hour 2 seconds"
    assert tzero._format_duration(3660) == "1 hour 1 minute"
    assert tzero._format_duration(3720) == "1 hour 2 minutes"
    assert tzero._format_duration(86399) == "23 hours 59 minutes 59 seconds"
    assert tzero._format_duration(86400) == "1 day"
    assert tzero._format_duration(86401) == "1 day 1 second"
    assert tzero._format_duration(86402) == "1 day 2 seconds"
    assert tzero._format_duration(90000) == "1 day 1 hour"
    assert tzero._format_duration(93600) == "1 day 2 hours"
    assert tzero._format_duration(172799) == "1 day 23 hours 59 minutes 59 seconds"
    assert tzero._format_duration(172800) == "2 days"
    assert tzero._format_duration(172801) == "2 days 1 second"
    assert tzero._format_duration(172802) == "2 days 2 seconds"
    assert tzero._format_duration(172860) == "2 days 1 minute"
    assert tzero._format_duration(172920) == "2 days 2 minutes"
