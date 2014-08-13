from ircbot.streams import get_new_streams, get_all_subs, Stream

def check_online_streams(bot):
	streams = get_new_streams(bot)

	if not streams:
		return None

	retval = 'New streams online: ' + ' - '.join([stream.url for stream in streams])

	subs = get_all_subs(bot).get('streams', {})
	highlights = []

	for stream in streams:
		for key, stream_subs in subs.items():
			if key in stream.url or stream.url in key:
				for user in stream_subs:
					highlights.append(user)

	if highlights:
		retval += ' (' + ' '.join(highlights) + ')'

	return retval
