import logging
log = logging.getLogger(__name__)


class Protocol:
	def new_client(self, config):
		raise NotImplementedError('method new_client must be defined')

	def new_user(self, *args, **kwargs):
		raise NotImplementedError('method new_user must be defined')

	def new_channel(self, *args, **kwargs):
		raise NotImplementedError('method new_channel must be defined')

	def new_message(self, *args, **kwargs):
		raise NotImplementedError('method new_channel must be defined')


class Client:
	def add_channel(self, channel):
		raise NotImplementedError('method add_channel must be defined')

	def run_forever(self, channel):
		raise NotImplementedError('method run_forever must be defined')


class Channel:
	pass


class User:
	def get_identifier(self):
		raise NotImplementedError('method get_identifier must be defined')

	def __eq__(self, other):
		if not isinstance(other, self.__class__):
			return False
		return other.get_identifier() == self.get_identifier()

	def __hash__(self):
		return hash(self.get_identifier())


class Message:
	def __init__(self, body, user):
		self.body = body
		self.words = body.strip().split()
		assert isinstance(user, User)
		self.user = user

	@property
	def message(self):
		return self.body
