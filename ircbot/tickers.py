from ircbot.plugin.streams import get_new_streams, get_all_subs

def check_online_streams(bot):
	streams = get_new_streams(bot)

	if not streams:
		return None

	retval = []

	subs = get_all_subs(bot) \
		.get('streams', {}) \
		.items()

	for stream in streams:
		highlights = []
		for key, stream_subs in subs:
			if key == stream.url:
				for user in stream_subs:
					highlights.append(user)
		stream_str = 'New stream online: ' + stream.full_url
		if stream.title:
			stream_str += ' - ' + stream.title
		if highlights:
			stream_str += ' (' + ' '.join(highlights) + ')'
		retval.append(stream_str)

	return retval
