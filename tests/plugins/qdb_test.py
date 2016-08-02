import unittest.mock as mock
from tests.plugins import PluginTestCase

f = 'plugins.qdb._get_qdb_data'

class QdbPluginTest(PluginTestCase):
	def create_plugin(self):
		from plugins.qdb import QdbPlugin
		return QdbPlugin(self.bot, self.channel)

	def test_search_quote_no_results(self):
		data = {'quotes': []}
		with mock.patch(f, return_value=data) as mf:
			ret = self.cmd('qdb foo')
			mf.assert_called_with('https://qdb.lutro.me/random', query_params={'s':'foo'})
			self.assertEqual('No quotes found!', ret)

		data = {'quotes': [{'id': 1, 'body': 'bar'}]}
		with mock.patch(f, return_value=data) as mf:
			ret = self.cmd('qdb foo')
			mf.assert_called_with('https://qdb.lutro.me/random', query_params={'s':'foo'})
			self.assertEqual('https://qdb.lutro.me/1 - bar', ret)

		data = {'quote': {'id': 1, 'body': 'bar'}}
		with mock.patch(f, return_value=data) as mf:
			ret = self.cmd('qdb #1')
			mf.assert_called_with('https://qdb.lutro.me/1', query_params=None)
			self.assertEqual('https://qdb.lutro.me/1 - bar', ret)

	def test_search_no_args(self):
		with mock.patch(f) as mf:
			ret = self.cmd('qdb')
			mf.assert_called_with('https://qdb.lutro.me/random', query_params=None)
