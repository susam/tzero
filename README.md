Tzero
=====

Tzero is a timeboxing manager for IRC channels.  This tool connects to
an IRC network as a client and functions as an IRC bot.  Users of the
channel may send bot commands like `,begin`, `,list`, `,mine`,
`,running`, etc. to manage and view their timeboxes.

Timeboxing is a time management technique that is believed to boost
productivity by limiting the time during which a task is supposed to
be completed.  A time box is a fixed period of time alloted for a task
or activity.  This tool lets users of an IRC channel start and manage
their timeboxes while they block off some time for productive work.

There is a time management technique known as the [Pomodoro Technique]
which is closely related to the timeboxing technique.  The Pomodoro
Technique prescribes specific guidelines like 25 minute timeboxes, 5
minute break after each timebox, a longer break after every 4
timeboxes, etc.  This tool, however, supports timeboxing in general
without any specific guidelines.  But if you wish to practice the
Pomodoro Technique with this tool, it is definitely possible to do so
since this tool is, after all, a simple timer bot for IRC.

To see Tzero in action, join either of the two channels:

- [#bitwise:libera.chat](https://web.libera.chat/#bitwise)
- [#bitwise:matrix.org](https://app.element.io/#/room/#bitwise:matrix.org)

The first one is an IRC channel and the second one is a Matrix room.
Both channels are bridged together, so messages posted to one channel
are visible in the other.  There is an instance of Tzero running in
the IRC channel.  It is connected to the channel with the nickname
`t0`.  Send the command `,help` to the channel to see `t0` reply with
a usage help message.

[Pomodoro Technique]: https://en.wikipedia.org/wiki/Pomodoro_Technique


Contents
--------

* [Get Started](#get-started)
* [Features](#features)
* [Example Session](#example-session)
* [Commands](#commands)
  * [begin](#begin)
  * [cancel](#cancel)
  * [delete](#delete)
  * [list](#list)
  * [mine](#mine)
  * [running](#running)
  * [summary](#summary)
  * [time](#time)
  * [help](#help)
  * [version](#version)
* [Configuration](#configuration)
* [NIMB Support](#nimb-support)
* [License](#license)
* [Support](#support)


Get Started
-----------

Perform the following steps to get started with Tzero.

 1. Clone this repository.  For example,

    ```sh
    git clone https://github.org/susam/tzero.git
    ```

 2. Create configuration file:

    ```sh
    cd tzero
    cp etc/tzero.json tzero.json
    ```

    Then edit the new configuration file named `tzero.json` to include
    connection details for the IRC nick that should be used to connect
    to an IRC network.  Some example values are already populated in
    this file to help you get started.

 3. Run Tzero:

    ```sh
    python3 tzero.py
    ```

Note that Tzero does not depend on any external Python library or
package.  It only depends on a recent version of Python 3 and its
standard library.


Features
--------

* Basic timeboxing: Tzero supports commands like `begin` and `cancel`
  to start a timebox and cancel a timebox before its completion (say,
  if you change your mind about it), respectively.  The `list` command
  lets you list all completed timeboxes in the current channel.  The
  `mine` command lets you list your own completed timeboxes in the
  current channel.

* Multi-channel: Tzero can log into multiple channels simultaneously
  and track timeboxes started by users of each channel separately.

* Channel isolation: Timeboxes are scoped to the channel where the
  timebox was started.  A user connected to one channel cannot see or
  list running or completed timeboxes on another channel.

* Private timeboxing: Users can run timeboxes privately by sending
  private messages to Tzero with `/msg` or `/query` commands.  A
  private message session is also treated like a virtual private
  channel, so it too benefits from the channel isolation feature.

* Persistent state: Data pertaining to running and completed timeboxes
  are saved to a configurable state file.  As a result, if the tool
  stops for any reason, it continues to track the timeboxes, as if
  nothing happened, after it restarts.

* Limited retention: Within each channel or private message session,
  only the most recent 10 timeboxes started in the last 48 hours are
  kept in the state file.  Older timeboxes are permanently deleted.
  Therefore there is no way to list such older timeboxes.

* One timebox per user per channel at a time: Within a channel, a user
  can run a maximum of only one timebox at a time.  However, the same
  user can run multiple timeboxes simultaneously as long as they are
  in different channels.


Example Session
---------------

```
20:07 <susam> ,begin Read "Galois Theory" by Stewart (2015)
20:07 <t0> Started timebox in #bitwise: susam [Sun 20:07 GMT] (30 min) Read "Galois Theory" by Stewart (2015)
20:37 <t0> Completed timebox in #bitwise: susam [Sun 20:07 GMT] (30 min) Read "Galois Theory" by Stewart (2015)
20:39 <susam> ,list
20:39 <t0> Completed timeboxes in #bitwise:
20:39 <t0> susam [Sun 20:07 GMT] (30 min) Read "Galois Theory" by Stewart (2015)
20:39 <t0> susam [Sun 19:27 GMT] (30 min) Read "Introduction to Analytic Number Theory" by Apostol (1976)
20:39 <t0> gigo [Sun 18:51 GMT] (30 min) Add Vertico to my Emacs setup
20:39 <t0> gigo [Sun 16:09 GMT] (30 min) Read <https://go.dev/tour/concurrency/1>
20:39 <t0> drwiz [Sun 16:09 GMT] (30 min) Solve the N Queens Problem in C++.
20:40 <susam> ,summary
20:40 <t0> I have run 15 timeboxes across all channels, totalling 900 minutes.  The average length of each timebox is 30 minutes.
```


Commands
--------

As can be seen in the previous section, Tzero supports several
commands like `begin`, `list`, `summary`, etc.  Commands must begin
with a prefix string.  In the example presented in the previous
section, the prefix string is `,` (the comma).  The prefix string
needs to be configured in the configuration file.  See section
[Configuration](#configuration) for more details.

A command name may be truncated to any positive length.  For example,
the `begin` command be written as `b`, `be`, `beg`, etc. too.

The following sections present the complete list of commands supported
by Tzero.


### begin

Usage: `begin [MINUTES] SUMMARY`

Start a new timebox for the specified number of `MINUTES`.  `MINUTES`
must be a multiple of 5 between 15 and 60, inclusive.  If `MINUTES` is
not specified, default to 30 minutes.

Examples:

  - `,begin Read SICP`
  - `,begin 45 Review article`
  - `,beg Read Galois Theory`
  - `,b Write blog post`


### cancel

Usage: `cancel`

Cancel your currently running timebox in the current channel.  No
record of your cancelled timebox is kept in the internally maintained
timeboxing history.

In a private message session, this command cancels your running
timebox in the private message session.


### delete

Usage: `delete`

Delete your last completed timebox in current channel.  This removes
the record of your last completed timebox from timeboxing history.  A
deleted timebox cannot be listed with the `list` and `mine` commands
described in the next two sections.

In a private message session, this command deletes your last completed
timebox that you ran in the private message session.


### list

Usage: `list`

List completed timeboxes in current channel.  Only most recent 10
timeboxes started within the last 2 days are listed.

In a private message session, this command lists your completed
timeboxes that you ran in a private message session.


### mine

Usage: `mine`

List only your completed timeboxes in the current channel.  Only your
most recent 10 timeboxes started within the last 2 days are available.
Older timeboxes are permanently removed from the system.

In a private message session, this command lists your completed
timeboxes that you ran in a private message session.  Note that in a
private message session, the `list` and `mine` commands present the
same list of timeboxes.


### running

Usage: `running`

List all running timeboxes of the channel.

In a private message session, this command lists your running timebox
in the private message sesion only.


### summary

Usage: `summary`

Show a summary of all timeboxes completed across all channels.

The summary information presents only the total number of completed
timeboxes and total number of minutes completed in these timeboxes.
The average length of each timebox is presented too.  No other data is
exposed by this command.  The summary data includes the timeboxes
completed in private message sessions too.


### time

Usage: `time`

Show current UTC time.


### help

Usage: `help [COMMAND]`

Show usage information about the specified `COMMAND`.

The specified `COMMAND` may or may not contain the Tzero prefix
string.  The prefix-free form of the command is accepted too as
`COMMAND` by the `help` command, i.e., both `,help ,begin` and
`,help begin` are valid commands when the prefix is `,`.

Further, the command name may be truncated to any positive length,
i.e., `,help ,b`, `,help b`, `,help etc. are valid commands when the
prefix is `,`.

Examples:

  - `,help`
  - `,help ,begin`
  - `,help begin`
  - `,help ,b`
  - `,help b`


### version

Usage: `version`

Show version, copyright, and license details.


Configuration
-------------

Tzero reads its configuation from a file named `tzero.json` in the
current working directory.  See [etc/tzero.json](etc/tzero.json) for a
simple example configuration.  Here is a brief explanation of each
configuration field in this file:

- `host` (type `string`): Hostname to be used to connect to the IRC
  network.
- `port` (type `number`): TCP port number to be used to connect to the
  IRC network.
- `tls` (type `boolean`): Whether to use TLS to connect to the IRC
  network.
- `nick` (type `string`): Nickname to assume while connecting to the
  IRC network.
- `password` (type `string`): Password to use while connecting to IRC
  network.
- `channels` (type `array` of `string`): A list of IRC channels to
  connect to.
- `state` (type `str`): Path of a file where Tzero should save its
  state to.
- `prefix` (type `str`): A prefix string that begins all Tzero
  commands.
- `nimb` (type `str`): Nickname of any [NIMB][] client that is present
  in the channel.  If no NIMB client is present, set this to an empty
  string.  See section [NIMB Support](#nimb-support) below for more
  details about this.
- `block` (type `array` of `string`): A list of strings to be blocked.
  If an IRC user sends a Tzero command that contains any string
  mentioned in this list, then Tzero rejects that command.

[NIMB]: https://github.com/susam/nimb


NIMB Support
------------

[NIMB][] is a relay bridge client that can forward messages between
IRC channels and Matrix rooms.  If Tzero is connected to an IRC
channel that is bridged to a Matrix room using NIMB, then Tzero can be
configured to accept commands arriving from Matrix users via NIMB.  To
do so, the `nimb` configuration option must be configured as explained
in the previous section.

There is one thing to be careful about while enabling NIMB support
though.  The [infix](https://github.com/susam/nimb#configuration-keys)
for the Matrix room must be set to an empty string in the NIMB
configuration.  Tzero cannot support Matrix rooms bridged via NIMB
that have a non-empty infix in the NIMB configuration.


License
-------

This is free and open source software.  You can use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of it,
under the terms of the MIT License.  See [LICENSE.md][L] for details.

This software is provided "AS IS", WITHOUT WARRANTY OF ANY KIND,
express or implied.  See [LICENSE.md][L] for details.

[L]: LICENSE.md


Support
-------

To report bugs, suggest improvements, or ask questions, please create
a new issue at <http://github.com/susam/tzero/issues>.


<!--
- Update version in pyproject.toml.

- Update CHANGES.md.

- Run the following commands:

  make checks

  git add -p
  git status
  git commit
  git push -u origin main

  make dist test-upload verify-test-upload
  make dist upload verify-upload

  VER=$(grep version pyproject.toml | cut -d '"' -f2)
  echo $VER
  git tag $VER -m "Tzero $VER"
  git push origin main $VER

  git remote add cb https://codeberg.org/susam/tzero.git
  git push cb --all
  git push cb --tags
-->
