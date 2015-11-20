import requests

import botologist.plugin


class PCDB:
	comments = []

	@classmethod
	def get_random(cls):
		if not cls.comments:
			response = requests.get('http://pcdb.lutro.me',
				headers={'accept': 'application/json'})
			cls.comments = response.json()['comments']
		return cls.comments.pop()


class PcdbPlugin(botologist.plugin.Plugin):
	"""porn comments database plugin."""

	@botologist.plugin.command('pcdb', alias=['random', 'r'])
	def get_pcdb_random(self, cmd):
		comment = PCDB.get_random()
		retval = comment['body'].replace('\n', ' ')

		if len(retval) > 400:
			retval = retval[:394] + ' [...]'

		if cmd.args and cmd.args[0] in ('+url', '--url', '-u'):
			retval += ' - '+comment['source_url']

		return retval
