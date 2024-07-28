Tzero
=====

Tzero is an timeboxing manager for IRC channels.  This tool logs into
an IRC network as a client and functions as an IRC bot.  Users of the
channel may send bot commands like `,begin`, `,list`, `,mine`,
`,running`, etc. to manage and view their timeboxes.

Timeboxing is a time management technique that is believed to boost
productivity by limiting the time during which a task is supposed to
be completed.  A time box is a fixed period of time alloted for a task
or activity.  This tool lets users of an IRC channel start and manage
their timeboxes while they block off some time for productive work.

To see Tzero in action, join either of the two channels:

- [#bitwise:libera.chat](https://web.libera.chat/#bitwise)
- [#bitwise:matrix.org](https://app.element.io/#/room/#bitwise:matrix.org)

The first one is an IRC channel and the second one is a Matrix room.
Both channels are bridged together, so messages posted to one channel
are visible in the other.  There is an instance of Tzero running in
the IRC channel.  It is connected to the channel with the nickname
`t0`.  Send the command `,help` to the channel to see `t0` reply with
a usage help message.


Contents
--------

* [Get Started](#get-started)
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
