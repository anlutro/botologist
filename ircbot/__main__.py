import logging, logging.handlers
log = logging.getLogger(__name__)

import os
import os.path
import sys
import yaml

import ircbot
import ircbot.bot

root_dir = os.getcwd()
config_path = os.path.join(root_dir, 'config.yml')

if len(sys.argv) > 1:
	config_path = sys.argv[1]
	if not config_path.startswith('/'):
		config_path = os.path.join(root_dir, config_path)

with open(config_path, 'r') as f:
	config = yaml.load(f.read())

if 'storage_dir' in config:
	if not config['storage_dir'].startswith('/'):
		config['storage_dir'] = os.path.join(root_dir, config['storage_dir'])
else:
	config['storage_dir'] = os.path.join(root_dir, 'storage')

# read the logging level from the config file, defaulting to INFO
log_level = logging.INFO
if 'log_level' in config:
	log_level = getattr(logging, config.get('log_level').upper())

# set the level
root = logging.getLogger()
root.setLevel(log_level)

log_path = config.get('log_path')

if log_path:
	handler = logging.handlers.RotatingFileHandler(
		log_path, maxBytes=(1048576*5), backupCount=7)
else:
	handler = logging.StreamHandler(sys.stdout)

handler.setLevel(log_level)

# define the logging format
formatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(name)s - %(message)s')
handler.setFormatter(formatter)

# add the logging handler for all loggers
root.addHandler(handler)

# initialize and run the bot
try:
	print('Starting IRC bot...')
	bot = ircbot.bot.Bot(config)
	bot.run_forever()
	print('Exiting!')
except:
	log.exception('Uncaught exception')
	print('An exception occurred - check log for details. Exiting!')
	sys.exit(1)
