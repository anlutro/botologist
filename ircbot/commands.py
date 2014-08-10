from ircbot.streams import get_online_streams, add_stream
from ircbot.web import get_google_result


def streams(bot, args):
	streams = get_online_streams(bot)

	if streams is None:
		return None
	elif streams:
		return 'Online streams: ' + ' -- '.join([stream.url for stream in streams])
	else:
		return 'No streams online!'


def addstream(bot, args):
	if add_stream(args[0], bot):
		return 'Stream added!'
	else:
		return 'Stream could not be added.'


def g(bot, args):
	result = get_google_result(args)

	if result:
		return result
