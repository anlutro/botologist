import unittest
from unittest import mock

from botologist import irc
from botologist import bot


class CommandMessageTest(unittest.TestCase):
	def test_commands_and_args_are_parsed(self):
		msg = irc.Message('nick!ident@host.com', '#channel', '!foo bar baz')
		cmd = bot.CommandMessage(msg)
		self.assertEqual('!foo', cmd.command)
		self.assertEqual(['bar', 'baz'], cmd.args)

class BotTest(unittest.TestCase):
	def test_matches_command_shorthand(self):
		channel = bot.Channel('#chan')
		def dummy_command_func(command):
			return 'test: '+command.command
		dummy_command_func._is_threaded = False
		channel.commands['asdf'] = dummy_command_func
		b = bot.Bot({'server': 'localhost:6667', 'storage_dir': '/tmp/botologist', 'admins': ['baz']})
		b.conn.channels['#chan'] = channel
		b._send_msg = mock.MagicMock()

		b._handle_privmsg(irc.Message('foo!bar@baz', '#chan', '!b'))
		b._send_msg.assert_not_called()
		b._handle_privmsg(irc.Message('foo!bar@baz', '#chan', '!a'))
		b._send_msg.assert_called_with('test: !asdf', '#chan')
		b._handle_privmsg(irc.Message('foo!bar@baz', '#chan', '!as'))
		b._send_msg.assert_called_with('test: !asdf', '#chan')
		b._handle_privmsg(irc.Message('foo!bar@baz', '#chan', '!asd'))
		b._send_msg.assert_called_with('test: !asdf', '#chan')
		b._handle_privmsg(irc.Message('foo!bar@baz', '#chan', '!asdf'))
		b._send_msg.assert_called_with('test: !asdf', '#chan')
		b._handle_privmsg(irc.Message('foo!bar@baz', '#chan', '!asdfg'))
		b._send_msg.assert_not_called()
