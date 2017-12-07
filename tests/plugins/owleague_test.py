import unittest.mock as mock
from tests.plugins import PluginTestCase

f = 'plugins.owleague.get_owl_data'


class OwleaguePluginTest(PluginTestCase):
	def create_plugin(self):
		from plugins.owleague import OwleaguePlugin
		return OwleaguePlugin(self.bot, self.channel)

	def test_returns_current_and_next_match(self):
		data = {
			'data': {
				'liveMatch': {
					'liveStatus': 'LIVE',
					'competitors': [
						{'name': 'team1'},
						{'name': 'team2'},
					],
				},
				'nextMatch': {
					'liveStatus': 'UPCOMING',
					'startDate': '2017-12-10T15:00:00Z+00:00',
					'competitors': [
						{'name': 'team1'},
						{'name': 'team2'},
					],
				}
			}
		}
		with mock.patch(f, return_value=data):
			ret = self.cmd('owl')
		self.assertEqual(ret, 'Live now: team1 vs team2 -- Next match: team1 vs team2 at 2017-12-10 15:00 +0000 -- https://overwatchleague.com')

	def test_returns_next_match(self):
		data = {
			'data': {
				'liveMatch': {
					'liveStatus': 'UPCOMING',
					'startDate': '2017-12-10T15:00:00Z+00:00',
					'competitors': [
						{'name': 'team1'},
						{'name': 'team2'},
					],
				},
				'nextMatch': {}
			}
		}
		with mock.patch(f, return_value=data):
			ret = self.cmd('owl')
		self.assertEqual(ret, 'Next match: team1 vs team2 at 2017-12-10 15:00 +0000 -- https://overwatchleague.com')
