import asyncio
import random
import logging

import botologist.plugin

log = logging.getLogger(__name__)


class TestPlugin(botologist.plugin.Plugin):
	@botologist.plugin.command('ping')
	def ping(self, cmd):
		return 'pong!'

	@botologist.plugin.command('slow')
	async def slow(self, cmd):
		wait = random.randint(5, 10)
		log.debug('sleeping for %d seconds', wait)
		await asyncio.sleep(wait)
		return 'slept for %d seconds' % wait

	@botologist.plugin.command('test_err')
	def test_err(self, cmd):
		raise RuntimeError('test exception')

	@botologist.plugin.command('test_err_threaded', threaded=True)
	def test_err_threaded(self, cmd):
		raise RuntimeError('test exception')

	@botologist.plugin.command('test_err_async')
	async def test_err_async(self, cmd):
		raise RuntimeError('test exception')

	@botologist.plugin.ticker()
	def test_err_ticker(self):
		raise RuntimeError('test exception')
