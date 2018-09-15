import unittest.mock as mock
from tests.plugins import PluginTestCase


class UrlPluginTest(PluginTestCase):
    def create_plugin(self):
        from plugins.url import UrlPlugin

        return UrlPlugin(self.bot, self.channel)

    def test_unshortens_url(self):
        url = "http://www.foobar.com"
        with mock.patch("plugins.url.get_location", return_value=url):
            ret = self.reply("asdad http://t.co/asdf sfgdgf")
        self.assertEqual(["http://t.co/asdf => http://www.foobar.com"], ret)

    def test_gets_title_of_youtube_url(self):
        fake_response = mock.Mock()
        fake_response.text = "<title>fake title</title>"
        with mock.patch("requests.get", return_value=fake_response):
            ret = self.reply("asdad https://youtu.be/asdf sfgdgf")
        self.assertEqual(["fake title"], ret)

    def test_title_includes_url_when_multiple_urls_in_msg(self):
        fake_response = mock.Mock()
        fake_response.text = "<title>fake title</title>"
        with mock.patch("requests.get", return_value=fake_response):
            ret = self.reply("https://youtu.be/asdf https://youtu.be/ghjk")
        self.assertEqual(
            [
                "fake title (https://youtu.be/asdf)",
                "fake title (https://youtu.be/ghjk)",
            ],
            sorted(ret),
        )

    def test_does_not_reply_title_when_title_in_msg(self):
        fake_response = mock.Mock()
        fake_response.text = "<title>fake title</title>"
        with mock.patch("requests.get", return_value=fake_response):
            ret = self.reply("https://youtu.be/asdf fake title")
        self.assertFalse(ret)
