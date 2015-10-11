import logging
log = logging.getLogger(__name__)

import sys
from botologist import protocol

class LocalProtocol(protocol.Protocol):
	pass

class LocalClient(protocol.Client):
	def __init__(self):
		self.on_privmsg = []

	def add_channel(self, channel):
		raise RuntimeError('local protocol does not use channels')

	def run_forever(self):
		log.info('Starting local server')

		for callback in self.on_welcome():
			callback()

		# the messages are always from the same user
		user = LocalUser()
		in_str = input('> ')
		while in_str != 'exit':
			message = LocalMessage(in_str, user)
			for callback in self.on_privmsg:
				callback(message)

		log.info('Quitting local server')
		

class LocalChannel(protocol.Channel):
	pass

class LocalUser(protocol.User):
	def get_identifier(self):
		return 'user@localhost'

class LocalMessage(protocol.Message):
	pass		
