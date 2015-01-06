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

	$ virtualenv -p python3 virtualenv

Activate the virtualenv:

	$ source ./venv/bin/activate

Install requirements (you only have to do this once):

	$ pip install -r ./requirements.txt

Copy `config.example.yml` to `config.yml` and edit it to your likings, then run the bot:

	$ ./run.py

### Streams plugin

Admins have access to `!addstream <stream_url>` and `!delstream <stream_url>`.

Users have access to `!sub <stream>` and `!unsub <stream>`, which toggles notification via highlighting when that stream goes online. Note that notifications are stored in a dictionary of IRC hostmask => streams, so if your user changes hostmask, your subscriptions will be reset.

`!sub` with no argument can be used to list your subscriptions. `!streams` can be used to list currently online streams.

### QLRanks plugin

`!elo <nick> [modes]` can be used to fetch a player's ELO from QLranks.com. `[modes]` can be omitted, or be a comma-separated list of game modes to fetch ELO for. For example:

	!elo raziel2p
	!elo raziel2p tdm,ca

## Development

Brief explanation of the program architecture.

The `ircbot/irc.py` module contains IRC abstractions with classes such as Server, Connection, Client and so on.

The `ircbot/bot.py` module contains 1 main class: `ircbot.bot.Bot` - which extends `ircbot.irc.Client` and adds bot-like features such as keeping track of what users are present in channels, as well as the ability to add commands, replies and timed repeating tasks via plugins.

The core plugin classes and functionality is defined in `ircbot/plugin/__init__.py`. Various plugins extend the `ircbot.plugin.Plugin` class to provide a plugin. Plugins can be associated with channels via the `config.yml` file.

Plugins define functionality such as commands, replies, join handlers and tickers via method decorators. The best way to see how to do this is to look at an existing plugin.
