import json
import re
import socket
import urllib.error
import urllib.request

import ircbot.plugin


def get_conversion_result(qs):
	url = 'http://api.duckduckgo.com/?q='+qs+'&format=json&no_html=1'
	try:
		response = urllib.request.urlopen(url, timeout=2)
		content = response.read().decode()
	except (urllib.error.URLError, socket.timeout):
		return False
	data = json.loads(content)
	if data['AnswerType'] == 'conversions' and data['Answer']:
		return data['Answer']


class ConversionPlugin(ircbot.plugin.Plugin):
	pattern = re.compile(r'([\d.,]+) ?([a-zA-Z]+) (into|in|to) ([a-zA-Z]+)')

	@ircbot.plugin.reply()
	def convert(self, msg):
		match = self.pattern.search(msg.message)
		if not match:
			return

		qs = '+'.join(match.groups())
		result = get_conversion_result(qs)
		if result:
			return result