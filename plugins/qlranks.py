import logging
log = logging.getLogger(__name__)

import json
import urllib.error

import botologist.http
import botologist.plugin


def _get_qlr_data(nick):
	url = 'http://www.qlranks.com/api.aspx'
	response = botologist.http.get(url, query_params={'nick': nick}, timeout=4)
	data = response.read().decode()
	response.close()
	return json.loads(data)['players'][0]


def _get_qlr_elo(nick, modes=None):
	"""Get someone's QLRanks ELO.

	nick should be a valid Quake Live nickname. modes should be an iterable
	(list, tuple) of game-modes to display ELO for (duel, ctf, tdm...)
	"""
	if modes is None:
		modes = ('duel',)

	try:
		data = _get_qlr_data(nick)
	except urllib.error.URLError:
		log.warning('QLRanks request caused an exception', exc_info=True)
		return 'HTTP error, try again!'

	# qlranks returns rank 0 indicating a player has no rating - if all modes
	# have rank 0, it is safe to assume the player does not exist
	unranked = [mode['rank'] == 0 for mode in data.values() if isinstance(mode, dict)]
	if all(unranked):
		return 'Player not found or no games played: ' + data.get('nick', 'unknown')

	retval = data['nick']

	# convert to set to prevent duplicates
	for mode in set(modes):
		if mode not in data:
			return 'Unknown mode: ' + mode

		if data[mode]['rank'] == 0:
			retval += ' - {mode}: unranked'.format(mode=mode)
		else:
			retval += ' - {mode}: {elo} (rank {rank:,})'.format(
				mode=mode, elo=data[mode]['elo'], rank=data[mode]['rank'])

	return retval


class QlranksPlugin(botologist.plugin.Plugin):
	"""QLRanks plugin."""
	@botologist.plugin.command('elo', threaded=True)
	def get_elo(self, msg):
		if len(msg.args) < 1:
			return

		if len(msg.args) > 1:
			if ',' in msg.args[1]:
				modes = msg.args[1].split(',')
			else:
				modes = msg.args[1:]
			return _get_qlr_elo(msg.args[0], modes)
		else:
			return _get_qlr_elo(msg.args[0])
