import unittest.mock as mock
from tests.plugins import PluginTestCase


class PcdbPluginTest(PluginTestCase):
	def create_plugin(self):
		from plugins.pcdb import PcdbPlugin
		return PcdbPlugin(self.bot, self.channel)

	def mock_get(self, comments_body):
		comments = [{'body': body, 'source_url': 'http://fake'} for body in comments_body]
		data = {'comments': comments}
		resp = mock.Mock()
		resp.json = mock.Mock(return_value=data)
		return mock.patch('requests.get', return_value=resp)

	def test_gives_random_with_no_args(self):
		with self.mock_get(['foobar']) as mock_get:
			ret = self.cmd('pcdb')
			mock_get.assert_called_once_with(
				'https://www.porncomment.com',
				headers={'accept': 'application/json'},
			)
			self.assertEqual(ret, 'foobar')

	def test_searches_when_given_args(self):
		with self.mock_get(['foobar']) as mock_get:
			ret = self.cmd('pcdb foo bar')
			mock_get.assert_called_once_with(
				'https://www.porncomment.com',
				{'search': 'foo bar'},
				headers={'accept': 'application/json'},
			)
			self.assertEqual(ret, 'foobar')

	def test_keeps_previous_result_in_memory(self):
		with self.mock_get(['foobar']):
			self.cmd('pcdb foo bar')
		ret = self.cmd('pcdbprev')
		self.assertEqual(ret, 'foobar - http://fake')
