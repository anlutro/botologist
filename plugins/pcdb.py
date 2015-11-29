import requests

import botologist.plugin


class PCDB:
	comments = []

	@staticmethod
	def search(search_for):
		response = requests.get('http://pcdb.lutro.me',
			{'search': search_for}, headers={'accept': 'application/json'})
		comments = response.json()['comments']
		if comments:
			return comments[0]

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
		include_url = False
		if cmd.args and cmd.args[-1] in ('+url', '--url', '-u'):
			include_url = True
			cmd.args.pop()

		if cmd.args:
			comment = PCDB.search(' '.join(cmd.args))
		else:
			comment = PCDB.get_random()

		if not comment:
			return 'No results!'

		retval = comment['body'].replace('\n', ' ')

		if len(retval) > 400:
			retval = retval[:394] + ' [...]'

		if include_url:
			retval += ' - '+comment['source_url']

		return retval
