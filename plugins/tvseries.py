import logging
log = logging.getLogger(__name__)

import datetime
import dateutil.parser
import requests

import botologist.plugin



def get_next_episode_info(show):
	query = {'q': show, 'embed': 'nextepisode'}
	try:
		response = requests.get('http://api.tvmaze.com/singlesearch/shows', query)
		response.raise_for_status()
	except requests.exceptions.RequestException:
		log.warning('TVMaze request caused an exception', exc_info=True)
		return None

	try:
		data = response.json()
	except ValueError:
		log.warning('TVMaze returned invalid JSON: %r', response.text, exc_info=True)
		return None

	info = data['name']
	nextepisode = data.get('_embedded', {}).get('nextepisode')
	if nextepisode:
		log.debug('next episode data: %r', nextepisode)
		dt = dateutil.parser.parse(nextepisode['airstamp'])
		info += ' - season %d, episode %d airs at %s' % (
			nextepisode['season'],
			nextepisode['number'],
			dt.strftime('%Y-%m-%d %H:%M %z'),
		)
		now = datetime.datetime.now(dt.tzinfo)
		if dt > now:
			time_left = dt - now
			if time_left.days > 0:
				time_left_str = '%dd %dh' % (
					time_left.days,
					round(time_left.seconds / 3600),
				)
			elif time_left.seconds > 3600:
				time_left_str = '%dh %dm' % (
					round(time_left.seconds / 3600),
					round((time_left.seconds % 3600) / 60),
				)
			else:
				time_left_str = '%dm' % round(time_left.seconds / 60)
			log.debug('time left: %r (%s)', time_left, time_left_str)
			info += ' (in %s)' % time_left_str
	else:
		info += ' - no next episode :('
	return info


class TvseriesPlugin(botologist.plugin.Plugin):
	@botologist.plugin.command('nextepisode')
	def nextepisode(self, msg):
		return get_next_episode_info(' '.join(msg.args))
