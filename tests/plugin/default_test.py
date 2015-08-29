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
		self.assertEqual(expected, self.reply('fuck you botologist'))
		self.assertEqual(expected, self.reply('fuck you, botologist'))
		self.assertEqual(expected, self.reply('fuck you, botologist!'))
		self.assertEqual(expected, self.reply('botologist fuck you'))
		self.assertEqual(expected, self.reply('botologist, fuck you'))
		self.assertEqual(expected, self.reply('botologist: fuck you'))
		self.assertEqual(expected, self.reply('botologist: fuck you!'))

	def test_works(self):
		expected = 'I always work'
		self.assertEqual(expected, self.reply('bot no work'))
		self.assertEqual(expected, self.reply('__bot__ no work'))

	def test_roll(self):
		self.assertIn('Rolling 2 die with 6 sides:', self.cmd('roll 2d6'))
		self.assertIn('Rolling 12 die with 34 sides:', self.cmd('roll 12d34'))
		self.assertEqual('Cannot roll less than 1 die!', self.cmd('roll 0d9'))
		self.assertEqual('Cannot roll die with less than 2 sides!', self.cmd('roll 1d1'))
