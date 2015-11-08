import logging
log = logging.getLogger(__name__)

import re
import requests
import requests.exceptions

import botologist.plugin


url_shorteners = r'|'.join((
	r'https?://bit\.ly',
	r'https?://goo\.gl',
	r'https?://is\.gd',
	r'https?://redd\.it',
	r'https?://t\.co',
	r'https?://tinyurl\.com',
))
short_url_regex = re.compile(r'((' + url_shorteners + r')\/[a-zA-Z0-9]+)')


def find_shortened_urls(message):
	matches = short_url_regex.findall(message)
	return [match[0] for match in matches]


def get_location(url):
	return requests.head(url).url


def unshorten_url(url):
	try:
		url = get_location(url)
	except requests.exceptions.RequestException:
		log.info('HTTP error while unshortening URL', exc_info=True)
		return None

	if len(url) > 300:
		log.info('Unshortened URL is too long (%d characters)', len(url))
		return None

	return url


class UrlPlugin(botologist.plugin.Plugin):
	@botologist.plugin.reply()
	def reply(self, msg):
		urls = find_shortened_urls(msg.message)
		ret = []

		for url in urls:
			real_url = unshorten_url(url)
			if real_url:
				ret.append('{} => {}'.format(url, real_url))

		if ret:
			return ret
