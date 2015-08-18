import logging, logging.handlers
log = logging.getLogger(__name__)

import importlib
import sys
import yaml

import ircbot.irc
import ircbot.bot
import ircbot.plugin

# makes it possible to `import ircbot.cfg` for global access to the config dict
cfg = {}

def run_bot(storage_dir, yml_config):
	def configure_logging(log_level, log_path=None):
		# set the level
		root = logging.getLogger()
		root.setLevel(log_level)

		if log_path is None:
			ch = logging.StreamHandler(sys.stdout)
		else:
			ch = logging.handlers.RotatingFileHandler(log_path, maxBytes=(1048576*5), backupCount=7)
		ch.setLevel(log_level)

		# define the logging format
		formatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(name)s - %(message)s')
		ch.setFormatter(formatter)

		# add the logging handler for all loggers
		root.addHandler(ch)


	def configure_plugins(bot, plugins_dict):
		for name, plugin_class in plugins_dict.items():
			# convenience compatibility layer for when plugins module was moved
			plugin_class = plugin_class.replace('ircbot.plugin.', 'plugins.')

			# dynamically import the plugin module and pass the class
			parts = plugin_class.split('.')
			module = importlib.import_module('.'.join(parts[:-1]))
			plugin_class = getattr(module, parts[-1])
			bot.register_plugin(name, plugin_class)


	def configure_channels(bot, channel_dict):
		for name, channel in channel_dict.items():
			bot.add_channel(name, channel.get('plugins', []), channel.get('admins', []))

	global cfg

	with open(yml_config, 'r') as f:
		cfg = yaml.load(f.read())

	# read the logging level from the config file, defaulting to INFO
	log_level = logging.INFO
	if 'log_level' in cfg:
		log_level = getattr(logging, cfg.get('log_level').upper())
	configure_logging(log_level, cfg.get('log_path'))

	try:
		# initialize the bot object
		bot = ircbot.bot.Bot(
			storage_dir = storage_dir,
			global_plugins = cfg.get('global_plugins', []),
			**cfg.get('bot', {})
		)

		configure_plugins(bot, cfg.get('plugins', {}))
		configure_channels(bot, cfg.get('channels', {}))

		# infinite loop go!
		bot.run_forever()
	except:
		log.exception('Uncaught exception')
		print('An exception occurred - check log for details. Exiting!')
		sys.exit(1)
