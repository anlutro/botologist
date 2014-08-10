import sys
import os.path

from ircbot.bot import run_bot

def main():
	if len(sys.argv) < 4:
		print('Usage: ./run.py <server> <channel> <nick>')
		return

	root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
	storage_path = os.path.join(root_dir, 'storage')

	run_bot(
		server=sys.argv[1],
		port=6667,
		channel=sys.argv[2],
		nick=sys.argv[3],
		storage_path=storage_path
	)
