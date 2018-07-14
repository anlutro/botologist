from freezegun import freeze_time
import unittest.mock as mock

from tests.plugins import PluginTestCase
from plugins.owleague import OwleaguePlugin

f = 'plugins.owleague.get_owl_data'


@freeze_time('2017-12-08 10:00:00')
class OwleaguePluginTest(PluginTestCase):
	def create_plugin(self):
		return OwleaguePlugin(self.bot, self.channel)

	def test_returns_current_and_next_match(self):
		data = {
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
		with mock.patch(f, return_value=data):
			ret = self.cmd('owl')
		self.assertEqual(ret, 'Live now: team1 vs team2 -- Next match: team3 vs team4 at 2017-12-10 15:00 +0000 (in 2d 5h) -- https://overwatchleague.com')

	def test_returns_next_match(self):
		data = {
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
		with mock.patch(f, return_value=data):
			ret = self.cmd('owl')
		self.assertEqual(ret, 'Next match: team1 vs team2 at 2017-12-10 15:00 +0000 (in 2d 5h) -- https://overwatchleague.com')

	def test_returns_nothing_when_no_matches(self):
		data = {
			'liveMatch': {},
			'nextMatch': {}
		}
		with mock.patch(f, return_value=data):
			ret = self.cmd('owl')
		self.assertEqual(ret, 'No matches live or scheduled -- https://overwatchleague.com')

	def test_ticker_returns_when_match_goes_live(self):
		data = {
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

		with mock.patch(f, return_value=data):
			ret1 = self.plugin.ticker()

		data['liveMatch']['liveStatus'] = 'LIVE'

		with mock.patch(f, return_value=data):
			ret2 = self.plugin.ticker()

		self.assertFalse(ret1)
		self.assertTrue(ret2)

	def test_ticker_does_not_repeat_itself(self):
		data = {
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
		with mock.patch(f, return_value=data):
			ret1 = self.plugin.ticker()
			ret2 = self.plugin.ticker()
		self.assertTrue(ret1)
		self.assertFalse(ret2)

	def test_ticker_does_not_trigger_on_next_match_time_change(self):
		data = {
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

		with mock.patch(f, return_value=data):
			ret1 = self.plugin.ticker()

		data['nextMatch']['startDate'] = '2017-12-10T16:00:00Z+00:00'

		with mock.patch(f, return_value=data):
			ret2 = self.plugin.ticker()

		self.assertTrue(ret1)
		self.assertFalse(ret2)

	def test_ticker_updates_when_match_changes(self):
		data = {
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

		with mock.patch(f, return_value=data):
			ret1 = self.plugin.ticker()

		data['liveMatch']['competitors'][0]['name'] = 'team3'
		data['liveMatch']['competitors'][1]['name'] = 'team4'
		data['nextMatch']['competitors'][0]['name'] = 'team5'
		data['nextMatch']['competitors'][1]['name'] = 'team6'

		with mock.patch(f, return_value=data):
			ret2 = self.plugin.ticker()

		self.assertTrue(ret1)
		self.assertTrue(ret2)
		self.assertNotEqual(ret1, ret2)

	def test_ticker_does_not_flap(self):
		data = [{
			'liveMatch': {
				'liveStatus': 'LIVE',
				'competitors': [
					{'name': 'team%d' % (i + 1)},
					{'name': 'team%d' % (i + 2)},
				],
			},
			'nextMatch': {
				'liveStatus': 'UPCOMING',
				'startDate': '2017-12-10T%d:00:00Z+00:00' % (15 + i * 2),
				'competitors': [
					{'name': 'team%d' % (i + 3)},
					{'name': 'team%d' % (i + 4)},
				],
			}
		} for i in range(0, 3)]

		with mock.patch(f, return_value=data[0]):
			ret = self.plugin.ticker()
			self.assertIsNotNone(ret)
			self.assertIn('team1 vs team2', ret)
		with mock.patch(f, return_value=data[1]):
			self.assertIsNotNone(self.plugin.ticker())
			self.assertIn('team3 vs team4', ret)
		with mock.patch(f, return_value=data[0]):
			self.assertIsNone(self.plugin.ticker())
		with mock.patch(f, return_value=data[1]):
			self.assertIsNone(self.plugin.ticker())
		with mock.patch(f, return_value=data[0]):
			self.assertIsNone(self.plugin.ticker())
			self.assertIsNone(self.plugin.ticker())
		with mock.patch(f, return_value=data[1]):
			self.assertIsNone(self.plugin.ticker())
			self.assertIsNone(self.plugin.ticker())
		with mock.patch(f, return_value=data[2]):
			ret = self.plugin.ticker()
			self.assertIsNotNone(ret)
			self.assertIn('team3 vs team4', ret)

	def test_ticker_does_not_flap_between_live_and_not_live(self):
		live_data = {
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
		upcoming_data = {
			'liveMatch': {},
			'nextMatch': {
				'liveStatus': 'UPCOMING',
				'startDate': '2017-12-10T15:00:00Z+00:00',
				'competitors': [
					{'name': 'team1'},
					{'name': 'team2'},
				],
			}
		}

		with mock.patch(f, return_value=live_data):
			ret = self.plugin.ticker()
			self.assertIsNotNone(ret)
			self.assertIn('team1 vs team2', ret)
		with mock.patch(f, return_value=upcoming_data):
			self.assertIsNone(self.plugin.ticker())
		with mock.patch(f, return_value=live_data):
			self.assertIsNone(self.plugin.ticker())

	def test_ticker_resets_after_several_not_live_results(self):
		live_data = {
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
		upcoming_data = {
			'liveMatch': {},
			'nextMatch': {
				'liveStatus': 'UPCOMING',
				'startDate': '2017-12-10T15:00:00Z+00:00',
				'competitors': [
					{'name': 'team1'},
					{'name': 'team2'},
				],
			}
		}

		with mock.patch(f, return_value=live_data):
			ret = self.plugin.ticker()
			self.assertIsNotNone(ret)
			self.assertIn('team1 vs team2', ret)
		with mock.patch(f, return_value=upcoming_data):
			self.assertIsNone(self.plugin.ticker())
		with mock.patch(f, return_value=upcoming_data):
			self.assertIsNone(self.plugin.ticker())
		with mock.patch(f, return_value=live_data):
			self.assertIsNotNone(ret)
			self.assertIn('team1 vs team2', ret)
