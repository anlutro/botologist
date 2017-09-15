import logging
log = logging.getLogger(__name__)

from inspect import iscoroutinefunction
import asyncio
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
		protocol = config.get('protocol', 'local')
		protocol_module = 'botologist.protocol.{}'.format(protocol)
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
				if channel is None:
					channel = {}
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
	def is_async(self):
		return self.client.is_async

	@property
	def is_threaded(self):
		return self.client.is_threaded

	@property
	def loop(self):
		return self.client.loop

	@property
	def executor(self):
		return self.client.executor

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
			if '.' not in plugin:
				plugin = 'plugins.' + plugin
			return '{}.{}Plugin'.format(plugin, plugin_class)

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
			log.debug('adding plugin %s to channel %s', plugin, channel.name)
			channel.register_plugin(self.plugins[plugin](self, channel))

		if admins:
			assert isinstance(admins, list)
			channel.admins = admins

		channel.allow_colors = allow_colors
		self.client.add_channel(channel)

	def send_msg(self, targets, messages):
		"""
		Send one or more message to one or more targets (users or channels).

		Args:
		  targets (str|list): The user(s)/channel(s) to send to.
		  messages (str|list): The message(s) to send.
		"""
		if targets == '*':
			targets = (channel for channel in self.client.channels)
		elif not isinstance(targets, (list, set, tuple)):
			targets = set([targets])

		if not isinstance(messages, (list, set, tuple)):
			messages = set([messages])

		for target in targets:
			self.client.send_msg(target, messages)

	def _send_msg(self, msgs, targets):
		log.warning('Bot._send_msg is deprecated! Use send_msg instead!')
		self.send_msg(targets, msgs)

	def _handle_join(self, channel, user):
		assert isinstance(channel, botologist.protocol.Channel)
		assert isinstance(user, botologist.protocol.User)

		# iterate through join callbacks. the first, if any, to return a
		# non-empty value, will be sent back to the channel as a response.
		response = None
		for join_func in channel.joins:
			response = join_func(user, channel)
			if response:
				self.send_msg(channel.name, response)
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
				self.send_msg(channel.name, response)
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
		message.channel = channel

		if message.message.startswith(self.CMD_PREFIX):
			func = self._handle_command
		else:
			func = self._handle_replies
		self._invoke_async(func, message)

	def _invoke_async(self, func, *args, **kwargs):
		if self.is_async:
			self.loop.create_task(func(*args, **kwargs))
		else:
			self.executor.submit(func, *args, **kwargs)

	async def _handle_command(self, message):
		# if the message starts with the command prefix, check for mathing
		# command and fire its callback
		cmd_string = message.words[0][1:].lower()
		channel = message.channel

		if cmd_string in channel.commands:
			command = CommandMessage(message)
			command_func = channel.commands[cmd_string]
		else:
			matching_commands = [cmd for cmd in channel.commands
				if cmd.startswith(cmd_string)]
			if not matching_commands:
				log.debug('"%s" did not match any commands in channel %s',
					cmd_string, channel.name)
				return
			elif len(matching_commands) != 1:
				log.debug('"%s" matched more than 1 command in channel %s',
					cmd_string, channel.name)
				return

			command = CommandMessage(message)
			command.command = self.CMD_PREFIX + matching_commands[0]
			command_func = channel.commands[matching_commands[0]]

		# check for spam
		now = datetime.datetime.now()
		if command.command in self._command_log and not command.user.is_admin:
			diff = now - self._command_log[command.command]
			if self._last_command == (command.user.identifier, command.command, command.args):
				threshold = self.SPAM_THROTTLE * 3
			else:
				threshold = self.SPAM_THROTTLE
			if diff.seconds < threshold:
				log.info('Command throttled: %s', command.command)
				return

		# log the command call for spam throttling
		self._last_command = (command.user.identifier, command.command, command.args)
		self._command_log[command.command] = now

		if iscoroutinefunction(command_func):
			response = await command_func(command)
		else:
			response = command_func(command)
		if response:
			self.send_msg(message.target, response)

	async def _handle_replies(self, message):
		channel = message.channel
		now = datetime.datetime.now()
		for reply_func in channel.replies:
			if iscoroutinefunction(reply_func):
				replies = await reply_func(message)
			else:
				replies = reply_func(message)

			if not replies:
				continue
			if isinstance(replies, str):
				replies = [replies]

			if not message.user.is_admin:
				for reply in replies:
					# throttle spam - prevents the same reply from being sent
					# more than once in a row within the throttle threshold
					if message.channel not in self._reply_log:
						self._reply_log[message.channel] = {}

					if reply in self._reply_log[message.channel]:
						diff = now - self._reply_log[message.channel][reply]
						if diff.seconds < self.SPAM_THROTTLE:
							log.info('reply throttled: %r', reply)
							replies.remove(reply)

					# log the reply for spam throttling
					self._reply_log[message.channel][reply] = now

			for reply in replies:
				# throttle spam - prevents the same reply from being sent
				# more than once in a row within the throttle threshold
				if channel.name not in self._reply_log:
					self._reply_log[channel.name] = {}

				if reply in self._reply_log[channel.name]:
					diff = now - self._reply_log[channel.name][reply]
					if diff.seconds < self.SPAM_THROTTLE:
						log.info('reply throttled: %r', reply)
						replies.remove(reply)

				# log the reply for spam throttling
				self._reply_log[channel.name][reply] = now

		for reply in replies:
			self.send_msg(message.channel, reply)

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
		if self.is_async:
			self.loop.create_task(self._atick())
		elif self.is_threaded:
			self.timer = threading.Timer(
				function=self._wrap_error_handler(self._tick),
				interval=self.TICK_INTERVAL,
			)
			self.timer.start()
		else:
			log.error("couldn't start ticker - not async and not threaded!")
		log.debug('started ticker with interval %d seconds', self.TICK_INTERVAL)

	def stop(self):
		self.client.stop()

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

	async def _atick(self):
		await asyncio.sleep(self.TICK_INTERVAL)
		self._tick()

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
						self.send_msg(channel.name, result)
		finally:
			self._start_tick_timer()

	def _wrap_error_handler(self, func):
		if self.error_handler:
			return self.error_handler.wrap(func)
		return func
