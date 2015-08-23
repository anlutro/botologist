import logging
log = logging.getLogger(__name__)

import datetime
import json
import os.path
import re
import urllib.error
import urllib.parse

import ircbot.http
import ircbot.plugin


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


class Stream:
	rerun_searches = ('[re]', 'rebroadcast', 'rerun')
	empty_title_rebroadcast = ('twitch.tv/gsl', 'twitch.tv/wcs', 'twitch.tv/esl_sc2')

	def __init__(self, user, url, title=''):
		self.user = user
		self.url = url
		self.full_url = 'http://' + url
		self.title = re.sub(r'\n', ' ', str(title))

		title_lower = self.title.lower()
		if any(s in title_lower for s in self.rerun_searches):
			self.is_rebroadcast = True
		elif url in self.empty_title_rebroadcast and not title:
			self.is_rebroadcast = True
		else:
			self.is_rebroadcast = False

	def __eq__(self, other):
		if isinstance(other, self.__class__):
			return self.url == other.url
		elif isinstance(other, str):
			# assume it is a valid url
			return self.url == other
		else:
			raise ValueError('Cannot compare Stream with {type}'.format(
				type=type(other).__name__))

	def __ne__(self, other):
		return not self.__eq__(other)

	def __hash__(self):
		return hash(self.url)

	def __repr__(self):
		return '<plugins.streams.Stream object \'{url}\'>'.format(url=self.url)

	@classmethod
	def from_twitch_data(cls, data):
		channel = data.get('channel', {}).get('name', '').lower()
		title = data.get('channel', {}).get('status', '')
		obj = cls(channel, 'twitch.tv/' + channel, title)
		return obj

	@classmethod
	def from_hitbox_data(cls, data):
		channel = data.get('media_user_name', '').lower()
		title = data.get('media_status')
		return cls(channel, 'hitbox.tv/' + channel, title)

	@staticmethod
	def normalize_url(url, validate=True):
		"""Normalize a stream URL."""
		if 'twitch.tv' in url:
			url = url[url.index('twitch.tv'):]
		elif 'hitbox.tv' in url:
			url = url[url.index('hitbox.tv'):]
		else:
			raise InvalidStreamException('Only twitch and hitbox URLs allowed')

		segments = url.split('/')

		if validate and len(segments) < 2:
			raise InvalidStreamException('Missing parts of URL')

		if validate and re.match(r'^[\w\_]+$', segments[1]) is None:
			raise InvalidStreamException('Invalid characters in channel name')

		url = '/'.join(segments[:2])

		return url.lower()


def _fetch_streams(streams):
	"""Return an array of Stream objects for the streams in the array of urls
	that are currently live."""
	twitch_streams = _fetch_twitch([s for s in streams if 'twitch.tv' in s])
	hitbox_streams = _fetch_hitbox([s for s in streams if 'hitbox.tv' in s])
	return twitch_streams + hitbox_streams


def _fetch_twitch_data(channels):
	url = 'https://api.twitch.tv/kraken/streams'
	log.debug('Fetching from %s: %s', url, ', '.join(channels))

	query_params = {'channel': ','.join(channels)}
	response = ircbot.http.get(url, query_params=query_params)
	contents = response.read().decode()
	response.close()
	return json.loads(contents)


def _fetch_twitch(urls):
	"""From a collection of URLs, get the ones that are live on twitch.tv."""
	channels = [
		_extract_channel(url, 'twitch.tv')
		for url in urls if url is not None
	]

	if not channels:
		return []

	data = _fetch_twitch_data(channels)
	log.debug('{streams} online twitch.tv streams'.format(
		streams=len(data['streams'])))

	return [
		Stream.from_twitch_data(stream)
		for stream in data['streams']
	]


def _fetch_hitbox_data(channels):
	channels = [urllib.parse.quote(channel) for channel in channels]
	url = 'http://api.hitbox.tv/media/live/' + ','.join(channels)
	log.debug('Fetching ' + url)

	response = ircbot.http.get(url)
	contents = response.read().decode()
	response.close()

	if contents == 'no_media_found':
		return []

	return json.loads(contents)


def _fetch_hitbox(urls):
	"""From a collection of URLs, get the ones that are live on hitbox.tv."""
	channels = [
		_extract_channel(url, 'hitbox.tv')
		for url in urls if url is not None
	]

	if not channels:
		return []

	data = _fetch_hitbox_data(channels)

	if not data:
		return data

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


class StreamCache:
	def __init__(self):
		self.initiated = False
		self.new_cache = []
		self.old_cache = []

	def push(self, streams):
		assert isinstance(streams, list)
		self.old_cache = self.new_cache
		self.new_cache = streams
		if not self.initiated:
			self.initiated = True

	def get_all(self):
		return set(self.new_cache + self.old_cache)

	def __contains__(self, stream):
		return stream in self.new_cache or stream in self.old_cache


class StreamManager:
	THROTTLE = 30 # seconds

	def __init__(self, stor_path):
		self.streams = []
		self.subs = {}
		self._last_fetch = None
		self._cached_streams = StreamCache()
		self.stor_path = stor_path
		self._read()

	def _read(self):
		if not os.path.isfile(self.stor_path):
			self._write()
		with open(self.stor_path, 'r') as f:
			data = json.loads(f.read())
		self.streams = data.get('streams', [])
		self.subs = data.get('subscriptions', {})
		self._repair_subs_file()

	def _repair_subs_file(self):
		changed = False
		new_subs = {}
		for host, subs in self.subs.items():
			if '@' in host:
				host = host[host.index('@')+1:]
				changed = True
			new_subs[host] = subs

		if changed:
			self.subs = new_subs
			self._write()

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
		url = Stream.normalize_url(url)

		if url in self.streams:
			return False

		self.streams.append(url)
		self._write()
		return True

	def find_stream(self, url):
		url = url.lower()

		if 'twitch.tv' in url or 'hitbox.tv' in url:
			url = Stream.normalize_url(url)

		streams = [s for s in self.streams if url in s]

		if not streams:
			raise StreamNotFoundException('Error: Stream not found: ' + url)

		if len(streams) > 1:
			# if there is an exact match, return that
			if url in streams:
				return url

			# try a bit harder to find an exact match
			exact_streams = [s for s in streams if s.endswith('/' + url)]
			if len(exact_streams) == 1:
				return exact_streams[0]

			# else, raise an exception
			raise AmbiguousStreamException(streams)

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
			if diff.seconds < self.THROTTLE:
				log.debug('Throttled, returning cached streams')
				return self._cached_streams.get_all()

		try:
			streams = _fetch_streams(self.streams)
			self._cached_streams.push(streams)
		except urllib.error.URLError:
			log.warning('Could not fetch online streams!', exc_info=True)

		self._last_fetch = now

		return self._cached_streams.get_all()

	def get_new_online_streams(self):
		if not self.streams:
			return None

		try:
			streams = _fetch_streams(self.streams)
		except urllib.error.URLError:
			log.warning('Could not fetch new online streams!', exc=True)
			return False

		diff = []

		if self._cached_streams.initiated:
			cached_stream_urls = [stream.url for stream in self._cached_streams.get_all()
				if not stream.is_rebroadcast]
			diff = [stream for stream in streams
				if stream.url not in cached_stream_urls
				and not stream.is_rebroadcast]
			log.debug('Cached streams: {cached} - Online streams: {online} - Diff: {diff}'.format(
				cached=len(cached_stream_urls), online=len(streams), diff=len(diff)))

		self._cached_streams.push(streams)
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

		stream = self.streams.del_stream(msg.args[0])
		if stream:
			return 'Stream deleted: {}'.format(stream)
		else:
			return '???'

	@ircbot.plugin.command('sub')
	@error_prone
	def subscribe_stream_cmd(self, msg):
		if 'irccloud' in msg.user.host:
			return 'irccloud users cannot subscribe! try /mode {} +x'.format(msg.user.nick)
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

	@ircbot.plugin.command('streams', threaded=True)
	def list_streams_cmd(self, msg):
		streams = self.streams.get_online_streams()
		if not streams:
			return 'No streams online!'

		stream_strings = []
		for stream in streams:
			s = stream.full_url
			if stream.is_rebroadcast:
				s += ' [R]'
			stream_strings.append(s)

		return ' - '.join(stream_strings)

	@ircbot.plugin.ticker()
	def check_new_streams_tick(self):
		streams = self.streams.get_new_online_streams()

		if not streams:
			log.debug('No new online streams')
			return None

		retval = []

		for stream in streams:
			if stream.is_rebroadcast:
				continue

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
