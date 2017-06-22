import logging
log = logging.getLogger(__name__)

import dateutil.parser
import requests

import botologist.plugin



def get_next_episode_info(show):
	query = {'q': '+'.join(show.split()), 'embed': 'nextepisode'}
	try:
		data = requests.get('http://api.tvmaze.com/singlesearch/shows', query).json()
		log.debug(data)
	except (requests.exceptions.RequestException, ValueError):
		log.warning('TVMaze request caused an exception', exc_info=True)
		return None

	info = data['name']
	if data.get('_embedded', {}).get('nextepisode'):
		dt = dateutil.parser.parse(data['_embedded']['nextepisode']['airstamp'])
		info += ' - next episode: %s' % dt.strftime('%Y-%m-%d %H:%I %Z')
	else:
		info += ' - no next episode :('
	return info


class TvseriesPlugin(botologist.plugin.Plugin):
	@botologist.plugin.command('nextepisode')
	def nextepisode(self, msg):
		return get_next_episode_info(' '.join(msg.args))
