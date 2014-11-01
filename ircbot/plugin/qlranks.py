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
		response = urllib.request.urlopen('http://www.qlranks.com/api.aspx?nick='+nick, timeout=2)
		content = response.read().decode()
	except (urllib.error.URLError, socket.timeout):
		return 'HTTP error, try again!'

	data = json.loads(content)['players'][0]

	retval = data['nick']

	for mode in modes:
		if mode not in data:
			return 'Unknown mode: ' + mode
		retval += ' - {mode}: {elo} (rank {rank})'.format(
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
