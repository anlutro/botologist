from ircbot import log

def command(command):
	def wrapper(func):
		func._command = command
		return func
	return wrapper

def reply(func):
	func._is_reply = True
	return func

def ticker(func):
	func._is_ticker = True
	return func

class PluginMetaclass(type):
	"""Metaclass for the Plugin class."""
	def __init__(self, name, bases, attrs):
		"""
		Initialize the metaclass, setting up the plugin's attributes.

		This method scans the class definition for methods decorated with
		@command(command), @reply or @ticker, and adds them to the commands,
		replies or tickers property, respectively.
		"""
		super().__init__(name, bases, attrs)

		self.commands = {}
		self.replies = []
		self.tickers = []

		for fname, f in attrs.items():
			if hasattr(f, '_command'):
				log.debug('{name}.{fname} is a command'.format(
					name=name, fname=fname))
				self.commands[f._command] = f
			if hasattr(f, '_is_reply'):
				log.debug('{name}.{fname} is a reply'.format(
					name=name, fname=fname))
				self.replies.append(f)
			if hasattr(f, '_is_ticker'):
				log.debug('{name}.{fname} is a ticker'.format(
					name=name, fname=fname))
				self.tickers.append(f)


class Plugin(metaclass=PluginMetaclass):
	pass
