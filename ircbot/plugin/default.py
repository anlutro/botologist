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

	@ircbot.plugin.reply()
	def tableflip(self, msg):
		if '(╯°□°)╯︵ ┻━┻' in msg.message:
			return '┬─┬ ノ( ゜-゜ノ)'

	insults = (
		(re.compile(r'.*fuck(\s+you)\s*,?\s*'+cfg['bot']['nick']+'.*', re.IGNORECASE),
		'fuck you too {nick}'),
		(re.compile(r'.*'+cfg['bot']['nick']+'[,:]?\s+fuck\s+you.*', re.IGNORECASE),
		'fuck you too {nick}'),
	)

	@ircbot.plugin.reply()
	def return_insults(self, msg):
		for expr, reply in self.insults:
			if expr.match(msg.message):
				return reply.format(nick=msg.user.nick)

	no_work = re.compile(r".*(__)?bot(__)?\s+(no|not|doesn.?t|does not)\s+work.*", re.IGNORECASE)

	@ircbot.plugin.reply()
	def bot_always_works(self, msg):
		if self.no_work.match(msg.message):
			return 'I always work'
