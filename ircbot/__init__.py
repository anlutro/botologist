from ircbot.bot import Bot
import sys

def run_bot(**kwargs):
	bot = Bot(**kwargs)

	try:
		bot.start()
	except KeyboardInterrupt:
		print('Quitting!')
		bot.die()
