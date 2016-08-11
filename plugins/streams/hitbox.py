import logging
log = logging.getLogger(__name__)

import requests
import requests.exceptions
import plugins.streams


def make_hitbox_stream(data):
	channel = data.get('media_user_name', '').lower()
	title = data.get('media_status')
	return plugins.streams.Stream(channel, 'hitbox.tv/' + channel, title)


def get_hitbox_data(channels):
	url = 'http://api.hitbox.tv/media/live/' + (','.join(channels))
	response = requests.get(url)
	response.raise_for_status()

	if response.text == 'no_media_found':
		return {}

	try:
		return response.json()
	except ValueError:
		log.warning('could not decode hitbox response: %r', response.text)
		return {}


def get_online_streams(urls):
	"""From a collection of URLs, get the ones that are live on hitbox.tv."""
	channels = plugins.streams.filter_urls(urls, 'hitbox.tv')

	if not channels:
		return []

	data = get_hitbox_data(channels)

	if not data:
		return []

	streams = [
		make_hitbox_stream(stream)
		for stream in data.get('livestream', [])
		if stream['media_is_live'] == '1'
	]

	log.debug('%s online hitbox.tv streams', len(streams))

	return streams
