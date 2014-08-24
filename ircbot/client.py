from ircbot.connection import Connection

class Client:
	channels = []

	def __init__(self, server, nick, username = None, realname = None):
		self.conn = Connection(nick, username, realname)
		parts = server.split(':')
		self.server_host = parts[0]
		self.server_port = parts[1]

		self.conn.on_welcome.append(self._join_channels)

	def _join_channels(self):
		for channel in self.channels:
			self.conn.join_channel(channel)

	def start(self):
		self.conn.connect(self.server_host, self.server_port)

	def stop(self):
		self.conn.quit()
