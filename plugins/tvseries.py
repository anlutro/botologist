import logging
log = logging.getLogger(__name__)

import datetime
import dateutil.parser
import requests
import pytz

import botologist.plugin



def get_next_episode_info(show, output_timezone=pytz.timezone('UTC')):
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
			dt.astimezone(tz=output_timezone).strftime('%Y-%m-%d %H:%M %z'),
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
	def __init__(self, bot, channel):
		super().__init__(bot, channel)
		self.output_tz = pytz.timezone('UTC')
		if self.bot.config.get('output_timezone'):
			self.output_tz = pytz.timezone(self.bot.config.get('output_timezone'))

	@botologist.plugin.command('nextepisode')
	def nextepisode(self, msg):
		info = get_next_episode_info(' '.join(msg.args), self.output_tz)
		return info or 'No show with that name found!'
