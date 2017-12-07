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
						{'name': 'team3'},
						{'name': 'team4'},
					],
				}
			}
		}
		with mock.patch(f, return_value=data):
			ret = self.cmd('owl')
		self.assertEqual(ret, 'Live now: team1 vs team2 -- Next match: team3 vs team4 at 2017-12-10 15:00 +0000 -- https://overwatchleague.com')

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

	def test_ticker_returns_when_match_goes_live(self):
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
			ret1 = self.plugin.ticker()

		data['data']['liveMatch']['liveStatus'] = 'LIVE'

		with mock.patch(f, return_value=data):
			ret2 = self.plugin.ticker()

		self.assertFalse(ret1)
		self.assertTrue(ret2)

	def test_ticker_does_not_repeat_itself(self):
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
						{'name': 'team3'},
						{'name': 'team4'},
					],
				}
			}
		}
		with mock.patch(f, return_value=data):
			ret1 = self.plugin.ticker()
			ret2 = self.plugin.ticker()
		self.assertTrue(ret1)
		self.assertFalse(ret2)

	def test_ticker_does_not_trigger_on_next_match_time_change(self):
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
						{'name': 'team3'},
						{'name': 'team4'},
					],
				}
			}
		}

		with mock.patch(f, return_value=data):
			ret1 = self.plugin.ticker()

		data['data']['nextMatch']['startDate'] = '2017-12-10T16:00:00Z+00:00'

		with mock.patch(f, return_value=data):
			ret2 = self.plugin.ticker()

		self.assertTrue(ret1)
		self.assertFalse(ret2)

	def test_ticker_updates_when_match_changes(self):
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
						{'name': 'team3'},
						{'name': 'team4'},
					],
				}
			}
		}

		with mock.patch(f, return_value=data):
			ret1 = self.plugin.ticker()

		data['data']['liveMatch']['competitors'][0]['name'] = 'team3'
		data['data']['liveMatch']['competitors'][1]['name'] = 'team4'
		data['data']['nextMatch']['competitors'][0]['name'] = 'team5'
		data['data']['nextMatch']['competitors'][1]['name'] = 'team6'

		with mock.patch(f, return_value=data):
			ret2 = self.plugin.ticker()

		self.assertTrue(ret1)
		self.assertTrue(ret2)
		self.assertNotEqual(ret1, ret2)
