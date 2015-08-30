import logging, logging.handlers
log = logging.getLogger(__name__)

import os
import os.path
import resource
import sys
import yaml

import botologist.bot

root_dir = os.getcwd()
config_path = os.path.join(root_dir, 'config.yml')

if len(sys.argv) > 1:
	config_path = sys.argv[1]
	if not config_path.startswith('/'):
		config_path = os.path.join(root_dir, config_path)

with open(config_path, 'r') as f:
	config = yaml.load(f.read())

# set some memory limits before getting started
mb = 1024 * 1024
resource.setrlimit(resource.RLIMIT_DATA, (
	config.get('memory_limit_soft', 64) * mb,
	config.get('memory_limit_hard', 96) * mb
))

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
	bot = botologist.bot.Bot(config)

	# use the git commit hash as version
	git_dir = os.path.join(root_dir, '.git')
	if os.path.isdir(git_dir):
		with open(os.path.join(git_dir, 'HEAD')) as f:
			ref = f.read().strip().split(': ')[-1]
		with open(os.path.join(git_dir, ref)) as f:
			bot.version = f.read().strip()[:8]

	bot.run_forever()
	print('Exiting!')
except:
	log.exception('Uncaught exception')
	print('An exception occurred - check log for details. Exiting!')
	sys.exit(1)
