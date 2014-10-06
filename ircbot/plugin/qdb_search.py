import json
import urllib.request
from datetime import datetime, timedelta

_BASE_URL = "http://bash.vaunt.eu/"
_JSON_URL = "{base_url}?json".format(base_url=_BASE_URL)
_URL_FORMAT_STRING = "{base_url}?{id}"
_MAX_SEARCH_RESULTS = 3
_QUOTES = []
_LAST_UPDATE = datetime.now()

class Quote:
    """Base Quote class."""
    id = None
    text = None
    score = None

    def __init__(self, _hash):
        self.id = _hash['id']
        self.text = _hash['quote']
        self.score = _hash['popularity']

    def __str__(self):
        return """#{id}: {url} ({score})""".format(
            id=self.id,
            score=self.score,
            url=_URL_FORMAT_STRING.format(base_url=_BASE_URL, id=self.id),
        )


def update_quotes():
    def sort_by_score(quote):
        """Sorts by score, we want the highest voted prioritised."""
        return quote.score
    response = urllib.request.urlopen(_JSON_URL)
    json_quotes = json.loads(response.read().decode('utf-8'))
    for j in json_quotes:
        quote = Quote(j)
        _QUOTES.append(quote)
    return sorted(_QUOTES, key=sort_by_score, reverse=True)


def search_quotes(string):
    """List of quotes matching search string."""
    if not _QUOTES or datetime.now() - _LAST_UPDATE > timedelta(minutes=30):
        update_quotes()
    matches = []
    for quote in _QUOTES:
        if string in quote.text and len(matches) < _MAX_SEARCH_RESULTS:
            matches.append(quote)
    return matches

