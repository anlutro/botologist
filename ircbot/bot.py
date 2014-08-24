from threading import Timer
import logging
log = logging.getLogger(__name__)

import ircbot.commands
import ircbot.tickers
import ircbot.replies
from ircbot.client import Client


class Bot(Client):
	storage_path = None
	timer = None

	# Commands have to be whitelisted here
	commands = ('streams', 'addstream', 'sub', 'repo')

	# The same goes for functions that are called on every "tick"
	tickers = ('check_online_streams',)

	# Tick interval in seconds
	tick_interval = 120

	def __init__(self, server, channel, nick, port, storage_path=None):
		server += ':' + str(port)
		super().__init__(server, nick, 'ircbotpy')
		self.channels.append(channel)
		self.storage_path = storage_path
		self.conn.on_welcome.append(self._on_welcome)
		self.conn.on_privmsg.append(self._on_privmsg)

	def stop(self):
		if self.timer is not None:
			self.timer.stop()
		super().stop()

	def _on_welcome(self):
		# self._start_tick_timer()
		pass

	def _on_privmsg(self, message):
		if len(message.message) > 1 and message.message[0] == '!':
			self._handle_cmd(message)
		elif len(message.words) > 1 and message.words[0][-1:] == ':' and message.words[1][0] == '!':
			self._handle_targetted_cmd(message)
		else:
			self._handle_regular_msg(message)

	def _handle_cmd(self, message):
		cmd = message.words[0][1:].strip()
		args = message.words[1:]

		response = self._call_cmd_reply(cmd, args, message.source_nick)
		if response:
			self._msg_chan(response, message)

	def _handle_targetted_cmd(self, message):
		target = message.words[0][:-1].strip()
		cmd = message.words[1][1:].strip()
		args = message.words[2:]

		response = self._call_cmd_reply(cmd, args, message.source_nick)
		if response:
			self._msg_chan(target + ': ' + response, message)

	def _call_cmd_reply(self, cmd, args, user):
		if cmd in self.commands:
			return getattr(ircbot.commands, cmd)(self, args, user)
		return None

	def _handle_regular_msg(self, message):
		target = message.words[0] \
			.replace(':', '') \
			.replace(',', '')

		if target == self.conn.nick:
			self._handle_reply(' '.join(message.words[1:]), message.source_nick)

	def _handle_reply(self, message, nick):
		for replier in ircbot.replies.repliers:
			response = replier.get_reply(message, nick)
			if response:
				self._msg_chan(response, message)

	def _msg_chan(self, messages, original):
		if not messages:
			return

		if type(messages) is str:
			messages = [messages]

		if original.target[0] == '#':
			target = original.target
		else:
			target = original.source_nick

		for message in messages:
			self.conn.send_msg(target, message)

	def _start_tick_timer(self):
		self.timer = Timer(self.tick_interval, self._tick)
		self.timer.start()

	def _tick(self):
		log.info('Tick!')
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
		log.info('Quitting!')
		bot.stop()
		return
