from ircbot import cfg
from tests.plugin import PluginTestCase

class DefaultPluginTest(PluginTestCase):
	def create_plugin(self):
		import ircbot.plugin.koth as koth
		return koth.KothPlugin(self.bot, self.channel)

	def test_start(self):
		self.assertEqual(None, self.cmd('koth start', is_admin=False))
		self.assertEqual(False, self.plugin.is_active)
		self.assertEqual(False, self.plugin.signups_open)
		self.assertEqual(None, self.plugin.queue)
		self.assertEqual('King of the hill started! Type \x02!koth add\x0f to add yourself!',
			self.cmd('koth start', is_admin=True))
		self.assertEqual('King of the hill already active!',
			self.cmd('koth start', is_admin=True))
		self.assertEqual(True, self.plugin.is_active)
		self.assertEqual(True, self.plugin.signups_open)
		self.assertNotEqual(None, self.plugin.queue)

	def test_add(self):
		self.cmd('koth start', is_admin=True)
		self.assertEqual(0, len(self.plugin.queue))
		self.assertEqual('You were added to the queue in position 1!',
			self.cmd('koth add'))
		self.assertEqual('You are already in the queue!',
			self.cmd('koth add'))
		self.assertEqual(1, len(self.plugin.queue))

	def test_remove(self):
		self.cmd('koth start', is_admin=True)
		self.assertEqual('You are not in the queue!',
			self.cmd('koth remove'))
		self.cmd('koth add')
		self.assertEqual('You were removed from the queue!',
			self.cmd('koth remove'))
		self.assertEqual(0, len(self.plugin.queue))

	def test_next(self):
		self.cmd('koth start', is_admin=True)
		self.cmd('koth add')
		self.assertEqual(None, self.cmd('koth next', is_admin=False))
		self.assertEqual('Last in queue: test - queue empty!',
			self.cmd('koth next', is_admin=True))
		self.assertEqual(0, len(self.plugin.queue))
		self.assertEqual('Queue is empty!',
			self.cmd('koth next', is_admin=True))

	def test_close(self):
		self.cmd('koth start', is_admin=True)
		self.assertEqual('Signups are now closed!',
			self.cmd('koth close', is_admin=True))
		self.assertEqual('Signups are closed!',
			self.cmd('koth add'))
