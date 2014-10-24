Plugin-based single-server IRC bot written in Python 3.

## Installation

Instructions for *nix systems only. If you use Windows, you're on your own.

Make sure you have python 3 and pip installed. If either of the following commands return nothing, you don't have that thing installed and should google how install it.

  $ which python3
  /usr/bin/python3
  $ which pip
  /usr/local/bin/pip

Create a virtualenv (you only have to do this once):

  $ virtualenv -p python3 virtualenv

Activate the virtualenv:

  $ source ./venv/bin/activate

Install requirements (you only have to do this once):

  $ pip install -r ./requirements.txt

Run the bot:

  $ ./run.py

### Streams plugin

Admins have access to `!addstream <stream_url>` and `!delstream <stream_url>`.

Users have access to `!sub <stream>` and `!unsub <stream>`, which toggles notification via highlighting when that stream goes online. Note that notifications are stored in a dictionary of IRC hostmask => streams, so if your user changes hostmask, your subscriptions will be reset.

`!sub` with no argument can be used to list your subscriptions. `!streams` can be used to list currently online streams.

### QLRanks plugin

`!elo <nick> [modes]` can be used to fetch a player's ELO from QLranks.com. `[modes]` can be omitted, or be a comma-separated list of game modes to fetch ELO for. For example:

  !elo raziel2p
  !elo raziel2p tdm,ca
