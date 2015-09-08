import logging
log = logging.getLogger(__name__)

import datetime
import json
import re
import urllib.error

import botologist.http
import botologist.plugin


def get_duckduckgo_data(url):
	response = botologist.http.get(url)
	content = response.read().decode()
	return json.loads(content)


def get_conversion_result(query):
	qs = urllib.parse.urlencode({'q': query, 'format': 'json', 'no_html': 1})
	url = 'http://api.duckduckgo.com/?' + qs

	try:
		data = get_duckduckgo_data(url)
	except urllib.error.URLError:
		log.warning('DuckDuckGo request failed', exc_info=True)
		return False

	if data['AnswerType'] == 'conversions' and data['Answer']:
		return data['Answer']


def get_currency_data():
	url = 'http://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml'
	try:
		response = botologist.http.get(url)
		content = response.read().decode()
	except urllib.error.URLError:
		log.warning('ECB exchange data request failed', exc_info=True)
		return {}

	matches = re.findall(r'<Cube currency=["\']([A-Za-z]{3})["\'] rate=["\']([\d.]+)["\']/>', content)
	currency_data = {}
	for currency, exchange_rate in matches:
		currency_data[currency.upper()] = float(exchange_rate)
	log.info('Found %d currencies', len(currency_data))

	return currency_data

class Currency:
	last_fetch = None
	currency_data = None

	@classmethod
	def currencies(cls):
		cls.load()
		return cls.currency_data.keys()

	@classmethod
	def convert(cls, amount, from_cur, to_cur):
		cls.load()

		try:
			amount = float(amount)
		except ValueError:
			return None

		from_cur = from_cur.upper()
		to_cur = to_cur.upper()

		if from_cur == 'EUR':
			if to_cur not in cls.currency_data:
				return None
			return amount * cls.currency_data[to_cur]
		if to_cur == 'EUR':
			if from_cur not in cls.currency_data:
				return None
			return amount / cls.currency_data[from_cur]

		if from_cur in cls.currency_data and to_cur in cls.currency_data:
			amount = amount / cls.currency_data[from_cur]
			return amount * cls.currency_data[to_cur]

		return None

	@classmethod
	def load(cls):
		now = datetime.datetime.now()
		if cls.last_fetch:
			diff = now - cls.last_fetch
		if not cls.last_fetch or diff.seconds > 3600:
			cls.currency_data = get_currency_data()
			cls.last_fetch = now


class ConversionPlugin(botologist.plugin.Plugin):
	pattern = re.compile(r'([\d.,]+) ?([a-zA-Z\s]+) (into|in|to) ([a-zA-Z\s]+)')

	@botologist.plugin.reply()
	def convert(self, msg):
		match = self.pattern.search(msg.message)
		if not match:
			return

		amount = match.group(1)
		conv_from = match.group(2)
		conv_to = match.group(4)

		result = Currency.convert(amount, conv_from, conv_to)
		if result:
			if len(amount) > 8:
				amount = '{:.2f}'.format(float(amount))
			return '{} {} = {:.2f} {}'.format(amount, conv_from, result, conv_to)

		result = get_conversion_result(' '.join(match.groups()))
		if result:
			return result
