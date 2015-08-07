import unittest
import os.path
from tests.plugin import PluginTestCase

import ircbot.plugin.streams as streams

class StreamTest(unittest.TestCase):
	def test_equals(self):
		s = streams.Stream('foobar', 'twitch.tv/foobar')
		self.assertEqual('twitch.tv/foobar', s)

	def test_from_twitch_data(self):
		data = {'channel': {'name': 'foobar'}}
		s = streams.Stream.from_twitch_data(data)
		self.assertEqual('foobar', s.user)
		self.assertEqual('twitch.tv/foobar', s.url)
		self.assertEqual('http://twitch.tv/foobar', s.full_url)

	def test_from_hitbox_data(self):
		data = {'media_user_name': 'foobar'}
		s = streams.Stream.from_hitbox_data(data)
		self.assertEqual('foobar', s.user)
		self.assertEqual('hitbox.tv/foobar', s.url)
		self.assertEqual('http://hitbox.tv/foobar', s.full_url)

	def test_normalize_url(self):
		f = streams.Stream.normalize_url
		self.assertEqual('twitch.tv/foobar', f('http://twitch.tv/foobar'))
		self.assertEqual('twitch.tv/foobar', f('http://www.twitch.tv/foobar'))
		self.assertEqual('twitch.tv/foobar', f('http://de.twitch.tv/foobar'))
		self.assertEqual('twitch.tv/foobar', f('http://twitch.tv/foobar/'))
		self.assertEqual('twitch.tv/foobar', f('http://twitch.tv/foobar/asdf'))
		self.assertEqual('twitch.tv/foobar', f('https://twitch.tv/foobar'))

	def test_is_rebroadcast(self):
		data = {'channel': {'name': 'foobar', 'status': 'asdf'}}
		s = streams.Stream.from_twitch_data(data)
		self.assertEqual(False, s.is_rebroadcast)

		data = {'channel': {'name': 'foobar', 'status': 'asdf rebroadcast asdf'}}
		s = streams.Stream.from_twitch_data(data)
		self.assertEqual(True, s.is_rebroadcast)

		data = {'channel': {'name': 'foobar', 'status': '[re] asdf'}}
		s = streams.Stream.from_twitch_data(data)
		self.assertEqual(True, s.is_rebroadcast)

		data = {'channel': {'name': 'gsl', 'status': 'asdf'}}
		s = streams.Stream.from_twitch_data(data)
		self.assertEqual(False, s.is_rebroadcast)

		data = {'channel': {'name': 'gsl', 'status': ''}}
		s = streams.Stream.from_twitch_data(data)
		self.assertEqual(True, s.is_rebroadcast)

		data = {'channel': {'name': 'wcs', 'status': 'asdf'}}
		s = streams.Stream.from_twitch_data(data)
		self.assertEqual(False, s.is_rebroadcast)

		data = {'channel': {'name': 'wcs', 'status': ''}}
		s = streams.Stream.from_twitch_data(data)
		self.assertEqual(True, s.is_rebroadcast)

class StreamCacheTest(unittest.TestCase):
	def test_init(self):
		sc = streams.StreamCache()
		self.assertFalse(sc.initiated)
		self.assertEqual(set(), sc.get_all())

	def test_cache_keeps_values_for_two_pushes(self):
		sc = streams.StreamCache()

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
	file_path = os.path.dirname(os.path.dirname(__file__)) + '/tmp/stream_test.json'

	def setUp(self):
		super().setUp()
		if os.path.isfile(self.file_path):
			os.remove(self.file_path)

	def tearDown(self):
		if os.path.isfile(self.file_path):
			os.remove(self.file_path)
		super().tearDown()

	def test_can_add_and_remove_streams(self):
		sm = streams.StreamManager(self.file_path)
		with self.assertRaises(streams.StreamNotFoundException):
			sm.find_stream('asdf')
		sm.add_stream('twitch.tv/asdf')
		self.assertEqual('twitch.tv/asdf', sm.find_stream('asdf'))
		sm.del_stream('asdf')
		with self.assertRaises(streams.StreamNotFoundException):
			sm.find_stream('asdf')

	def test_streams_are_persisted(self):
		sm = streams.StreamManager(self.file_path)
		sm.add_stream('twitch.tv/asdf')
		sm = streams.StreamManager(self.file_path)
		self.assertEqual('twitch.tv/asdf', sm.find_stream('asdf'))

	def test_can_subscribe_to_stream(self):
		sm = streams.StreamManager(self.file_path)
		sm.add_stream('twitch.tv/asdf')
		sm.add_subscriber('host.com', 'asdf')
		self.assertEqual(['twitch.tv/asdf'], sm.get_subscriptions('host.com'))

	def test_subscription_persists_when_stream_removed(self):
		sm = streams.StreamManager(self.file_path)
		sm.add_stream('twitch.tv/asdf')
		sm.add_subscriber('host.com', 'asdf')
		sm.del_stream('asdf')
		self.assertEqual(['twitch.tv/asdf'], sm.get_subscriptions('host.com'))

class StreamPluginTest(unittest.TestCase):
	pass
