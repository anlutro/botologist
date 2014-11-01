import random
import urllib.request
import urllib.error
import re
import ircbot.plugin


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


class RedditeuPlugin(ircbot.plugin.Plugin):
	"""#redditeu plugin."""
	@ircbot.plugin.command('btc')
	def get_btc_worth(self, msg):
		return '1 bitcoin is currently worth ' + Bitcoin.get_worth()

	@ircbot.plugin.command('random')
	def get_yp_comment(self, msg):
		url = "http://www.youporn.com/random/video/"

		try:
			result = urllib.request.urlopen(url, timeout=2)
			response = result.read().decode()
			result.close()

			result = re.findall('<p class="message">((?:.|\\n)*?)</p>', response)

			if result:
				return random.choice(result).strip()
		except (timeout, urllib.error.URLError, UnicodeDecodeError):
			pass

		return 'Try again!'

	@ircbot.plugin.reply
	def nay_here(self, msg):
		if 'nay' not in msg.user.nick.lower():
			return

		# strip all non-standard characters
		msg_str = ''.join([c for c in msg.message if 32 <= ord(c) <= 122])
		msg_str = msg_str.lower().strip()

		if 'sup' == msg_str or 'yo' == msg_str:
			return 'gay here'
