import unittest
from unittest import mock
from plugins import spotify

class CommandMessageTest(unittest.TestCase):
	def test_track(self):
		track_data = {
			'artists': [{'name': 'artist'}],
			'name': 'track',
			'album': {'name': 'album'},
		}
		spotipy = mock.MagicMock()
		spotipy.track = mock.MagicMock(return_value=track_data)
		sp = spotify.Spotify(spotipy)
		ret = sp.get_info_str('track', 'asdf')
		self.assertEqual('artist - track [album: album]', ret)
