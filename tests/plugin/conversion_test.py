import unittest.mock as mock
from tests.plugin import PluginTestCase

class ConversionPluginTest(PluginTestCase):
	def create_plugin(self):
		from plugins.conversion import ConversionPlugin
		return ConversionPlugin(self.bot, self.channel)

	@mock.patch('plugins.conversion.get_currency_data', return_value={})
	@mock.patch('plugins.conversion.get_conversion_result', return_value='TEST')
	def test_converts(self, currency_mock, convert_mock):
		self.assertEqual('TEST', self.reply('100 kg into stones'))
		self.assertEqual('TEST', self.reply('100 kg to stones'))
		self.assertEqual('TEST', self.reply('100 kg in stones'))
		self.assertEqual('TEST', self.reply('100 KG in stones'))
		self.assertEqual('TEST', self.reply('asdsa 100 kg in stones asda'))

	@mock.patch('plugins.conversion.get_currency_data',
		return_value={ 'NOK': 8.00, 'DKK': 6.00 })
	@mock.patch('plugins.conversion.get_conversion_result', return_value='TEST')
	def test_converts(self, currency_mock, convert_mock):
		self.assertEqual('10 eur = 80.00 nok', self.reply('10 eur into nok'))
		self.assertEqual('10 eur = 60.00 dkk', self.reply('10 eur into dkk'))
		self.assertEqual('10 nok = 1.25 eur', self.reply('10 nok into eur'))
		self.assertEqual('10 dkk = 1.67 eur', self.reply('10 dkk into eur'))
		self.assertEqual('10 nok = 7.50 dkk', self.reply('10 nok into dkk'))
		self.assertEqual('10 dkk = 13.33 nok', self.reply('10 dkk into nok'))
		self.assertEqual('TEST', self.reply('10 cny into eur'))
		self.assertEqual('TEST', self.reply('10 eur into cny'))
		self.assertEqual('TEST', self.reply('10 usd into cny'))
