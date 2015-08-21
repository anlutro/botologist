import logging, logging.handlers
log = logging.getLogger(__name__)

import sys
import ircbot.bot


def run_bot(config):
	try:
		# initialize the bot object
		bot = ircbot.bot.Bot(config)

		# infinite loop go!
		bot.run_forever()
	except:
		log.exception('Uncaught exception')
		print('An exception occurred - check log for details. Exiting!')
		sys.exit(1)
