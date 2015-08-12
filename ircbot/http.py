import http.server


class RequestHandler(http.server.BaseHTTPRequestHandler):
	@property
	def bot(self):
	    return self.server.bot

	def do_GET(self):
		self.send_response(200)
		self.send_header('Content-type', 'text/plain')
		self.end_headers()

		for channel in self.bot.channels.values():
			for handler in channel.http_handlers:
				if handler._http_method == 'GET':
					ret = handler()
					if ret:
						self.bot._send_msg(ret, channel.channel)

		self.wfile.write(b'OK\n')

	def do_POST(self):
		self.send_response(200)
		self.send_header('Content-type', 'text/plain')
		self.end_headers()

		length = int(self.headers['Content-Length'])
		body = self.rfile.read(length).decode()
		self.send_msg('POST', body)
		self.wfile.write(b'OK\n')

	def send_msg(self, method, body=None):
		kwargs = {}
		if body:
			kwargs['body'] = body

		for channel in self.bot.channels.values():
			for handler in channel.http_handlers:
				if handler._http_method == method:
					ret = None

					if not handler._http_path:
						ret = handler(path=path, **kwargs)
					else:
						if handler._http_path == self.path:
							ret = handler(**kwargs)

					if ret:
						self.bot._send_msg(ret, channel.channel)


class HTTPServer(http.server.HTTPServer):
	def set_bot(self, bot):
		self.bot = bot
		bot.http_server = self


def run_http_server(bot, host='', port=8000):
	httpd = HTTPServer((host, port), RequestHandler)
	httpd.set_bot(bot)
	httpd.serve_forever()

if __name__ == '__main__':
	run_http_server('hello world', 8000)
