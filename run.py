#!/usr/bin/env python3

"""IRC bot

Usage:
  run.py <server> <nick> <channel>
"""

from docopt import docopt
from bot import Bot

def parse_server(input):
	args = input.split(':')
	server = args[0]
	if len(args) > 1:
		port = args[1]
	else:
		port = 6667
	return server, port

def main():
	args = docopt(__doc__)
	server, port = parse_server(args['<server>'])
	nick = args['<nick>']
	channel = '#' + args['<channel>']

	bot = Bot(channel, nick, server, port)
	
	try:
		bot.start()
	except KeyboardInterrupt:
		bot.stop()

if __name__ == '__main__':
	main()