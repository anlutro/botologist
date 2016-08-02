import unittest.mock as mock
from tests.plugins import PluginTestCase

class UrlPluginTest(PluginTestCase):
	def create_plugin(self):
		from plugins.url import UrlPlugin
		return UrlPlugin(self.bot, self.channel)

	def test_unshortens_url(self):
		url = 'http://www.foobar.com'
		with mock.patch('plugins.url.get_location', return_value=url):
			ret = self.reply('asdad http://t.co/asdf sfgdgf')
		self.assertEqual(['http://t.co/asdf => http://www.foobar.com'], ret)

	def test_shorten_goo_gl_maps(self):
		with mock.patch('plugins.url.get_location') as mock_get_location:
			self.reply('http://goo.gl/maps/asdf')
		mock_get_location.assert_called_once_with('http://goo.gl/maps/asdf')
