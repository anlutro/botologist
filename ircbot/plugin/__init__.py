from ircbot import log
import ircbot.irc
import ircbot.bot


def command(command, threaded=False):
	"""Plugin command decorator."""
	def wrapper(func):
		func._command = command
		func._is_threaded = threaded
		return func
	return wrapper


def reply(threaded=False):
	"""Plugin reply decorator."""
	def wrapper(func):
		func._is_reply = true
		func._is_threaded = threaded
		return func
	return wrapper


def join(func):
	"""Plugin join reply decorator."""
	func._is_join = True
	return func


def ticker(func):
	"""Plugin ticker decorator."""
	func._is_ticker = True
	return func


class PluginMetaclass(type):
	"""Metaclass for the Plugin class."""
	def __init__(self, name, bases, attrs):
		"""Initialize the metaclass, setting up the plugin's attributes.

		This method scans the class definition for methods decorated with
		@command(command), @reply or @ticker, and adds them to the commands,
		replies or tickers property, respectively.
		"""

		self._commands = {}
		self._joins = []
		self._replies = []
		self._tickers = []

		for fname, f in attrs.items():
			if hasattr(f, '_command'):
				log.debug('{name}.{fname} is a command'.format(
					name=name, fname=fname))
				self._commands[f._command] = fname

			if hasattr(f, '_is_join'):
				log.debug('{name}.{fname} is a join reply'.format(
					name=name, fname=fname))
				self._joins.append(fname)

			if hasattr(f, '_is_reply'):
				log.debug('{name}.{fname} is a reply'.format(
					name=name, fname=fname))
				self._replies.append(fname)

			if hasattr(f, '_is_ticker'):
				log.debug('{name}.{fname} is a ticker'.format(
					name=name, fname=fname))
				self._tickers.append(fname)

		return super().__init__(name, bases, attrs)


class Plugin(metaclass=PluginMetaclass):
	"""Base plugin class."""
	def __init__(self, bot, channel):
		assert isinstance(channel, ircbot.irc.Channel)
		assert isinstance(bot, ircbot.bot.Bot)

		self.commands = {}
		for command, callback in self._commands.items():
			self.commands[command] = getattr(self, callback)

		self.joins = []
		for join in self._joins:
			self.joins.append(getattr(self, join))

		self.replies = []
		for reply in self._replies:
			self.replies.append(getattr(self, reply))

		self.tickers = []
		for ticker in self._tickers:
			self.tickers.append(getattr(self, ticker))

		log.debug('Instantiating plugin {plugin} for channel {channel}'.format(
			plugin=self.__class__.__name__, channel=channel.channel))
		self.bot = bot
		self.channel = channel
