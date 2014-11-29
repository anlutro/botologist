import logging
log = logging.getLogger(__name__)

import sys
import importlib
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

	log_level = logging.INFO
	if 'log_level' in cfg:
		log_level = getattr(logging, cfg.get('log_level').upper())
	_configure_logging(log_level)

	bot = ircbot.bot.Bot(
		storage_dir = storage_dir,
		global_plugins = cfg.get('global_plugins'),
		**cfg.get('bot', {})
	)

	_configure_plugins(bot, cfg.get('plugins', {}))
	_configure_channels(bot, cfg.get('channels', {}))

	bot.run_forever()


def _configure_logging(log_level):
	root = logging.getLogger()
	root.setLevel(log_level)
	ch = logging.StreamHandler(sys.stdout)
	ch.setLevel(log_level)
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	ch.setFormatter(formatter)
	root.addHandler(ch)


def _configure_plugins(bot, plugins_dict):
	for name, plugin_class in plugins_dict.items():
		parts = plugin_class.split('.')
		module = importlib.import_module('.'.join(parts[:-1]))
		plugin_class = getattr(module, parts[-1])
		bot.register_plugin(name, plugin_class)


def _configure_channels(bot, channel_dict):
	for channel, cfg in channel_dict.items():
		bot.add_channel(channel, cfg.get('plugins', []))
