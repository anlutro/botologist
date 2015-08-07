from tests.plugin import PluginTestCase

class DefaultPluginTest(PluginTestCase):
	cfg = {'bot': {'nick': 'foobar'}}

	def create_plugin(self):
		import ircbot.plugin.default as default
		return default.DefaultPlugin(self.bot, self.channel)

	def test_tablethrow(self):
		ret = self.reply('(╯°□°)╯︵ ┻━┻')
		self.assertEqual('┬─┬ ノ( ゜-゜ノ)', ret)

	def test_mumble(self):
		self.assertEqual(None, self.cmd('mumble'))

		from ircbot import cfg
		cfg.update({'mumble': {'address': 'localhost', 'port': 1234}})
		self.assertEqual('Mumble (http://mumble.info) - address: localhost - port: 1234', self.cmd('mumble'))

	def test_insults(self):
		expected = 'fuck you too test'
		self.assertEqual(expected, self.reply('fuck you foobar'))
		self.assertEqual(expected, self.reply('fuck you, foobar'))
		self.assertEqual(expected, self.reply('fuck you, foobar!'))
		self.assertEqual(expected, self.reply('foobar fuck you'))
		self.assertEqual(expected, self.reply('foobar, fuck you'))
		self.assertEqual(expected, self.reply('foobar: fuck you'))
		self.assertEqual(expected, self.reply('foobar: fuck you!'))

	def test_works(self):
		expected = 'I always work'
		self.assertEqual(expected, self.reply('bot no work'))
		self.assertEqual(expected, self.reply('__bot__ no work'))
