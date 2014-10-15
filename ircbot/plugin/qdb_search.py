import json
import urllib.request
import operator
from datetime import datetime, timedelta

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

	def __init__(self):
		self._last_update = datetime.now()
		self._quotes = self.update_quotes()


	def update_quotes(self):
		"""Fetches and sorts our quoties."""
		response = urllib.request.urlopen(_JSON_URL)
		json_quotes = json.loads(response.read().decode('utf-8'))
		quotes = []
		for j in json_quotes:
			quote = Quote(j)
			quotes.append(quote)
		self._last_update = datetime.now()
		return self.ordered_quotes(quotes)


	def search_quotes(self, string):
		"""List of quotes matching search string."""
		if not self._quotes or datetime.now() - self._last_update > timedelta(minutes=30):
			self._quotes = self.update_quotes()
		matches = []
		for quote in self._quotes:
			if string in quote.text and len(matches) < self._max_results:
				matches.append(quote)
		return matches


	def ordered_quotes(self, quotes):
		"""Reverse ordered quotes by score."""
		return sorted(quotes, key=operator.attrgetter('score'), reverse=True)

# vim: ts=4
