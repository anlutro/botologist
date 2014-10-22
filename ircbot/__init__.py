import logging
log = logging.getLogger(__name__)

import sys
import yaml
import ircbot.irc
# import ircbot.bot

def run_bot(storage_dir, yml_config):
	with open(yml_config, 'r') as f:
		cfg = yaml.load(f.read())

	log_level = logging.INFO
	if 'log_level' in cfg:
		log_level = getattr(logging, cfg.get('log_level').upper())
	_configure_logging(log_level)

	client = ircbot.irc.Client(
		server = cfg.get('bot').get('server'),
		nick = 'pyircbot'
	)
	client.add_channel('#rzbot')
	client.run_forever()
	return

	bot = ircbot.bot.Bot(
		server = cfg.get('server'),
		storage_dir = storage_dir,
		**cfg.get('bot', {})
	)

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


def _configure_channels(bot, channel_dict):
	for channel, cfg in channel_dict.items():
		channel = ircbot.irc.Channel(channel)
		bot.add_channel(channel)
		for plugin in cfg.get('plugin', []):
			bot.register_plugin(plugin, channel)
