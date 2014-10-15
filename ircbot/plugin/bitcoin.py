import random

currencies = (
	'USD', 'EUR', 'hamburgers', 'farts', 'Razielcoins', 'BTC', 'salmons',
	'marble eggs in a shitty condom', 'typematrix keyboards', 'clean teeth',
	'dead Palestinian children', 'cmd.exe resizes', 'warp-in staplers',
	'mutalisks on creep', 'mutalisks off creep', 'floating cars',
	'burned rice', 'wordpress conference tickets', 'ice creams',
	'base64 encoded o\'reilly books', 'rolls of vitamin E toilet paper',
	'WISPY BEARDED POT SMOKING FAT FAGCUNT BITCOIN WORSHIPPERS WHO OBSESS OVER ME AND MAKE A SPORT OUT OF DRIVING ME INSANE AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'
)

def get_bitcoin_worth():
	num = random.randint(100,100000) / 100
	global currencies
	currency = random.choice(currencies)

	return '%.2f %s' % (num, currency)
