import logging
log = logging.getLogger(__name__)

from botologist import protocol


def get_client(config):
	return Client(config.get('nick', 'botologist'))


class Client(protocol.Client):
	def run_forever(self):
		log.info('Starting local server')

		for callback in self.on_connect:
			callback()

		self.user = User('user', 'user@localhost')
		self.channel = next(iter(self.channels.values()))
		self.input_loop()

		log.info('Quitting local server')
		for callback in self.on_disconnect:
			callback()

	def input_loop(self):
		print('Running locally. Hit ^C, ^D or type "/exit" or "/quit" to quit.')
		try:
			in_str = input('>> ')
			while in_str != '/exit' and in_str != '/quit':
				message = Message(in_str, self.user, self.channel.name)
				for callback in self.on_privmsg:
					callback(message)
				in_str = input('>> ')
		except (KeyboardInterrupt, EOFError):
			print()

	def send_msg(self, target, msg):
		print('<< {}'.format(msg))


class Channel(protocol.Channel):
	pass


class User(protocol.User):
	pass


class Message(protocol.Message):
	pass
