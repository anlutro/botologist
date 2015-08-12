import unittest.mock as mock
from tests.plugin import PluginTestCase

f = 'plugins.qlranks._get_qlr_data'

class QlranksPluginTest(PluginTestCase):
	def create_plugin(self):
		from plugins.qlranks import QlranksPlugin
		return QlranksPlugin(self.bot, self.channel)

	def test_qlranks(self):
		data = {'nick': 'test'}
		with mock.patch(f, return_value=data) as mf:
			ret = self.cmd('elo test')
			self.assertEqual('Player not found or no games played: test', ret)

		data = {'nick': 'test', 'duel': {'elo': 1337, 'rank': 9999}}
		with mock.patch(f, return_value=data) as mf:
			ret = self.cmd('elo test')
			self.assertEqual('test - duel: 1337 (rank 9,999)', ret)

		data = {'nick': 'test', 'duel': {'elo': 1337, 'rank': 9999}, 'ca': {'elo': 1227, 'rank': 8888}}
		with mock.patch(f, return_value=data) as mf:
			ret = self.cmd('elo test ca')
			self.assertEqual('test - ca: 1227 (rank 8,888)', ret)

			ret = self.cmd('elo test ca duel')
			self.assertTrue(ret.index('ca: 1227 (rank 8,888)'))
			self.assertTrue(ret.index('duel: 1337 (rank 9,999)'))
			self.assertEqual(ret, self.cmd('elo test ca,duel'))
