import logging
import signal
import threading

import botologist.util
from botologist.protocol.irc import (
	ServerPool, BaseClient, IRCSocket, IRCSocketError,
)

log = logging.getLogger(__name__)


def get_client(config):
	nick = config.get('nick', 'botologist')
	return ThreadedClient(
		ServerPool.from_config(config),
		nick=nick,
		username=config.get('username', nick),
		realname=config.get('realname', nick),
	)


class ThreadedClient(BaseClient):
	is_threaded = True

	def __init__(self, server_pool, nick, username=None, realname=None):
		super().__init__(nick, server_pool, nick, username=username, realname=realname)

		self.irc_socket = None
		self.quitting = False
		self.reconnect_timer = False
		self.ping_timer = None
		self.ping_response_timer = None
		self.connect_thread = None

	def run_forever(self):
		log.info('Starting IRC client')

		def sigterm_handler(signo, stack_frame): # pylint: disable=unused-argument
			self.stop('Terminating, probably back soon!')
		signal.signal(signal.SIGQUIT, sigterm_handler)
		signal.signal(signal.SIGTERM, sigterm_handler)
		signal.signal(signal.SIGINT, sigterm_handler)

		try:
			self.connect()
		except (InterruptedError, SystemExit, KeyboardInterrupt):
			self.stop('Terminating, probably back soon!')
		except:
			self.stop('An error occured!')
			raise

	def connect(self):
		if self.irc_socket is not None:
			self.disconnect()

		if self.connect_thread is not None and self.connect_thread.isAlive():
			log.warning('connect_thread is already alive, not doing anything')
			return

		self.connect_thread = threading.Thread(
			target=self._wrap_error_handler(self._connect)
		)
		self.connect_thread.start()

	def disconnect(self):
		for callback in self.on_disconnect:
			callback()

		if self.connect_thread is None or not self.connect_thread.isAlive():
			log.warning('connect_thread is not alive, not doing anything')
			return

		log.info('Disconnecting')
		self.quitting = True
		self.irc_socket.close()
		self.irc_socket = None

	def reconnect(self, time=None):
		if self.irc_socket:
			self.disconnect()

		if self.connect_thread is not None and self.connect_thread.isAlive():
			log.warning('connect_thread is already alive, not doing anything')
			return

		if time:
			log.info('Reconnecting in %d seconds', time)
			self.connect_thread = threading.Timer(time, self._connect)
			self.reconnect_timer = self.connect_thread
		else:
			self.connect_thread = threading.Thread(self._connect)

		self.connect_thread.start()

	def _connect(self):
		self.quitting = False

		if self.reconnect_timer:
			self.reconnect_timer = None

		self.server = self.server_pool.get()
		log.info('Connecting to %s:%s', self.server.host, self.server.port)
		self.irc_socket = IRCSocket(self.server)
		self.irc_socket.connect()
		log.info('Successfully connected to server!')

		self.send('NICK ' + self.nick)
		self.send('USER ' + self.username + ' 0 * :' + self.realname)
		self.loop()

	def loop(self):
		handle_func = self._wrap_error_handler(self.handle_msg)

		while self.irc_socket:
			try:
				data = self.irc_socket.recv()
			except OSError:
				if self.quitting:
					log.info('socket.recv threw an OSError, but quitting, '
						'so exiting loop', exc_info=True)
				else:
					log.exception('socket.recv threw an exception')
					self.reconnect(5)
				return

			if data == b'':
				if self.quitting:
					log.info('received empty binary data, but quitting, so exiting loop')
					return
				else:
					raise IRCSocketError('Received empty binary data')

			for msg in botologist.util.decode_lines(data):
				if not msg:
					continue

				log.debug('[recv] %r', msg)

				if self.quitting and msg.startswith('ERROR :'):
					log.info('received an IRC ERROR, but quitting, so exiting loop')
					return

				handle_func(msg)

	def send(self, msg):
		if len(msg) > self.MAX_MSG_CHARS:
			log.warning('Message too long (%d characters), upper limit %d',
				len(msg), self.MAX_MSG_CHARS)
			msg = msg[:(self.MAX_MSG_CHARS - 3)] + '...'

		log.debug('[send] %r', msg)
		self.irc_socket.send(msg + '\r\n')

	def stop(self, reason='Leaving'):
		super().stop()

		if self.reconnect_timer:
			log.info('Aborting reconnect timer')
			self.reconnect_timer.cancel()
			self.reconnect_timer = None
			return

		if self.ping_timer:
			self.ping_timer.cancel()
			self.ping_timer = None

		if self.ping_response_timer:
			self.ping_response_timer.cancel()
			self.ping_response_timer = None

		if not self.irc_socket:
			log.warning('Tried to quit, but irc_socket is None')
			return

		log.info('Quitting, reason: %s', reason)
		self.quitting = True
		self.send('QUIT :' + reason)

	def reset_ping_timer(self):
		if self.ping_response_timer:
			self.ping_response_timer.cancel()
			self.ping_response_timer = None
		if self.ping_timer:
			self.ping_timer.cancel()
			self.ping_timer = None
		self.ping_timer = threading.Timer(
			self.PING_EVERY,
			self._wrap_error_handler(self.send_ping),
		)
		self.ping_timer.start()

	def send_ping(self):
		if self.ping_response_timer:
			log.warning('Already waiting for PONG, cannot send another PING')
			return

		self.send('PING ' + self.server.host)
		self.ping_response_timer = threading.Timer(
			self.PING_TIMEOUT,
			self._wrap_error_handler(self.handle_ping_timeout),
		)
		self.ping_response_timer.start()

	def handle_ping_timeout(self):
		log.warning('Ping timeout')
		self.ping_response_timer = None
		self.reconnect()
