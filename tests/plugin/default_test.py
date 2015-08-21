from tests.plugin import PluginTestCase

class DefaultPluginTest(PluginTestCase):
	def create_plugin(self):
		import plugins.default as default
		return default.DefaultPlugin(self.bot, self.channel)

	def test_tablethrow(self):
		ret = self.reply('(╯°□°)╯︵ ┻━┻')
		self.assertEqual('┬─┬ ノ( ゜-゜ノ)', ret)

	def test_mumble(self):
		self.assertEqual(None, self.cmd('mumble'))

		self.bot.config.update({'mumble': {
			'address': 'localhost', 'port': 1234
		}})
		self.assertEqual('Mumble (http://mumble.info) - address: localhost - port: 1234', self.cmd('mumble'))

	def test_insults(self):
		expected = 'fuck you too test'
		self.assertEqual(expected, self.reply('fuck you pyircbot'))
		self.assertEqual(expected, self.reply('fuck you, pyircbot'))
		self.assertEqual(expected, self.reply('fuck you, pyircbot!'))
		self.assertEqual(expected, self.reply('pyircbot fuck you'))
		self.assertEqual(expected, self.reply('pyircbot, fuck you'))
		self.assertEqual(expected, self.reply('pyircbot: fuck you'))
		self.assertEqual(expected, self.reply('pyircbot: fuck you!'))

	def test_works(self):
		expected = 'I always work'
		self.assertEqual(expected, self.reply('bot no work'))
		self.assertEqual(expected, self.reply('__bot__ no work'))
