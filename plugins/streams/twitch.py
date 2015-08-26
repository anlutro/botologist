import logging
log = logging.getLogger(__name__)

import json

import ircbot.http
import plugins.streams


def make_twitch_stream(data):
	channel = data.get('channel', {}).get('name', '').lower()
	title = data.get('channel', {}).get('status', '')
	return plugins.streams.Stream(channel, 'twitch.tv/' + channel, title)


def extract_channel(url):
	parts = url.split('/')

	for (key, part) in enumerate(parts):
		if 'twitch.tv' in part:
			return parts[key + 1].lower()


def get_twitch_data(channels):
	url = 'https://api.twitch.tv/kraken/streams'

	query_params = {'channel': ','.join(channels)}
	response = ircbot.http.get(url, query_params=query_params)
	contents = response.read().decode()
	response.close()
	return json.loads(contents)


def get_online_streams(urls):
	"""From a collection of URLs, get the ones that are live on twitch.tv."""
	channels = [
		extract_channel(url)
		for url in urls if url is not None
	]

	if not channels:
		return []

	data = get_twitch_data(channels)
	log.debug('{streams} online twitch.tv streams'.format(
		streams=len(data['streams'])))

	return [
		make_twitch_stream(stream)
		for stream in data['streams']
	]
