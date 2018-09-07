import unittest

from botologist.protocol import irc


class StripFormattingTest(unittest.TestCase):
    def test_strip_irc_formatting(self):
        self.assertEqual("foo bar", irc.strip_irc_formatting("\x0301,02foo\x03 bar"))
        self.assertEqual("foo bar", irc.strip_irc_formatting("\x0301,02foo\x0F bar"))
        self.assertEqual("foo bar", irc.strip_irc_formatting("\x02foo\x0F \x16bar\x0F"))


class DecodeTest(unittest.TestCase):
    def test_decode_lines(self):
        self.assertEqual(["foo", "bar"], list(irc.decode_lines(b"foo\r\nbar")))


class IrcServerTest(unittest.TestCase):
    def test_init(self):
        srv = irc.Server("irc.host.com:6667")
        self.assertEqual("irc.host.com", srv.host)
        self.assertEqual(6667, srv.port)

    def test_init_without_port(self):
        srv = irc.Server("irc.host.com")
        self.assertEqual("irc.host.com", srv.host)
        self.assertEqual(6667, srv.port)


class IrcChannelTest(unittest.TestCase):
    def test_init(self):
        chan = irc.Channel("#foobar")
        self.assertEqual("#foobar", chan.name)
        chan = irc.Channel("foobar")
        self.assertEqual("#foobar", chan.name)

    def test_add_user(self):
        chan = irc.Channel("#foobar")
        user = irc.User("nick", "host.com", "ident")
        chan.add_user(user)
        self.assertEqual(user.nick, chan.find_nick_from_host(user.host))
        self.assertEqual(None, chan.find_nick_from_host("asdsaff"))
        self.assertEqual(user.host, chan.find_host_from_nick(user.nick))
        self.assertEqual(None, chan.find_host_from_nick("asdsaff"))

    def test_remove_user(self):
        chan = irc.Channel("#foobar")
        user = irc.User("nick", "host.com", "ident")
        chan.add_user(user)
        self.assertEqual(user.nick, chan.find_nick_from_host(user.host))
        chan.remove_user(identifier=user.host)
        self.assertEqual(None, chan.find_nick_from_host(user.host))
        chan.add_user(user)
        self.assertEqual(user.nick, chan.find_nick_from_host(user.host))
        chan.remove_user(name=user.nick)
        self.assertEqual(None, chan.find_nick_from_host(user.host))

    def test_update_nick(self):
        chan = irc.Channel("#foobar")
        user = irc.User("oldnick", "host.com", "ident")
        chan.add_user(user)
        self.assertEqual(user.nick, chan.find_nick_from_host(user.host))
        self.assertEqual(user.host, chan.find_host_from_nick("oldnick"))
        user.name = "newnick"
        self.assertEqual(None, chan.find_host_from_nick("oldnick"))
        self.assertEqual("newnick", chan.find_nick_from_host(user.host))
        self.assertEqual(user.host, chan.find_host_from_nick("newnick"))

    def test_issue66(self):
        chan = irc.Channel("#foobar")
        user1 = irc.User("nick", "host.com", "ident")
        chan.add_user(user1)
        user2 = irc.User("nick_", "host.com", "ident")
        chan.add_user(user2)
        chan.remove_user(name=user1.nick, identifier=user1.host)
        user2.name = "nick"
        chan.remove_user(name=user2.nick, identifier=user2.host)


class IrcUserTest(unittest.TestCase):
    def test_strips_tilde(self):
        user = irc.User("foo_bar", "bar.baz", "~foo")
        self.assertEqual("foo_bar", user.nick)
        self.assertEqual("bar.baz", user.host)
        self.assertEqual("foo", user.ident)

    def test_from_ircformat(self):
        strings = ("foo_bar!~foo@bar.baz", ":foo_bar!~foo@bar.baz")
        for string in strings:
            user = irc.User.from_ircformat("foo_bar!~foo@bar.baz")
            self.assertEqual("foo_bar", user.nick)
            self.assertEqual("bar.baz", user.host)
            self.assertEqual("foo", user.ident)


class IrcMessageTest(unittest.TestCase):
    def do_assertions(self, msg):
        self.assertIsInstance(msg.user, irc.User)
        self.assertEqual("#chan", msg.target)
        self.assertEqual("foo bar baz", msg.message)
        self.assertEqual(["foo", "bar", "baz"], msg.words)

    def test_init(self):
        msg = irc.Message("foo!foo@bar.baz", "#chan", "foo bar baz")
        self.do_assertions(msg)

    def test_from_privmsg(self):
        msg = irc.Message.from_privmsg(":foo!foo@bar.baz PRIVMSG #chan :foo bar baz")
        self.do_assertions(msg)

    def test_is_private(self):
        msg = irc.Message("foo!foo@bar.baz", "#chan", "foo bar baz")
        self.assertFalse(msg.is_private)
        msg = irc.Message("foo!foo@bar.baz", "nick", "foo bar baz")
        self.assertTrue(msg.is_private)
