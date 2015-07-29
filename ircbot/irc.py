from ircbot import log

import socket
import sys
import threading


def _decode(bytes):
	"""Attempt to decode a byte string into a UTF-8 string.

	Because IRC doesn't enforce any particular encoding, we have to either guess
	what encoding is being used, or keep trying until it works. UTF-8 and
	ISO-8859-1 (Windows) are the most common, so we just try those two.
	"""
	try:
		return bytes.decode('utf-8').strip()
	except UnicodeDecodeError:
		try:
			return bytes.decode('iso-8859-1').strip()
		except:
			log.error('Could not decode message')


class User:
	def __init__(self, nick, host=None, ident=None):
		self.nick = nick
		if host and '@' in host:
			host = host[host.index('@')+1:]
		self.host = host
		if ident and ident[0] == '~':
			ident = ident[1:]
		self.ident = ident

	@classmethod
	def from_ircformat(cls, string):
		if string[0] == ':':
			string = string[1:]
		parts = string.split('!')
		nick = parts[0]
		ident, host = parts[1].split('@')
		return cls(nick, host, ident)

	def __eq__(self, other):
		if not isinstance(other, self.__class__):
			return False
		return other.host == self.host

class Message:
	def __init__(self, source, target, message=None):
		self.user = User.from_ircformat(source)
		self.target = target
		self.message = message
		self.words = message.strip().split()
		self.channel = None

	@classmethod
	def from_privmsg(cls, msg):
		words = msg.split()
		return cls(words[0][1:], words[2], ' '.join(words[3:])[1:])

	@property
	def is_private(self):
		return self.target[0] != '#'


class Server:
	def __init__(self, address):
		parts = address.split(':')
		self.host = parts[0]
		self.port = int(parts[1])
		self.channels = {}

	def add_channel(self, channel):
		assert isinstance(channel, Channel)
		self.channels[channel.channel] = channel


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
		if '@' in host:
			host = host[host.index('@')+1:]
		if host in self.host_map:
			return self.host_map[host]
		return False

	def find_host_from_nick(self, nick):
		if nick in self.nick_map:
			return self.nick_map[nick]
		return False

	def remove_user(self, nick=None, host=None):
		assert nick or host

		if host and '@' in host:
			host = host[host.index('@')+1:]

		if nick is not None and nick in self.nick_map:
			host = self.nick_map[nick]
		if host is not None and host in self.host_map:
			nick = self.host_map[host]
		if nick is not None and nick in self.nick_map:
			del self.nick_map[nick]
		if host is not None and host in self.host_map:
			del self.host_map[host]

	def update_nick(self, old_nick, new_nick):
		host = self.nick_map[old_nick]
		del self.nick_map[old_nick]
		self.nick_map[new_nick] = host
		self.host_map[host] = new_nick


class Connection:
	MAX_MSG_CHARS = 500

	def __init__(self, nick, username = None, realname = None):
		self.nick = nick
		self.username = username or nick
		self.realname = realname or nick
		self.sock = None
		self.server = None
		self.channels = {}
		self.on_welcome = []
		self.on_join = []
		self.on_privmsg = []

	def connect(self, server):
		assert isinstance(server, Server)
		if self.sock is not None:
			self.disconnect()
		self.server = server
		self._connect()

	def disconnect(self):
		print('Disconnecting')
		self.sock.close()
		self.sock = None

	def reconnect(self, time=None):
		self.disconnect()
		if time:
			log.info('Reconnecting in {} seconds'.format(time))
			timer = threading.Timer(time, self._connect)
			timer.start()
		else:
			self._connect()

	def _connect(self):
		print('Connecting')
		addrinfo = socket.getaddrinfo(
			self.server.host, self.server.port,
			socket.AF_UNSPEC, socket.SOCK_STREAM
		)

		for res in addrinfo:
			af, socktype, proto, canonname, sa = res

			try:
				self.sock = socket.socket(af, socktype, proto)
			except OSError:
				self.sock = None
				continue

			try:
				self.sock.connect(sa)
			except OSError:
				self.sock.close()
				self.sock = None
				continue

			# if we reach this point, the socket has been successfully created,
			# so break out of the loop
			break

		if self.sock is None:
			raise OSError('Could not open socket')

		print('Connected!')
		self.send('NICK ' + self.nick)
		self.send('USER ' + self.username + ' 0 * :' + self.realname)
		self.loop()

	def loop(self):
		while True:
			try:
				data = self.sock.recv(4096)
			except OSError:
				self.reconnect()
				continue

			if data == b'':
				self.reconnect()

			# 13 = \r -- 10 = \n
			while data[-1] != 10 and data[-2] != 13:
				try:
					data += self.sock.recv(4096)
				except OSError:
					self.reconnect()
					continue

			text = _decode(data)

			for msg in text.split('\r\n'):
				if msg:
					log.debug(repr(msg))
					self.handle_msg(msg)

	def join_channel(self, channel):
		assert isinstance(channel, Channel)
		self.channels[channel.channel] = channel
		self.send('JOIN ' + channel.channel)

	def handle_msg(self, msg):
		words = msg.split()

		if words[0] == 'PING':
			self.send('PONG ' + words[1])
		elif words[0] == 'ERROR':
			log.warning('Received error message: ' + msg)
			self.reconnect(10)
		elif len(words) > 1:
			if words[1] == '001':
				# welcome message, lets us know that we're connected
				for callback in self.on_welcome:
					callback()

			elif words[1] == 'JOIN':
				user = User.from_ircformat(words[0])
				channel = words[2]
				log.debug('User {user} ({ident} @ {host}) joined channel {channel}'.format(
					user=user.nick, ident=user.ident, host=user.host, channel=channel))
				if user.nick == self.nick:
					self.send('WHO '+channel)
				else:
					self.channels[words[2]].add_user(user)
					for callback in self.on_join:
						callback(self.channels[words[2]], user)

			# response to WHO command
			elif words[1] == '352':
				channel = words[3]
				ident = words[4]
				host = words[5]
				nick = words[7]
				user = User(nick, host, ident)
				self.channels[channel].add_user(user)

			elif words[1] == 'NICK':
				user = User.from_ircformat(words[0])
				new_nick = words[2][1:]
				log.debug('User {user} changing nick: {nick}'.format(
					user=user.host, nick=new_nick))
				for channel in self.channels.values():
					if channel.find_nick_from_host(user.host):
						log.debug('Updating nick for user in Channel {channel}'.format(
							channel=channel.channel))
						channel.update_nick(user.nick, new_nick)

			elif words[1] == 'PART':
				user = User.from_ircformat(words[0])
				channel = words[2]
				self.channels[channel].remove_user(host=user.host)
				log.debug('User {user} parted from channel {channel}'.format(
					user=user.host, channel=channel))

			elif words[1] == 'QUIT':
				user = User.from_ircformat(words[0])
				log.debug('User {user} quit'.format(user=user.host))
				for channel in self.channels.values():
					log.debug('Checking if user was in ' + channel.channel)
					if channel.find_nick_from_host(user.host):
						channel.remove_user(host=user.host)
						log.debug('Removing user from channel {channel}'.format(
							channel=channel.channel))

			elif words[1] == 'PRIVMSG':
				message = Message.from_privmsg(msg)
				if not message.is_private:
					message.channel = self.channels[message.target]
				if not message.is_private and message.user.host not in self.channels[message.target].host_map:
					log.debug('Unknown user {user} ({host}) added to channel {channel}'.format(
						user=message.user.nick, host=message.user.host, channel=message.target))
					self.channels[message.target].add_user(User.from_ircformat(words[0]))
				for callback in self.on_privmsg:
					callback(message)

	def send_msg(self, target, message):
		self.send('PRIVMSG ' + target + ' :' + message)

	def send(self, msg):
		if len(msg) > self.MAX_MSG_CHARS:
			msg = msg[:(self.MAX_MSG_CHARS - 3)] + '...'

		self.sock.send(str.encode(msg + '\r\n'))

	def quit(self, reason='Leaving'):
		print('Quitting gracefully: '+reason)
		self.send('QUIT :' + reason)


class Client:
	def __init__(self, server, nick = '__bot__', username = None, realname = None):
		self.conn = Connection(nick, username, realname)
		self.server = Server(server)
		self.conn.on_welcome.append(self._join_channels)

	def add_channel(self, channel):
		channel = Channel(channel)
		self.server.add_channel(channel)

	def _join_channels(self):
		for channel in self.server.channels.values():
			self.conn.join_channel(channel)

	def run_forever(self):
		try:
			self.conn.connect(self.server)
		except KeyboardInterrupt:
			self.stop('Goodbye!')
		except:
			self.stop('An error occured!')
			raise

	def stop(self, msg=None):
		if msg is None:
			msg = 'Leaving'
		self.conn.quit(msg)
