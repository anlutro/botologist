import datetime
from freezegun import freeze_time
from tests.plugins import PluginTestCase


class DefaultPluginTest(PluginTestCase):
    def create_plugin(self):
        import plugins.default as default

        return default.DefaultPlugin(self.bot, self.channel)

    def test_tablethrow(self):
        ret = self.reply("(╯°□°)╯︵ ┻━┻")
        self.assertEqual("┬─┬ ノ( ゜-゜ノ)", ret)

    def test_mumble(self):
        self.assertEqual(None, self.cmd("mumble"))

        self.bot.config.update({"mumble": {"address": "localhost", "port": 1234}})
        self.assertEqual(
            "Mumble (http://mumble.info) - address: localhost - port: 1234",
            self.cmd("mumble"),
        )

    def test_roll(self):
        usage_msg = "Usage: \x02!roll 6\x0F or \x02!roll 2d10"
        self.assertEqual(usage_msg, self.cmd("roll"))
        self.assertEqual(usage_msg, self.cmd("roll 9x9"))
        self.assertEqual(usage_msg, self.cmd("roll asdf"))
        self.assertIn("Rolling 1 die with 6 sides:", self.cmd("roll 6"))
        self.assertIn("Rolling 2 die with 6 sides:", self.cmd("roll 2d6"))
        self.assertIn("Rolling 10 die with 20 sides:", self.cmd("roll 10d20"))
        self.assertEqual("Maximum 10d20!", self.cmd("roll 11d20"))
        self.assertEqual("Maximum 10d20!", self.cmd("roll 10d21"))
        self.assertEqual("Cannot roll less than 1 die!", self.cmd("roll 0d9"))
        self.assertEqual(
            "Cannot roll die with less than 2 sides!", self.cmd("roll 1d1")
        )

    @freeze_time("2019-01-01 00:00:00")
    def test_uptime(self):
        self.bot.started = datetime.datetime(2018, 12, 30, 12, 30, 30)
        self.assertEqual(self.cmd("uptime"), "1d 11h")
