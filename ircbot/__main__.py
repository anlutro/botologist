import os
import os.path
import sys

import ircbot

root = os.getcwd()
yml_config = os.path.join(root, 'config.yml')
storage_dir = os.path.join(root, 'storage')

if len(sys.argv) > 1:
	yml_config = sys.argv[1]
	if not yml_config.startswith('/'):
		yml_config = os.path.join(root, yml_config)

ircbot.run_bot(
	yml_config = yml_config,
	storage_dir = storage_dir
)
