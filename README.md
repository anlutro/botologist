# Botologist

[![Build Status](https://travis-ci.org/anlutro/botologist.png?branch=master)](https://travis-ci.org/anlutro/botologist)

Plugin-based single-server IRC bot written in Python 3. This is a private project, meaning no promises of backwards compatibility and no guarantees of safety/security running the program yourself.

## Installation

Instructions for linux-like systems only. If you use Windows, you're on your own.

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

## Plugins

Plugins can be added globally or to individual channels:

```yaml
global_plugins:
  - default
  - twitter

channels:
  mychannel:
    plugins:
      - koth
```

The name of the plugin corresponds to the name of the python file in the `plugins` directory.

As long as the plugin class matches the module (file) name, you don't need to do anything more than that. For example, `foo.py` should contain the class `FooPlugin`. If the plugin class name differs from the module, you need to register an alias in the config. This can also be used to import plugins that are part of an external module.

```yaml
plugins:
  foo: plugins.foo.RandomlyNamedPlugin
  bar: externalmodule.ExternalPlugin

global_plugins:
  - foo
  - bar
```

### Default plugin

Just a plugin with simple functionality that doesn't deserve its own plugin.

### Conversion plugin

Get the results of conversion queries like "100 kg to stones" or "100 eur in usd".

### KOTH (king of the hill) plugin

Run a king of the hill tournament (winner stays on). Admins have access to the following commands:

- **!koth start** starts a new KOTH.
- **!koth next** lets you know who the next player up is.
- **!koth close** prevents further signups.
- **!koth end** ends the KOTH.

Regular users have access to these commands:

- **!koth** lists the current participant queue.
- **!koth add** adds you to the queue.
- **!koth remove** removes you from the queue.

### Streams plugin

Admins have access to `!addstream <stream_url>` and `!delstream <stream_url>`.

Users have access to `!sub <stream>` and `!unsub <stream>`, which toggles notification via highlighting when that stream goes online. Note that notifications are stored in a dictionary of IRC hostmask => streams, so if your user changes hostmask, your subscriptions will be reset.

`!sub` with no argument can be used to list your subscriptions. `!streams` can be used to list currently online streams.

### QLRanks plugin

`!elo <nick> [modes]` can be used to fetch a player's ELO from QLranks.com. `[modes]` can be omitted, or be a comma-separated list of game modes to fetch ELO for. For example:

	!elo raziel2p
	!elo raziel2p tdm,ca

### Twitter plugin

When a twitter link is pasted into IRC, fetches and announces the tweet body. Requires the `twitter_api` config values to be present in `config.yml`.

### URL plugin

When a shortened link (is.gd, t.co, goo.gl etc) is posted, the real URL will be announced.

## Development

To run tests, `./run tests`. Note that not all parts of the code is under test, so do try to actually run the bot with your new functionaliy before you decide it's a success.

To run code linting, first make sure pylint is installed in your virtualenv with `pip install pylint`. To run linting, run `./run lint`. Optionally, you can lint only a single module, for example `./run lint plugins.default` Note that linting will show some false positives, but important ones should show up in red.

### Pull requests

How to effectively make a pull request:

1. Fork the repository on Github.
2. Add your fork as a remote (or clone the fork and add the original as a remote). `git remote add fork git@github.com:my_user/botologist`
3. Create a branch for the change you want to make. `git checkout -b my_branch`
4. Commit and push the changes you want to make to your fork. `git push fork`
5. Visit the forked repository on Github's website and you should see a green button for making a pull request.

When you've made one pull request, making the next one is simpler:

1. Run `git checkout master` and `git pull --ff-only origin master` (assuming "origin" is the original repository, not your fork). This will ensure that you aren't making changes based on an old version of the code.
2. Repeat steps 3-5 as described above.

### Architecture

`botologist/__main__.py` is the main entry point for running the bot. It reads the config file, sets up logging, instantiates the Bot object and starts the bot's IRC connection.

The `botologist/irc.py` module contains IRC abstractions with classes such as Server, Connection, Client and so on.

The `botologist/bot.py` module contains 1 main class: `botologist.bot.Bot` - which extends `botologist.irc.Client` and adds bot-like features such as keeping track of what users are present in channels, as well as the ability to add commands, replies and timed repeating tasks via plugins.

The core plugin classes and functionality is defined in `botologist/plugin.py`. Various plugins extend the `botologist.plugin.Plugin` class to provide a plugin. Plugins can be associated with channels via the `config.yml` file.

Plugins define functionality such as commands, replies, join handlers and tickers via method decorators. The best way to see how to do this is to look at an existing plugin.

## Licence

The contents of this repository are released under the [MIT license](http://opensource.org/licenses/MIT). See the [LICENSE](LICENSE) file included for more information.
