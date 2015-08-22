import unittest
import os.path

import ircbot
import ircbot.irc as irc
import ircbot.bot as bot

class PluginTestCase(unittest.TestCase):
	cfg = {}

	def setUp(self):
		self.channel = irc.Channel('#test')
		self.bot = bot.Bot({
			'storage_dir': '/tmp/ircbot',
			'bot': {
				'server': 'localhost:6667',
			},
		})
		self.bot.config.update(self.cfg)
		self.plugin = self.create_plugin()

	def create_plugin(self):
		pass

	def _create_msg(self, message, source=None, is_admin=False):
		if not isinstance(message, irc.Message):
			if not source:
				source = 'test!bar@baz.com'
			message = irc.Message(source, '#test', message)
		message.user.is_admin = is_admin
		return message

	def _create_user(self, nick, host=None, is_admin=False):
		user = irc.User(nick, host=host)
		user.is_admin = is_admin
		return user

	def reply(self, message, **kwargs):
		message = self._create_msg(message, **kwargs)
		for reply in self.plugin.replies:
			ret = reply(message)
			if ret:
				return ret

	def cmd(self, message, **kwargs):
		message = self._create_msg(message, **kwargs)
		command = bot.CommandMessage(message)
		func = self.plugin.commands[command.command]
		return func(command)

	def join(self, nick, is_admin=False, channel=None):
		user = self._create_user(nick, is_admin)
		if channel and not isinstance(channel, irc.Channel):
			channel = irc.Channel(channel)
		for join in self.plugin.joins:
			ret = join(user, channel)
			if ret:
				return ret

	def http(self, method, path, body=None, headers=None):
		if body is None:
			body = ''
		if headers is None:
			headers = {}

		kwargs = {
			'body': body,
			'headers': headers,
		}

		for handler in self.plugin.http_handlers:
			if handler._http_method == method:
				ret = None

				if not handler._http_path:
					ret = handler(path=path, **kwargs)
				else:
					if handler._http_path == path:
						ret = handler(**kwargs)

				if ret:
					return ret
