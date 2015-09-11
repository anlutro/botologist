import unittest
from unittest import mock

import os.path
import botologist.irc
import botologist.bot


class CommandMessageTest(unittest.TestCase):
	def test_commands_and_args_are_parsed(self):
		msg = botologist.irc.Message('nick!ident@host.com', '#channel', '!foo bar baz')
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
		chan = botologist.bot.Channel('#chan')
		bot.add_channel(chan)
		self.assertEqual(set(), bot.get_admin_nicks())
		chan.add_user(botologist.irc.User('admin1', 'admin1.com'))
		self.assertEqual({'admin1'}, bot.get_admin_nicks())

	def test_matches_command_shorthand(self):
		channel = botologist.bot.Channel('#chan')
		def dummy_command_func(command):
			return 'test: '+command.command
		dummy_command_func._is_threaded = False
		channel.commands['asdf'] = dummy_command_func
		bot = self.make_bot()
		bot.admins = ['baz']
		bot.conn.channels['#chan'] = channel
		bot._send_msg = mock.MagicMock()

		bot._handle_privmsg(botologist.irc.Message('foo!bar@baz', '#chan', '!b'))
		bot._send_msg.assert_not_called()
		bot._handle_privmsg(botologist.irc.Message('foo!bar@baz', '#chan', '!a'))
		bot._send_msg.assert_called_with('test: !asdf', '#chan')
		bot._handle_privmsg(botologist.irc.Message('foo!bar@baz', '#chan', '!as'))
		bot._send_msg.assert_called_with('test: !asdf', '#chan')
		bot._handle_privmsg(botologist.irc.Message('foo!bar@baz', '#chan', '!asd'))
		bot._send_msg.assert_called_with('test: !asdf', '#chan')
		bot._handle_privmsg(botologist.irc.Message('foo!bar@baz', '#chan', '!asdf'))
		bot._send_msg.assert_called_with('test: !asdf', '#chan')
		bot._handle_privmsg(botologist.irc.Message('foo!bar@baz', '#chan', '!asdfg'))
		bot._send_msg.assert_not_called()
