import logging
log = logging.getLogger(__name__)

import random
import re

import botologist.plugin


class Bitcoin:
	currencies = (
		'Razielcoins', 'bitcoins', 'cmd.exe resizes', 'scotweb extortions',
		'warp-in staplers', 'dead Palestinian children', 'typematrix keyboards',
		'marble eggs in a shitty condom', 'clean teeth', 'mutalisks on creep',
		'mutalisks off creep', 'floating cars', 'floating keys', 'burned rice',
		'wordpress conference tickets', 'base64 encoded o\'reilly books',
		'rolls of vitamin E toilet paper', 'one-night trips to Rhodos',
		('WISPY BEARDED POT SMOKING FAT FAGCUNT BITCOIN WORSHIPPERS WHO OBSESS '
		 'OVER ME AND MAKE A SPORT OUT OF DRIVING ME INSANE AAAAAAAAAAAAAAAAAAA'
		 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'),
	)

	@classmethod
	def get_worth(cls):
		num = random.randint(100, 100000) / 100
		currency = random.choice(cls.currencies)
		return '%.2f %s' % (num, currency)


class Raziel:
	nicks = ('radio', 'brazier', 'easel', 'raIel', 'easiek', 'ramen', 'russell',
		'fazorø', 'razu', 'rsdirø', 'rasjjmm', 'fszirh', 'eterisk feKfl',
		'Raskelf', 'was oro', 'raIeö', 'fackförbund', 'taxiförare', 'Dr Dre',
		'e as isj')

	@classmethod
	def get_random_nick(cls):
		return random.choice(cls.nicks)


def get_random_time():
	hour = random.choice((
		random.randint(-23, -1),
		random.randint(13, 32),
	))
	minute = random.randint(0, 99)
	ampm = random.choice(('AM', 'PM'))

	return '{}:{} {}'.format(hour, str(minute).zfill(2), ampm)


def get_random_date():
	year = random.randint(1000, 9999)
	month = random.randint(0, 12)
	day = random.randint(0, 31)

	args = [str(day).zfill(2), str(month).zfill(2), str(year)]
	random.shuffle(args)

	separator = random.choice(('-', '/', '.'))

	return separator.join(args)


class RedditeuPlugin(botologist.plugin.Plugin):
	"""#redditeu plugin."""

	def __init__(self, bot, channel):
		super().__init__(bot, channel)

		self.insults = (
			re.compile(r'.*fuck(\s+you)\s*,?\s*'+self.bot.nick+r'.*', re.IGNORECASE),
			re.compile(r'.*'+self.bot.nick+r'[,:]?\s+fuck\s+you.*', re.IGNORECASE),
			re.compile(r'.*shut\s*up\s*,?\s*'+self.bot.nick+r'.*', re.IGNORECASE),
			re.compile(r'.*'+self.bot.nick+r'[,:]?\s+shut\s+up.*', re.IGNORECASE),
		)

		self.monologue_lastuser = None
		self.monologue_counter = 0

	@botologist.plugin.reply()
	def return_insults(self, msg):
		for expr in self.insults:
			if expr.match(msg.message):
				return ('{}: I feel offended by your recent action(s). Please '
					'read http://stop-irc-bullying.eu/stop').format(msg.user.nick)

	no_work = re.compile(r".*(__)?bot(__)?\s+(no|not|does ?n.?t)\s+work.*", re.IGNORECASE)

	@botologist.plugin.reply()
	def bot_always_works(self, msg):
		if self.no_work.match(msg.message):
			return 'I always work'

	@botologist.plugin.command('btc')
	def get_btc_worth(self, cmd):
		return '1 bitcoin is currently worth ' + Bitcoin.get_worth()

	@botologist.plugin.command('michael')
	def who_is_michael(self, cmd):
		'''Find out what nick Michael is hiding under.'''
		channel = self.bot.client.channels.get(cmd.message.target)
		if not channel:
			return
		for user in channel.users:
			if 'cunt' in user.ident or '78.153.150.16' in user.host:
				return 'The new Micahel is ' + user.name
			if 'nevzetz' in user.host or 'ip51cc146b.speed.planet.nl' in user.host:
				return 'Michael is ' + user.name
			if 'steele' in user.name.lower():
				return "There's a chance it's " + user.name
		return 'Michael not found!'

	@botologist.plugin.command('time')
	def the_time(self, cmd):
		'''If you need to know what the time really is. For really reals.'''
		return 'the time is {} - the date is {}'.format(
			get_random_time(), get_random_date())

	@botologist.plugin.command('speedtest')
	def speedtest(self, cmd):
		return 'Pretty fast, thank you.'

	@botologist.plugin.join()
	def welcome(self, user, channel):
		if 'happy0' in user.nick.lower():
			return 'ypyotootp hippy 0'
		if user.nick.lower().startswith('raziel'):
			return 'hello ' + Raziel.get_random_nick()

	@botologist.plugin.reply()
	def no_more_that_are_stupid(self, msg):
		if 'no more irc binds that are stupid' in msg.message.lower():
			return 'https://www.youtube.com/watch?v=LGxS-qjViNQ'

	@botologist.plugin.reply()
	def garner_masturbation_video(self, msg):
		if 'garner masturbation video' in msg.message.lower():
			return 'https://www.youtube.com/watch?v=akTE1n-U0C0'

	@botologist.plugin.reply()
	def deridu(self, msg):
		msgl = msg.message.lower()
		if msgl == 'deridu':
			return 'what the fuck is this'
		elif 'fuck is this' in msgl or 'what the fuck is' msgl:
			return 'watch yo profamity'
		elif msgl == 'watch your profanity' or msgl == 'watch your profamity' \
				or msgl == 'watch yo profamity' or msgl == 'watchoprofamity' \
				or msgl == 'watcho profamity':
			return 'right I\'m sorry'

	@botologist.plugin.reply()
	def monologue_detector(self, msg):
		if msg.user == self.monologue_lastuser:
			self.monologue_counter += 1
		else:
			self.monologue_lastuser = msg.user
			count = self.monologue_counter
			self.monologue_counter = 1
			if count > 15:
				return 'AUTISM C-C-C-C-COMBO BREAKER! ({} line long monologue)'.format(count)

	@botologist.plugin.kick()
	def kick_handler(self, kicked_user, channel, user):
		print(kicked_user.identifier, self.monologue_lastuser.identifier)
		if kicked_user == self.monologue_lastuser:
			self.monologue_lastuser = None
			count = self.monologue_counter
			self.monologue_counter = 1
			if count > 15:
				return 'AUTISM C-C-C-C-COMBO BREAKER! ({} line long monologue)'.format(count)

	@botologist.plugin.reply()
	def nooooo(self, msg):
		if 'nooo' in msg.message.lower():
			return 'https://vid.me/1VfD'

	@botologist.plugin.reply()
	def guys(self, msg):
		msgl = msg.message.lower()
		if 'dont be late' in msgl or "don't be late" in msgl:
			return 'same to you'
