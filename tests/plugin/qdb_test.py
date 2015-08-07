import unittest.mock as mock
from tests.plugin import PluginTestCase

f = 'ircbot.plugin.redditeu_qdb._get_qdb_data'

class RedditeuQdbPluginTest(PluginTestCase):
	def create_plugin(self):
		from ircbot.plugin.redditeu_qdb import RedditeuQdbPlugin
		return RedditeuQdbPlugin(self.bot, self.channel)

	def test_search_quote_no_results(self):
		data = {'quotes': []}
		with mock.patch(f, return_value=data) as mf:
			ret = self.cmd('qdb foo')
			mf.assert_called_with('http://qdb.lutro.me/random?s=foo')
			self.assertEqual('No quotes found!', ret)

		data = {'quotes': [{'id': 1, 'body': 'bar'}]}
		with mock.patch(f, return_value=data) as mf:
			ret = self.cmd('qdb foo')
			mf.assert_called_with('http://qdb.lutro.me/random?s=foo')
			self.assertEqual('http://qdb.lutro.me/1 - bar', ret)

		data = {'quote': {'id': 1, 'body': 'bar'}}
		with mock.patch(f, return_value=data) as mf:
			ret = self.cmd('qdb #1')
			mf.assert_called_with('http://qdb.lutro.me/1')
			self.assertEqual('http://qdb.lutro.me/1 - bar', ret)
