import os.path
import unittest.mock as mock

from tests.plugin import PluginTestCase
import plugins.weather


f = 'plugins.weather.make_http_request'


def get_json(state):
	path = os.path.join(
		os.path.dirname(os.path.dirname(__file__)),
		'files', 'openweathermap_'+state+'.json'
	)
	with open(path, 'r') as f:
		return f.read()


class WeatherPluginTest(PluginTestCase):
	def create_plugin(self):
		return plugins.weather.WeatherPlugin(self.bot, self.channel)

	@mock.patch(f, return_value=get_json('edinburgh'))
	def test_cmd_simple(self, mock):
		ret = self.cmd('weather edinburgh')
		self.assertEqual('Weather in Edinburgh, GB: Rain - the temperature is 17.64°C', ret)

	@mock.patch(f, return_value=get_json('tel_aviv'))
	def test_cmd_multiword_city(self, mock):
		ret = self.cmd('weather tel aviv')
		self.assertEqual('Weather in Tel Aviv District, IL: Clouds - the temperature is 33.11°C', ret)

	@mock.patch(f, return_value=get_json('404'))
	def test_not_found(self, mock):
		ret = self.cmd('weather asljkhajkhf')
		self.assertEqual('Error: City not found', ret)

	@mock.patch(f, return_value=get_json('404'))
	def test_query_params_cannot_be_injected(self, mock):
		ret = self.cmd('weather foo&format=xml')
		mock.assert_called_with('http://api.openweathermap.org/data/2.5/weather?q=foo%26format%3Dxml&units=metric')
