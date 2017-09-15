import logging
log = logging.getLogger(__name__)

import requests
import requests.exceptions
import plugins.streams
from botologist import http


def make_twitch_stream(data):
	channel_data = data.get('channel', {})
	channel = channel_data.get('name', '').lower()
	title = channel_data.get('status', '')
	game = data.get('game')

	return plugins.streams.Stream(channel, 'twitch.tv/' + channel, title, game)


async def get_twitch_data(channels, auth_token):
	url = 'https://api.twitch.tv/kraken/streams'
	query_params = {'channel': ','.join(channels)}
	headers = {'Authorization': 'OAuth %s' % auth_token}
	response = await http.get(url, params=query_params, headers=headers)
	return await response.json()


async def get_online_streams(urls, auth_token):
	"""From a collection of URLs, get the ones that are live on twitch.tv."""
	channels = plugins.streams.filter_urls(urls, 'twitch.tv')

	if not channels:
		return []

	data = await get_twitch_data(channels, auth_token)
	streams = data.get('streams') or []
	log.debug('%s online twitch.tv streams', len(streams))

	return [make_twitch_stream(stream) for stream in streams]
