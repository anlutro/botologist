from tests.plugin import PluginTestCase

class QlredditPluginTest(PluginTestCase):
	def create_plugin(self):
		from plugins.qlreddit import QlredditPlugin
		return QlredditPlugin(self.bot, self.channel)

	def test_opa_opa(self):
		ret = self.reply('askdlj opa opa kajsdl')
		self.assertEqual('https://www.youtube.com/watch?v=Dqzrofdwi-g', ret)

	def test_locomotion(self):
		ret = self.reply('askdlj LoCoMoTiOn kajsdl')
		self.assertEqual('https://www.youtube.com/watch?v=dgjc-6L0Wm4#t=5', ret)
