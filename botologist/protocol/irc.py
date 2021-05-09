import logging

log = logging.getLogger(__name__)

import re
import signal
import socket
import ssl
import threading

import botologist.protocol


# https://github.com/myano/jenni/wiki/IRC-String-Formatting
irc_format_pattern = re.compile(r"(\x03\d{1,2}(,\d{1,2})?)|[\x02\x03\x0F\x16\x1D\x1F]")


def strip_irc_formatting(string):
    return irc_format_pattern.sub("", string)


def decode(bytestring):
    try:
        return bytestring.decode("utf-8").strip()
    except UnicodeDecodeError:
        try:
            return bytestring.decode("iso-8859-1").strip()
        except:
            log.error("Could not decode string: %r", bytestring)
            return None


def decode_lines(bytestring):
    for substring in bytestring.split(b"\r\n"):
        line = decode(substring)
        if line:
            yield line


def get_client(config, bot=None):
    nick = config.get("nick", "botologist")

    def _make_server_obj(cfg):
        if isinstance(cfg, dict):
            if "ssl" in cfg:
                log.warning('"ssl" config is deprecated, rename to "use_ssl"')
                cfg["use_ssl"] = cfg["ssl"]
                del cfg["ssl"]
            return Server(**cfg)
        elif isinstance(cfg, str):
            return Server(cfg)
        else:
            raise ValueError(
                "server config must be dict or str, {} given".format(type(cfg))
            )

    if "servers" in config:
        assert isinstance(config["servers"], list)
        servers = (_make_server_obj(s) for s in config["servers"])
    else:
        servers = (_make_server_obj(config["server"]),)

    server_pool = ServerPool(servers)

    return Client(
        server_pool,
        nick=nick,
        username=config.get("username", nick),
        realname=config.get("realname", nick),
        bot=bot,
    )


def _find_user(channel, host, nick):
    if channel:
        user = channel.find_user(identifier=host, name=nick)
        if user:
            return user
    if host and nick:
        return User(nick, host)
    return None


class Client(botologist.protocol.Client):
    MAX_MSG_CHARS = 500
    PING_EVERY = 3 * 60  # seconds
    PING_TIMEOUT = 20  # seconds

    def __init__(self, server_pool, nick, username=None, realname=None, bot=None):
        super().__init__(nick, bot=bot)
        self.server_pool = server_pool
        self.server = None
        self.username = username or nick
        self.realname = realname or nick
        self.irc_socket = None
        self.quitting = False
        self.reconnect_timer = False
        self.ping_timer = None
        self.ping_response_timer = None
        self.connect_thread = None

        def join_channels():
            for channel in self.channels.values():
                self.join_channel(channel)

        self.on_connect.append(join_channels)

    def run_forever(self):
        log.info("Starting IRC client")

        def sigterm_handler(signo, stack_frame):  # pylint: disable=unused-argument
            self.stop(self._get_exit_msg())

        signal.signal(signal.SIGQUIT, sigterm_handler)
        signal.signal(signal.SIGTERM, sigterm_handler)
        signal.signal(signal.SIGINT, sigterm_handler)

        try:
            self.connect()
        except (InterruptedError, SystemExit, KeyboardInterrupt):
            self.stop(self._get_exit_msg())
        except:
            self.stop("An error occured!")
            raise

    def _get_exit_msg(self):
        return (
            "Terminating after %s, probably back soon!"
            % self.bot.get_uptime_human_readable()
        )

    def connect(self):
        if self.irc_socket is not None:
            self.disconnect()

        if self.connect_thread is not None and self.connect_thread.is_alive():
            log.warning("connect_thread is already alive, not doing anything")
            return

        self.connect_thread = threading.Thread(
            target=self._wrap_error_handler(self._connect)
        )
        self.connect_thread.start()

    def disconnect(self):
        for callback in self.on_disconnect:
            callback()

        if self.connect_thread is None or not self.connect_thread.is_alive():
            log.warning("connect_thread is not alive, not doing anything")
            return

        log.info("Disconnecting")
        self.quitting = True
        self.irc_socket.close()
        self.irc_socket = None

    def reconnect(self, time=None):
        if self.irc_socket:
            self.disconnect()

        if self.connect_thread is not None and self.connect_thread.is_alive():
            log.warning("connect_thread is already alive, not doing anything")
            return

        if time:
            log.info("Reconnecting in %d seconds", time)
            self.connect_thread = threading.Timer(time, self._connect)
            self.reconnect_timer = self.connect_thread
        else:
            self.connect_thread = threading.Thread(target=self._connect)

        self.connect_thread.start()

    def _connect(self):
        self.quitting = False

        if self.reconnect_timer:
            self.reconnect_timer = None

        self.server = self.server_pool.get()
        log.info("Connecting to %s:%s", self.server.host, self.server.port)
        self.irc_socket = IRCSocket(self.server)
        self.irc_socket.connect()
        log.info("Successfully connected to server!")

        self.send("NICK " + self.nick)
        self.send("USER " + self.username + " 0 * :" + self.realname)
        self.loop()

    def loop(self):
        handle_func = self._wrap_error_handler(self.handle_msg)

        while self.irc_socket:
            try:
                data = self.irc_socket.recv()
            except OSError:
                if self.quitting:
                    log.info(
                        "socket.recv threw an OSError, but quitting, "
                        "so exiting loop",
                        exc_info=True,
                    )
                else:
                    log.exception("socket.recv threw an exception")
                    self.reconnect(5)
                return

            if data == b"":
                if self.quitting:
                    log.info(
                        "received empty binary data, but quitting, so exiting loop"
                    )
                    return
                else:
                    raise IRCSocketError("Received empty binary data")

            for msg in decode_lines(data):
                if not msg:
                    continue

                log.debug("[recv] %r", msg)

                if self.quitting and msg.startswith("ERROR :"):
                    log.info("received an IRC ERROR, but quitting, so exiting loop")
                    return

                handle_func(msg)

    def join_channel(self, channel):
        assert isinstance(channel, Channel)
        log.info("Joining channel: %s", channel.name)
        self.channels[channel.name] = channel
        self.send("JOIN " + channel.name)

    def handle_msg(self, msg):
        words = msg.split()

        if words[0] == "PING":
            self.reset_ping_timer()
            self.send("PONG " + words[1])

        elif words[0] == "ERROR":
            if ":Your host is trying to (re)connect too fast -- throttled" in msg:
                log.warning("Throttled for (re)connecting too fast")
                self.reconnect(60)
            else:
                log.warning("Received error: %s", msg)
                self.reconnect(10)

        elif "600" > words[0] > "400":
            log.warning("Received error reply: %s", msg)

        elif len(words) > 1:
            try:
                nick, host, _ = User.split_ircformat(words[0])
            except:
                nick = host = None

                # welcome message, lets us know that we're connected
            if words[1] == "001":
                for callback in self.on_connect:
                    callback()

            elif words[1] == "PONG":
                self.reset_ping_timer()

            elif words[1] == "JOIN":
                channel = words[2]
                user = User.from_ircformat(words[0])
                log.debug(
                    "User %s (%s @ %s) joined channel %s",
                    user.nick,
                    user.ident,
                    user.host,
                    channel,
                )
                if user.nick == self.nick:
                    self.send("WHO " + channel)
                else:
                    channel = words[2].lstrip(":")
                    self.channels[channel].add_user(user)
                    for callback in self.on_join:
                        callback(self.channels[channel], user)

                        # response to WHO command
            elif words[1] == "352":
                channel = self.channels[words[3].lstrip(":")]
                host = words[5]
                nick = words[7]
                if not channel.find_user(identifier=host, name=nick):
                    ident = words[4]
                    user = User(nick, host, ident)
                    channel.add_user(user)

            elif words[1] == "NICK":
                new_nick = words[2][1:]
                log.debug("User %s changing nick: %s", host, new_nick)
                for channel in self.channels.values():
                    channel_user = channel.find_user(identifier=host)
                    if channel_user:
                        log.debug(
                            "Updating nick for user %r in channel %s",
                            channel_user,
                            channel.name,
                        )
                        channel_user.name = new_nick

            elif words[1] == "PART":
                channel = self.channels[words[2].lstrip(":")]
                log.debug("User %s parted from channel %s", host, channel)
                channel.remove_user(name=nick, identifier=host)

            elif words[1] == "KICK":
                channel = self.channels[words[2].lstrip(":")]
                user = _find_user(channel, host, nick)
                kicked_nick = words[3]
                kicked_user = _find_user(channel, None, kicked_nick)
                log.debug(
                    "User %s was kicked by %s from channel %s",
                    kicked_nick,
                    user.nick,
                    channel.name,
                )
                channel.remove_user(name=kicked_nick)
                for callback in self.on_kick:
                    callback(channel, kicked_user, user)
                if kicked_nick == self.nick:
                    self.join_channel(channel)

            elif words[1] == "QUIT":
                log.debug("User %s!%s quit", nick, host)
                for channel in self.channels.values():
                    channel.remove_user(name=nick, identifier=host)

            elif words[1] == "PRIVMSG":
                channel = self.channels.get(words[2].lstrip(":"))
                user = _find_user(channel, host, nick)
                message = Message.from_privmsg(msg, user)
                message.channel = channel

                if not message.is_private:
                    message.channel = self.channels[message.target]
                    if not user:
                        log.debug(
                            "Unknown user %s (%s) added to channel %s",
                            user.nick,
                            user.host,
                            message.target,
                        )
                        self.channels[message.target].add_user(user)
                for callback in self.on_privmsg:
                    callback(message)

    def send_msg(self, target, message):
        if isinstance(target, Channel):
            target = target.name
        if target in self.channels:
            if not self.channels[target].allow_colors:
                message = strip_irc_formatting(message)
        messages = self._parse_messages(message)
        for privmsg in messages:
            self.send("PRIVMSG " + target + " :" + privmsg)

    def send(self, msg):
        if len(msg) > self.MAX_MSG_CHARS:
            log.warning(
                "Message too long (%d characters), upper limit %d",
                len(msg),
                self.MAX_MSG_CHARS,
            )
            msg = msg[: (self.MAX_MSG_CHARS - 3)] + "..."

        log.debug("[send] %s", repr(msg))
        self.irc_socket.send(msg + "\r\n")

    def stop(self, reason="Leaving"):
        super().stop()

        if self.reconnect_timer:
            log.info("Aborting reconnect timer")
            self.reconnect_timer.cancel()
            self.reconnect_timer = None
            return

        if self.ping_timer:
            self.ping_timer.cancel()
            self.ping_timer = None

        if self.ping_response_timer:
            self.ping_response_timer.cancel()
            self.ping_response_timer = None

        if not self.irc_socket:
            log.warning("Tried to quit, but irc_socket is None")
            return

        log.info("Quitting, reason: %s", reason)
        self.quitting = True
        self.send("QUIT :" + reason)

    def reset_ping_timer(self):
        if self.ping_response_timer:
            self.ping_response_timer.cancel()
            self.ping_response_timer = None
        if self.ping_timer:
            self.ping_timer.cancel()
            self.ping_timer = None
        self.ping_timer = threading.Timer(
            self.PING_EVERY, self._wrap_error_handler(self.send_ping)
        )
        self.ping_timer.start()

    def send_ping(self):
        if self.ping_response_timer:
            log.warning("Already waiting for PONG, cannot send another PING")
            return

        self.send("PING " + self.server.host)
        self.ping_response_timer = threading.Timer(
            self.PING_TIMEOUT, self._wrap_error_handler(self.handle_ping_timeout)
        )
        self.ping_response_timer.start()

    def handle_ping_timeout(self):
        log.warning("Ping timeout")
        self.ping_response_timer = None
        self.reconnect()


class User(botologist.protocol.User):
    def __init__(self, nick, host=None, ident=None):
        if host and "@" in host:
            ident, host = host.split("@")
        self.host = host
        if ident and ident[0] == "~":
            ident = ident[1:]
        self.ident = ident
        super().__init__(nick, host)

    @staticmethod
    def split_ircformat(string):
        if string[0] == ":":
            string = string[1:]
        parts = string.split("!")
        nick = parts[0]
        ident, host = parts[1].split("@")
        return (nick, host, ident)

    @classmethod
    def from_ircformat(cls, string):
        nick, host, ident = cls.split_ircformat(string)
        return cls(nick, host, ident)

    def __repr__(self):
        return '<botologist.protocol.irc.User "{}!{}@{}" at {}>'.format(
            self.name, self.ident, self.host, hex(id(self))
        )


class Message(botologist.protocol.Message):
    def __init__(self, user, target, message):
        if not isinstance(user, User):
            user = User.from_ircformat(user)
        super().__init__(message, user, target)
        self.is_private = self.target[0] != "#"

    @classmethod
    def from_privmsg(cls, msg, user=None):
        words = msg.split()
        return cls(user or words[0][1:], words[2], " ".join(words[3:])[1:])


class Server:
    def __init__(self, address, use_ssl=False):
        parts = address.split(":")
        self.host = parts[0]
        if len(parts) > 1:
            self.port = int(parts[1])
        else:
            self.port = 6667

        self.use_ssl = use_ssl


class ServerPool:
    def __init__(self, servers=None):
        self.index = 0
        self.servers = []
        if servers:
            for server in servers:
                self.add_server(server)

    def add_server(self, server):
        assert isinstance(server, Server)
        self.servers.append(server)

    def get(self):
        server = self.servers[self.index]
        self.index += 1
        if self.index >= len(self.servers):
            self.index = 0
        return server


class Channel(botologist.protocol.Channel):
    def __init__(self, name):
        if name[0] != "#":
            name = "#" + name
        super().__init__(name)
        self.allow_colors = True

    def find_nick_from_host(self, host):
        if "@" in host:
            host = host[host.index("@") + 1 :]

        user = self.find_user(identifier=host)
        if user:
            return user.name

    def find_host_from_nick(self, nick):
        user = self.find_user(name=nick)
        if user:
            return user.host

    def remove_user(self, user=None, name=None, identifier=None):
        if not user and identifier and "@" in identifier:
            identifier = identifier[identifier.index("@") + 1 :]

        return super().remove_user(user=user, name=name, identifier=identifier)


class IRCSocketError(OSError):
    pass


class IRCSocket:
    def __init__(self, server):
        self.server = server
        self.socket = None
        self.ssl_context = None
        if self.server.use_ssl:
            # https://docs.python.org/3/library/ssl.html#protocol-versions
            self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
            self.ssl_context.options |= ssl.OP_NO_SSLv2
            self.ssl_context.options |= ssl.OP_NO_SSLv3

            if hasattr(self.ssl_context, "load_default_certs"):
                self.ssl_context.verify_mode = ssl.CERT_REQUIRED
                self.ssl_context.check_hostname = True
                self.ssl_context.load_default_certs()  # pylint: disable=no-member
            else:
                log.warning(
                    "TLS connections may not be secure in Python 3.3 - upgrade to 3.4 or newer!"
                )
                self.ssl_context.verify_mode = ssl.CERT_OPTIONAL

    def connect(self):
        log.debug(
            "Looking up address info for %s:%s", self.server.host, self.server.port
        )
        addrinfo = socket.getaddrinfo(
            self.server.host, self.server.port, socket.AF_UNSPEC, socket.SOCK_STREAM
        )

        for res in addrinfo:
            af, socktype, proto, canonname, address = res

            try:
                self.socket = socket.socket(af, socktype, proto)
            except OSError:
                log.warning(
                    "uncaught exception while initialising socket", exc_info=True
                )
                self.socket = None
                continue

            if self.server.use_ssl:
                log.debug("server is using SSL")
                self.socket = self.ssl_context.wrap_socket(
                    self.socket, server_hostname=self.server.host
                )

            try:
                self.socket.settimeout(10)
                log.debug("Trying to connect to %s:%s", address[0], address[1])
                self.socket.connect(address)
            except OSError:
                log.warning(
                    "uncaught exception while connecting to socket", exc_info=True
                )
                self.close()
                continue

                # if we reach this point, the socket has been successfully created,
                # so break out of the loop
            break

        if self.socket is None:
            raise IRCSocketError("Could not open socket")

        self.socket.settimeout(None)

    def recv(self, bufsize=4096):
        data = self.socket.recv(bufsize)

        # 13 = \r -- 10 = \n
        while data != b"" and (data[-1] != 10 and data[-2] != 13):
            data += self.socket.recv(bufsize)

        return data

    def send(self, data):
        if isinstance(data, str):
            data = data.encode("utf-8")
        self.socket.send(data)

    def close(self):
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
        except OSError:
            # shutdown will fail if the socket has already been closed by the
            # server, which will happen if we get throttled for example
            pass
        self.socket.close()
        self.socket = None
