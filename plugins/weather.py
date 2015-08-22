import logging
log = logging.getLogger(__name__)

import urllib
import json
import ircbot.plugin
import socket


class WeatherPlugin(ircbot.plugin.Plugin):
	@ircbot.plugin.command('weather')
	def weather(self, cmd):
		api_key = self.bot.config.get('wunderground_api_key')
		if not api_key:
			log.warning('Wunderground API key not set on config.yml!')
			return

		url = 'http://api.wunderground.com/api/{}/geolookup/conditions/q/{}/{}.json'
			.format(api_key, cmd.args[1], cmd.args[0])

		if len(cmd.args) < 2:
			return 'Usage: !weather city state/country'
		try:
			response = urllib.request.urlopen(url, timeout=2).read()
		except (urllib.error.URLError, socket.timeout) as e:
			return 'An HTTP error occured, try again later!'

		data = json.loads(response.decode('utf-8'))

		try:
			city = data['location']['city']
			state = data['location']['state']
			weather = data['current_observation']['weather']
			temperature_string = data['current_observation']['temperature_string']
		except KeyError as e:
			return 'Invalid data returned!'

		return 'Weather in {}: {}, the temperature is {} '.format(
			city, weather.lower(), temperature_string)
