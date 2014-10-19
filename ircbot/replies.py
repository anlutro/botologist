def tableflip(bot, message, nick):
	if '(╯°□°)╯︵ ┻━┻' in message:
		return '┬─┬ ノ( ゜-゜ノ)'

def nay_here(bot, message, nick):
	if 'nay' not in nick.lower():
		return

	# remove all non-ascii characters
	msg = ''.join([i if ord(i) < 128 else '' for i in message.strip()])

	if 'sup' in msg.split() or 'yo' == msg:
		return 'gay here'
