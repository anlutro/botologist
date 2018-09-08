import logging

log = logging.getLogger(__name__)

import botologist.bot


def command(cmd_name, alias=None, threaded=False):
    """Plugin command decorator."""
    if alias is None:
        alias = []
    elif isinstance(alias, str):
        alias = [alias]

    def wrapper(func):
        func._command = cmd_name
        func._command_aliases = alias
        func._is_threaded = threaded
        return func

    return wrapper


def reply(threaded=False):
    """Plugin reply decorator."""

    def wrapper(func):
        func._is_reply = True
        func._is_threaded = threaded
        return func

    return wrapper


def join():
    """Plugin join reply decorator."""

    def wrapper(func):
        func._is_join = True
        return func

    return wrapper


def kick():
    """Plugin kick reply decorator."""

    def wrapper(func):
        func._is_kick = True
        return func

    return wrapper


def ticker():
    """Plugin ticker decorator."""

    def wrapper(func):
        func._is_ticker = True
        return func

    return wrapper


def http_handler(method="POST", path=None):
    """Plugin command decorator."""

    def wrapper(func):
        func._http_method = method
        func._http_path = path
        return func

    return wrapper


class PluginMetaclass(type):
    """Metaclass for the Plugin class."""

    def __init__(cls, name, bases, attrs):
        """
        Initialize the metaclass, setting up the plugin's attributes.

        This method scans the class definition for methods decorated with
        @command(command), @reply or @ticker, and adds them to the commands,
        replies or tickers property, respectively.
        """

        cls._commands = {}
        cls._joins = []
        cls._kicks = []
        cls._replies = []
        cls._tickers = []
        cls._http_handlers = []

        for fname, f in attrs.items():
            log_msg = None

            if hasattr(f, "_command"):
                log_msg = "%s.%s is a command"
                cls._commands[f._command] = fname
                if f._command_aliases:
                    log_msg += " - aliases: " + ", ".join(f._command_aliases)
                for alias in f._command_aliases:
                    cls._commands[alias] = fname

            if hasattr(f, "_is_join"):
                log_msg = "%s.%s is a join reply"
                cls._joins.append(fname)

            if hasattr(f, "_is_kick"):
                log_msg = "%s.%s is a kick reply"
                cls._kicks.append(fname)

            if hasattr(f, "_is_reply"):
                log_msg = "%s.%s is a reply"
                cls._replies.append(fname)

            if hasattr(f, "_is_ticker"):
                log_msg = "%s.%s is a ticker"
                cls._tickers.append(fname)

            if hasattr(f, "_http_method"):
                log_msg = "%s.%s is a HTTP request handler"
                cls._http_handlers.append(fname)

            if log_msg:
                log.debug(log_msg, name, fname)

        super().__init__(name, bases, attrs)


class Plugin(metaclass=PluginMetaclass):
    """Base plugin class."""

    def __init__(self, bot, channel):
        assert isinstance(channel, botologist.protocol.Channel)
        assert isinstance(bot, botologist.bot.Bot)

        # pylint: disable=no-member
        self.commands = {}
        for cmd_name, callback in self._commands.items():
            self.commands[cmd_name] = getattr(self, callback)

        self.joins = []
        for join_fn in self._joins:
            self.joins.append(getattr(self, join_fn))

        self.kicks = []
        for kick_fn in self._kicks:
            self.kicks.append(getattr(self, kick_fn))

        self.replies = []
        for reply_fn in self._replies:
            self.replies.append(getattr(self, reply_fn))

        self.tickers = []
        for ticker_fn in self._tickers:
            self.tickers.append(getattr(self, ticker_fn))

        self.http_handlers = []
        for http_handler in self._http_handlers:
            self.http_handlers.append(getattr(self, http_handler))
            # pylint: enable=no-member

        log.debug(
            "Instantiating plugin %s for channel %s",
            self.__class__.__name__,
            channel.name,
        )

        self.bot = bot
        self.channel = channel
