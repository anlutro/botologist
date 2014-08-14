import sys
import os.path
import configparser
import argparse

from ircbot.bot import run_bot

def main():
	root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
	storage_path = os.path.join(root_dir, 'storage')
	options = ('server', 'nick', 'port', 'channel',)

	deets = dict.fromkeys(options)
	deets.update({'storage_path': storage_path})

	parser = argparse.ArgumentParser(description='Raziel IRC Bot')
	parser.add_argument('-c', '--config',
		help="Specify config file",
		type=argparse.FileType('r'),
		default='{path}/ircbot.conf'.format(path=storage_path),
	)
	parser.add_argument('-s', '--server',
		help='IRC server',
	)
	parser.add_argument('-n', '--nick',
		help='Bot nickname',
	)
	parser.add_argument('-p', '--port',
		help='IRC port',
		type=int,
	)
	parser.add_argument('-x', '--channel',
		help='IRC channel',
	)
	args = parser.parse_args()
	
	config = configparser.ConfigParser()
	config.read_file(args.config)
	

	if 'server' in config:
		for option in options:
			if option in config['server']:
				deets[option] = config['server'][option]
	
	# Overwrite if cmd line specified
	for option in options:
		if getattr(args, option):
			deets[option] = getattr(args, option)

	run_bot(**deets)
