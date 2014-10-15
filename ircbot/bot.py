from threading import Timer
import logging
log = logging.getLogger(__name__)

import ircbot.tickers
import ircbot.replies
from ircbot.commands import Command
from ircbot.client import Client


class Bot(Client):
	storage_path = None
	timer = None
	admins = []
	bans = []

	admin_commands = ('addstream', 'delstream', 'random')
	user_commands = ('streams', 'sub', 'repo', 'qdb', 'btc')

	replies = ('tableflip',)

	tickers = ('check_online_streams',)
	# Tick interval in seconds
	tick_interval = 120

	def __init__(self, server, channel, nick, port, storage_path=None, admins=None, bans=None):
		server += ':' + str(port)
		super().__init__(server, nick, 'ircbotpy')
		self.channels.append(channel)
		self.storage_path = storage_path
		if admins:
			self.admins = admins
		if bans:
			self.bans = bans
		self.conn.on_welcome.append(self._on_welcome)
		self.conn.on_privmsg.append(self._on_privmsg)

	def stop(self, msg=None):
		if self.timer is not None:
			self.timer.cancel()
		super().stop(msg)

	def _on_welcome(self):
		self._start_tick_timer()

	def _on_privmsg(self, message):
		if message.source_host in self.bans:
			pass
		elif len(message.message) > 1 and message.message[0] == '!' or (len(message.words) > 1 and message.words[0][-1:] == ':' and message.words[1][0] == '!'):
			self._handle_cmd(message)
		else:
			self._handle_regular_msg(message)

	def _handle_cmd(self, message):
		cmd = Command(self, message)
		if self._cmd_allowed(cmd, message):
			response = cmd.get_response()
			if response:
				self._send_msg(response, self._get_target(message))

	def _cmd_allowed(self, cmd, message):
		if cmd.cmd in self.user_commands:
			return True
		if cmd.cmd in self.admin_commands and message.source_host in self.admins:
			return True
		return False

	def _handle_regular_msg(self, message):
		for reply in self.replies:
			response = getattr(ircbot.replies, reply)(self, message.message, message.source_nick)
			if response:
				self._send_msg(response, self._get_target(message))

	def _get_target(self, message):
		if message.target[0] == '#':
			return message.target
		else:
			return message.source_nick

	def _send_msg(self, messages, target):
		if not messages:
			return

		if type(messages) is str:
			messages = [messages]

		for message in messages:
			self.conn.send_msg(target, message)

	def _msg_chans(self, messages):
		for chan in self.channels:
			self._send_msg(messages, chan)

	def _start_tick_timer(self):
		self.timer = Timer(self.tick_interval, self._tick)
		self.timer.start()

	def _tick(self):
		log.info('Tick!')
		try:
			for func in self.tickers:
				result = getattr(ircbot.tickers, func)(self)
				if result is not None:
					self._msg_chans(result)
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
	except:
		bot.stop('Error :(')
		raise
