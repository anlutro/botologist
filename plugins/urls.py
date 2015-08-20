import logging
log = logging.getLogger(__name__)

import urllib.request
import urllib.error
import socket
import re

import ircbot.plugin


url_shorteners = (
	'https?://bit\.ly',
	'https?://goo\.gl',
	'https?://is\.gd',
	'https?://redd\.it',
	'https?://t\.co',
	'https?://tinyurl\.com',
)
url_shorteners = '|'.join(url_shorteners)
short_url_regex = re.compile(r'((' + url_shorteners + ')\/[a-zA-Z0-9]+)')


def find_shortened_urls(message):
	matches = short_url_regex.findall(message)
	return [match[0] for match in matches]


def get_location(url):
	request = urllib.request.Request(url=url, method='HEAD')
	response = urllib.request.urlopen(request, timeout=2)
	return response.url


def unshorten_url(url):
	try:
		url = get_location(url)
	except (urllib.error.URLError, socket.timeout):
		log.debug('HTTP error, aborting')
		return None

	if len(url) > 300:
		return None

	return url


class UrlPlugin(ircbot.plugin.Plugin):
	@ircbot.plugin.reply()
	def reply(self, msg):
		urls = find_shortened_urls(msg.message)
		ret = []

		for url in urls:
			real_url = unshorten_url(url)
			if real_url:
				ret.append('{} => {}'.format(url, real_url))

		if ret:
			return ret
