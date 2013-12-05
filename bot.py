from threading import Thread
from handler import MsgHandler
from ticker import Ticker
from irc.bot import SingleServerIRCBot

class Bot(SingleServerIRCBot):
	def __init__(self, channel, nick, server, port=6667):
		SingleServerIRCBot.__init__(self, [(server, port)], nick, nick)
		self.channel = channel
		self.nick = nick
		self.handler = MsgHandler(self)
		self.ticker = Ticker(self)

	def on_nicknameinuse(self, connection, event):
		self.nick = connection.get_nickname() + '_'
		connection.nick(self.nick)

	def on_welcome(self, connection, event):
		print('Connected!')
		connection.join(self.channel)
		self.thread = Thread(target=self.ticker.run, args=(60,))
		self.thread.start()

	def on_pubmsg(self, connection, event):
		print(event.source, '->', event.target, ':', event.arguments[0])
		response = self.handler.handle(event)

		if response is not None:
			self.msg_chan(response)

	def msg_chan(self, message):
		self.connection.privmsg(self.channel, message)
		print(self.channel, '<-', message)

	def stop(self):
		self.ticker.stop()
		self.die()