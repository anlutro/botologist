#!/usr/bin/env python3

import os.path

from ircbot import run_bot

if __name__ == '__main__':
	cwd = os.path.dirname(os.path.realpath(__file__))
	storage_path = os.path.join(cwd, 'storage')

	run_bot(
		server='irc.quakenet.org',
		port=6667,
		channel='#rzbot',
		nick='rzbot',
		storage_path=storage_path
	)
