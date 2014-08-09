from irc.bot import SingleServerIRCBot
from threading import Timer

import ircbot.commands
import ircbot.tickers
import ircbot.replies

class Bot(SingleServerIRCBot):
	# commands have to be whitelisted here
	commands = ('hello', 'whoareyou', 'streams', 'addstream')

	# the same goes for functions that are called on every "tick"
	tickers = ('check_online_streams',)

	# tick interval in seconds
	tick_interval = 120

	def __init__(self, server, channel, nick, port=6667, storage_path=None):
		print('Connecting...')
		super().__init__([(server, port)], nick, nick)
		self.channel = channel
		self.nick = nick
		self.storage_path = storage_path

	def on_nicknameinuse(self, connection, event):
		self.nick = connection.get_nickname() + '_'
		connection.nick(self.nick)

	def on_welcome(self, connection, event):
		print('Connected!')
		connection.join(self.channel)
		self._start_tick_timer()

	def on_pubmsg(self, connection, event):
		message = event.arguments[0]
		print(event.source, '->', event.target, ':', message)
		words = message.strip().split(' ')

		if len(message) > 1 and message[0] == '!':
			self._handle_cmd(words)
		elif len(words) > 1 and words[0][-1:] == ':' and words[1][0] == '!':
			self._handle_targetted_cmd(words)
		else:
			self._handle_regular_msg(words, event.source)

	def _handle_cmd(self, words):
		cmd = words[0][1:].strip()
		args = words[1:]

		response = self._get_cmd_reply(cmd, args)
		if response:
			self._msg_chan(response)

	def _handle_targetted_cmd(self, words):
		target = words[0][:-1].strip()
		cmd = words[1][1:].strip()
		args = words[2:]

		response = self._get_cmd_reply(cmd, args)
		if response:
			self._msg_chan(target + ': ' + response)

	def _get_cmd_reply(self, cmd, args):
		if cmd in self.commands:
			return getattr(ircbot.commands, cmd)(self, args)
		return None

	def _handle_regular_msg(self, words, nick):
		target = words[0].replace(':', '').replace(',', '')

		if target == self.nick:
			self._handle_reply(' '.join(words[1:]), nick)

	def _handle_reply(self, message, nick):
		for replier in ircbot.replies.repliers:
			response = replier.get_reply(message, nick)
			if response:
				self._msg_chan(response)

	def _msg_chan(self, message):
		self.connection.privmsg(self.channel, message)
		print(self.channel, '<-', message)		

	def _start_tick_timer(self):
		Timer(self.tick_interval, self._tick).start()

	def _tick(self):
		print('Tick!')
		for func in self.tickers:
			result = getattr(ircbot.tickers, func)(self)
			if result is not None:
				self._msg_chan(result)
		self._start_tick_timer()
