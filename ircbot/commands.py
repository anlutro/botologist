from datetime import datetime
import sys

from ircbot.plugin.web import get_google_result, get_random_yp_comment
from ircbot.plugin.qdb_search import Quotes
from ircbot.plugin.bitcoin import get_bitcoin_worth
import ircbot.plugin.streams as stream_plugin

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
				return getattr(sys.modules[__name__], self.cmd)
			except AttributeError:
				return None


def streams(bot, args, user):
	streams = stream_plugin.get_online_streams(bot)

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
		if stream_plugin.add_stream(args[0].lower(), bot):
			return 'Stream added!'
		else:
			return 'Stream could not be added.'
	except stream_plugin.InvalidStreamException as e:
		return 'Invalid stream URL - ' + e.msg


def delstream(bot, args, user):
	if len(args) < 1:
		return

	try:
		if stream_plugin.del_stream(args[0].lower(), bot):
			return 'Stream deleted!'
	except stream_plugin.AmbiguousStreamException as e:
		return 'Ambiguous stream choice - options: ' + ', '.join(e.streams)
	except stream_plugin.StreamNotFoundException:
		return 'That stream has not been added.'
	except stream_plugin.InvalidStreamException as e:
		return 'Invalid stream URL - ' + e.msg

def sub(bot, args, user):
	if len(args) > 0:
		try:
			stream = stream_plugin.sub_stream(bot, user, args[0].lower())
			return 'You ('+user+') are now subscribed to ' + stream + '!'
		except stream_plugin.AmbiguousStreamException as e:
			return 'Ambiguous stream choice - options: ' + ', '.join(e.streams)
		except stream_plugin.StreamNotFoundException:
			return 'That stream has not been added.'
		except stream_plugin.AlreadySubscribedException as e:
			return 'Already subscribed to ' + e.stream
		except stream_plugin.InvalidStreamException as e:
			return 'Invalid stream URL - ' + e.msg
	else:
		streams = stream_plugin.list_user_subs(bot, user)
		if streams:
			return 'You ('+user+') are subscribed to: ' + ', '.join(streams)
		else:
			return 'You ('+user+') are not subscribed to any stream_plugin.'


def repo(bot, args, user):
	return 'https://github.com/anlutro/ircbot'


def g(bot, args, user):
	return get_google_result(args)


def random(bot, args, user):
	return get_random_yp_comment()


def qdb(bot, args, user):
	search_string = str(' '.join(args)).lower()
	q = Quotes()
	quotes = q.search_quotes(search_string)
	if quotes:
		return ', '.join([str(_) for _ in quotes])
	else:
		return "Nothing found matching those deets."

def btc(bot, args, user):
	return '1 BTC is currently worth %s' % get_bitcoin_worth()
