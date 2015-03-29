import ircbot.plugin
from ircbot import log

import urllib.request
import urllib.error
import socket
import re


url_shorteners = (
	'https?://bit\.ly',
	'https?://goo\.gl',
	'https?://is\.gd',
	'https?://redd\.it',
	'https?://t\.co',
)
url_shorteners = '|'.join(url_shorteners)
short_url_regex = re.compile(r'((' + url_shorteners + ')\/[a-zA-Z0-9]+)')

def find_shortened_urls(message):
	matches = short_url_regex.findall(message)
	return [match[0] for match in matches]

def unshorten_url(url):
	limit = 2

	try:
		request = urllib.request.Request(url=url, method='HEAD')
		response = urllib.request.urlopen(request, timeout=2)
		url = response.url
	except (urllib.error.URLError, socket.timeout):
		log.debug('HTTP error, aborting')
		return None

	if len(url) > 300:
		return None

	return url


class UrlPlugin(ircbot.plugin.Plugin):
	@ircbot.plugin.reply
	def reply(self, msg):
		urls = find_shortened_urls(msg.message)

		for url in urls:
			real_url = unshorten_url(url)
			if real_url:
				text = '{} => {}'.format(url, real_url)
				self.bot._send_msg(text, msg.target)
