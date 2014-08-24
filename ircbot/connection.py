import socket
import sys

class Message:
	def __init__(self, source, target, message=None):
		self.source = source
		parts = source.split('!')
		self.source_nick = parts[0]
		self.source_host = parts[1]
		self.target = target
		self.message = message
		self.words = message.strip().split()

	@classmethod
	def from_privmsg(cls, msg):
		words = msg.split()
		return cls(words[0][1:], words[2], ' '.join(words[3:])[1:])

class Connection:
	s = None
	on_welcome = []
	on_privmsg = []

	nick = None
	username = None
	realname = None

	def __init__(self, nick, username = None, realname = None):
		self.nick = nick
		if not username:
			username = nick
		if not realname:
			realname = nick
		self.username = username
		self.realname = realname

	def connect(self, host, port):
		for res in socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM):
			af, socktype, proto, canonname, sa = res
			try:
				self.s = socket.socket(af, socktype, proto)
			except OSError as msg:
				self.s = None
				continue
			try:
				self.s.connect(sa)
			except OSError as msg:
				self.s.close()
				self.s = None
				continue
			break

		if self.s is None:
			print('could not open socket')
			sys.exit(1)

		self.send('NICK ' + self.nick)
		self.send('USER ' + self.username + ' 0 * :' + self.realname)
		self.loop()

	def loop(self):
		while True:
			data = self.s.recv(4096)
			# 13 = \r -- 10 = \n
			while data[-1] != 10 and data[-2] != 13:
				data += self.s.recv(4096)
			text = data.decode().strip()

			for msg in text.split('\r\n'):
				if msg:
					print('<- ' + msg)
					self.handle_msg(msg)

	def handle_msg(self, msg):
		words = msg.split()

		if words[0] == 'PING':
			self.send('PONG ' + words[1])
		elif words[0] == 'ERROR':
			self.s.close()
			sys.exit(1)
		elif len(words) > 1:
			if words[1] == '001':
				# welcome message, lets us know that we're connected
				for callback in self.on_welcome:
					callback()
			elif words[1] == 'PRIVMSG':
				message = Message.from_privmsg(msg)
				for callback in self.on_privmsg:
					callback(message)

	def join_channel(self, channel):
		if channel[0] != '#':
			channel = '#' + channel
		self.send('JOIN ' + channel)

	def send_msg(self, target, message):
		self.send('PRIVMSG ' + target + ' :' + message)

	def send(self, msg):
		print('-> ' + msg)
		self.s.send(str.encode(msg + '\r\n'))

	def quit(self, reason='Leaving'):
		print('** Quitting!')
		self.send('QUIT ' + reason)
		self.s.close()
