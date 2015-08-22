import hmac
import hashlib
import os.path

from tests.plugin import PluginTestCase
import plugins.github

class DefaultPluginTest(PluginTestCase):
	def create_plugin(self):
		self.bot.config['github_secret'] = 'asdf'
		return plugins.github.GithubPlugin(self.bot, self.channel)

	def get_json(self, event):
		path = os.path.join(
			os.path.dirname(os.path.dirname(__file__)),
			'files', 'github_'+event+'.json'
		)
		with open(path, 'r') as f:
			return f.read()

	def get_headers(self, body, event):
		hmac_obj = hmac.new(self.plugin.secret, body.encode('utf-8'), hashlib.sha1)
		signature = hmac_obj.hexdigest()
		return {
			'X-GitHub-Event': event,
			'X-GitHub-Delivery': 'FAKEGUID',
			'X-Hub-Signature': 'sha1=' + signature,
		}

	def trigger_webhook(self, event):
		body = self.get_json(event)
		headers = self.get_headers(body, event)
		return self.http('POST', '/github', body, headers)

	def test_push(self):
		ret = self.trigger_webhook('push')
		self.assertEqual('[baxterthehacker/public-repo] New commit to changes by baxterthehacker: Update README.md - https://github.com/baxterthehacker/public-repo/commit/0d1a26e67d', ret[0])

	def test_issue(self):
		ret = self.trigger_webhook('issues')
		self.assertEqual('[baxterthehacker/public-repo] Issue opened: Spelling error in the README file - https://github.com/baxterthehacker/public-repo/issues/2', ret)

	def test_pull_request(self):
		ret = self.trigger_webhook('pull_request')
		self.assertEqual('[baxterthehacker/public-repo] Pull request opened: Update the README with new information - https://github.com/baxterthehacker/public-repo/pull/1', ret)
