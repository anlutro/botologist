#!/usr/bin/env python3

import os.path
from sys import argv

from ircbot import run_bot

def main():
	if len(argv) < 4:
		print('Usage: ./run.py <server> <channel> <nick>')
		return

	cwd = os.path.dirname(os.path.realpath(__file__))
	storage_path = os.path.join(cwd, 'storage')

	run_bot(
		server=argv[1],
		port=6667,
		channel=argv[2],
		nick=argv[3],
		storage_path=storage_path
	)

if __name__ == '__main__':
	main()
