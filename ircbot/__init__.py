import logging, logging.handlers
# makes it possible to `import ircbot.log` for global access to application logging
log = logging.getLogger(__name__)

import importlib
import os
import os.path
import sys
import yaml

import ircbot.irc
import ircbot.bot
import ircbot.plugin

# makes it possible to `import ircbot.cfg` for global access to the config dict
cfg = {}

def run_bot(storage_dir, yml_config):
	global cfg

	with open(yml_config, 'r') as f:
		cfg = yaml.load(f.read())

	# read the logging level from the config file, defaulting to INFO
	log_level = logging.INFO
	if 'log_level' in cfg:
		log_level = getattr(logging, cfg.get('log_level').upper())
	_configure_logging(log_level, cfg.get('log_path'))

	# initialize the bot object
	bot = ircbot.bot.Bot(
		storage_dir = storage_dir,
		global_plugins = cfg.get('global_plugins', []),
		**cfg.get('bot', {})
	)

	_configure_plugins(bot, cfg.get('plugins', {}))
	_configure_channels(bot, cfg.get('channels', {}))

	# infinite loop go!
	bot.run_forever()


def _configure_logging(log_level, log_path=None):
	# set the level
	root = logging.getLogger()
	root.setLevel(log_level)

	if log_path is None:
		ch = logging.StreamHandler(sys.stdout)
	else:
		ch = logging.handlers.RotatingFileHandler(log_path, maxBytes=(1048576*5), backupCount=7)
	ch.setLevel(log_level)

	# define the logging format
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	ch.setFormatter(formatter)

	# add the logging handler for all loggers
	root.addHandler(ch)


def _configure_plugins(bot, plugins_dict):
	for name, plugin_class in plugins_dict.items():
		# dynamically import the plugin module and pass the class
		parts = plugin_class.split('.')
		module = importlib.import_module('.'.join(parts[:-1]))
		plugin_class = getattr(module, parts[-1])
		bot.register_plugin(name, plugin_class)


def _configure_channels(bot, channel_dict):
	for channel, cfg in channel_dict.items():
		bot.add_channel(channel, cfg.get('plugins', []), cfg.get('admins', []))


def main():
	root = os.getcwd()
	yml_config = os.path.join(root, 'config.yml')
	storage_dir = os.path.join(root, 'storage')

	if len(sys.argv) > 1:
		yml_config = sys.argv[1]
		if not yml_config.startswith('/'):
			yml_config = os.path.join(root, yml_config)

	run_bot(
		yml_config = yml_config,
		storage_dir = storage_dir
	)

if __name__ == '__main__':
	main()
