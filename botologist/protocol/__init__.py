import logging
log = logging.getLogger(__name__)

import botologist.plugin


class Client:
	def __init__(self, name):
		self.name = name
		self.channels = {}

		self.error_handler = None
		self.on_connect = []
		self.on_disconnect = []
		self.on_join = []
		self.on_privmsg = []

	@property
	def nick(self):
		return self.name

	def add_channel(self, channel):
		self.channels[channel.name] = channel

	def send_msg(self, target, message):
		raise NotImplementedError('method send_msg must be defined')

	def run_forever(self):
		raise NotImplementedError('method run_forever must be defined')


class Channel:
	def __init__(self, name):
		self.name = name
		self.users = set()

		self.commands = {}
		self.joins = []
		self.replies = []
		self.tickers = []
		self.admins = []
		self.http_handlers = []
		self.plugins = []

	@property
	def channel(self):
		return self.name

	def register_plugin(self, plugin):
		assert isinstance(plugin, botologist.plugin.Plugin)
		self.plugins.append(plugin.__class__.__name__)
		for cmd, callback in plugin.commands.items():
			self.commands[cmd] = callback
		for join_callback in plugin.joins:
			self.joins.append(join_callback)
		for reply_callback in plugin.replies:
			self.replies.append(reply_callback)
		for tick_callback in plugin.tickers:
			self.tickers.append(tick_callback)
		for http_handler in plugin.http_handlers:
			self.http_handlers.append(http_handler)

	def add_user(self, user):
		assert isinstance(user, User)
		self.users.add(user)

	def find_user(self, user=None, name=None, identifier=None):
		assert user or name or identifier

		if user:
			identifier = user.identifier
			name = user.name

		for user in self.users:
			if (identifier and user.identifier == identifier) or \
					(name and user.name == name):
				return user
		return None

	def remove_user(self, user=None, name=None, identifier=None):
		assert user or name or identifier

		user = self.find_user(user, name, identifier)
		if user:
			self.users.remove(user)


class User:
	def __init__(self, name, identifier):
		self.name = name
		self.identifier = identifier

	@property
	def nick(self):
		return self.name

	def __eq__(self, other):
		if not isinstance(other, self.__class__):
			return False
		return other.identifier == self.identifier

	def __hash__(self):
		return hash(self.identifier)


class Message:
	def __init__(self, body, user, target):
		self.body = body
		self.words = body.strip().split()
		assert isinstance(user, User)
		self.user = user
		self.target = target
		self.channel = None
		self.is_private = False

	@property
	def message(self):
		return self.body
