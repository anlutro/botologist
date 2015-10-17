import unittest
from unittest import mock

import os.path
import botologist.protocol.irc as irc
import botologist.bot


def make_channel(channel):
	return irc.Channel(channel)


class CommandMessageTest(unittest.TestCase):
	def test_commands_and_args_are_parsed(self):
		msg = irc.Message('nick!ident@host.com', '#channel', '!foo bar baz')
		cmd = botologist.bot.CommandMessage(msg)
		self.assertEqual('!foo', cmd.command)
		self.assertEqual(['bar', 'baz'], cmd.args)


class BotTest(unittest.TestCase):
	def make_bot(self):
		return botologist.bot.Bot({
			'server': 'localhost:6667',
			'storage_dir': os.path.join(os.path.dirname(__file__), 'tmp'),
		})

	def test_only_returns_online_admins(self):
		bot = self.make_bot()
		bot.admins = ['admin1.com']
		chan = make_channel('#chan')
		bot.add_channel(chan)
		self.assertEqual(set(), bot.get_admin_nicks())
		chan.add_user(irc.User('admin1', 'admin1.com'))
		self.assertEqual({'admin1'}, bot.get_admin_nicks())

	def test_matches_command_shorthand(self):
		channel = make_channel('#chan')
		def dummy_command_func(command):
			return 'test: '+command.command
		dummy_command_func._is_threaded = False
		channel.commands['asdf'] = dummy_command_func
		bot = self.make_bot()
		bot.admins = ['baz']
		bot.client.channels['#chan'] = channel
		bot._send_msg = mock.MagicMock()

		bot._handle_privmsg(irc.Message('foo!bar@baz', '#chan', '!b'))
		bot._send_msg.assert_not_called()
		bot._handle_privmsg(irc.Message('foo!bar@baz', '#chan', '!a'))
		bot._send_msg.assert_called_with('test: !asdf', '#chan')
		bot._handle_privmsg(irc.Message('foo!bar@baz', '#chan', '!as'))
		bot._send_msg.assert_called_with('test: !asdf', '#chan')
		bot._handle_privmsg(irc.Message('foo!bar@baz', '#chan', '!asd'))
		bot._send_msg.assert_called_with('test: !asdf', '#chan')
		bot._handle_privmsg(irc.Message('foo!bar@baz', '#chan', '!asdf'))
		bot._send_msg.assert_called_with('test: !asdf', '#chan')
		bot._handle_privmsg(irc.Message('foo!bar@baz', '#chan', '!asdfg'))
		bot._send_msg.assert_not_called()
