import datetime
import random
import re
import socket
import urllib.error
import urllib.request

from ircbot import log
import ircbot.plugin


class YouPornComment():
	_last_fetch = None
	THROTTLE_SECS = 30

	@classmethod
	def get_random(cls, include_url=False):
		now = datetime.datetime.now()
		if cls._last_fetch is not None:
			diff = now - cls._last_fetch
			if diff.seconds < (cls.THROTTLE_SECS):
				log.debug('YouPorn comment less than {secs} seconds old, blocking'.format(
					secs=cls.THROTTLE_SECS))
				return False

		cls._last_fetch = now
		result = cls._get_random(include_url)

		return result

	@staticmethod
	def _get_random(include_url=False):
		try:
			response = urllib.request.urlopen('http://www.youporn.com/random/video/',
				timeout=2)
			result = response.read().decode()
			response.close()

			result = re.findall('<p class="message">((?:.|\\n)*?)</p>', result)

			if result is None:
				log.debug('No comments found in '+response.url)
				return None

			result = random.choice(result).strip().replace('\r', '').replace('\n', ' ')

			if ' ' not in result and '+' in result:
				result = result.replace('+', ' ')

			if include_url:
				# remove the long slug at the end of the URL
				url = '/'.join(response.url.split('/')[:-2])

				result = result + ' (' + url + ')'

			return result
		except (socket.timeout, urllib.error.URLError, UnicodeDecodeError):
			log.debug('HTTP request failed')
			pass

		return None


class Bitcoin:
	currencies = (
		'USD', 'EUR', 'hamburgers', 'farts', 'Razielcoins', 'BTC', 'salmons',
		'marble eggs in a shitty condom', 'typematrix keyboards', 'clean teeth',
		'dead Palestinian children', 'cmd.exe resizes', 'warp-in staplers',
		'mutalisks on creep', 'mutalisks off creep', 'floating cars',
		'burned rice', 'wordpress conference tickets', 'ice creams',
		'base64 encoded o\'reilly books', 'rolls of vitamin E toilet paper',
		'WISPY BEARDED POT SMOKING FAT FAGCUNT BITCOIN WORSHIPPERS WHO OBSESS OVER ME AND MAKE A SPORT OUT OF DRIVING ME INSANE AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'
	)

	@classmethod
	def get_worth(cls):
		num = random.randint(100,100000) / 100
		currency = random.choice(cls.currencies)
		return '%.2f %s' % (num, currency)	


class Raziel:
	nicks = ('radio', 'brazier', 'easel', 'raIel', 'easiek', 'ramen', 'russell')

	@classmethod
	def get_random_nick(cls):
		return random.choice(cls.nicks)


class RedditeuPlugin(ircbot.plugin.Plugin):
	"""#redditeu plugin."""
	@ircbot.plugin.command('btc')
	def get_btc_worth(self, cmd):
		return '1 bitcoin is currently worth ' + Bitcoin.get_worth()

	@ircbot.plugin.command('random')
	def get_yp_comment(self, cmd):
		result = YouPornComment.get_random(True)
		if result is False:
			return None

		if result:
			return result
		else:
			return 'No comment found, try again later!'

	@ircbot.plugin.command('michael')
	def who_is_michael(self, cmd):
		channel = self.bot.conn.channels.get(cmd.message.target)
		if not channel:
			return
		for (host,nick) in channel.host_map.items():
			if 'nevzetz' in host or 'ip51cc146b.speed.planet.nl' in host:
				return 'Michael is ' + nick
		return 'Michael not found!'

	@ircbot.plugin.join
	def welcome(self, user, channel):
		if 'happy0' in user.nick.lower():
			return 'ypyotootp hippy 0'
		if user.nick.lower().startswith('raziel'):
			return 'hello ' + Raziel.get_random_nick()
