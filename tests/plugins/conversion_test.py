import unittest.mock as mock
from tests.plugins import PluginTestCase

@mock.patch('plugins.conversion.get_duckduckgo_data', return_value={ 'AnswerType': 'conversions', 'Answer': 'TEST' })
@mock.patch('plugins.conversion.get_currency_data', return_value={ 'NOK': 8.00, 'DKK': 6.00 })
class ConversionPluginTest(PluginTestCase):
	def create_plugin(self):
		from plugins.conversion import ConversionPlugin, Currency
		Currency.last_fetch = None
		Currency.currency_data = None
		return ConversionPlugin(self.bot, self.channel)

	def test_converts_currencies(self, currency_mock, convert_mock):
		self.assertEqual('10 eur = 80.00 nok', self.reply('10 eur into nok'))
		self.assertEqual('10 eur = 60.00 dkk', self.reply('10 eur into dkk'))
		self.assertEqual('10 nok = 1.25 eur', self.reply('10 nok into eur'))
		self.assertEqual('10 dkk = 1.67 eur', self.reply('10 dkk into eur'))
		self.assertEqual('10 nok = 7.50 dkk', self.reply('10 nok into dkk'))
		self.assertEqual('10 dkk = 13.33 nok', self.reply('10 dkk into nok'))
		self.assertEqual('10 dkk = 13.33 nok', self.reply('what is 10 dkk into nok?'))
		self.assertEqual('TEST', self.reply('10 cny into eur'))
		self.assertEqual('TEST', self.reply('10 eur into cny'))
		self.assertEqual('TEST', self.reply('10 usd into cny'))

	def test_converts_units(self, currency_mock, convert_mock):
		self.assertEqual('TEST', self.reply('100 kg into stones'))
		self.assertEqual('TEST', self.reply('100 kg to stones'))
		self.assertEqual('TEST', self.reply('100 kg in stones'))
		self.assertEqual('TEST', self.reply('100 KG in stones'))
		self.assertEqual('TEST', self.reply('asdsa 100 kg in stones asda'))
		self.assertEqual('TEST', self.reply('what is 100 kg in stones?'))
