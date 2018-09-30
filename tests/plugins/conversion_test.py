import datetime
import unittest
from unittest import mock

import freezegun

from tests.plugins import PluginTestCase
from plugins.conversion import get_currency_data


class GetCurrencyDataTest(unittest.TestCase):
    def test_uses_cached_data_if_recent_enough(self):
        currency_data = {"_timestamp": datetime.datetime(2018, 9, 30, 15, 30)}
        get_patch = mock.patch("requests.get")
        data_patch = mock.patch.dict("plugins.conversion._currency_data", currency_data)
        with freezegun.freeze_time(
            "2018-09-30 16:00:00"
        ), data_patch, get_patch as get_mock:
            assert get_currency_data() == currency_data
            get_mock.assert_not_called()
        with freezegun.freeze_time(
            "2018-09-30 17:00:00"
        ), data_patch, get_patch as get_mock:
            get_mock.return_value = mock.Mock(text="")
            assert get_currency_data() == {
                "_timestamp": datetime.datetime(2018, 9, 30, 17, 0)
            }
            get_mock.assert_called_once_with(
                "http://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml",
                timeout=2,
            )


ddg_f = "plugins.conversion.get_duckduckgo_data"
ecb_f = "plugins.conversion.get_currency_data"


class ConversionPluginTest(PluginTestCase):
    def create_plugin(self):
        from plugins.conversion import ConversionPlugin

        return ConversionPlugin(self.bot, self.channel)

    @mock.patch(ddg_f, return_value={"AnswerType": "conversions", "Answer": "TEST"})
    @mock.patch(ecb_f, return_value={"NOK": 8.00, "DKK": 6.00})
    def test_converts_currencies(self, currency_mock, convert_mock):
        self.assertEqual("10 eur = 80 nok", self.reply("10 eur into nok"))
        self.assertEqual("10 eur = 60 dkk", self.reply("10 eur into dkk"))
        self.assertEqual("10 nok = 1.25 eur", self.reply("10 nok into eur"))
        self.assertEqual("10 dkk = 1.67 eur", self.reply("10 dkk into eur"))
        self.assertEqual("10 nok = 7.50 dkk", self.reply("10 nok into dkk"))
        self.assertEqual("10 dkk = 13.33 nok", self.reply("10 dkk into nok"))
        self.assertEqual("10 dkk = 13.33 nok", self.reply("what is 10 dkk into nok?"))
        self.assertEqual("10,000 eur = 80,000 nok", self.reply("10k eur into nok"))
        self.assertEqual("1,100 eur = 8,800 nok", self.reply("1.1k eur into nok"))
        self.assertEqual("TEST", self.reply("10 cny into eur"))
        self.assertEqual("TEST", self.reply("10 eur into cny"))
        self.assertEqual("TEST", self.reply("10 usd into cny"))
        self.assertEqual("10 eur = 80 nok, 60 dkk", self.reply("10 eur into nok,dkk"))
        self.assertEqual(
            "10 eur = 80 nok, 60 dkk", self.reply("10 eur into nok,dkk,cny")
        )

    def check_convert_reply(self, message, expected_qs, response="DEFAULT"):
        if response == "DEFAULT":
            response = message + " reply"
        return_value = {"AnswerType": "conversions", "Answer": response}
        with mock.patch(ddg_f, return_value=return_value) as mf:
            self.assertEqual(response, self.reply(message))
        mf.assert_called_with(
            "https://api.duckduckgo.com",
            {"q": expected_qs, "format": "json", "no_html": 1},
        )

    @mock.patch(ecb_f, return_value={})
    def test_converts_units(self, currency_mock):
        self.check_convert_reply("100kg into stones", "100 kg into stones")
        self.check_convert_reply("100 kg into stones", "100 kg into stones")
        self.check_convert_reply("100 kg in stones", "100 kg in stones")
        self.check_convert_reply("100 KG IN STONES", "100 kg in stones")
        self.check_convert_reply("asdf 100 kg in stones asdf", "100 kg in stones")
        self.check_convert_reply("what is 100 kg in stones?", "100 kg in stones")
        self.check_convert_reply(
            "100 square metres in acres", "100 square metres in acres"
        )
        self.check_convert_reply(
            "100 cubic metres in litres", "100 cubic metres in litres"
        )
        self.check_convert_reply("100 fl.oz in litres", "100 fl.oz in litres")
        self.check_convert_reply("100 000 kg in tons", "100000 kg in tons")
        self.check_convert_reply("100,000 kg in tons", "100000 kg in tons")
        self.check_convert_reply("100k kg in tons", "100000 kg in tons")
        self.check_convert_reply("123 456.78 kg in lbs", "123456.78 kg in lbs")
        self.check_convert_reply("0.5 kg in lbs", "0.5 kg in lbs")
        self.check_convert_reply(".5 kg in lbs", "0.5 kg in lbs")
