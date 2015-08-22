import logging
log = logging.getLogger(__name__)

import urllib
import json
import ircbot.plugin
import socket


def get_wunderground_data(url):
	return urllib.request.urlopen(url, timeout=2).read().decode('utf-8')


class WeatherPlugin(ircbot.plugin.Plugin):
	@ircbot.plugin.command('weather')
	def weather(self, cmd):
		api_key = self.bot.config.get('wunderground_api_key')
		if not api_key:
			log.warning('Wunderground API key not set on config.yml!')
			return

		if len(cmd.args) < 2:
			return 'Usage: !weather city state/country'

		city = '_'.join(cmd.args[:-1])
		state_or_country = cmd.args[-1]
		url = 'http://api.wunderground.com/api/{}/geolookup/conditions/q/{}/{}.json'.format(
			api_key, city, state_or_country)

		try:
			response = get_wunderground_data(url)
		except (urllib.error.URLError, socket.timeout):
			return 'An HTTP error occured, try again later!'

		data = json.loads(response)

		if 'error' in data['response']:
			return 'Error: {}'.format(data['response']['error']['description'])

		location = data['location']['city']
		weather = data['current_observation']['weather'].lower()
		temperature = data['current_observation']['temp_c']

		return 'Weather in {}: {} - the temperature is {}°C'.format(
			location, weather, temperature)
