from ircbot.web import get_google_result
import ircbot.streams
from datetime import datetime


_command_log = {}

class Command():
	bot = None
	message = None
	target = None
	cmd = None
	callback = None

	def __init__(self, bot, message):
		self.bot = bot
		self.message = message

		if (message.words[0][-1] == ':' or message.words[0][-1] == ',') and message.words[1][0] == '!':
			self.target = message.words[0][:-1]
			self.cmd = message.words[1][1:]
			self.args = message.words[2:]
		elif message.words[0][0] == '!':
			self.cmd = message.words[0][1:]
			self.args = message.words[1:]
			self.target = None
		else:
			raise Exception('Not a valid command: ' + self.message.message)

	def get_response(self):
		f = self.get_callback()
		if not f:
			return None

		if self.is_throttled():
			return None

		response = f(self.bot, self.args, self.message.source_nick)
		if self.target:
			response = self.target + ': ' + response
		return response

	def is_throttled(self):
		global _command_log
		now = datetime.now()
		prev = _command_log.get(self.cmd)
		if prev:
			diff = now - prev
			if diff and diff.seconds < 3:
				return True
		_command_log[self.cmd] = now
		return False

	def get_callback(self):
		if self.callback:
			return self.callback
		else:
			try:
				return getattr(ircbot.commands, self.cmd)
			except AttributeError:
				return None


def streams(bot, args, user):
	streams = ircbot.streams.get_online_streams(bot)

	if streams is None:
		return None
	elif streams:
		return 'Online streams: ' + ' -- '.join([stream.full_url for stream in streams])
	else:
		return 'No streams online!'


def addstream(bot, args, user):
	if len(args) < 1:
		return

	try:
		if ircbot.streams.add_stream(args[0].lower(), bot):
			return 'Stream added!'
		else:
			return 'Stream could not be added.'
	except ircbot.streams.InvalidStreamException as e:
		return 'Invalid stream URL - ' + e.msg


def sub(bot, args, user):
	if len(args) > 0:
		try:
			stream = ircbot.streams.sub_stream(bot, user, args[0].lower())
			return 'You ('+user+') are now subscribed to ' + stream + '!'
		except ircbot.streams.AmbiguousStreamException as e:
			return 'Ambiguous stream choice - options: ' + ', '.join(e.streams)
		except ircbot.streams.StreamNotFoundException:
			return 'That stream has not been added.'
		except ircbot.streams.AlreadySubscribedException as e:
			return 'Already subscribed to ' + e.stream
		except ircbot.streams.InvalidStreamException as e:
			return 'Invalid stream URL - ' + e.msg
	else:
		streams = ircbot.streams.list_user_subs(bot, user)
		if streams:
			return 'You ('+user+') are subscribed to: ' + ', '.join(streams)
		else:
			return 'You ('+user+') are not subscribed to any streams.'


def repo(bot, args, user):
	return 'https://github.com/anlutro/ircbot'


def g(bot, args, user):
	result = get_google_result(args)

	if result:
		return result
