import logging
log = logging.getLogger(__name__)

import datetime
import json
import os.path
import re
import urllib.error
import urllib.parse

import botologist.http
import botologist.plugin
from plugins.streams import twitch, hitbox, error, cache


def filter_urls(urls, service):
	def extract_channel(url):
		parts = url.split('/')

		for (key, part) in enumerate(parts):
			if service in part:
				return parts[key + 1].lower()

	return [extract_channel(url) for url in urls if url is not None]


class Stream:
	rerun_searches = ('[re]', 'rebroadcast', 'rerun')
	empty_title_rebroadcast = ('twitch.tv/gsl', 'twitch.tv/wcs', 'twitch.tv/esl_sc2')

	def __init__(self, user, url, title='', game=None):
		self.user = user
		self.url = url
		self.full_url = 'http://' + url
		self.title = re.sub(r'\n', ' ', str(title))
		self.game = game

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
		return "<plugins.streams.Stream object '{}'>".format(self.url)

	@staticmethod
	def normalize_url(url, validate=True):
		"""Normalize a stream URL."""
		if 'twitch.tv' in url:
			url = url[url.index('twitch.tv'):]
		elif 'hitbox.tv' in url:
			url = url[url.index('hitbox.tv'):]
		else:
			raise error.InvalidStreamException('Only twitch and hitbox URLs allowed')

		segments = url.split('/')

		if validate and len(segments) < 2:
			raise error.InvalidStreamException('Missing parts of URL')

		if validate and re.match(r'^[\w\_]+$', segments[1]) is None:
			raise error.InvalidStreamException('Invalid characters in channel name')

		url = '/'.join(segments[:2])

		return url.lower()



class StreamManager:
	THROTTLE = 30 # seconds

	def __init__(self, stor_path, twitch_auth_token):
		self.streams = []
		self.subs = {}
		self.game_filter = None
		self._last_fetch = None
		self._cached_streams = cache.StreamCache()
		self.stor_path = stor_path
		self._read()
		self.twitch_auth_token = twitch_auth_token

	def _read(self):
		if not os.path.isfile(self.stor_path):
			self._write()
		with open(self.stor_path, 'r') as f:
			data = json.loads(f.read())
		self.streams = data.get('streams', [])
		self.subs = data.get('subscriptions', {})
		game_filter_pattern = data.get('game_filter')
		if game_filter_pattern:
			self.game_filter = re.compile(game_filter_pattern)
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
		data = {'streams': self.streams, 'subscriptions': self.subs, 'game_filter': None}
		if self.game_filter:
			data['game_filter'] = self.game_filter.pattern
		content = json.dumps(data, indent=2)
		with open(self.stor_path, 'w') as f:
			f.write(content)

	def _fetch_streams(self):
		"""Return a list of Stream objects for the streams in the array of urls
		that are currently live."""
		twitch_streams = [s for s in self.streams if 'twitch.tv' in s]
		twitch_streams = twitch.get_online_streams(
			twitch_streams,
			self.twitch_auth_token
		)

		hitbox_streams = [s for s in self.streams if 'hitbox.tv' in s]
		hitbox_streams = hitbox.get_online_streams(hitbox_streams)

		return twitch_streams + hitbox_streams

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
			raise error.StreamNotFoundException('Error: Stream not found: ' + url)

		if len(streams) > 1:
			# if there is an exact match, return that
			if url in streams:
				return url

			# try a bit harder to find an exact match
			exact_streams = [s for s in streams if s.endswith('/' + url)]
			if len(exact_streams) == 1:
				return exact_streams[0]

			# else, raise an exception
			raise error.AmbiguousStreamException(streams)

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
			# user is already subscribed
			return False

		self.subs[host].append(url)
		self._write()

		return url

	def del_subscriber(self, host, url):
		url = self.find_stream(url)
		if host not in self.subs or url not in self.subs[host]:
			# user is not subscribed to that stream
			return False

		self.subs[host].remove(url)
		self._write()

		return url

	def get_subscriptions(self, host):
		if host not in self.subs:
			return None

		return [stream for stream in self.subs[host] if stream in self.streams]

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
			streams = self._fetch_streams()
			self._cached_streams.push(streams)
		except urllib.error.URLError:
			log.warning('Could not fetch online streams!', exc_info=True)

		self._last_fetch = now

		return self._cached_streams.get_all()

	def get_new_online_streams(self):
		if not self.streams:
			return None

		try:
			streams = self._fetch_streams()
		except urllib.error.URLError:
			log.warning('Could not fetch new online streams!', exc_info=True)
			return False

		diff = []

		if self._cached_streams.initiated:
			cached_stream_urls = [stream.url for stream
				in self._cached_streams.get_all()
				if not stream.is_rebroadcast]
			diff = [stream for stream in streams
				if stream.url not in cached_stream_urls
				and not stream.is_rebroadcast]
			log.debug('Cached streams: %d - Online streams: %d - Diff: %d',
				len(cached_stream_urls), len(streams), len(diff))

		self._cached_streams.push(streams)
		self._last_fetch = datetime.datetime.now()

		return diff


class StreamsPlugin(botologist.plugin.Plugin):
	def __init__(self, bot, channel):
		if 'twitch_auth_token' not in bot.config:
			raise ValueError('Must add twitch_auth_token to config.yml to use stream plugin!')
		super().__init__(bot, channel)
		filename = 'streams_' + channel.channel.replace('#', '') + '.json'
		stor_path = os.path.join(bot.storage_dir, filename)
		self.streams = StreamManager(stor_path, bot.config['twitch_auth_token'])

	@botologist.plugin.command('addstream')
	@error.return_streamerror_message
	def add_stream_cmd(self, msg):
		'''Add a stream. Admins only.'''
		if len(msg.args) < 1:
			return None
		if not msg.user.is_admin:
			return None
		if self.streams.add_stream(msg.args[0]):
			return 'Stream added!'
		else:
			return 'Stream already added.'

	@botologist.plugin.command('delstream')
	@error.return_streamerror_message
	def del_stream_cmd(self, msg):
		'''Delete a stream. Admins only.'''
		if len(msg.args) < 1:
			return None
		if not msg.user.is_admin:
			return None

		stream = self.streams.del_stream(msg.args[0])

		return 'Stream deleted: {}'.format(stream)

	@botologist.plugin.command('sub')
	@error.return_streamerror_message
	def subscribe_stream_cmd(self, msg):
		'''Add yourself as a subscriber for a stream.'''
		if 'irccloud' in msg.user.host:
			return 'irccloud users cannot subscribe! try /mode {} +x'.format(
				msg.user.nick)
		if len(msg.args) < 1:
			streams = self.streams.get_subscriptions(msg.user.host)
			if streams:
				return ', '.join(streams)
			else:
				return 'You are not subscribed to any streams'
		else:
			result = self.streams.add_subscriber(msg.user.host, msg.args[0])
			if result:
				return 'You are now subscribed to {}!'.format(result)
			else:
				return 'You are already subscribed to that stream.'

	@botologist.plugin.command('unsub')
	@error.return_streamerror_message
	def unsubscribe_stream_cmd(self, msg):
		'''Remove yourself as a subscriber for a stream.'''
		if len(msg.args) < 1:
			return None
		result = self.streams.del_subscriber(msg.user.host, msg.args[0])
		if result:
			return 'You are no longer subscribed to {}.'.format(result)
		else:
			return 'You are not subscribed to that stream.'

	@botologist.plugin.command('streams', alias='s', threaded=True)
	def list_streams_cmd(self, msg):
		'''Show currently online streams.'''
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

	@botologist.plugin.ticker()
	def check_new_streams_tick(self):
		streams = self.streams.get_new_online_streams()

		if not streams:
			log.debug('No new online streams')
			return None

		retval = []

		for stream in streams:
			if stream.is_rebroadcast:
				continue

			if self.streams.game_filter and stream.game:
				if not self.streams.game_filter.match(stream.game.lower()):
					continue

			highlights = []
			for user_id, subs in self.streams.subs.items():
				if stream.url in subs:
					user = self.channel.find_user(identifier=user_id)
					if user:
						highlights.append(user.name)
			stream_str = 'New stream online: ' + stream.full_url
			if stream.title:
				stream_str += ' - ' + stream.title
			if stream.game and stream.game not in stream.title:
				stream_str += ' [game: {}]'.format(stream.game)
			if highlights:
				stream_str += ' ({})'.format(' '.join(highlights))
			retval.append(stream_str)

		return retval


	@botologist.plugin.command('addstreamfilter')
	@error.return_streamerror_message
	def filter_on_games_cmd(self, msg):
		'''Filter streams on specific games via regular expressions.'''
		if len(msg.args) < 1:
			if self.streams.game_filter:
				return 'Streams are filtered on: ' + self.streams.game_filter.pattern
			return 'There is no stream game filter active at this moment.'
		if not msg.user.is_admin:
			return None
		else:
			self.streams.game_filter = re.compile(' '.join(msg.args))
			return 'Now filtering streams on: ' + self.streams.game_filter.pattern


	@botologist.plugin.command('delstreamfilter')
	@error.return_streamerror_message
	def delete_filter_on_games_cmd(self, msg):
		'''Delete the filtering of certain stream games.'''
		if not msg.user.is_admin:
			return None
		if self.streams.game_filter:
			self.streams.game_filter = None
			return 'Stream game filter deleted!'
		return 'There is no stream game filter active at this moment.'

