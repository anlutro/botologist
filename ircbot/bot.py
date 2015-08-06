import datetime
import threading

from ircbot import log
import ircbot.irc
import ircbot.plugin


class CommandMessage:
	"""Representation of an IRC message that is a command.

	When a user sends a message to the bot that is a bot command, an instance
	of this class should be constructed and will be passed to the command
	handler to figure out a response.
	"""
	def __init__(self, message):
		assert isinstance(message, ircbot.irc.Message)
		self.message = message
		self.command = message.words[0]
		self.args = message.words[1:]

	@property
	def user(self):
		return self.message.user


class Channel(ircbot.irc.Channel):
	"""Extended channel class.

	Added functionality for adding various handlers from plugins, as plugins are
	registered on a per-channel basis.
	"""
	def __init__(self, channel, **kwargs):
		super().__init__(channel)
		self.commands = {}
		self.joins = []
		self.replies = []
		self.tickers = []
		self.admins = []

	def register_plugin(self, plugin):
		assert isinstance(plugin, ircbot.plugin.Plugin)
		for cmd, callback in plugin.commands.items():
			self.commands[cmd] = callback
		for join_callback in plugin.joins:
			self.joins.append(join_callback)
		for reply_callback in plugin.replies:
			self.replies.append(reply_callback)
		for tick_callback in plugin.tickers:
			self.tickers.append(tick_callback)


class Bot(ircbot.irc.Client):
	"""IRC bot."""

	# the character commands start with
	CMD_PREFIX = '!'

	# ticker interval in seconds
	TICK_INTERVAL = 120

	# spam throttling in seconds
	SPAM_THROTTLE = 2

	def __init__(self, server, admins=None, bans=None, storage_dir=None,
	             global_plugins=None, **kwargs):
		super().__init__(server, **kwargs)
		self.conn.on_welcome.append(self._start_tick_timer)
		self.conn.on_join.append(self._handle_join)
		self.conn.on_privmsg.append(self._handle_privmsg)
		self.storage_dir = storage_dir
		self.plugins = {}
		self.admins = admins or []
		self.bans = bans or []
		self.global_plugins = global_plugins or []
		self._command_log = {}
		self._last_command = None
		self._reply_log = {}
		self.timer = None

	def stop(self, msg=None):
		self._stop_tick_timer()
		super().stop(msg)

	def register_plugin(self, name, plugin):
		assert issubclass(plugin, ircbot.plugin.Plugin)
		log.debug('Plugin {name} registered'.format(name=name))
		self.plugins[name] = plugin

	def add_channel(self, channel, plugins=None, admins=None):
		channel = Channel(channel)

		# channel-specific plugins
		if plugins:
			assert isinstance(plugins, list)
			for plugin in plugins:
				assert isinstance(plugin, str)
				log.debug('Adding plugin {plugin} to channel {channel}'.format(
					plugin=plugin, channel=channel.channel))
				channel.register_plugin(self.plugins[plugin](self, channel))

		# global plugins
		for plugin in self.global_plugins:
			assert isinstance(plugin, str)
			log.debug('Adding plugin {plugin} to channel {channel}'.format(
				plugin=plugin, channel=channel.channel))
			channel.register_plugin(self.plugins[plugin](self, channel))

		if admins:
			assert isinstance(admins, list)
			channel.admins = admins

		self.server.channels[channel.channel] = channel

	def _send_msg(self, msg, target):
		if isinstance(msg, list):
			for item in msg:
				self.conn.send_msg(target, item)
		else:
			self.conn.send_msg(target, msg)

	def _handle_join(self, channel, user):
		assert isinstance(channel, Channel)
		assert isinstance(user, ircbot.irc.User)

		# iterate through join callbacks. the first, if any, to return a
		# non-empty value, will be sent back to the channel as a response.
		response = None
		for join_func in channel.joins:
			response = join_func(user, channel)
			if response:
				self._send_msg(response, channel.channel)
				return

	def _handle_privmsg(self, message):
		assert isinstance(message, ircbot.irc.Message)

		if message.user.host in self.bans:
			return

		# check if the user is an admin - add it to the message.user object for
		# later re-use
		message.user.is_admin = (message.user.host in self.admins or
			message.user.host in message.channel.admins)

		# self-explanatory...
		if message.is_private:
			log.debug('Message is private, not replying')
			return None

		channel = self.conn.channels[message.target]
		assert isinstance(channel, Channel)

		response = None

		if message.message.startswith(self.CMD_PREFIX):
			return self._handle_command(message, channel)

		# otherwise, call the channel's repliers
		response = self._call_repliers(channel.replies, message)

		if response:
			self._send_msg(response, message.target)

	def _handle_command(self, message, channel):
		# if the message starts with the command prefix, check for mathing
		# command and fire its callback
		cmd_string = message.words[0][1:].lower()
		log.debug('Message starts with command prefix')

		if not cmd_string in channel.commands:
			return

		log.debug('Message is a channel registered command: {cmd}'.format(
			cmd=cmd_string))
		command_func = channel.commands[cmd_string]

		if command_func._is_threaded:
			thread = threading.Thread(target=self._maybe_send_cmd_reply,
				args=(command_func, message))
			thread.start()
		else:
			self._maybe_send_cmd_reply(command_func, message)

	def _maybe_send_cmd_reply(self, command_func, message):
		response = self._call_command(command_func, message)
		if response:
			self._send_msg(response, message.target)

	def _call_command(self, command_func, message):
		# turn the Message into a CommandMessage
		command = CommandMessage(message)

		# check for spam
		now = datetime.datetime.now()
		if command.command in self._command_log and not message.user.is_admin:
			diff = now - self._command_log[command.command]
			if self._last_command == (command.user.host, command.command, command.args):
				threshold = self.SPAM_THROTTLE * 3
			else:
				threshold = self.SPAM_THROTTLE
			if diff.seconds < threshold:
				log.info('Command {cmd} throttled'.format(cmd=command.command))
				return None

		# log the command call for spam throttling
		self._last_command = (command.user.host, command.command, command.args)
		self._command_log[command.command] = now

		return command_func(command)

	def _call_repliers(self, replies, message):
		now = datetime.datetime.now()

		# iterate through reply callbacks
		for reply_func in replies:
			reply = reply_func(message)
			if not reply:
				continue

			# throttle spam - prevents the same reply from being sent more than
			# once in a row within the throttle threshold
			if reply in self._reply_log and not message.user.is_admin:
				diff = now - self._reply_log[reply]
				if diff.seconds < self.SPAM_THROTTLE:
					log.debug('Reply throttled: "{reply}"'.format(reply=reply))
					continue

			# log the reply for spam throttling
			self._reply_log[reply] = now
			return reply

		return None

	def _start_tick_timer(self):
		self.timer = threading.Timer(self.TICK_INTERVAL, self._tick)
		self.timer.start()
		log.debug('Ticker started')

	def _stop_tick_timer(self):
		if self.timer is not None:
			self.timer.cancel()
			self.timer = None
			log.info('Ticker stopped')

	def _tick(self):
		log.info('Tick!')
		# reset the spam throttle to prevent the log dictionaries from becoming
		# too large
		self._command_log = {}
		self._reply_log = {}

		try:
			for channel in self.server.channels.values():
				for ticker in channel.tickers:
					result = ticker()
					if result:
						self._send_msg(result, channel.channel)
		finally:
			self._start_tick_timer()
