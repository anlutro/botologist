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

		# the messages are always from the same user
		user = User()
		channel = next(iter(self.channels.values()))

		print('Running locally. Hit ^C, ^D or type "/exit" or "/quit" to quit.')
		try:
			in_str = input('>> ')
			while in_str != '/exit' and in_str != '/quit':
				message = Message(in_str, user, channel.name)
				for callback in self.on_privmsg:
					callback(message)
				in_str = input('>> ')
		except (KeyboardInterrupt, EOFError):
			print()

		log.info('Quitting local server')
		for callback in self.on_disconnect:
			callback()

	def send_msg(self, target, msg):
		print('<< {}'.format(msg))


class Channel(protocol.Channel):
	pass


class User(protocol.User):
	def __init__(self):
		super().__init__('user', 'user@localhost')


class Message(protocol.Message):
	pass
