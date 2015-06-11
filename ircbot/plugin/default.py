import re

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

	insults = (
		(re.compile(r'.*fuck(\s+you)\s*,?\s*'+cfg['bot']['nick']+'.*'),
		'fuck you too {nick}'),
		(re.compile(r'.*'+cfg['bot']['nick']+'[,:]?\s+fuck\s+you.*'),
		'fuck you too {nick}'),
	)

	@ircbot.plugin.reply
	def return_insults(self, msg):
		for expr, reply in self.insults:
			if expr.match(msg.message):
				return reply.format(nick=msg.user.nick)
