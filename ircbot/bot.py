import ircbot.irc
import ircbot.plugin

class CommandMessage:
	def __init__(self, message):
		assert isinstance(message, ircbot.irc.Message)
		self.message = message
		self.command = message.words[0]
		self.args = message.words[1:]


class Channel(ircbot.irc.Channel):
	def __init__(self, channel, **kwargs):
		super().__init__(channel)
		self.commands = {}
		self.replies = []
		self.tickers = []

	def register_plugin(self, plugin):
		for cmd, callback in plugin.commands.items():
			self.commands[cmd] = callback
		for reply_callback in plugin.replies:
			self.replies.append(reply_callback)
		for tick_callback in plugin.tickers:
			self.tickers.append(tick_callback)


class Bot(ircbot.irc.Client):
	def __init__(self, server, admins=None, bans=None, storage_dir=None, **kwargs):
		super().__init__(server, **kwargs)
		self.conn.on_privmsg.append(self._handle_privmsg)
		self.storage_dir = storage_dir
		self.plugins = {}
		self.admins = admins or []
		self.bans = bans or []

	def register_plugin(self, name, plugin):
		assert isinstance(plugin, ircbot.plugin.Plugin)
		self.plugins[name] = plugin

	def add_channel(self, channel, plugins=None):
		channel = Channel(channel)
		if plugins is not None:
			assert isinstance(plugins, list)
			for plugin in plugins:
				assert isinstance(plugin, str)
				channel.register_plugin(self.plugins[plugin])
		self.server.channels[channel.channel] = channel

	def _handle_privmsg(self, message):
		assert isinstance(message, ircbot.irc.Message)

		retval = None

		if message.is_private():
			pass
		else:
			channel = self.conn.channels[message.target]
			if message.message[0] == '!':
				if message.words[0] in channel.commands:
					callback = channel.commands[message.words[0]]
					retval = self._call_command(callback, message)
			else:
				for reply in channel.replies:
					reply_return = self._call_replier(reply, message)
					if reply_return:
						retval = reply_return
						break

		if retval:
			if isinstance(retval, list):
				for item in retval:
					self.conn.send_msg(message.taget, item)
			else:
				self.conn.send_msg(message.taget, retval)

	def _call_command(self, callback, message):
		command = CommandMessage(message)
		return callback(self, message)

	def _call_replier(self, callback, message):
		return callback(self, message)

	def _call_ticker(self, callback):
		return callback(self)
