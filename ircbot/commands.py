from ircbot.streams import get_online_streams, add_stream, sub_stream, list_user_subs, \
                           StreamNotFoundException, AlreadySubscribedException, \
                           AmbiguousStreamException, InvalidStreamException
from ircbot.web import get_google_result


def streams(bot, args, user):
	streams = get_online_streams(bot)

	if streams is None:
		return None
	elif streams:
		return 'Online streams: ' + ' -- '.join([stream.url for stream in streams])
	else:
		return 'No streams online!'


def addstream(bot, args, user):
	if len(args) < 1:
		return

	try:
		if add_stream(args[0].lower(), bot):
			return 'Stream added!'
		else:
			return 'Stream could not be added.'
	except InvalidStreamException as e:
		return 'Invalid stream URL - ' + e.msg


def sub(bot, args, user):
	if len(args) > 0:
		try:
			stream = sub_stream(bot, user, args[0].lower())
			return 'You ('+user+') are now subscribed to ' + stream + '!'
		except AmbiguousStreamException as e:
			return 'Ambiguous stream choice - options: ' + ', '.join(e.streams)
		except StreamNotFoundException:
			return 'That stream has not been added.'
		except AlreadySubscribedException as e:
			return 'Already subscribed to ' + e.stream
		except InvalidStreamException as e:
			return 'Invalid stream URL - ' + e.msg
	else:
		streams = list_user_subs(bot, user)
		if streams:
			return 'You ('+user+') are subscribed to: ' + ', '.join(streams)
		else:
			return 'You ('+user+') are not subscribed to any streams.'

def g(bot, args, user):
	result = get_google_result(args)

	if result:
		return result
