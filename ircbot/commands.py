from ircbot.streams import get_online_streams, add_stream

def hello(bot, args):
	return 'Hello world!'

def whoareyou(bot, args):
	return 'I am ' + bot.nick

def streams(bot, args):
	streams = get_online_streams(bot)

	if streams is None:
		return None
	elif streams:
		return ' -- '.join([stream.url for stream in streams])
	else:
		return 'No streams online!'

def addstream(bot, args):
	if add_stream(args[0], bot):
		return 'Stream added!'
	else:
		return 'Stream could not be added.'
