import logging

log = logging.getLogger(__name__)

import http.server


class RequestHandler(http.server.BaseHTTPRequestHandler):
    @property
    def bot(self):
        return self.server.bot

    def do_GET(self):
        try:
            self.trigger_handlers("GET")
            self.send_200()
        except:
            self.send_500()
            raise

    def do_POST(self):
        content_length = self.headers["Content-Length"]
        if not content_length:
            log.warning("POST request with no Content-Length received")
            self.send_response(400)
            self.wfile.write(b"Content-Length header missing\n")
            return
        length = int(self.headers["Content-Length"])
        body = self.rfile.read(length).decode()

        try:
            self.trigger_handlers("POST", body)
            self.send_200()
        except:
            self.send_500()
            raise

    def send_500(self):
        self.send_response(500)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"An internal error occured.\n")

    def send_200(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK\n")

    def trigger_handlers(self, method, body=None):
        kwargs = {"body": body, "headers": self.headers}

        for channel in self.bot.channels.values():
            for handler in channel.http_handlers:
                if handler._http_method == method:
                    ret = None

                    if not handler._http_path:
                        ret = handler(path=self.path, **kwargs)
                    else:
                        if handler._http_path == self.path:
                            ret = handler(**kwargs)

                    if ret:
                        self.bot.send_msg(channel.name, ret)

    def log_message(self, string, *args):
        log.info(string, *args)


class HTTPServer(http.server.HTTPServer):
    def set_bot(self, bot):
        self.bot = bot
        bot.http_server = self

    def handle_error(self, request, client_address):
        msg = "Exception while handling HTTP request from {}".format(client_address)
        self.bot.error_handler.handle_error(msg)


def run_http_server(bot, host="", port=8000):
    httpd = HTTPServer((host, port), RequestHandler)
    httpd.set_bot(bot)
    httpd.serve_forever()
