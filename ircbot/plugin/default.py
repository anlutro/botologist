import ircbot.plugin
from ircbot import cfg

class DefaultPlugin(ircbot.plugin.Plugin):
	@ircbot.plugin.command('mumble')
	def mumble(self, msg):
		mumble_cfg = cfg.get('mumble')
		if not mumble_cfg:
			return None
		retstr = 'Mumble (http://mumble.info) - address: {address} - port: {port}'
		if mumble_cfg.get('password'):
			retstr += ' - password: {password}'
		return retstr.format(**mumble_cfg)

	@ircbot.plugin.reply
	def tableflip(self, msg):
		if '(╯°□°)╯︵ ┻━┻' in msg.message:
			return '┬─┬ ノ( ゜-゜ノ)'

	@ircbot.plugin.reply
	def unacceptable(self, msg):
		msg_str = ''.join([c for c in msg.message if 32 <= ord(c) <= 122])
		msg_str = msg_str.lower().strip()
		if msg == 'unacceptable':
			return 'https://www.youtube.com/watch?v=07So_lJQyqw'
