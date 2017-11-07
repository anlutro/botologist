import requests

import botologist.plugin

# Not very scalable solution
redis_storage_item = None

class PCDB:
	comments = []

	@staticmethod
	def search(search_for):
		response = requests.get('https://porncomment.com',
			{'search': search_for}, headers={'accept': 'application/json'})
		comments = response.json()['comments']
		if comments:
			return comments[0]

	@classmethod
	def get_random(cls):
		if not cls.comments:
			response = requests.get('http://porncomment.com',
				headers={'accept': 'application/json'})
			cls.comments = response.json()['comments']
		return cls.comments.pop()


class PcdbPlugin(botologist.plugin.Plugin):
	"""porn comments database plugin."""

	@botologist.plugin.command('pcdb', alias=['random', 'r'])
	def get_pcdb_random(self, cmd):
		global redis_storage_item
		include_url = False
		if cmd.args and cmd.args[-1] in ('+url', '--url', '-u'):
			include_url = True
			cmd.args.pop()

		if cmd.args:
			comment = PCDB.search(' '.join(cmd.args))
			redis_storage_item = comment
		else:
			comment = PCDB.get_random()
			redis_storage_item = comment

		if not comment:
			return 'No results!'

		retval = comment['body'].replace('\n', ' ').replace('\r', '')

		if len(retval) > 400:
			retval = retval[:394] + ' [...]'

		if include_url:
			retval += ' - '+comment['source_url']

		return retval
	
	
	@botologist.plugin.command('pcdbprev', alias=['previous', 'prev', 'p'])
	def get_pcdb_prev(self, cmd):
		include_url = False
		if cmd.args and cmd.args[-1] in ('+url', '--url', '-u'):
			include_url = True
			cmd.args.pop()

		if not redis_storage_item:
			return 'No previous search! Do one!'

		retval = redis_storage_item['body'].replace('\n', ' ').replace('\r', '')

		if len(retval) > 400:
			retval = retval[:394] + ' [...]'

		if include_url:
			retval += ' - '+redis_storage_item['source_url']

		return retval
