from tests.plugins import PluginTestCase


class RedditeuPluginTest(PluginTestCase):
    def create_plugin(self):
        from plugins.redditeu import RedditeuPlugin

        return RedditeuPlugin(self.bot, self.channel)

    def test_bitcoin(self):
        ret = self.cmd("btc")
        self.assertEqual(0, ret.index("1 bitcoin is currently worth"))
        self.assertNotEqual(ret, self.cmd("btc"))

    def test_time(self):
        self.assertNotEqual(self.cmd("time"), self.cmd("time"))

    def test_welcome(self):
        ret = self.join("happy0")
        self.assertEqual("ypyotootp hippy 0", ret)
