from ircbot import log
import ircbot.irc
import ircbot.plugin
import threading
import datetime


class CommandMessage:
	def __init__(self, message):
		assert isinstance(message, ircbot.irc.Message)
		self.message = message
		self.command = message.words[0]
		self.args = message.words[1:]

	@property
	def user(self):
		return self.message.user

class Channel(ircbot.irc.Channel):
	def __init__(self, channel, **kwargs):
		super().__init__(channel)
		self.commands = {}
		self.replies = []
		self.tickers = []

	def register_plugin(self, plugin):
		assert isinstance(plugin, ircbot.plugin.Plugin)
		for cmd, callback in plugin.commands.items():
			self.commands[cmd] = callback
		for reply_callback in plugin.replies:
			self.replies.append(reply_callback)
		for tick_callback in plugin.tickers:
			self.tickers.append(tick_callback)


class Bot(ircbot.irc.Client):
	# the character commands start with
	cmd_prefix = '!'

	# interval in seconds
	tick_interval = 120

	# spam throttling in seconds
	throttle = 2

	def __init__(self, server, admins=None, bans=None, storage_dir=None,
	             global_plugins=None, **kwargs):
		super().__init__(server, **kwargs)
		self.conn.on_welcome.append(self._start_tick_timer)
		self.conn.on_privmsg.append(self._handle_privmsg)
		self.storage_dir = storage_dir
		self.plugins = {}
		self.admins = admins or []
		self.bans = bans or []
		self.global_plugins = global_plugins or []
		self._command_log = {}
		self._reply_log = {}

	def stop(self, msg=None):
		self._stop_tick_timer()
		super().stop(msg)

	def register_plugin(self, name, plugin):
		assert issubclass(plugin, ircbot.plugin.Plugin)
		log.debug('Plugin {name} registered'.format(name=name))
		self.plugins[name] = plugin

	def add_channel(self, channel, plugins=None):
		channel = Channel(channel)
		if plugins is not None:
			assert isinstance(plugins, list)
			for plugin in plugins:
				assert isinstance(plugin, str)
				log.debug('Adding plugin {plugin} to channel {channel}'.format(
					plugin=plugin, channel=channel.channel))
				channel.register_plugin(self.plugins[plugin](self, channel))
		for plugin in self.global_plugins:
			assert isinstance(plugin, str)
			log.debug('Adding plugin {plugin} to channel {channel}'.format(
				plugin=plugin, channel=channel.channel))
			channel.register_plugin(self.plugins[plugin](self, channel))
		self.server.channels[channel.channel] = channel

	def _handle_privmsg(self, message):
		assert isinstance(message, ircbot.irc.Message)
		message.user.is_admin = message.user.host in self.admins

		if message.is_private:
			return None

		channel = self.conn.channels[message.target]
		assert isinstance(channel, Channel)

		retval = None

		if message.message.startswith(self.cmd_prefix):
			if message.words[0][1:] in channel.commands:
				callback = channel.commands[message.words[0][1:]]
				retval = self._call_command(callback, message)
		else:
			retval = self._call_repliers(channel.replies, message)

		if retval:
			self._send_msg(retval, message.target)

	def _send_msg(self, msg, target):
		if isinstance(msg, list):
			for item in msg:
				self.conn.send_msg(target, item)
		else:
			self.conn.send_msg(target, msg)

	def _call_command(self, callback, message):
		command = CommandMessage(message)
		now = datetime.datetime.now()
		if command in self._command_log:
			diff = now - self._command_log[command.command]
			if diff.seconds < self.throttle:
				log.debug('Command {cmd} throttled'.format(cmd=command.command))
				return None
		self._command_log[command.command] = now
		return callback(command)

	def _call_repliers(self, replies, message):
		now = datetime.datetime.now()
		for callback in replies:
			reply = callback(message)
			if not reply:
				continue
			if reply in self._reply_log:
				diff = now - self._reply_log[reply]
				if diff.seconds < self.throttle:
					log.debug('Reply throttled: "{reply}"'.format(reply=reply))
					continue
			self._reply_log[reply] = now
			return reply
		return None

	def _start_tick_timer(self):
		self.timer = threading.Timer(self.tick_interval, self._tick)
		self.timer.start()
		log.debug('Ticker started')

	def _stop_tick_timer(self):
		if self.timer is not None:
			self.timer.cancel()
			self.timer = None
			log.info('Ticker stopped')

	def _tick(self):
		log.info('Tick!')
		self._command_log = {}
		self._reply_log = {}
		try:
			for channel in self.server.channels.values():
				for ticker in channel.tickers:
					result = self._call_ticker(ticker)
					if result:
						self._send_msg(result, channel.channel)
		finally:
			self._start_tick_timer()

	def _call_ticker(self, callback):
		return callback()
