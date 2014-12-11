from ircbot import log
import ircbot.plugin

import datetime
import json
import os.path
import re
import socket
import urllib.error
import urllib.request


class StreamException(RuntimeError):
	pass

class StreamNotFoundException(StreamException):
	def __init__(self, message=None):
		super().__init__(message or 'Error: Stream not found')

class InvalidStreamException(StreamException):
	def __init__(self, message=None):
		super().__init__(message or 'Error: Invalid stream URL')

class AmbiguousStreamException(StreamException):
	def __init__(self, streams):
		msg = 'Ambiguous stream choice - '
		if len(streams) > 5:
			msg += str(len(streams)) + ' options'
		else:
			msg += 'options: ' + ', '.join(streams)
		super().__init__(msg)
		self.streams = streams

class AlreadySubscribedException(StreamException):
	def __init__(self, stream):
		super().__init__('Already subscribed to stream: ' + stream)
		self.stream = stream


def error_prone(func):
	"""Decorator that automatically catches stream exceptions and returns the
	exception's string representation."""
	def wrapper(*args, **kwargs):
		try:
			return func(*args, **kwargs)
		except StreamException as e:
			return str(e)
	return wrapper


def _normalize_url(url):
	"""Normalize a stream URL."""
	if 'twitch.tv' not in url and 'hitbox.tv' not in url:
		raise InvalidStreamException('Only twitch and hitbox URLs allowed')

	url = url.replace('http://', '') \
		.replace('https://', '') \
		.replace('www.', '')

	segments = url.split('/')

	if len(segments) < 2:
		raise InvalidStreamException('Missing parts of URL')

	if re.match('^[\w\_]+$', segments[1]) is None:
		raise InvalidStreamException('Invalid characters in channel name')

	url = '/'.join(segments[:2])

	return url


class Stream:
	def __init__(self, user, url, title=None):
		self.user = user
		self.url = url
		self.full_url = 'http://'+url
		self.title = re.sub(r'\n', ' ', title)

	def __eq__(self, other):
		if isinstance(other, self.__class__):
			return self.url == other.url
		elif isinstance(other, str):
			# assume it is a valid url
			return self.url == other
		else:
			raise ValueError('Cannot compare Stream with {type}'.format(
				type=type(other).__name__))

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


def _fetch_streams(streams):
	"""Return an array of Stream objects for the streams in the array of urls
	that are currently live."""
	twitch_streams = _fetch_twitch([s for s in streams if 'twitch.tv' in s])
	hitbox_streams = _fetch_hitbox([s for s in streams if 'hitbox.tv' in s])
	return twitch_streams + hitbox_streams

def _fetch_twitch(urls):
	channels = [_extract_channel(url, 'twitch.tv') for url in urls if url is not None]
	if not channels:
		return []

	url = 'https://api.twitch.tv/kraken/streams?channel=' + ','.join(channels)
	log.info('Fetching ' + url)

	result = urllib.request.urlopen(url, timeout=2)
	response = result.read().decode()
	result.close()
	data = json.loads(response)
	log.debug('{streams} online twitch.tv streams'.format(streams=len(data['streams'])))

	return [
		Stream.from_twitch_data(stream)
		for stream in data['streams']
	]


def _fetch_hitbox(urls):
	"""From a collection of urls, get the ones that are live on hitbox.tv."""
	channels = [_extract_channel(url, 'hitbox.tv') for url in urls if url is not None]
	if not channels:
		return []

	url = 'http://api.hitbox.tv/media/live/' + ','.join(channels)
	log.info('Fetching ' + url)

	result = urllib.request.urlopen(url, timeout=2)
	response = result.read().decode()
	result.close()

	if response == 'no_media_found':
		return []

	data = json.loads(response)

	streams = [
		Stream.from_hitbox_data(stream)
		for stream in data['livestream']
		if stream['media_is_live'] == '1'
	]

	log.debug('{streams} online hitbox.tv streams'.format(streams=len(streams)))

	return streams


def _extract_channel(url, service):
	parts = url.split('/')

	for (key, part) in enumerate(parts):
		if service in part:
			return parts[key + 1].lower()

	return None


class StreamManager:
	def __init__(self, stor_path):
		self.streams = []
		self.subs = {}
		self._last_fetch = None
		self._cached_streams = None
		self.stor_path = stor_path
		self._read()

	def _read(self):
		if not os.path.isfile(self.stor_path):
			self._write()
		with open(self.stor_path, 'r') as f:
			data = json.loads(f.read())
		self.streams = data.get('streams', [])
		self.subs = data.get('subscriptions', {})

	def _write(self):
		data = {'streams': self.streams, 'subscriptions': self.subs}
		content = json.dumps(data, indent=2)
		with open(self.stor_path, 'w') as f:
			f.write(content)

	def add_stream(self, url):
		"""Add a stream.

		Returns true on success, false if the stream has already been added, and
		throws some sort of exception if anything else goes wrong.
		"""
		url = _normalize_url(url)

		if url in self.streams:
			return False

		self.streams.append(url)
		self._write()
		return True

	def find_stream(self, url):
		if 'twitch.tv' in url or 'hitbox.tv' in url:
			url = _normalize_url(url)

		streams = [s for s in self.streams if url in s]

		if not streams:
			raise StreamNotFoundException('Error: Stream not found: ' + url)
		elif len(streams) > 1:
			# if there is an exact match, return that
			if url in streams:
				return url
			# else, raise an exception
			raise AmbiguousStreamException(streams)
		else:
			return streams[0]

	def del_stream(self, url):
		url = self.find_stream(url)
		self.streams.remove(url)
		self._write()
		return url

	def add_subscriber(self, host, url):
		url = self.find_stream(url)
		if host not in self.subs:
			self.subs[host] = []
		elif url in self.subs[host]:
			return False
		self.subs[host].append(url)
		self._write()
		return url

	def del_subscriber(self, host, url):
		url = self.find_stream(url)
		if host not in self.subs or url not in self.subs[host]:
			return False
		self.subs[host].remove(url)
		self._write()
		return url

	def get_subscriptions(self, host):
		return self.subs.get(host, None)

	def get_online_streams(self):
		if not self.streams:
			return None

		now = datetime.datetime.now()
		if self._last_fetch is not None:
			diff = now - self._last_fetch
			if diff.seconds < 30:
				log.debug('Stream data less than 30 seconds old, returning cached')
				return self._cached_streams

		try:
			self._cached_streams = _fetch_streams(self.streams)
		except (urllib.error.HTTPError, socket.timeout):
			log.warning('Could not fetch online streams!')
			pass

		self._last_fetch = now

		return self._cached_streams

	def get_new_online_streams(self):
		if not self.streams:
			return None

		try:
			streams = _fetch_streams(self.streams)
		except (urllib.error.HTTPError, socket.timeout):
			log.warning('Could not fetch new online streams!')
			return None

		diff = []
		if self._cached_streams is not None:
			cached_stream_urls = [stream.url for stream in self._cached_streams]
			diff = [stream for stream in streams if stream.url not in cached_stream_urls]
			log.debug('Cached streams: {cached} - Online streams: {online} - Diff: {diff}'.format(
				cached=len(self._cached_streams), online=len(streams), diff=len(diff)))
		self._cached_streams = streams
		self._last_fetch = datetime.datetime.now()

		return diff


class StreamsPlugin(ircbot.plugin.Plugin):
	def __init__(self, bot, channel):
		super().__init__(bot, channel)
		filename = 'streams_' + channel.channel.replace('#', '') + '.json'
		stor_path = os.path.join(bot.storage_dir, filename)
		self.streams = StreamManager(stor_path)

	@ircbot.plugin.command('addstream')
	@error_prone
	def add_stream_cmd(self, msg):
		if len(msg.args) < 1:
			return None
		if not msg.user.is_admin:
			return None
		if self.streams.add_stream(msg.args[0]):
			return 'Stream added!'
		else:
			return 'Stream already added.'

	@ircbot.plugin.command('delstream')
	@error_prone
	def del_stream_cmd(self, msg):
		if len(msg.args) < 1:
			return None
		if not msg.user.is_admin:
			return None
		if self.streams.del_stream(msg.args[0]):
			return 'Stream deleted!'
		else:
			return '???'

	@ircbot.plugin.command('sub')
	@error_prone
	def subscribe_stream_cmd(self, msg):
		if len(msg.args) < 1:
			streams = self.streams.get_subscriptions(msg.user.host)
			if streams:
				return ', '.join(streams)
			else:
				return 'You are not subscribed to any streams'
		else:
			result = self.streams.add_subscriber(msg.user.host, msg.args[0])
			if result:
				return 'You are now subscribed to ' + result + '!'
			else:
				return 'You are already subscribed to that stream.'

	@ircbot.plugin.command('unsub')
	@error_prone
	def unsubscribe_stream_cmd(self, msg):
		if len(msg.args) < 1:
			return None
		result = self.streams.del_subscriber(msg.user.host, msg.args[0])
		if result:
			return 'You are no longer subscribed to ' + result + '.'
		else:
			return 'You are not subscribed to that stream.'

	@ircbot.plugin.command('streams')
	def list_streams_cmd(self, msg):
		streams = self.streams.get_online_streams()
		if streams:
			return ' - '.join([s.full_url for s in streams])
		else:
			return 'No streams online!'

	@ircbot.plugin.ticker
	def check_new_streams_tick(self):
		streams = self.streams.get_new_online_streams()
		if not streams:
			log.debug('No new online streams')
			return None

		retval = []

		for stream in streams:
			highlights = []
			for user, subs in self.streams.subs.items():
				if stream.url in subs:
					nick = self.channel.find_nick_from_host(user)
					if nick:
						highlights.append(nick)
			stream_str = 'New stream online: ' + stream.full_url
			if stream.title:
				stream_str += ' - ' + stream.title
			if highlights:
				stream_str += ' (' + ' '.join(highlights) + ')'
			retval.append(stream_str)

		return retval
