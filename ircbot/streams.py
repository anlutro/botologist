import json
import os.path
import re
import urllib.error
import urllib.request
from datetime import datetime

from ircbot.bot import log

_last_fetch = None
_cached_streams = None


class StreamNotFoundException(Exception):
	pass

class AmbiguousStreamException(Exception):
	def __init__(self, streams):
		self.streams = streams

class AlreadySubscribedException(Exception):
	def __init__(self, stream):
		self.stream = stream

class InvalidStreamException(Exception):
	def __init__(self, msg):
		self.msg = msg


class Stream:
	def __init__(self, user, url, title=None):
		self.user = user
		self.url = url
		self.full_url = 'http://'+url
		self.title = title

	def __eq__(self, other):
		return self.url == other.url

	@classmethod
	def from_twitch_data(cls, data):
		channel = data.get('channel', {}).get('name', '').lower()
		title = data.get('channel', {}).get('status')
		obj = cls(channel, 'twitch.tv/' + channel, title)
		obj.full_url = obj.full_url + '/popout'
		return obj

	@classmethod
	def from_hitbox_data(cls, data):
		channel = data.get('media_user_name', '').lower()
		title = data.get('media_status')
		return cls(channel, 'hitbox.tv/' + channel, title)


def get_online_streams(bot):
	streams = _get_streams_from_file(bot)

	if not streams:
		return None

	global _last_fetch
	global _cached_streams
	now = datetime.now()
	if _last_fetch is not None:
		diff = now - _last_fetch
		if diff.seconds < 30:
			return _cached_streams
	_last_fetch = now

	try:
		_cached_streams = _fetch_streams(streams)
	except (urllib.error.HTTPError, TimeoutError):
		pass

	return _cached_streams


def get_new_streams(bot):
	streams = _get_streams_from_file(bot)

	if not streams:
		return None

	try:
		streams = _fetch_streams(streams)
	except (urllib.error.HTTPError, TimeoutError):
		return []

	diff = []
	global _cached_streams
	if _cached_streams is not None:
		cached_stream_urls = [stream.url for stream in _cached_streams]
		diff = [stream for stream in streams if stream.url not in cached_stream_urls]

	_cached_streams = streams

	return diff


def _get_streams_from_file(bot):
	streams_path = os.path.join(bot.storage_path, 'streams.txt')

	# create file if it doesn't exist
	if not os.path.exists(streams_path):
		open(streams_path, 'w+')
		return []

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
	url = _normalize_url(url)

	if url in _get_streams_from_file(bot):
		return False

	streams_path = os.path.join(bot.storage_path, 'streams.txt')

	with open(streams_path, 'a') as f:
		f.write(url + '\n')
		return True

	return False


def _normalize_url(url):
	url = url.replace('http://', '') \
		.replace('https://', '') \
		.replace('www.', '')

	if 'twitch.tv' not in url and 'hitbox.tv' not in url:
		raise InvalidStreamException('Only twitch and hitbox URLs allowed')

	segments = url.split('/')

	if len(segments) < 2:
		raise InvalidStreamException('Missing parts of URL')

	if re.match('^[\w\_]+$', segments[1]) is None:
		raise InvalidStreamException('Invalid characters in channel name')

	url = '/'.join(segments[:2])

	return url


def _get_twitch_streams(urls):
	channels = [_extract_twitch_channel(url) for url in urls if url is not None]
	if not channels:
		return []

	url = 'https://api.twitch.tv/kraken/streams' + '?channel=' + ','.join(channels)
	log.info('Fetching ' + str(datetime.now()) + ' - ' + url)

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
	log.info('Fetching ' + str(datetime.now()) + ' - ' + url)

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


def sub_stream(bot, user, stream):
	if 'twitch.tv' in stream or 'hitbox.tv' in stream:
		stream = _normalize_url(stream)

	streams = [s for s in _get_streams_from_file(bot) if stream in s]

	if not streams:
		raise StreamNotFoundException()
	elif len(streams) > 1:
		# don't raise if there is an exact match
		if stream not in streams:
			raise AmbiguousStreamException(streams)
	else:
		stream = streams[0]

	subs = get_all_subs(bot)

	if not subs.get('streams'):
		subs['streams'] = {}
	if not subs['streams'].get(stream):
		subs['streams'][stream] = []

	if stream in list_user_subs(bot, user):
		raise AlreadySubscribedException(stream)

	subs['streams'][stream].append(user)

	subs_path = os.path.join(bot.storage_path, 'subscriptions.json')
	with open(subs_path, 'w') as f:
		f.write(json.dumps(subs))

	return stream


def list_user_subs(bot, user):
	subs_path = os.path.join(bot.storage_path, 'subscriptions.json')

	if not os.path.exists(subs_path):
		with open(subs_path, 'w+') as f:
			f.write('{}')
		return []

	with open(subs_path, 'r') as f:
		all_subs = json.loads(f.read())

	user_subs = []

	for stream, subs in all_subs.get('streams', {}).items():
		if user in subs:
			user_subs.append(stream)

	return user_subs


def list_stream_subs(bot, stream_url):
	subs = get_all_subs(bot)

	return subs.get('streams', {}).get(stream_url, [])


def get_all_subs(bot):
	subs_path = os.path.join(bot.storage_path, 'subscriptions.json')

	if not os.path.exists(subs_path):
		with open(subs_path, 'w+') as f:
			f.write('{}')
		return {}

	with open(subs_path, 'r') as f:
		subs = json.loads(f.read())

	return subs
