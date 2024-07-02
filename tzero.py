#!/usr/bin/env python3

"""IRC Channel Timebox Keeper."""

from __future__ import annotations

import enum
import json
import logging
import pathlib
import select
import socket
import ssl
import time
from typing import Any, ClassVar, Iterator

_NAME = "tzero"
_LOG = logging.getLogger(_NAME)
_DEV_MODE = False

_DEFAULT_DURATION = 30
_MIN_DURATION = 15
_MAX_DURATION = 60
_DURATION_MULTIPLE = 5

_MAX_KEEP_TIMEBOXES = 3 if _DEV_MODE else 10
_MAX_KEEP_DURATION = 60 if _DEV_MODE else 2 * 86400


class _Ctx:
    retry_delay: ClassVar[int] = 1
    state: ClassVar[dict[str, Any]] = {"timebox": {}}
    commands: ClassVar[list[str]] = [
        "begin",
        "cancel",
        "delete",
        "list",
        "mine",
        "running",
        "time",
        "help",
    ]


class _TState(enum.StrEnum):
    RUNNING = enum.auto()
    COMPLETED = enum.auto()


def main() -> None:
    """Run this tool."""
    log_fmt = (
        "%(asctime)s %(levelname)s %(filename)s:%(lineno)d "
        "%(funcName)s() %(message)s"
    )
    log_level = logging.DEBUG if _DEV_MODE else logging.INFO
    logging.basicConfig(format=log_fmt, level=log_level)

    # Read configuration.
    with pathlib.Path(f"{_NAME}.json").open() as stream:
        config = json.load(stream)

    # Ensure we can write to state file.
    _read_state(config["state"])
    _clean_state()
    _write_state(config["state"])

    # Run application forever.
    while True:
        try:
            _run(
                config["host"],
                config["port"],
                config["tls"],
                config["nick"],
                config["password"],
                config["channels"],
                config["prefix"],
                config["block"],
                config["state"],
            )
        except Exception:  # noqa: PERF203, BLE001 (try-except-in-loop, blind-except)
            _LOG.exception("Client encountered error")
            _LOG.info("Reconnecting in %d s", _Ctx.retry_delay)
            time.sleep(_Ctx.retry_delay)
            _Ctx.retry_delay = min(_Ctx.retry_delay * 2, 3600)


def _run(
    host: str,
    port: int,
    tls: bool,
    nick: str,
    password: str,
    channels: list[str],
    prefix: str,  # e.g., ","
    blocked_words: list[str],
    state_filename: str,
) -> None:
    _LOG.info("Connecting ...")
    sock = socket.create_connection((host, port))
    if tls:
        tls_context = ssl.create_default_context()
        sock = tls_context.wrap_socket(sock, server_hostname=host)

    _LOG.info("Authenticating ...")
    _send(sock, f"PASS {password}")
    _send(sock, f"NICK {nick}")
    _send(sock, f"USER {nick} {nick} {host} :{nick}")

    _LOG.info("Joining channels ...")
    for channel in channels:
        _send(sock, f"JOIN {channel}")

    _LOG.info("Receiving messages ...")
    for line in _recv(sock):
        if line is not None:
            sender, command, middle, trailing = _parse_line(line)
            if command == "PING":
                _send(sock, f"PONG :{trailing}")
                _Ctx.retry_delay = 1
            elif command == "PRIVMSG":
                _LOG.info(
                    "sender: %s; command: %s; middle: %s; trailing: %s",
                    sender,
                    command,
                    middle,
                    trailing,
                )
                if sender and middle and trailing and trailing.startswith(prefix):
                    try:
                        _process_message(
                            sock, nick, prefix, blocked_words, sender, middle, trailing
                        )
                        _Ctx.retry_delay = 1
                    except Exception:  # noqa: BLE001 (blind-except)
                        _LOG.exception("Command processor encountered error")
        try:
            _complete_timeboxes(sock)
            _clean_state()
            _write_state(state_filename)
        except Exception:  # noqa: BLE001 (blind-except)
            _LOG.exception("Task processor encountered error")


def _process_message(
    sock: socket.socket,
    nick: str,
    prefix: str,  # e.g., ","
    blocked_words: list[str],
    sender: str,
    recipient: str,
    message: str,
) -> None:
    # If this tool's nickname is same as the receiver name (recipient)
    # found in the received message, the message was sent privately to
    # this tool.
    private = nick == recipient

    # While replying to private messages, the response should be sent
    # to the sender.  While replying to channel messages, the response
    # should be sent to the channel (recipient).
    audience = sender if private else recipient

    words = message.split()
    command = _remove_prefix(words[0], prefix)
    params = words[1:]

    # Validate command.
    matches = _find_command(command)
    if len(matches) == 0:
        msg = (
            "Error: Unrecognized command.  Available commands: "
            f"{_command_list(prefix, _Ctx.commands)}."
        )
        _send_message(sock, audience, msg)
        return

    if len(matches) > 1:
        msg = (
            "Error: Ambiguous command.  Matching commands: "
            f"{_command_list(prefix, matches)}."
        )
        _send_message(sock, audience, msg)
        return

    command = matches[0]

    if any(word in params for word in blocked_words):
        msg = "Error: Parameters contain blocked word."
        _send_message(sock, audience, msg)
        return

    command_function = globals()[f"_{command}_command"]
    throttle_delay = 0
    for msg in command_function(prefix, sender, command, params, audience, private):
        _send_message(sock, audience, msg)
        time.sleep(throttle_delay)
        throttle_delay = 1


# Command begin
def _begin_command(  # noqa: PLR0911 (too-many-return-statements)
    prefix: str,
    person: str,
    command: str,
    params: list[str],
    audience: str,
    private: bool,
) -> list[str]:
    if len(params) == 0:
        return ["Error: " + _begin_help(prefix, command)[0]]

    if params[0].isdigit():
        if len(params) == 1:
            return ["Error: Duration must be followed by task summary."]
        duration = int(params[0])
        summary = " ".join(params[1:])
    else:
        duration = _DEFAULT_DURATION
        summary = " ".join(params)

    if duration < _MIN_DURATION:
        return [f"Error: Duration must be at least {_MIN_DURATION} minutes."]

    if duration > _MAX_DURATION:
        return [f"Error: Duration must not exceed {_MAX_DURATION}  minutes."]

    if duration % _DURATION_MULTIPLE != 0:
        return [f"Error: Duration must be a multiple of {_DURATION_MULTIPLE} minutes."]

    audkey = "private" if private else audience
    timeboxes = _Ctx.state["timebox"].get(audkey, {}).get(person, [])
    if len(timeboxes) > 0 and timeboxes[-1]["state"] == _TState.RUNNING:
        return [
            f"Error: Another timebox is in progress in {audkey}: "
            f"{_format_timebox(person, timeboxes[-1])}.  "
            f"Send {prefix}cancel to cancel the currently running "
            "timebox before starting a new timebox."
        ]

    persons = _Ctx.state["timebox"].get(audkey, {})
    if not persons:
        _Ctx.state["timebox"][audkey] = {}  # Empty persons dictionary.

    timeboxes = _Ctx.state["timebox"][audkey].get(person)
    if timeboxes is None:
        timeboxes = _Ctx.state["timebox"][audkey][person] = []

    new_timebox = {
        "audience": audience,  # Used for notifying completed timeboxes.
        "start": int(time.time()),
        "duration": duration,
        "summary": summary,
        "state": _TState.RUNNING,
    }

    timeboxes.append(new_timebox)
    return [f"Started timebox in {audkey}: {_format_timebox(person, new_timebox)}"]


def _begin_help(prefix: str, command: str) -> list[str]:
    return [
        f"Usage: {prefix}{command} [MINUTES] SUMMARY.  "
        f"Example #1: {prefix}{command} Read SICP.  "
        f"Example #2: {prefix}{command} 45 Review article.  "
        "Start a new timebox for the specified number of MINUTES.  "
        "MINUTES must be a multiple of 5 between 15 and 60, inclusive.  "
        "If MINUTES is not specified, default to 30 minutes."
    ]


# Command cancel
def _cancel_command(
    prefix: str,
    person: str,
    command: str,
    params: list[str],
    audience: str,
    private: bool,
) -> list[str]:
    if len(params) > 0:
        return ["Error: " + _cancel_help(prefix, command)[0]]

    audkey = "private" if private else audience
    timeboxes = _Ctx.state["timebox"].get(audkey, {}).get(person)
    if timeboxes is None or timeboxes[-1]["state"] != _TState.RUNNING:
        return [f"Error: No running timeboxes found for {person} in {audkey}."]

    cancelled_timebox = timeboxes[-1]
    del timeboxes[-1]
    return ["Cancelled running timebox: " + _format_timebox(person, cancelled_timebox)]


def _cancel_help(prefix: str, command: str) -> list[str]:
    return [f"Usage: {prefix}{command}.  Cancel your currently running timebox."]


# Command delete
def _delete_command(
    prefix: str,
    person: str,
    command: str,
    params: list[str],
    audience: str,
    private: bool,
) -> list[str]:
    if len(params) > 0:
        return ["Error: " + _delete_help(prefix, command)[0]]

    audkey = "private" if private else audience
    timeboxes = _Ctx.state["timebox"].get(audkey, {}).get(person)
    if timeboxes is None:
        return [f"Error: No timeboxes found for {person} in {audkey}."]

    if timeboxes[-1]["state"] == _TState.RUNNING:
        return [
            f"Warning: Another timebox is in progress in {audkey}: "
            f"{_format_timebox(person, timeboxes[-1])}.  "
            f"First cancel the running timebox with {prefix}cancel.  "
            f"Then delete the last completed timebox with {prefix}delete."
        ]

    deleted_timebox = timeboxes[-1]
    del timeboxes[-1]
    return [
        "Deleted the last completed timebox: "
        f"{_format_timebox(person, deleted_timebox)}"
    ]


def _delete_help(prefix: str, command: str) -> list[str]:
    return [
        f"Usage: {prefix}{command}.  "
        "Delete your last completed timebox in current channel."
    ]


def _list_command(
    prefix: str,
    person: str,
    command: str,
    params: list[str],
    audience: str,
    private: bool,
) -> list[str]:
    if len(params) > 0:
        return ["Error: " + _list_help(prefix, command)[0]]

    audkey = "private" if private else audience

    completed = []
    persons = _Ctx.state["timebox"].get(audkey, {})
    for person, timeboxes in persons.items():
        completed.extend(
            [(person, t) for t in timeboxes if t["state"] == _TState.COMPLETED]
        )

    if len(completed) == 0:
        return [f"No completed timeboxes found in {audkey}."]

    completed.sort(key=lambda x: x[1]["start"], reverse=True)
    return [f"Completed timeboxes in {audkey}:"] + [
        _format_timebox(person, t) for person, t in completed
    ]


def _list_help(prefix: str, command: str) -> list[str]:
    return [
        f"Usage: {prefix}{command}.  List completed timeboxes in current channel.  "
        f"Only most recent {_MAX_KEEP_TIMEBOXES} timeboxes started "
        f"within the last {_MAX_KEEP_DURATION} hours are listed.  "
    ]


# Command mine.
def _mine_command(
    prefix: str,
    person: str,
    command: str,
    params: list[str],
    audience: str,
    private: bool,
) -> list[str]:
    if len(params) > 0:
        return ["Error: " + _list_help(prefix, command)[0]]

    audkey = "private" if private else audience
    timeboxes = _Ctx.state["timebox"].get(audkey, {}).get(person)
    if timeboxes is None:
        return [f"No timeboxes found for {person} in {audkey}."]

    completed = [t for t in timeboxes if t["state"] == _TState.COMPLETED]
    if len(completed) == 0:
        return [f"No completed timeboxes found for {person} in {audkey}."]

    completed.sort(key=lambda x: x["start"], reverse=True)
    return [f"Completed timeboxes of {person} in {audkey}:"] + [
        _format_timebox(person, t) for t in completed
    ]


def _mine_help(prefix: str, command: str) -> list[str]:
    return [
        f"Usage: {prefix}{command}.  List your completed timeboxes.  "
        f"Only your most recent {_MAX_KEEP_TIMEBOXES} timeboxes started "
        f"within the last {_MAX_KEEP_DURATION} hours are available.  "
        "Older timeboxes are permanently removed from the system."
    ]


# Command running.
def _running_command(
    prefix: str,
    person: str,
    command: str,
    params: list[str],
    audience: str,
    private: bool,
) -> list[str]:
    if len(params) > 0:
        return ["Error: " + _running_help(prefix, command)[0]]

    running = []
    audkey = "private" if private else audience
    persons = _Ctx.state["timebox"].get(audkey, {})
    for person, timeboxes in persons.items():
        if timeboxes[-1]["state"] == _TState.RUNNING:
            running.append((person, timeboxes[-1]))

    if len(running) == 0:
        return [f"No running timeboxes found in {audkey}."]

    running.sort(key=lambda x: x[1]["start"], reverse=True)
    return [f"Timeboxes currently running in {audkey}:"] + [
        _format_timebox(person, timebox) for person, timebox in running
    ]


def _running_help(prefix: str, command: str) -> list[str]:
    return [f"Usage: {prefix}{command}.  List all running timeboxes of the channel."]


# Command time
def _time_command(
    prefix: str,
    _person: str,
    command: str,
    params: list[str],
    _audience: str,
    _private: bool,
) -> list[str]:
    if len(params) > 0:
        return ["Error: " + _time_help(prefix, command)[0]]
    return [time.strftime("%Y-%m-%d %H:%M:%S %Z", time.gmtime())]


def _time_help(prefix: str, command: str) -> list[str]:
    return [f"Usage: {prefix}{command}.  Show current UTC time."]


# Command help
def _help_command(
    prefix: str,
    _person: str,
    command: str,
    params: list[str],
    _audience: str,
    _private: bool,
) -> list[str]:
    if len(params) == 0:
        return _help_help(prefix, command)

    params[0] = _remove_prefix(params[0], prefix)
    matches = _find_command(params[0])

    if len(matches) == 0:
        return [
            "Error: Unrecognized command.  Available commands: "
            f"{_command_list(prefix, _Ctx.commands)}."
        ]

    if len(matches) > 1:
        return [
            "Error: Ambiguous command.  Matching commands: "
            f"{_command_list(prefix, matches)}."
        ]

    command = matches[0]
    help_function = globals()[f"_{command}_help"]
    return help_function(prefix, command)


def _help_help(prefix: str, command: str) -> list[str]:
    return [
        f"Usage: {prefix}{command} [COMMAND].  Available commands: "
        + _command_list(prefix, _Ctx.commands)
        + "."
    ]


# Tasks.
def _complete_timeboxes(sock: socket.socket) -> None:
    current_time = int(time.time())
    multiplier = 1 if _DEV_MODE else 60
    for audkey, persons in _Ctx.state["timebox"].items():
        for person, timeboxes in persons.items():
            if len(timeboxes) == 0:
                continue
            last = timeboxes[-1]
            if (
                last["state"] == _TState.RUNNING
                and last["start"] + last["duration"] * multiplier <= current_time
            ):
                last["state"] = _TState.COMPLETED
                msg = f"Completed timebox in {audkey}: {_format_timebox(person, last)}"
                _send_message(sock, last["audience"], msg)


def _clean_state() -> None:
    current_time = int(time.time())
    cleaned_timebox_state: dict[str, dict[str, list[dict[str, int | str]]]] = {}
    for audkey, persons in _Ctx.state["timebox"].items():
        for person, timeboxes in persons.items():
            cleaned_timeboxes = [
                timebox
                for timebox in timeboxes
                if current_time <= timebox["start"] + _MAX_KEEP_DURATION
            ]
            cleaned_timeboxes = cleaned_timeboxes[-_MAX_KEEP_TIMEBOXES:]
            if len(cleaned_timeboxes) > 0:
                if audkey not in cleaned_timebox_state:
                    cleaned_timebox_state[audkey] = {}
                cleaned_timebox_state[audkey][person] = cleaned_timeboxes
    _Ctx.state["timebox"] = cleaned_timebox_state


# Utility functions
def _read_state(filename: str) -> None:
    if pathlib.Path(filename).exists():
        with pathlib.Path(filename).open() as stream:
            _Ctx.state = json.load(stream)
        _LOG.debug("Loaded state from %s: %s", filename, _Ctx.state)
    else:
        _LOG.debug("State file %s does not exist", filename)


def _write_state(filename: str) -> None:
    _LOG.debug("Saving state: %s", _Ctx.state)
    with pathlib.Path(filename).open("w") as stream:
        json.dump(_Ctx.state, stream, indent=2)


def _find_command(command: str) -> list[str]:
    return [c for c in _Ctx.commands if c.startswith(command)]


def _command_list(prefix: str, commands: list[str]) -> str:
    return " ".join(prefix + c for c in commands)


def _remove_prefix(word: str, prefix: str) -> str:
    if word.startswith(prefix):
        return word[len(prefix) :]
    return word


def _format_timebox(person: str, timebox: dict[str, Any]) -> str:
    start = timebox["start"]
    duration = timebox["duration"]
    summary = timebox["summary"]
    start_str = time.strftime("%H:%M %Z", time.gmtime(start))
    return f"{person} [{start_str}] ({duration} min) {summary}"


# Protocol functions
def _recv(sock: socket.socket) -> Iterator[str | None]:
    buffer = ""
    while True:
        # Check if any data has been received.
        rlist, _, _ = select.select([sock], [], [], 1)
        if len(rlist) == 0:
            yield None
            continue

        # If data has been received, validate data length.
        data = sock.recv(1024)
        if len(data) == 0:
            message = "Received zero-length payload from server"
            _LOG.error(message)
            raise ValueError(message)

        # If there is nonempty data, yield lines from it.
        buffer += data.decode(errors="replace")
        lines = buffer.split("\r\n")
        lines, buffer = lines[:-1], lines[-1]
        for line in lines:
            _LOG.info("recv: %s", line)
            yield line


def _send_message(sock: socket.socket, recipient: str, message: str) -> None:
    size = 400
    for line in message.splitlines():
        chunks = [line[i : i + size] for i in range(0, len(line), size)]
        for chunk in chunks:
            _send(sock, f"PRIVMSG {recipient} :{chunk}")


def _send(sock: socket.socket, message: str) -> None:
    sock.sendall(message.encode() + b"\r\n")
    _LOG.info("sent: %s", message)


def _parse_line(line: str) -> tuple[str | None, str, str | None, str | None]:
    # RFC 1459 - 2.3.1
    # <message>  ::= [':' <prefix> <SPACE> ] <command> <params> <crlf>
    # <prefix>   ::= <servername> | <nick> [ '!' <user> ] [ '@' <host> ]
    # <command>  ::= <letter> { <letter> } | <number> <number> <number>
    # <SPACE>    ::= ' ' { ' ' }
    # <params>   ::= <SPACE> [ ':' <trailing> | <middle> <params> ]
    #
    # Example: :alice!Alice@user/alice PRIVMSG #hello :hello
    # Example: PING :foo.example.com
    if line[0] == ":":
        prefix, rest = line[1:].split(maxsplit=1)
    else:
        prefix, rest = None, line

    sender, command, middle, trailing = None, None, None, None

    if prefix:
        sender = prefix.split("!")[0]

    command_and_rest = rest.split(None, 1)
    command = command_and_rest[0].upper()

    if len(command_and_rest) == 2:  # noqa: PLR2004 (magic-value-comparison)
        params = command_and_rest[1].split(":", 1)
        middle = params[0].strip()
        if len(params) == 2:  # noqa: PLR2004 (magic-value-comparison)
            trailing = params[1].strip()

    return sender, command, middle, trailing


if __name__ == "__main__":
    main()
