import unittest.mock as mock
from tests.plugin import PluginTestCase

class ConversionPluginTest(PluginTestCase):
	def create_plugin(self):
		from plugins.convert import ConversionPlugin
		return ConversionPlugin(self.bot, self.channel)

	@mock.patch('plugins.convert.get_conversion_result',
		return_value='test conversion result')
	def test_converts(self, mock):
		expected = 'test conversion result'
		self.assertEqual('test conversion result', self.reply('100 nok into eur'))
		self.assertEqual('test conversion result', self.reply('100 nok to eur'))
		self.assertEqual('test conversion result', self.reply('100 nok in eur'))
		self.assertEqual('test conversion result', self.reply('100 NOK in EUR'))
		self.assertEqual('test conversion result', self.reply('asdsa 100 nok in eur asda'))
