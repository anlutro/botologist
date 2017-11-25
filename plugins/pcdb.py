import logging
import requests
import botologist.plugin

log = logging.getLogger(__name__)


class PCDB:
	comments = []
	url = 'https://porncomment.com'

	@classmethod
	def search(cls, search_for):
		response = requests.get(
			cls.url,
			{'search': search_for},
			headers={'accept': 'application/json'},
			timeout=2,
		)
		comments = response.json()['comments']
		if comments:
			return comments[0]

	@classmethod
	def get_random(cls):
		if not cls.comments:
			response = requests.get(
				cls.url,
				headers={'accept': 'application/json'},
				timeout=2,
			)
			cls.comments = response.json()['comments']
		return cls.comments.pop()


def _get_comment_str(comment, include_url=False):
	ret = comment['body'].replace('\n', ' ').replace('\r', '')

	if len(ret) > 400:
		ret = ret[:394] + ' [...]'

	if include_url:
		ret += ' - ' + comment['source_url']

	return ret


class PcdbPlugin(botologist.plugin.Plugin):
	"""porn comments database plugin."""

	prev_comment = None

	@botologist.plugin.command('pcdb', alias=['random', 'r'])
	def get_pcdb_random(self, cmd):
		include_url = False
		if cmd.args and cmd.args[-1] in ('+url', '--url', '-u'):
			include_url = True
			cmd.args.pop()

		try:
			if cmd.args:
				comment = PCDB.search(' '.join(cmd.args))
			else:
				comment = PCDB.get_random()
		except:
			log.warning('exception fetching from PCDB', exc_info=True)
			return 'Error while fetching comment!'

		if not comment:
			return 'No results!'

		self.prev_comment = comment

		return _get_comment_str(comment, include_url=include_url)

	@botologist.plugin.command('pcdbprev', alias=['previous', 'prev', 'p'])
	def get_pcdb_prev(self, cmd):
		if not self.prev_comment:
			return 'No previous search! Do one!'

		return _get_comment_str(self.prev_comment, include_url=True)
