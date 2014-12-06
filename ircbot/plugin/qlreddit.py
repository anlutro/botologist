import ircbot.plugin

class QlredditPlugin(ircbot.plugin.Plugin):
	"""#qlreddit plugin."""

	@ircbot.plugin.reply
	def opa_opa(self, msg):
		if 'opa opa' in msg.message.lower():
			return 'https://www.youtube.com/watch?v=Dqzrofdwi-g'
