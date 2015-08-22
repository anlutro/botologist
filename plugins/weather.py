import urllib
import json
import ircbot.plugin

class WeatherPlugin(ircbot.plugin.Plugin):
	@ircbot.plugin.command('weather')
	def weather(self, cmd):
		if len(cmd.args) < 2:
			return 'Usage: !weather city state/country'
		try:
			url = 'http://api.wunderground.com/api/ba6f8fecb3824c22/geolookup/conditions/q/' + cmd.args[1] + '/' + cmd.args[0] + '.json'
			response = urllib.request.urlopen(url, timeout=2).read()
			json_string = json.loads(response.decode('utf-8'))
		except (urllib.error.URLError, urllib.error.HTTPError) as e:
			return 'An error occured, try again later!'
		try:
			city = json_string['location']['city']
			state = json_string['location']['state']
			weather = json_string['current_observation']['weather']
			temperature_string = json_string['current_observation']['temperature_string']
		except KeyError as e:
			return 'Usage: !weather city state/country'
		return 'Weather in ' + city + ': ' + weather.lower() + ', the temperature is ' + temperature_string
