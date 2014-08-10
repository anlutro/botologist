import json
import urllib.request
import os.path
from datetime import datetime

_last_fetch = None
_cached_streams = None


class Stream:
	def __init__(self, name, url):
		self.name = name
		self.url = url

	def __eq__(self, other):
		return self.url == other.url

	@classmethod
	def from_twitch_data(cls, data):
		channel = data['channel']['display_name']
		return cls(channel, 'http://twitch.tv/' + channel.lower())

	@classmethod
	def from_hitbox_data(cls, data):
		channel = data['media_user_name']
		return cls(channel, 'http://twitch.tv/' + channel.lower())


def get_online_streams(bot):
	streams_path = os.path.join(bot.storage_path, 'streams.txt')

	with open(streams_path, 'r') as f:
		text = f.read()
		streams = text.strip().split('\n')

	if not streams:
		return None

	global _last_fetch
	global _cached_streams
	now = datetime.now()
	if _last_fetch is not None:
		diff = now - _last_fetch
		if diff.seconds < 60:
			return _cached_streams
	_last_fetch = now

	_cached_streams = _fetch_streams(streams)

	return _cached_streams


def get_new_streams(bot):
	streams_path = os.path.join(bot.storage_path, 'streams.txt')

	with open(streams_path, 'r') as f:
		text = f.read()
		streams = text.strip().split('\n')

	if not streams:
		return None

	streams = _fetch_streams(streams)

	diff = []
	global _cached_streams
	if _cached_streams is not None:
		cached_stream_urls = [stream.url for stream in _cached_streams]
		diff = [stream for stream in streams if stream.url not in cached_stream_urls]

	_cached_streams = streams

	return diff


def _get_streams_from_file(bot):
	streams_path = os.path.join(bot.storage_path, 'streams.txt')

	with open(streams_path, 'r') as f:
		text = f.read()
		streams = text.strip().split('\n')

	return streams


def _fetch_streams(streams):
	twitch_streams = _get_twitch_streams([s for s in streams if 'twitch.tv' in s])
	hitbox_streams = _get_hitbox_streams([s for s in streams if 'hitbox.tv' in s])

	streams = twitch_streams + hitbox_streams

	return streams


def add_stream(url, bot):
	streams_path = os.path.join(bot.storage_path, 'streams.txt')

	with open(streams_path, 'r') as f:
		text = f.read()
		if url in text:
			return False

	with open(streams_path, 'a') as f:
		f.write(url + '\n')
		return True

	return False

def _get_twitch_streams(urls):
	channels = [_extract_twitch_channel(url) for url in urls if url is not None]
	if not channels:
		return []

	url = 'https://api.twitch.tv/kraken/streams' + '?channel=' + ','.join(channels)
	print(str(datetime.now()) + ' - ' + url)

	result = urllib.request.urlopen(url)
	response = result.read().decode()
	data = json.loads(response)
	result.close()

	return [
		Stream.from_twitch_data(stream)
		for stream in data['streams']
	]


def _get_hitbox_streams(urls):
	channels = [_extract_hitbox_channel(url) for url in urls if url is not None]
	if not channels:
		return []

	url = 'http://api.hitbox.tv/media/live/' + ','.join(channels)
	print(str(datetime.now()) + ' - ' + url)

	result = urllib.request.urlopen(url)
	response = result.read().decode()
	result.close()

	if response == 'no_media_found':
		return []

	data = json.loads(response)

	return [
		Stream.from_hitbox_data(stream)
		for stream in data['livestream']
		if stream['media_is_live'] == '1'
	]


def _extract_twitch_channel(url):
	return _extract_channel(url, 'twitch.tv')


def _extract_hitbox_channel(url):
	return _extract_channel(url, 'hitbox.tv')


def _extract_channel(url, service):
	parts = url.split('/')

	for (key, part) in enumerate(parts):
		if service in part:
			return parts[key + 1].lower()

	return None
