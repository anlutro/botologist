import json
import urllib.request
from urllib.error import URLError
import operator
from datetime import datetime, timedelta
import ircbot.plugin
from ircbot import log

_BASE_URL = "http://bash.vaunt.eu/"
_JSON_URL = "{base_url}?json".format(base_url=_BASE_URL)


class Quote:
	"""Base Quote class."""
	id = None
	text = None
	score = None

	def __init__(self, _hash):
		self.id = _hash['id']
		self.text = _hash['quote'].lower()
		self.score = int(_hash['popularity'])

	def __str__(self):
		return """#{id}: {url} ({score})""".format(
			id=self.id,
			score=self.score,
			url="{base_url}?{id}".format(
				base_url=_BASE_URL,
				id=self.id,
				)
			)


class Quotes:
	_max_results = 5  # Max returned quotes.
	_last_update = None
	_quotes = None

	def __init__(self):
		self.update()


	def update(self):
		"""Fetches and sorts our quoties."""
		log.info('Fetching quotes from {url}'.format(url=_JSON_URL))
		try:
			response = urllib.request.urlopen(_JSON_URL, timeout=2)
		except URLError:
			return
		json_quotes = json.loads(response.read().decode('utf-8'))
		quotes = [Quote(data) for data in json_quotes]
		self._last_update = datetime.now()
		self._quotes = self.order(quotes)


	def search(self, string):
		"""List of quotes matching search string."""
		if not self._quotes or datetime.now() - self._last_update > timedelta(minutes=30):
			self.update()
		matches = []
		for quote in self._quotes:
			if string in quote.text and len(matches) < self._max_results:
				matches.append(quote)
		return matches


	def order(self, quotes):
		"""Reverse ordered quotes by score."""
		return sorted(quotes, key=operator.attrgetter('score'), reverse=True)


class RedditeuQdbPlugin(ircbot.plugin.Plugin):
	def __init__(self, bot, channel):
		super().__init__(bot, channel)
		self.quotes = Quotes()

	@ircbot.plugin.command('qdb')
	def qdb_search_cmd(self, msg):
		if len(msg.args) < 1:
			return None

		search_string = ' '.join(msg.args).lower()
		quotes = self.quotes.search(search_string)
		if quotes:
			return ', '.join([str(quote) for quote in quotes])
		else:
			return "Nothing found matching those deets."
