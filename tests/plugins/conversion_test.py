import unittest.mock as mock
from tests.plugins import PluginTestCase

ddg_f = 'plugins.conversion.get_duckduckgo_data'
ecb_f = 'plugins.conversion.get_currency_data'

class ConversionPluginTest(PluginTestCase):
	def create_plugin(self):
		from plugins.conversion import ConversionPlugin, Currency
		Currency.last_fetch = None
		Currency.currency_data = None
		return ConversionPlugin(self.bot, self.channel)

	@mock.patch(ddg_f, return_value={ 'AnswerType': 'conversions', 'Answer': 'TEST' })
	@mock.patch(ecb_f, return_value={ 'NOK': 8.00, 'DKK': 6.00 })
	def test_converts_currencies(self, currency_mock, convert_mock):
		self.assertEqual('10 eur = 80 nok', self.reply('10 eur into nok'))
		self.assertEqual('10 eur = 60 dkk', self.reply('10 eur into dkk'))
		self.assertEqual('10 nok = 1.25 eur', self.reply('10 nok into eur'))
		self.assertEqual('10 dkk = 1.67 eur', self.reply('10 dkk into eur'))
		self.assertEqual('10 nok = 7.50 dkk', self.reply('10 nok into dkk'))
		self.assertEqual('10 dkk = 13.33 nok', self.reply('10 dkk into nok'))
		self.assertEqual('10 dkk = 13.33 nok', self.reply('what is 10 dkk into nok?'))
		self.assertEqual('10,000 eur = 80,000 nok', self.reply('10k eur into nok'))
		self.assertEqual('1,100 eur = 8,800 nok', self.reply('1.1k eur into nok'))
		self.assertEqual('TEST', self.reply('10 cny into eur'))
		self.assertEqual('TEST', self.reply('10 eur into cny'))
		self.assertEqual('TEST', self.reply('10 usd into cny'))

	def check_convert_reply(self, message, expected_qs, response='DEFAULT'):
		if response == 'DEFAULT':
			response = message + ' reply'
		return_value={'AnswerType': 'conversions', 'Answer': response}
		with mock.patch(ddg_f, return_value=return_value) as mf:
			self.assertEqual(response, self.reply(message))
		expected_args = ['http://api.duckduckgo.com/?q='+expected_qs+'&format=json&no_html=1']
		mf.assert_called_with(*expected_args)

	@mock.patch(ecb_f, return_value={})
	def test_converts_units(self, currency_mock):
		self.check_convert_reply('100kg into stones', '100+kg+into+stones')
		self.check_convert_reply('100 kg into stones', '100+kg+into+stones')
		self.check_convert_reply('100 kg in stones', '100+kg+in+stones')
		self.check_convert_reply('100 KG IN STONES', '100+kg+in+stones')
		self.check_convert_reply('asdf 100 kg in stones asdf', '100+kg+in+stones')
		self.check_convert_reply('what is 100 kg in stones?', '100+kg+in+stones')
		self.check_convert_reply('100 square metres in acres', '100+square+metres+in+acres')
		self.check_convert_reply('100 cubic metres in litres', '100+cubic+metres+in+litres')
		self.check_convert_reply('100 fl.oz in litres', '100+fl.oz+in+litres')
		self.check_convert_reply('100k kg in tons', '100000+kg+in+tons')
