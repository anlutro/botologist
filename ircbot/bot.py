from irc.bot import SingleServerIRCBot
from threading import Timer
from datetime import datetime

import ircbot.commands
import ircbot.tickers
import ircbot.replies


class Bot(SingleServerIRCBot):
	channel = None
	nick = None
	storage_path = None
	timer = None

	# Commands have to be whitelisted here
	commands = ('streams', 'addstream', 'sub')

	# The same goes for functions that are called on every "tick"
	tickers = ('check_online_streams',)

	# Tick interval in seconds
	tick_interval = 120

	def __init__(self, server, channel, nick, port, storage_path=None):
		print('Connecting to {server}:{port}...'.format(server=server, port=port))
		super().__init__([(server, int(port))], nick, nick)
		self.channel = channel
		self.nick = nick
		self.storage_path = storage_path

	def on_nicknameinuse(self, connection, event):
		self.nick = connection.get_nickname() + '_'
		connection.nick(self.nick)

	def on_welcome(self, connection, event):
		print('Connected, joining {channel}'.format(channel=self.channel))
		connection.join(self.channel)
		self._start_tick_timer()

	def disconnect(self, msg="Leaving"):
		if self.timer is not None:
			self.timer.cancel()
		self.connection.disconnect(msg)

	def on_pubmsg(self, connection, event):
		message = event.arguments[0]
		print(event.source, '->', event.target, ':', message)
		user = event.source.split('!')[0]
		words = message.strip().split(' ')

		if len(message) > 1 and message[0] == '!':
			self._handle_cmd(words, user)
		elif len(words) > 1 and words[0][-1:] == ':' and words[1][0] == '!':
			self._handle_targetted_cmd(words, user)
		else:
			self._handle_regular_msg(words, user)

	def _handle_cmd(self, words, source):
		cmd = words[0][1:].strip()
		args = words[1:]

		response = self._call_cmd_reply(cmd, args, source)
		if response:
			self._msg_chan(response)

	def _handle_targetted_cmd(self, words, source):
		target = words[0][:-1].strip()
		cmd = words[1][1:].strip()
		args = words[2:]

		response = self._call_cmd_reply(cmd, args, source)
		if response:
			self._msg_chan(target + ': ' + response)

	def _call_cmd_reply(self, cmd, args, source):
		if cmd in self.commands:
			return getattr(ircbot.commands, cmd)(self, args, source)
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
		self.timer = Timer(self.tick_interval, self._tick)
		self.timer.start()

	def _tick(self):
		print(str(datetime.now()) + ' - Tick!')
		try:
			for func in self.tickers:
				result = getattr(ircbot.tickers, func)(self)
				if result is not None:
					self._msg_chan(result)
		finally:
			self._start_tick_timer()


def run_bot(**kwargs):
	bot = Bot(**kwargs)

	try:
		bot.start()
	except KeyboardInterrupt:
		print('Quitting!')
		bot.disconnect()
		return
