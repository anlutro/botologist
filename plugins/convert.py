import logging
log = logging.getLogger(__name__)

import datetime
import json
import re
import socket
import urllib.error
import urllib.request

import ircbot.plugin


def get_conversion_result(qs):
	url = 'http://api.duckduckgo.com/?q='+qs+'&format=json&no_html=1'
	log.info('Fetching: '+url)
	try:
		response = urllib.request.urlopen(url, timeout=2)
		content = response.read().decode()
	except (urllib.error.URLError, socket.timeout):
		return False
	data = json.loads(content)
	if data['AnswerType'] == 'conversions' and data['Answer']:
		return data['Answer']

def get_currency_data():
	url = 'http://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml'
	log.info('Fetching: '+url)
	try:
		response = urllib.request.urlopen(url, timeout=2)
		content = response.read().decode()
	except (urllib.error.URLError, socket.timeout):
		return {}

	matches = re.findall(r'<Cube currency=["\']([A-Za-z]{3})["\'] rate=["\']([\d.]+)["\']/>', content)
	currency_data = {}
	for currency, exchange_rate in matches:
		currency_data[currency.upper()] = float(exchange_rate)
	log.info('Found {} currencies'.format(len(currency_data)))
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


class ConversionPlugin(ircbot.plugin.Plugin):
	pattern = re.compile(r'([\d.,]+) ?([a-zA-Z]+) (into|in|to) ([a-zA-Z]+)')

	@ircbot.plugin.reply()
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

		qs = '+'.join(match.groups())
		result = get_conversion_result(qs)
		if result:
			return result
