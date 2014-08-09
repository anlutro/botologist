from ircbot.streams import get_online_streams

_last_online_streams = None

def check_online_streams(bot):
	global _last_online_streams

	streams = get_online_streams(bot)
	if _last_online_streams is None:
		new_streams = streams
	else:
		new_streams = list(set(_last_online_streams) - set(streams))
	_last_online_streams = streams

	if new_streams:
		return 'New streams online: ' + ' - '.join([stream.url for stream in new_streams])
