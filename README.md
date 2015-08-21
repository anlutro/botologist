# IRC bot

[![Build Status](https://travis-ci.org/anlutro/ircbot.png?branch=master)](https://travis-ci.org/anlutro/ircbot)

Plugin-based single-server IRC bot written in Python 3.

## Installation

Instructions for *nix systems only. If you use Windows, you're on your own.

Make sure you have python 3, pip and virtualenv installed. If either of the following commands return nothing, you don't have that thing installed and should google how install it.

	$ which python3
	/usr/bin/python3
	$ which pip
	/usr/local/bin/pip
	$ which virtualenv
	/usr/local/bin/virtualenv

Create a virtualenv (you only have to do this once):

	$ virtualenv -p python3 .virtualenv

Activate the virtualenv:

	$ source ./.virtualenv/bin/activate

Install requirements (you only have to do this once):

	$ pip install -r requirements.txt

Copy `config.example.yml` to `config.yml` and edit it to your likings, then run the bot:

	$ ./run

### Streams plugin

Admins have access to `!addstream <stream_url>` and `!delstream <stream_url>`.

Users have access to `!sub <stream>` and `!unsub <stream>`, which toggles notification via highlighting when that stream goes online. Note that notifications are stored in a dictionary of IRC hostmask => streams, so if your user changes hostmask, your subscriptions will be reset.

`!sub` with no argument can be used to list your subscriptions. `!streams` can be used to list currently online streams.

### QLRanks plugin

`!elo <nick> [modes]` can be used to fetch a player's ELO from QLranks.com. `[modes]` can be omitted, or be a comma-separated list of game modes to fetch ELO for. For example:

	!elo raziel2p
	!elo raziel2p tdm,ca

## Development

To run tests, `./run tests`. Note that not all parts of the code is under test, so do try to actually run the bot with your new functionaliy before you decide it's a success.

To run code linting, first make sure pylint is installed in your virtualenv with `pip install pylint`. To run linting, run `./run lint`. Optionally, you can lint only a single module, for example `./run lint plugins.default` Note that linting will show some false positives, but important ones should show up in red.

### Pull requests

How to effectively make a pull request:

1. Fork the repository on Github.
2. Add your fork as a remote (or clone the fork and add the original as a remote). `git remote add fork git@github.com:my_user/ircbot`
3. Create a branch for the change you want to make. `git checkout -b my_branch`
4. Commit and push the changes you want to make to your fork. `git push fork`
5. Visit the forked repository on Github's website and you should see a green button for making a pull request.

When you've made one pull request, making the next one is simpler:

1. Run `git checkout master` and `git pull --ff-only origin master` (assuming "origin" is the original repository, not your fork). This will ensure that you aren't making changes based on an old version of the code.
2. Repeat steps 3-5 as described above.

### Architecture

`ircbot/__main__.py` is the main entry point for running the bot. It reads the config file, sets up logging, instantiates the Bot object and starts the bot's IRC connection.

The `ircbot/irc.py` module contains IRC abstractions with classes such as Server, Connection, Client and so on.

The `ircbot/bot.py` module contains 1 main class: `ircbot.bot.Bot` - which extends `ircbot.irc.Client` and adds bot-like features such as keeping track of what users are present in channels, as well as the ability to add commands, replies and timed repeating tasks via plugins.

The core plugin classes and functionality is defined in `ircbot/plugin.py`. Various plugins extend the `ircbot.plugin.Plugin` class to provide a plugin. Plugins can be associated with channels via the `config.yml` file.

Plugins define functionality such as commands, replies, join handlers and tickers via method decorators. The best way to see how to do this is to look at an existing plugin.
