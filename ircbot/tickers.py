from ircbot.streams import get_new_streams

def check_online_streams(bot):
	streams = get_new_streams(bot)

	if streams:
		return 'New streams online: ' + ' - '.join([stream.url for stream in streams])
