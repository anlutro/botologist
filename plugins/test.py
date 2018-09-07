import logging

log = logging.getLogger(__name__)

import botologist.plugin


class TestPlugin(botologist.plugin.Plugin):
    @botologist.plugin.command("ping")
    def ping(self, cmd):
        return "pong!"

    @botologist.plugin.command("test_err")
    def test_err(self, cmd):
        raise RuntimeError("test exception")

    @botologist.plugin.command("test_err_threaded", threaded=True)
    def test_err_threaded(self, cmd):
        raise RuntimeError("test exception")

    @botologist.plugin.ticker()
    def test_err_ticker(self):
        raise RuntimeError("test exception")
