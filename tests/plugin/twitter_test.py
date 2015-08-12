import unittest.mock as mock
from tests.plugin import PluginTestCase

class TwitterPluginTest(PluginTestCase):
	cfg = {'twitter_api': True}

	def create_plugin(self):
		from plugins.twitter import TwitterPlugin
		plugin = TwitterPlugin(self.bot, self.channel)
		plugin.api = self.api = mock.MagicMock()
		return plugin

	def test_calls_api(self):
		tweet = mock.MagicMock()
		tweet.author.screen_name = 'author'
		tweet.text = 'text'
		self.api.get_status = mock.MagicMock(return_value=tweet)

		ret = self.reply('https://twitter.com/author/status/625945123789119488')
		self.assertEqual('[@author] text', ret)
