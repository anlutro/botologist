import os.path
import unittest.mock as mock

from tests.plugin import PluginTestCase
import plugins.weather


f = 'plugins.weather.get_wunderground_data'


def get_json(state):
	path = os.path.join(
		os.path.dirname(os.path.dirname(__file__)),
		'files', 'wunderground_'+state+'.json'
	)
	with open(path, 'r') as f:
		return f.read()


class WeatherPluginTest(PluginTestCase):
	def create_plugin(self):
		self.bot.config.update({'wunderground_api_key': 'API_KEY'})
		return plugins.weather.WeatherPlugin(self.bot, self.channel)

	@mock.patch(f, return_value=get_json('edinburgh'))
	def test_cmd_with_valid_city(self, mock):
		ret = self.cmd('weather edinburgh uk')
		self.assertEqual('Weather in Edinburgh: scattered clouds - the temperature is 17.2°C', ret)

	@mock.patch(f, return_value=get_json('tel_aviv'))
	def test_cmd_multiword_city(self, mock):
		ret = self.cmd('weather tel aviv israel')
		self.assertEqual('Weather in Tel Aviv: clear - the temperature is 33.4°C', ret)

	@mock.patch(f, return_value=get_json('invalid'))
	def test_cmd_with_invalid_city(self, mock):
		ret = self.cmd('weather asdaf asdasd')
		self.assertEqual('Error: No cities match your search query', ret)
