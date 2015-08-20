import ircbot.plugin
import json
import socket
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = 'http://qdb.lutro.me'


def _get_quote_url(quote):
	return BASE_URL + '/' + str(quote['id'])


def _get_qdb_data(url):
	request = urllib.request.Request(url)
	request.add_header('Accept', 'application/json')
	response = urllib.request.urlopen(request, timeout=2)
	content = response.read().decode()
	return json.loads(content)


def _search_for_quote(quote):
	search = False
	if isinstance(quote, int):
		url = BASE_URL+'/'+str(quote)
		single_quote = True
	else:
		single_quote = False
		if quote == 'random':
			url = BASE_URL+'/random'
		elif quote == 'latest':
			url = BASE_URL
		else:
			search = str(quote)
			url = BASE_URL+'/random?'+urllib.parse.urlencode({'s': search})

	try:
		data = _get_qdb_data(url)
	except (urllib.error.URLError, socket.timeout):
		return 'HTTP error!'

	if single_quote:
		quote = data['quote']
	else:
		quotes = data['quotes']
		if 'items' in quotes:
			quotes = quotes['items']
		if len(quotes) < 1:
			return 'No quotes found!'
		quote = quotes[0]

	url = BASE_URL+'/'+str(quote['id'])

	if len(quote['body']) > 160:
		body = quote['body']
		if search:
			try:
				body_len = len(body)
				substr_pos = body.lower().index(search.lower())
				start = body.rfind('\n', 0, substr_pos) + 1
				while body_len - start < 100:
					substr_pos = body.rfind('\n', 0, start - 1) + 1
					if body_len - substr_pos < 100:
						start = substr_pos
					else:
						break
				end = start + 150 - len(search)
			except ValueError:
				start = 0
				end = 100
		else:
			start = 0
			end = 100

		body = body.replace('\r', '').replace('\n', ' ').replace('\t', ' ')
		excerpt = body[start:end]

		if start > 0:
			excerpt = '[...] ' + excerpt
		if end < len(quote['body']):
			excerpt = excerpt + ' [...]'
		body = excerpt
	else:
		body = quote['body'].replace('\r', '').replace('\n', ' ').replace('\t', ' ')

	return url + ' - ' + body


class RedditeuQdbPlugin(ircbot.plugin.Plugin):
	@ircbot.plugin.command('qdb')
	def search(self, cmd):
		if len(cmd.args) < 1:
			return

		if cmd.args[0][0] == '#':
			try:
				arg = int(cmd.args[0][1:])
			except ValueError:
				arg = ' '.join(cmd.args)
		else:
			arg = ' '.join(cmd.args)

		return _search_for_quote(arg)

	@ircbot.plugin.http_handler(method='POST', path='/qdb-update')
	def quote_updated(self, body):
		data = json.loads(body)
		quote = data['quote']
		if quote['approved']:
			return 'New quote approved! ' + _get_quote_url(quote)
		else:
			return 'Quote pending approval!'
