import random
import re

import botologist.plugin


class DefaultPlugin(botologist.plugin.Plugin):
	def __init__(self, bot, channel):
		super().__init__(bot, channel)

		self.insults = (
			(re.compile(r'.*fuck(\s+you)\s*,?\s*'+self.bot.nick+'.*', re.IGNORECASE),
			'fuck you too {nick}'),
			(re.compile(r'.*'+self.bot.nick+r'[,:]?\s+fuck\s+you.*', re.IGNORECASE),
			'fuck you too {nick}'),
		)

	@botologist.plugin.command('mumble')
	def mumble(self, msg):
		mumble_cfg = self.bot.config.get('mumble')
		if not mumble_cfg:
			return None
		retstr = 'Mumble (http://mumble.info) - address: {address} - port: {port}'
		if mumble_cfg.get('password'):
			retstr += ' - password: {password}'
		return retstr.format(**mumble_cfg)

	@botologist.plugin.reply()
	def tableflip(self, msg):
		if '(╯°□°)╯︵ ┻━┻' in msg.message:
			return '┬─┬ ノ( ゜-゜ノ)'

	@botologist.plugin.reply()
	def return_insults(self, msg):
		for expr, reply in self.insults:
			if expr.match(msg.message):
				return reply.format(nick=msg.user.nick)

	no_work = re.compile(r".*(__)?bot(__)?\s+(no|not|does ?n.?t)\s+work.*", re.IGNORECASE)

	@botologist.plugin.reply()
	def bot_always_works(self, msg):
		if self.no_work.match(msg.message):
			return 'I always work'

	@botologist.plugin.command('coinflip')
	def coinflip(self, cmd):
		value = random.randint(0, 1)
		if value == 1:
			return 'Heads!'
		return 'Tails!'

	@botologist.plugin.command('repo')
	def repo(self, msg):
		return 'https://github.com/anlutro/botologist'

	@botologist.plugin.command('version')
	def version(self, msg):
		return self.bot.version
