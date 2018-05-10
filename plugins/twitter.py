import datetime
import tweepy

import botologist.plugin
import botologist.util


class TwitterPlugin(botologist.plugin.Plugin):
	SPAM_THROTTLE = 10

	def __init__(self, bot, channel):
		super().__init__(bot, channel)
		self.cfg = self.bot.config.get('twitter_api')
		if not self.cfg:
			raise RuntimeError('twitter_api config missing - check your config file!')
		self.api = None
		self.last_fetch = None

	@botologist.plugin.reply()
	async def twitter(self, msg):
		if 'twitter.com/' not in msg.message:
			return

		for word in msg.words:
			if 'twitter.com/' in word:
				break

		parts = word.split('/')
		if len(parts) < 5 or parts[4] != 'status':
			return

		return self.get_tweet_text(parts[5])

	def get_tweet_text(self, tweet_id):
		if self.api is None:
			self.api = self.make_api()

		now = datetime.datetime.now()
		if self.last_fetch:
			diff = now - self.last_fetch
			if diff.seconds < self.SPAM_THROTTLE:
				return
		self.last_fetch = now

		tweet = self.api.get_status(tweet_id)

		author = tweet.author.screen_name
		body = tweet.text.replace('\n', ' ')
		body = botologist.util.unescape_html(body)

		return '[{author}] {body}'.format(author='@'+author, body=body)

	def make_api(self):
		auth = tweepy.OAuthHandler(consumer_key=self.cfg['consumer_key'],
			consumer_secret=self.cfg['consumer_secret'])
		auth.set_access_token(key=self.cfg['access_token'],
			secret=self.cfg['access_token_secret'])
		return tweepy.API(auth)
