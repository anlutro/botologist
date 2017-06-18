import logging
log = logging.getLogger(__name__)

import re

import spotipy
import spotipy.client
from spotipy.oauth2 import SpotifyClientCredentials

import botologist.plugin


def _get_artist_str(artists):
	return ', '.join(artist['name'] for artist in artists)


class Spotify:
	def __init__(self, spotify=None):
		self.spotipy = spotify or spotipy.Spotify()

	def get_artist(self, artist_id):
		data = self.spotipy.artist(artist_id)
		return data['name'], ', '.join(data['genres'])

	def get_album(self, album_id):
		data = self.spotipy.album(album_id)
		return _get_artist_str(data['artists']), data['name']

	def get_track(self, track_id):
		data = self.spotipy.track(track_id)
		return _get_artist_str(data['artists']), data['album']['name'], data['name']

	def get_info_str(self, item_type, item_id):
		log.info('looking up spotify:%s:%s', item_type, item_id)
		try:
			if item_type == 'artist':
				return '%s (%s)' % self.get_artist(item_id)
			elif item_type == 'album':
				return '%s - %s' % self.get_album(item_id)
			elif item_type == 'track':
				return '%s - %s - %s' % self.get_track(item_id)
			else:
				raise ValueError('unknown item type: %r' % item_type)
		except spotipy.client.SpotifyException as e:
			log.warning('spotipy threw an exception while looking up spotify:%s:%s',
				item_type, item_id, exc_info=True)
			return


class SpotifyPlugin(botologist.plugin.Plugin):
	pattern = re.compile(r'(open\.spotify\.com\/|spotify:)(artist|album|track)[:/](\w+)')

	def __init__(self, bot, channel):
		super().__init__(bot, channel)
		ccm = None
		if bot.config.get('spotify_client_id'):
			ccm = SpotifyClientCredentials(
				client_id=bot.config.get('spotify_client_id'),
				client_secret=bot.config.get('spotify_client_secret'),
			)
		sp = spotipy.Spotify(client_credentials_manager=ccm)
		self.spotify = Spotify(sp)

	@botologist.plugin.reply(threaded=True)
	def convert(self, msg):
		ret = []

		for match in self.pattern.finditer(msg.message):
			info = self.spotify.get_info_str(match.group(2), match.group(3))
			if info:
				ret.append('[spotify] %s' % info)

		if len(ret) < 3:
			return ret
