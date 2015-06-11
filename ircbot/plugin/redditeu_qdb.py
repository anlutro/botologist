import ircbot.plugin
import json
import socket
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = 'http://qdb.lutro.me'


def _search_for_quote(quote):
	if isinstance(quote, int):
		url = BASE_URL+'/'+str(quote)
		single = True
	else:
		search = str(quote)
		single = False
		if quote == 'random':
			url = BASE_URL+'/random'
		elif quote == 'latest':
			url = BASE_URL
		else:
			url = BASE_URL+'?'+urllib.parse.urlencode({'s': search})

	try:
		request = urllib.request.Request(url)
		request.add_header('Accept', 'application/json')
		response = urllib.request.urlopen(request, timeout=2)
		content = response.read().decode()
	except (urllib.error.URLError, socket.timeout):
		return 'HTTP error, try again!'

	data = json.loads(content)

	if single:
		quote = data['quote']
	else:
		quotes = data['quotes']
		if 'items' in quotes:
			quotes = quotes['items']
		if len(quotes) < 1:
			return 'No quotes found!'
		quote = quotes[0]

	url = BASE_URL+'/'+str(quote['id'])
	body = quote['body'].replace('\r', '').replace('\n', ' ').replace('\t', ' ')

	if len(body) > 160:
		if not single:
			start = body.rfind('<', 0, body.index(search))
			start = max(start, body.index(search) - 70)
			end = start + 100 - len(search)
		else:
			start = 0
			end = 100

		if start > 0:
			body = '[...] ' + body[start:end] + ' [...]'
		else:
			body = body[start:end] + ' [...]'

	return url + ' - ' + body


class RedditeuQdbPlugin(ircbot.plugin.Plugin):
	@ircbot.plugin.command('qdb')
	def search(self, cmd):
		if len(cmd.args) < 1:
			return

		if cmd.args[0][0] == '#':
			arg = int(cmd.args[0][1:])
		else:
			arg = ' '.join(cmd.args)

		return _search_for_quote(arg)
