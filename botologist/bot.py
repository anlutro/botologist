import logging
log = logging.getLogger(__name__)

import datetime
import threading
import importlib

import botologist.error
import botologist.http
import botologist.protocol
import botologist.plugin
import botologist.util


class CommandMessage:
	"""Representation of an IRC message that is a command.

	When a user sends a message to the bot that is a bot command, an instance
	of this class should be constructed and will be passed to the command
	handler to figure out a response.
	"""
	def __init__(self, message):
		assert isinstance(message, botologist.protocol.Message)
		self.message = message
		self.command = message.words[0]
		self.args = message.words[1:]

	@property
	def user(self):
		return self.message.user

	@property
	def target(self):
		return self.message.target


class Bot:
	"""IRC bot."""

	version = None

	# the character commands start with
	CMD_PREFIX = '!'

	# ticker interval in seconds
	TICK_INTERVAL = 120

	# spam throttling in seconds
	SPAM_THROTTLE = 2

	def __init__(self, config):
		protocol_module = 'botologist.protocol.{}'.format(config.get('protocol', 'local'))
		self.protocol = importlib.import_module(protocol_module)
		self.client = self.protocol.get_client(config)

		self.config = config
		self.storage_dir = config['storage_dir']
		self.admins = config.get('admins', [])
		self.bans = config.get('bans', [])
		self.global_plugins = config.get('global_plugins', [])
		self.started = None

		self.plugins = {}
		self._command_log = {}
		self._last_command = None
		self._reply_log = {}
		self.timer = None

		self.http_port = config.get('http_port')
		self.http_host = config.get('http_host')
		self.http_server = None
		self.http_thread = None

		self.error_handler = botologist.error.ErrorHandler(self)
		self.client.error_handler = self.error_handler
		self.client.on_connect.append(self._start)
		self.client.on_disconnect.append(self._stop)
		self.client.on_join.append(self._handle_join)
		self.client.on_privmsg.append(self._handle_privmsg)
		self.client.on_kick.append(self._handle_kick)

		# configure plugins
		for name, plugin_class in config.get('plugins', {}).items():
			# convenience compatibility layer for when plugins module was moved
			plugin_class = plugin_class.replace('botologist.plugin.', 'plugins.')

			# dynamically import the plugin module and pass the class
			parts = plugin_class.split('.')
			module = importlib.import_module('.'.join(parts[:-1]))
			plugin_class = getattr(module, parts[-1])
			self.register_plugin(name, plugin_class)

		# configure channels
		channels = config.get('channels')
		if isinstance(channels, dict):
			for name, channel in channels.items():
				self.add_channel(name, **channel)
		elif isinstance(channels, list):
			for channel in channels:
				if isinstance(channel, dict):
					name = channel.pop('channel')
				else:
					name = channel
					channel = {}
				self.add_channel(name, **channel)

	@property
	def nick(self):
		return self.client.nick

	@property
	def channels(self):
		return self.client.channels

	def get_admin_nicks(self):
		admin_nicks = set()
		for channel in self.client.channels.values():
			for admin_id in self.admins:
				users = channel.find_users(identifier=admin_id)
				for user in users:
					if user.nick != self.nick:
						admin_nicks.add(user.name)
		return admin_nicks

	def run_forever(self):
		self.started = datetime.datetime.now()
		self.client.run_forever()

	def register_plugin(self, name, plugin):
		if isinstance(plugin, str):
			parts = plugin.split('.')
			try:
				module = importlib.import_module('.'.join(parts[:-1]))
				plugin = getattr(module, parts[-1])
			except (AttributeError, ImportError) as exception:
				msg = 'Could not find plugin class: {}'.format(plugin)
				raise Exception(msg) from exception

		assert issubclass(plugin, botologist.plugin.Plugin)
		self.plugins[name] = plugin
		log.debug('plugin %r registered', name)

	def add_channel(self, channel, plugins=None, admins=None, allow_colors=True):
		def guess_plugin_class(plugin):
			plugin_class = ''.join(part.title() for part in plugin.split('_'))
			return 'plugins.{}.{}Plugin'.format(plugin, plugin_class)

		if not isinstance(channel, botologist.protocol.Channel):
			channel = self.protocol.Channel(channel)

		# create a combined list of plugins to reduce code duplication and help
		# prevent duplicate plugins. could be a set, but that would randomize
		# the order of plugins
		all_plugins = []

		# global plugins
		for plugin in self.global_plugins:
			if plugin not in all_plugins:
				all_plugins.append(plugin)

		# channel-specific plugins
		if plugins:
			assert isinstance(plugins, list)
			for plugin in plugins:
				if plugin not in all_plugins:
					all_plugins.append(plugin)

		for plugin in all_plugins:
			assert isinstance(plugin, str)
			if plugin not in self.plugins:
				plugin_class = guess_plugin_class(plugin)
				self.register_plugin(plugin, plugin_class)
			log.debug('adding plugin %s to channel %s', plugin, channel.channel)
			channel.register_plugin(self.plugins[plugin](self, channel))

		if admins:
			assert isinstance(admins, list)
			channel.admins = admins

		channel.allow_colors = allow_colors
		self.client.add_channel(channel)

	def _send_msg(self, msgs, targets):
		if targets == '*':
			targets = (channel for channel in self.client.channels)
		elif not isinstance(targets, list) and not isinstance(targets, set):
			targets = set([targets])

		if not isinstance(msgs, list) and not isinstance(msgs, set):
			msgs = set([msgs])

		for msg in msgs:
			for target in targets:
				self.client.send_msg(target, msg)

	def _handle_join(self, channel, user):
		assert isinstance(channel, botologist.protocol.Channel)
		assert isinstance(user, botologist.protocol.User)

		# iterate through join callbacks. the first, if any, to return a
		# non-empty value, will be sent back to the channel as a response.
		response = None
		for join_func in channel.joins:
			response = join_func(user, channel)
			if response:
				self._send_msg(response, channel.channel)
				return

	def _handle_kick(self, channel, kicked_user, user):
		assert isinstance(channel, botologist.protocol.Channel)
		assert isinstance(kicked_user, botologist.protocol.User)
		assert isinstance(user, botologist.protocol.User)

		# iterate through join callbacks. the first, if any, to return a
		# non-empty value, will be sent back to the channel as a response.
		response = None
		for kick_func in channel.kicks:
			response = kick_func(kicked_user, channel, user)
			if response:
				self._send_msg(response, channel.channel)
				return

	def _handle_privmsg(self, message):
		assert isinstance(message, botologist.protocol.Message)

		if message.user.identifier in self.bans:
			return

		# self-explanatory...
		if message.is_private:
			log.debug('Message is private, not replying')
			return None

		# check if the user is an admin - add it to the message.user object for
		# later re-use
		message.user.is_admin = (
			message.user.identifier in self.admins or (
				message.channel and
				message.user.identifier in message.channel.admins
			))

		channel = self.client.channels[message.target]
		assert isinstance(channel, botologist.protocol.Channel)

		if message.message.startswith(self.CMD_PREFIX):
			return self._handle_command(message, channel)

		# otherwise, call the channel's repliers
		response = self._call_repliers(channel, message)

		if response:
			self._send_msg(response, message.target)

	def _handle_command(self, message, channel):
		# if the message starts with the command prefix, check for mathing
		# command and fire its callback
		cmd_string = message.words[0][1:].lower()

		if cmd_string in channel.commands:
			command = CommandMessage(message)
			command_func = channel.commands[cmd_string]
		else:
			matching_commands = [cmd for cmd in channel.commands
				if cmd.startswith(cmd_string)]
			if len(matching_commands) == 0:
				log.debug('"%s" did not match any commands in channel %s',
					cmd_string, channel.channel)
				return
			elif len(matching_commands) != 1:
				log.debug('"%s" matched more than 1 command in channel %s',
					cmd_string, channel.channel)
				return

			command = CommandMessage(message)
			command.command = self.CMD_PREFIX + matching_commands[0]
			command_func = channel.commands[matching_commands[0]]

		if command_func._is_threaded:
			log.debug('Starting thread for command %s', cmd_string)
			cmd_thread = threading.Thread(
				target=self._wrap_error_handler(self._maybe_send_cmd_reply),
				args=(command_func, command),
			)
			cmd_thread.start()
		else:
			self._maybe_send_cmd_reply(command_func, command)

	def _maybe_send_cmd_reply(self, command_func, message):
		# check for spam
		now = datetime.datetime.now()
		if message.command in self._command_log and not message.user.is_admin:
			diff = now - self._command_log[message.command]
			if self._last_command == (message.user.identifier, message.command, message.args):
				threshold = self.SPAM_THROTTLE * 3
			else:
				threshold = self.SPAM_THROTTLE
			if diff.seconds < threshold:
				log.info('Command throttled: %s', message.command)
				return

		# log the command call for spam throttling
		self._last_command = (message.user.identifier, message.command, message.args)
		self._command_log[message.command] = now

		response = command_func(message)
		if response:
			self._send_msg(response, message.target)

	def _call_repliers(self, channel, message):
		now = datetime.datetime.now()
		final_replies = []

		# iterate through reply callbacks
		for reply_func in channel.replies:
			replies = reply_func(message)

			if not replies:
				continue

			if isinstance(replies, list):
				final_replies = final_replies + replies
			else:
				final_replies.append(replies)

		if not message.user.is_admin:
			for reply in final_replies:
				# throttle spam - prevents the same reply from being sent
				# more than once in a row within the throttle threshold
				if channel.channel not in self._reply_log:
					self._reply_log[channel.channel] = {}

				if reply in self._reply_log[channel.channel]:
					diff = now - self._reply_log[channel.channel][reply]
					if diff.seconds < self.SPAM_THROTTLE:
						log.info('Reply throttled: "%s"', reply)
						final_replies.remove(reply)

				# log the reply for spam throttling
				self._reply_log[channel.channel][reply] = now

		return final_replies

	def _start(self):
		if self.http_port and not self.http_server:
			log.info('Running HTTP server on %s:%s', self.http_host, self.http_port)
			self.http_thread = threading.Thread(
				target=self._wrap_error_handler(botologist.http.run_http_server),
				args=(self, self.http_host, self.http_port),
			)
			self.http_thread.start()

		self._start_tick_timer()

	def _start_tick_timer(self):
		self.timer = threading.Timer(
			function=self._wrap_error_handler(self._tick),
			interval=self.TICK_INTERVAL,
		)
		self.timer.start()
		log.debug('started ticker with interval %d seconds', self.TICK_INTERVAL)

	def _stop(self):
		if self.http_server:
			log.info('shutting down HTTP server')
			self.http_server.shutdown()
			self.http_server = None
		if self.http_thread:
			self.http_thread.join()
			self.http_thread = None

		if self.timer:
			log.info('ticker stopped')
			self.timer.cancel()
			self.timer = None

	def _tick(self):
		log.debug('ticker running')

		# reset the spam throttle to prevent the log dictionaries from becoming
		# too large. TODO: replace with a queue
		self._command_log = {}
		for channel in self._reply_log:
			self._reply_log[channel] = {}

		try:
			for channel in self.client.channels.values():
				for ticker in channel.tickers:
					result = ticker()
					if result:
						self._send_msg(result, channel.channel)
		finally:
			self._start_tick_timer()

	def _wrap_error_handler(self, func):
		if self.error_handler:
			return self.error_handler.wrap(func)
		return func
