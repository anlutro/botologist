import logging
log = logging.getLogger(__name__)

import hmac
import hashlib
import json
import ircbot.plugin


class GithubPlugin(ircbot.plugin.Plugin):
	def __init__(self, bot, channel):
		super().__init__(bot, channel)
		self.secret = bot.config['github_secret'].encode('ascii')

	@ircbot.plugin.http_handler(method='POST', path='/github')
	def handle_github_hook(self, body, headers):
		event = headers['X-GitHub-Event']
		guid = headers['X-GitHub-Delivery']
		log.info('Received github event: %s - GUID: %s', event, guid)

		signature = headers['X-Hub-Signature']
		self.check_hmac(body, signature)

		data = json.loads(body)
		ret = None

		if event == 'issues':
			ret = self.handle_issue(data)
		elif event == 'pull_request':
			ret = self.handle_pr(data)
		elif event == 'push':
			ret = self.handle_push(data)

		if ret:
			return ret

	def check_hmac(self, body, signature):
		hmac_obj = hmac.new(self.secret, body.encode('utf-8'), hashlib.sha1)
		calculated = 'sha1=' + hmac_obj.hexdigest()
		if not hmac.compare_digest(calculated, signature):
			log.warn('HMAC mismatch: %s %s', signature, calculated)
			raise Exception('Github webhook signature mismatch!')

	# https://developer.github.com/v3/activity/events/types/#issuesevent
	def handle_issue(self, data):
		action = data['action']

		if action not in ('opened', 'closed'):
			log.info('Not doing anything with Github issue action: %s', action)
			return None

		title = data['issue']['title']
		url = data['issue']['html_url']
		user = data['issue']['user']['login']
		repository = data['repository']['full_name']

		return '[{}] Issue {}: {} - {}'.format(repository, action, title, url)

	# https://developer.github.com/v3/activity/events/types/#pullrequestevent
	def handle_pr(self, data):
		action = data['action']

		if action not in ('opened', 'closed'):
			log.info('Not doing anything with Github pull request action: %s', action)
			return None

		title = data['pull_request']['title']
		url = data['pull_request']['html_url']
		user = data['pull_request']['user']['login']
		repository = data['repository']['full_name']

		return '[{}] Pull request {}: {} - {}'.format(
			repository, action, title, url)

	# https://developer.github.com/v3/activity/events/types/#pushevent
	def handle_push(self, data):
		def shorten_commit_url(url):
			parts = url.split('/')
			parts[-1] = parts[-1][:10]
			return '/'.join(parts)

		commits = [commit for commit in data['commits'] if not commit['distinct']]

		if len(commits) > 2:
			return self.handle_push_many(data, commits)

		ret = []
		repository = data['repository']['full_name']
		branch = data['ref'].split('/')[-1]

		for commit in data['commits']:
			author = commit['author']['username']
			title = commit['message'].split('\n')[0]
			url = shorten_commit_url(commit['url'])
			ret.append('[{}] New commit to {} by {}: {} - {}'.format(
				repository, branch, author, title, url))

		return ret

	def handle_push_many(self, data, commits):
		repository = data['repository']['full_name']
		ret = '[{}] {} commits pushed'.format(repository, data['size'])

		# check if there's more than 1 author of the commits
		author = None
		for commit in commits:
			if author is None:
				author = commit['author']
			elif commit['author'] != author:
				author = False
				break
		if author:
			ret += ' by {}'.format(author)
		else:
			ret += ' by multiple authors'

		ret += ' - {}'.format(data['compare'])
		return ret
