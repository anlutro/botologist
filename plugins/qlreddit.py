import botologist.plugin


class QlredditPlugin(botologist.plugin.Plugin):
	"""#qlreddit plugin."""

	@botologist.plugin.reply()
	def opa_opa(self, msg):
		if 'opa opa' in msg.message.lower():
			return 'https://www.youtube.com/watch?v=Dqzrofdwi-g'

	@botologist.plugin.reply()
	def locomotion(self, msg):
		if 'locomotion' in msg.message.lower():
			return 'https://www.youtube.com/watch?v=dgjc-6L0Wm4#t=5'
