import random

from ircbot import log
import ircbot.plugin


class Bitcoin:
	currencies = (
		'Razielcoins', 'bitcoins', 'cmd.exe resizes', 'scotweb extortions',
		'warp-in staplers', 'dead Palestinian children', 'typematrix keyboards',
		'marble eggs in a shitty condom', 'clean teeth', 'mutalisks on creep',
		'mutalisks off creep', 'floating cars', 'floating keys', 'burned rice',
		'wordpress conference tickets', 'base64 encoded o\'reilly books',
		'rolls of vitamin E toilet paper', 'one-night trips to Rhodos',
		'WISPY BEARDED POT SMOKING FAT FAGCUNT BITCOIN WORSHIPPERS WHO OBSESS OVER ME AND MAKE A SPORT OUT OF DRIVING ME INSANE AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA',
	)

	@classmethod
	def get_worth(cls):
		num = random.randint(100,100000) / 100
		currency = random.choice(cls.currencies)
		return '%.2f %s' % (num, currency)	


class Raziel:
	nicks = ('radio', 'brazier', 'easel', 'raIel', 'easiek', 'ramen', 'russell',
		'fazorø', 'razu', 'rsdirø', 'rasjjmm', 'fszirh', 'eterisk feKfl')

	@classmethod
	def get_random_nick(cls):
		return random.choice(cls.nicks)


def get_random_time():
	h = random.choice((
		random.randint(-23, -1),
		random.randint(13, 32),
	))

	m = random.randint(0,99)

	ampm = random.choice(('AM', 'PM'))

	return '{}:{} {}'.format(h, str(m).zfill(2), ampm)


class RedditeuPlugin(ircbot.plugin.Plugin):
	"""#redditeu plugin."""
	@ircbot.plugin.command('btc')
	def get_btc_worth(self, cmd):
		return '1 bitcoin is currently worth ' + Bitcoin.get_worth()

	@ircbot.plugin.command('michael')
	def who_is_michael(self, cmd):
		channel = self.bot.conn.channels.get(cmd.message.target)
		if not channel:
			return
		for (host,nick) in channel.host_map.items():
			if 'nevzetz' in host or 'ip51cc146b.speed.planet.nl' in host:
				return 'Michael is ' + nick
		return 'Michael not found!'

	@ircbot.plugin.command('time')
	def the_time(self, cmd):
		return 'the time is ' + get_random_time()

	@ircbot.plugin.join
	def welcome(self, user, channel):
		if 'happy0' in user.nick.lower():
			return 'ypyotootp hippy 0'
		if user.nick.lower().startswith('raziel'):
			return 'hello ' + Raziel.get_random_nick()
