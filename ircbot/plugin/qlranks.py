import ircbot.plugin
import json
import urllib.request
import urllib.error
import socket


def _get_qlr_elo(nick, modes = None):
	"""Get someone's QLRanks ELO.

	nick should be a valid Quake Live nickname. modes should be an iterable
	(list, tuple) of game-modes to display ELO for (duel, ctf, tdm...)
	"""
	if modes is None:
		modes = ('duel',)

	try:
		response = urllib.request.urlopen('http://www.qlranks.com/api.aspx?nick='+nick, timeout=4)
		content = response.read().decode()
	except (urllib.error.URLError, socket.timeout):
		return 'HTTP error, try again!'

	data = json.loads(content)['players'][0]

	# qlranks returns a player with Elo 1200 for all modes if the player either
	# has no games played or does not exist
	elos = [mode['elo'] == 1200 for mode in data]
	if all(elos):
		return 'Player not found or no games played: ' + data['nick']

	retval = data['nick']

	# convert to set to prevent duplicates
	for mode in set(modes):
		if mode not in data:
			return 'Unknown mode: ' + mode
		retval += ' - {mode}: {elo} (rank {rank:,})'.format(
			mode=mode, elo=data[mode]['elo'], rank=data[mode]['rank'])

	return retval


class QlranksPlugin(ircbot.plugin.Plugin):
	"""QLRanks plugin."""
	@ircbot.plugin.command('elo')
	def get_elo(self, msg):
		if len(msg.args) < 1:
			return

		if len(msg.args) > 1:
			return _get_qlr_elo(msg.args[0], msg.args[1:])
		else:
			return _get_qlr_elo(msg.args[0])
