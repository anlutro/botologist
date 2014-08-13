from ircbot.streams import get_new_streams, get_all_subs

def check_online_streams(bot):
	streams = get_new_streams(bot)

	if not streams:
		return None

	retval = 'New streams online: ' + ' - '.join([stream.url for stream in streams])

	subs = get_all_subs(bot)
	highlights = []

	for stream in streams:
		stream_subs = subs.get('streams', {}).get(stream.url, [])
		for sub in stream_subs:
			highlights.append(sub)

	if highlights:
		retval += ' (' + ' '.join(highlights) + ')'

	return retval
