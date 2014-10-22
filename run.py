#!/usr/bin/env python

from ircbot import run_bot
import os.path

if __name__ == '__main__':
	root = os.path.dirname(__file__)
	yml_config = os.path.join(root, 'config.yml')
	storage_dir = os.path.join(root, 'storage')

	run_bot(
		yml_config = yml_config,
		storage_dir = storage_dir
	)
