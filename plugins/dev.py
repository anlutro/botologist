import json
import ircbot.plugin

class DevPlugin(ircbot.plugin.Plugin):
	@ircbot.plugin.http_handler(method='POST', path='/git-commit')
	def git_commit(self, body):
		data = json.loads(body)
		return '[{repo} {hash}] {message}'.format(**data)
