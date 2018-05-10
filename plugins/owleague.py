import logging

import requests

from botologist.util import parse_dt, time_until
import botologist.plugin

log = logging.getLogger(__name__)


def get_owl_data():
	resp = requests.get('https://api.overwatchleague.com/live-match')
	resp.raise_for_status()
	return resp.json().get('data', {})


def get_match_info(match_data):
	teams = match_data['competitors']
	return '%s vs %s' % (teams[0]['name'], teams[1]['name'])


def get_match_time(match_data, tz=None):
	dt = parse_dt(match_data['startDate'], tz)
	info = dt.strftime('%Y-%m-%d %H:%M %z')
	time_until_str = time_until(dt)
	if time_until_str:
		info += ' (in %s)' % time_until_str
	return info


def get_current_match_info(data):
	match = data.get('liveMatch', {})
	if not match or match.get('liveStatus') != 'LIVE':
		return
	return 'Live now: %s' % get_match_info(match)


def get_next_match_info(data, tz=None):
	match = data.get('nextMatch', {})
	if not match:
		match = data.get('liveMatch', {})
		if not match or match.get('liveStatus') != 'UPCOMING':
			return
	return 'Next match: %s at %s' % (
		get_match_info(match),
		get_match_time(match, tz=tz),
	)


class OwleaguePlugin(botologist.plugin.Plugin):
	def __init__(self, bot, channel):
		super().__init__(bot, channel)
		self.cur_state = None
		self.cur_match = None
		self.prev_match = None
		self.tz = self.bot.config.get('output_timezone', 'UTC')

	def _get_info_str(self, ticker):
		try:
			data = get_owl_data()
		except requests.exceptions.RequestException as exc:
			log.warning('exception getting OWL data', exc_info=True)
			if ticker:
				return
			return 'Problem fetching OWL data: %s' % exc

		cur_match = get_current_match_info(data)
		next_match = get_next_match_info(data, tz=self.tz)

		skip = ticker and (
			cur_match == self.cur_state or
			cur_match == self.cur_match or
			cur_match == self.prev_match or
			not cur_match
		)

		if not skip:
			log.debug('cur_state=%r; cur_match=%r; prev_match=%r; data=%r',
				self.cur_state, self.cur_match, self.prev_match, data)

		self.cur_state = cur_match
		if cur_match and cur_match != self.cur_match:
			self.prev_match = self.cur_match
			self.cur_match = cur_match

		if skip:
			return

		match_infos = [m for m in (cur_match, next_match) if m] or \
			['No matches live or scheduled']
		return ' -- '.join(match_infos + ['https://overwatchleague.com'])

	@botologist.plugin.ticker()
	def ticker(self):
		return self._get_info_str(ticker=True)

	@botologist.plugin.command('owl')
	def command(self, msg):
		return self._get_info_str(ticker=False)
