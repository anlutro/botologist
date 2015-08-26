import logging
log = logging.getLogger(__name__)

import json
import urllib.parse

import ircbot.http
import plugins.streams


def make_hitbox_stream(data):
	channel = data.get('media_user_name', '').lower()
	title = data.get('media_status')
	return plugins.streams.Stream(channel, 'hitbox.tv/' + channel, title)


def extract_channel(url):
	parts = url.split('/')

	for (key, part) in enumerate(parts):
		if 'hitbox.tv' in part:
			return parts[key + 1].lower()


def get_hitbox_data(channels):
	channels = [urllib.parse.quote(channel) for channel in channels]
	url = 'http://api.hitbox.tv/media/live/' + ','.join(channels)

	response = ircbot.http.get(url)
	contents = response.read().decode()
	response.close()

	if contents == 'no_media_found':
		return []

	return json.loads(contents)


def get_online_streams(urls):
	"""From a collection of URLs, get the ones that are live on hitbox.tv."""
	channels = [
		extract_channel(url)
		for url in urls if url is not None
	]

	if not channels:
		return []

	data = get_hitbox_data(channels)

	if not data:
		return data

	streams = [
		make_hitbox_stream(stream)
		for stream in data['livestream']
		if stream['media_is_live'] == '1'
	]

	log.debug('{streams} online hitbox.tv streams'.format(streams=len(streams)))

	return streams
