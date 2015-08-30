import unittest

from botologist.irc import Server, Channel, User, Message


class IrcServerTest(unittest.TestCase):
	def test_init(self):
		srv = Server('irc.host.com:6667')
		self.assertEqual('irc.host.com', srv.host)
		self.assertEqual(6667, srv.port)

	def test_add_channel(self):
		srv = Server('irc.host.com:6667')
		chan = Channel('#foobar')
		srv.add_channel(chan)
		self.assertEqual(srv.channels['#foobar'], chan)


class IrcChannelTest(unittest.TestCase):
	def test_init(self):
		chan = Channel('#foobar')
		self.assertEqual('#foobar', chan.channel)
		chan = Channel('foobar')
		self.assertEqual('#foobar', chan.channel)

	def test_add_user(self):
		chan = Channel('#foobar')
		user = User('nick', 'ident@host.com')
		chan.add_user(user)
		self.assertEqual(user.nick, chan.host_map[user.host])
		self.assertEqual(user.host, chan.nick_map[user.nick])
		self.assertEqual(user.nick, chan.find_nick_from_host(user.host))
		self.assertEqual(False, chan.find_nick_from_host('asdsaff'))
		self.assertEqual(user.host, chan.find_host_from_nick(user.nick))
		self.assertEqual(False, chan.find_host_from_nick('asdsaff'))

	def test_remove_user(self):
		chan = Channel('#foobar')
		user = User('nick', 'ident@host.com')
		chan.add_user(user)
		self.assertEqual(user.nick, chan.find_nick_from_host(user.host))
		chan.remove_user(host=user.host)
		self.assertEqual(False, chan.find_nick_from_host(user.host))
		chan.add_user(user)
		self.assertEqual(user.nick, chan.find_nick_from_host(user.host))
		chan.remove_user(nick=user.nick)
		self.assertEqual(False, chan.find_nick_from_host(user.host))

	def test_update_nick(self):
		chan = Channel('#foobar')
		user = User('oldnick', 'ident@host.com')
		chan.add_user(user)
		self.assertEqual(user.nick, chan.find_nick_from_host(user.host))
		self.assertEqual(user.host, chan.find_host_from_nick('oldnick'))
		chan.update_nick(user, 'newnick')
		self.assertEqual(False, chan.find_host_from_nick('oldnick'))
		self.assertEqual('newnick', chan.find_nick_from_host(user.host))
		self.assertEqual(user.host, chan.find_host_from_nick('newnick'))


class IrcUserTest(unittest.TestCase):
	def test_strips_tilde(self):
		user = User('foo_bar', '@bar.baz', '~foo')
		self.assertEqual('foo_bar', user.nick)
		self.assertEqual('bar.baz', user.host)
		self.assertEqual('foo', user.ident)

	def test_from_ircformat(self):
		strings = (
			'foo_bar!~foo@bar.baz',
			':foo_bar!~foo@bar.baz'
		)
		for string in strings:
			user = User.from_ircformat('foo_bar!~foo@bar.baz')
			self.assertEqual('foo_bar', user.nick)
			self.assertEqual('bar.baz', user.host)
			self.assertEqual('foo', user.ident)


class IrcMessageTest(unittest.TestCase):
	def do_assertions(self, msg):
		self.assertIsInstance(msg.user, User)
		self.assertEqual('#chan', msg.target)
		self.assertEqual('foo bar baz', msg.message)
		self.assertEqual(['foo', 'bar', 'baz'], msg.words)

	def test_init(self):
		msg = Message('foo!foo@bar.baz', '#chan', 'foo bar baz')
		self.do_assertions(msg)

	def test_from_privmsg(self):
		msg = Message.from_privmsg(':foo!foo@bar.baz PRIVMSG #chan :foo bar baz')
		self.do_assertions(msg)

	def test_is_private(self):
		msg = Message('foo!foo@bar.baz', '#chan', 'foo bar baz')
		self.assertFalse(msg.is_private)
		msg = Message('foo!foo@bar.baz', 'nick', 'foo bar baz')
		self.assertTrue(msg.is_private)
