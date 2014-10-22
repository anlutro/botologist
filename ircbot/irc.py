from ircbot import log

import socket
import sys


def decode(bytes):
	try:
		return bytes.decode().strip()
	except UnicodeDecodeError:
		try:
			return bytes.decode('iso-8859-1').strip()
		except:
			print('<- UNDECODABLE BYTES')


class User:
	def __init__(self, source):
		self.source = source
		parts = source.split('!')
		self.nick = parts[0]
		self.host = parts[1]
		log.debug('{source} parsed into nick: {nick}, host: {host}'.format(
			source=source, nick=self.nick, host=self.host
		))


class Message:
	def __init__(self, source, target, message=None):
		self.user = User(source)
		self.target = target
		self.message = message
		self.words = message.strip().split()

	@classmethod
	def from_privmsg(cls, msg):
		words = msg.split()
		return cls(words[0][1:], words[2], ' '.join(words[3:])[1:])

	def is_privmsg(self):
		return self.target[0] != '#'


class Server:
	def __init__(self, address):
		parts = address.split(':')
		self.host = parts[0]
		self.port = parts[1]
		self.channels = []

	def add_channel(self, channel):
		assert isinstance(channel, Channel)
		self.channels.append(channel)


class Channel:
	def __init__(self, channel):
		if channel[0] != '#':
			channel = '#' + channel
		self.channel = channel
		self.host_map = {}
		self.nick_map = {}

	def add_user(self, user):
		assert isinstance(user, User)
		self.host_map[user.host] = user.nick
		self.nick_map[user.nick] = user.host

	def find_nick_from_host(self, host):
		if host in self.host_map:
			return self.host_map[host]
		return False

	def find_host_from_nick(self, nick):
		if nick in self.nick_map:
			return self.nick_map[nick]
		return False

	def remove_user(self, nick=None, host=None):
		if not nick and not host:
			raise ValueError('Must provide nick or host')
		if nick is not None:
			host = self.nick_map[nick]
		if host is not None:
			nick = self.host_map[host]
		del self.nick_map[nick]
		del self.host_map[host]

	def update_nick(self, old_nick, new_nick):
		host = self.nick_map[old_nick]
		del self.nick_map[old_nick]
		self.nick_map[new_nick] = host
		self.host_map[host] = new_nick


class Connection:
	def __init__(self, nick, username = None, realname = None):
		self.nick = nick
		self.username = username or nick
		self.realname = realname or nick
		self.sock = None
		self.server = None
		self.channels = {}
		self.on_welcome = []
		self.on_privmsg = []

	def connect(self, server):
		assert isinstance(server, Server)
		if self.sock is not None:
			self.disconnect()
		self.server = server
		self._connect()

	def disconnect(self):
		self.sock.close()
		self.sock = None

	def reconnect(self):
		self.disconnect()
		self._connect()

	def _connect(self):
		addrinfo = socket.getaddrinfo(
			self.server.host, self.server.port,
			socket.AF_UNSPEC, socket.SOCK_STREAM
		)

		for res in addrinfo:
			af, socktype, proto, canonname, sa = res

			try:
				self.sock = socket.socket(af, socktype, proto)
			except OSError as msg:
				self.sock = None
				continue

			try:
				self.sock.connect(sa)
			except OSError as msg:
				self.sock.close()
				self.sock = None
				continue

			# if we reach this point, the socket has been successfully created,
			# so break out of the loop
			break

		if self.sock is None:
			raise OSError('Could not open socket')

		self.send('NICK ' + self.nick)
		self.send('USER ' + self.username + ' 0 * :' + self.realname)
		self.loop()

	def loop(self):
		while True:
			data = self.sock.recv(4096)
			if data == b'':
				self.reconnect()
			# 13 = \r -- 10 = \n
			while data[-1] != 10 and data[-2] != 13:
				data += self.sock.recv(4096)
			text = decode(data)

			for msg in text.split('\r\n'):
				if msg:
					print('<- ' + msg)
					self.handle_msg(msg)

	def handle_msg(self, msg):
		words = msg.split()

		if words[0] == 'PING':
			self.send('PONG ' + words[1])
		elif words[0] == 'ERROR':
			self.sock.close()
			raise RuntimeError('IRC server returned an error:' + ' '.join(words[1:]))
		elif len(words) > 1:
			if words[1] == '001':
				# welcome message, lets us know that we're connected
				for callback in self.on_welcome:
					callback()
			elif words[1] == 'JOIN':
				user = User(words[0][1:])
				channel = words[2]
				log.debug('User {user} ({host}) joined channel {channel}'.format(
					user=user.nick, host=user.host, channel=channel
				))
				self.channels[words[2]].add_user(user)
			elif words[1] == 'NICK':
				user = User(words[0][1:])
				new_nick = words[2][1:]
				log.debug('User {user} changing nick: {nick}'.format(
					user=user.host, nick=new_nick
				))
				for channel in self.channels.values():
					if channel.find_nick_from_host(user.host):
						log.debug('Updating nick for user in Channel {channel}'.format(
							channel=channel.channel
						))
						channel.update_nick(user.nick, new_nick)
					print(channel.host_map)
			elif words[1] == 'PRIVMSG':
				message = Message.from_privmsg(msg)
				for callback in self.on_privmsg:
					callback(message)

	def join_channel(self, channel):
		assert isinstance(channel, Channel)
		self.channels[channel.channel] = channel
		self.send('JOIN ' + channel.channel)

	def send_msg(self, target, message):
		self.send('PRIVMSG ' + target + ' :' + message)

	def send(self, msg):
		print('-> ' + msg)
		self.sock.send(str.encode(msg + '\r\n'))

	def quit(self, reason='Leaving'):
		print('** Quitting!')
		self.send('QUIT :' + reason)
		self.disconnect()


class Client:
	def __init__(self, server, nick = '__bot__', username = None, realname = None):
		self.conn = Connection(nick, username, realname)
		self.server = Server(server)
		self.channels = []
		self.conn.on_welcome.append(self._join_channels)

	def add_channel(self, channel):
		self.server.channels.append(Channel(channel))

	def _join_channels(self):
		for channel in self.server.channels:
			self.conn.join_channel(channel)

	def run_forever(self):
		try:
			self.conn.connect(self.server)
		except KeyboardInterrupt:
			self.stop()

	def stop(self, msg=None):
		if msg is None:
			msg = 'Leaving'
		self.conn.quit(msg)
