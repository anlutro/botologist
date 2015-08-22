import logging
log = logging.getLogger(__name__)

import urllib
import json
import ircbot.plugin
import socket


def make_http_request(url):
	return urllib.request.urlopen(url, timeout=2).read().decode('utf-8')


class WeatherPlugin(ircbot.plugin.Plugin):
	@ircbot.plugin.command('weather')
	def weather(self, cmd):
		if len(cmd.args) < 1:
			return 'Usage: !weather city'

		city = '-'.join(cmd.args)
		url = 'http://api.openweathermap.org/data/2.5/weather?q={}&units=metric'.format(
			city)

		try:
			response = make_http_request(url)
		except (urllib.error.URLError, socket.timeout):
			return 'An HTTP error occured, try again later!'

		data = json.loads(response)
		status = int(data['cod'])

		if status == 404:
			return 'Error: City not found'
		elif status != 200:
			return data['message']

		location = '{}, {}'.format(data['name'], data['sys']['country'])
		weather = data['weather'][0]['main']
		temperature = data['main']['temp']

		return 'Weather in {}: {} - the temperature is {}°C'.format(
			location, weather, temperature)
