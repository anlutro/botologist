import random
import re

import ircbot.plugin


class DefaultPlugin(ircbot.plugin.Plugin):
	def __init__(self, bot, channel):
		super().__init__(bot, channel)

		self.insults = (
			(re.compile(r'.*fuck(\s+you)\s*,?\s*'+self.bot.nick+'.*', re.IGNORECASE),
			'fuck you too {nick}'),
			(re.compile(r'.*'+self.bot.nick+'[,:]?\s+fuck\s+you.*', re.IGNORECASE),
			'fuck you too {nick}'),
		)

	@ircbot.plugin.command('mumble')
	def mumble(self, msg):
		mumble_cfg = self.bot.config.get('mumble')
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

	@ircbot.plugin.command('coinflip')
	def coinflip(self, cmd):
		if not cmd.user.is_admin:
			return

		value = random.randint(0, 1)
		if value == 1:
			return 'Heads!'
		return 'Tails!'
