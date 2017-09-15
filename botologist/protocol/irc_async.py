from inspect import iscoroutinefunction
import asyncio
import logging

from botologist.protocol.irc import Channel, ServerPool, BaseClient

log = logging.getLogger(__name__)


def get_client(config, loop=None):
	loop = loop or asyncio.get_event_loop()
	nick = config.get('nick', 'botologist')
	return AsyncClient(
		loop,
		ServerPool.from_config(config),
		nick=nick,
		username=config.get('username', nick),
		realname=config.get('realname', nick),
	)


class AsyncClient(BaseClient):
	is_async = True

	def __init__(self, loop, server_pool, nick, username=None, realname=None):
		super().__init__(server_pool, nick, username=username, realname=realname)
		self.loop = loop
		self.ping_future = None
		self.ping_timeout_future = None

	def invoke_callback(self, callback, *args, **kwargs):
		if iscoroutinefunction(callback):
			self.loop.create_task(callback(*args, **kwargs))
		else:
			return super().invoke_callback(callback, *args, **kwargs)

	def run_forever(self):
		self.loop.create_task(self.async_run_forever())
		try:
			self.loop.run_forever()
		except (KeyboardInterrupt, asyncio.CancelledError):
			pass
		finally:
			for task in asyncio.Task.all_tasks():
				task.cancel()
				try:
					self.loop.run_until_complete(task)
				except asyncio.CancelledError:
					pass
			self.loop.stop()
			self.loop.close()

	async def async_run_forever(self):
		try:
			await self.connect()
			while True:
				line = await self.reader.readuntil(b'\r\n')
				msg = line.decode('utf-8').rstrip('\r\n')
				self.loop.create_task(self.ahandle_msg(msg))
		finally:
			if self.ping_future:
				self.ping_future.cancel()
			if self.ping_timeout_future:
				self.ping_timeout_future.cancel()

	async def ahandle_msg(self, msg):
		log.debug('[recv] %r', msg)
		self.handle_msg(msg)

	async def connect(self):
		server = self.server_pool.get()
		self.reader, self.writer = await asyncio.open_connection(
			server.host, server.port, loop=self.loop
		)
		self.send('NICK %s' % self.nick)
		self.send('USER %s 0 * :%s' % (self.username, self.realname))

	async def asend(self, msg):
		log.debug('[send] %r', msg)
		data = msg.encode('utf-8') + b'\r\n'
		self.writer.write(data)
		await self.writer.drain()

	def send(self, line):
		self.loop.create_task(self.asend(line))

	async def asend_msg(self, target, msg):
		if isinstance(target, Channel):
			target = target.name
		await self.asend('PRIVMSG ' + target + ' :' + msg)

	def send_msg(self, target, msg):
		self.loop.create_task(self.asend_msg(target, msg))

	def reset_ping_timer(self):
		if self.ping_future:
			log.debug('cancelling ping_future')
			self.ping_future.cancel()
			self.ping_future = None
		if self.ping_timeout_future:
			log.debug('cancelling ping_timeout_future')
			self.ping_timeout_future.cancel()
			self.ping_timeout_future = None
		log.debug('setting up ping_future')
		self.ping_future = self.loop.call_later(30, self.send_ping)

	def send_ping(self):
		log.debug('sending ping')
		self.send('PING :localhost')
		log.debug('setting up ping_timeout_future')
		self.ping_timeout_future = self.loop.call_later(10, self.handle_ping_timeout)

	def handle_ping_timeout(self):
		self.stop()

	def reconnect(self, delay=0):
		self.loop.call_later(delay, self._reconnect)

	def _reconnect(self):
		self.stop()

	def stop(self, reason='Leaving'):
		log.info('Quitting, reason: %s', reason)
		self.send('QUIT :' + reason)
		self.loop.stop()
