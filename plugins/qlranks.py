import logging
log = logging.getLogger(__name__)

import requests
import requests.exceptions

import botologist.plugin
from botologist import http


async def _get_qlr_data(nick):
	url = 'http://www.qlranks.com/api.aspx'
	response = await http.get(url, params={'nick': nick}, timeout=4)
	data = await response.json()
	return data['players'][0]


def _get_qlr_elo(data, modes=None):
	"""Get someone's QLRanks ELO."""
	if modes is None:
		modes = ('duel',)

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
	@botologist.plugin.command('elo')
	async def get_elo(self, msg):
		'''Get a player's ELO from qlranks.'''
		if len(msg.args) < 1:
			return

		modes = None
		if len(msg.args) > 1:
			if ',' in msg.args[1]:
				modes = msg.args[1].split(',')
			else:
				modes = msg.args[1:]

		try:
			data = await _get_qlr_data(msg.args[0])
		except requests.exceptions.RequestException:
			log.warning('QLRanks request caused an exception', exc_info=True)
			return 'HTTP error, try again!'

		return _get_qlr_elo(data, modes)
