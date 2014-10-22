import ircbot.irc

class Bot(ircbot.irc.Client):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.conn.on_privmsg.append(self._handle_privmsg)
