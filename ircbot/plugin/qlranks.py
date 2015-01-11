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

	# qlranks returns rank 0 indicating a player has no rating - if all modes
	# have rank 0, it is safe to assume the player does not exist
	unranked = [mode['rank'] == 0 for mode in data.values() if isinstance(mode, dict)]
	if all(unranked):
		return 'Player not found or no games played: ' + data['nick']

	retval = data['nick']

	# convert to set to prevent duplicates
	for mode in set(modes):
		if mode not in data:
			return 'Unknown mode: ' + mode

		if data[mode]['rank'] == 0:
			retval += ' - {mode}: unranked'
		else:
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
