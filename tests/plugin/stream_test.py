import unittest
from tests.plugin import PluginTestCase

from ircbot.plugin.streams import Stream, StreamCache, StreamManager, StreamsPlugin

class StreamTest(unittest.TestCase):
	def test_equals(self):
		s = Stream('foobar', 'twitch.tv/foobar')
		self.assertEqual('twitch.tv/foobar', s)

	def test_from_twitch_data(self):
		data = {'channel': {'name': 'foobar'}}
		s = Stream.from_twitch_data(data)
		self.assertEqual('foobar', s.user)
		self.assertEqual('twitch.tv/foobar', s.url)
		self.assertEqual('http://twitch.tv/foobar', s.full_url)

	def test_from_hitbox_data(self):
		data = {'media_user_name': 'foobar'}
		s = Stream.from_hitbox_data(data)
		self.assertEqual('foobar', s.user)
		self.assertEqual('hitbox.tv/foobar', s.url)
		self.assertEqual('http://hitbox.tv/foobar', s.full_url)

	def test_normalize_url(self):
		self.assertEqual('twitch.tv/foobar', Stream.normalize_url('http://twitch.tv/foobar'))
		self.assertEqual('twitch.tv/foobar', Stream.normalize_url('http://www.twitch.tv/foobar'))
		self.assertEqual('twitch.tv/foobar', Stream.normalize_url('http://de.twitch.tv/foobar'))
		self.assertEqual('twitch.tv/foobar', Stream.normalize_url('http://twitch.tv/foobar/'))
		self.assertEqual('twitch.tv/foobar', Stream.normalize_url('http://twitch.tv/foobar/asdf'))
		self.assertEqual('twitch.tv/foobar', Stream.normalize_url('https://twitch.tv/foobar'))

	def test_is_rebroadcast(self):
		data = {'channel': {'name': 'foobar', 'status': 'asdf'}}
		s = Stream.from_twitch_data(data)
		self.assertEqual(False, s.is_rebroadcast)

		data = {'channel': {'name': 'foobar', 'status': 'asdf rebroadcast asdf'}}
		s = Stream.from_twitch_data(data)
		self.assertEqual(True, s.is_rebroadcast)

		data = {'channel': {'name': 'foobar', 'status': '[re] asdf'}}
		s = Stream.from_twitch_data(data)
		self.assertEqual(True, s.is_rebroadcast)

		data = {'channel': {'name': 'gsl', 'status': 'asdf'}}
		s = Stream.from_twitch_data(data)
		self.assertEqual(False, s.is_rebroadcast)

		data = {'channel': {'name': 'gsl', 'status': ''}}
		s = Stream.from_twitch_data(data)
		self.assertEqual(True, s.is_rebroadcast)

		data = {'channel': {'name': 'wcs', 'status': 'asdf'}}
		s = Stream.from_twitch_data(data)
		self.assertEqual(False, s.is_rebroadcast)

		data = {'channel': {'name': 'wcs', 'status': ''}}
		s = Stream.from_twitch_data(data)
		self.assertEqual(True, s.is_rebroadcast)

class StreamCacheTest(unittest.TestCase):
	def test_init(self):
		sc = StreamCache()
		self.assertFalse(sc.initiated)
		self.assertEqual(set(), sc.get_all())

	def test_cache_keeps_values_for_two_pushes(self):
		sc = StreamCache()

		sc.push(['a', 'b'])
		self.assertEqual(set(['a', 'b']), sc.get_all())
		self.assertTrue('a' in sc)
		self.assertTrue('b' in sc)

		sc.push([])
		self.assertEqual(set(['a', 'b']), sc.get_all())
		self.assertTrue('a' in sc)
		self.assertTrue('b' in sc)

		sc.push([])
		self.assertEqual(set([]), sc.get_all())
		self.assertFalse('a' in sc)
		self.assertFalse('b' in sc)

class StreamManagerTest(unittest.TestCase):
	pass

class StreamPluginTest(unittest.TestCase):
	pass
