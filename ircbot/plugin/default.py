import ircbot.plugin

class DefaultPlugin(ircbot.plugin.Plugin):
	@ircbot.plugin.command('!repo')
	def repo(self, msg):
		return 'https://github.com/anlutro/ircbot'

	@ircbot.plugin.reply
	def tableflip(self, msg):
		if '(╯°□°)╯︵ ┻━┻' in msg.message:
			return '┬─┬ ノ( ゜-゜ノ)'
