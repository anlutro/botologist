import json
import os.path

from mods.docs import docs_cmd, apidocs_cmd, ghsearch_cmd
from mods.paste import repaste
from mods.packagist import pkg_search
from mods.welcome import addgreet

class MsgHandler():
	# commands that have a method assigned to them
	commands = ['docs', 'api', 'gh', 'pkg']

	# replies are methods that scan a full message. if they return anything,
	# the return value will be the bot's reply in the channel
	replies = ['hello', 'pastebin', 'greetme']

	# commands loaded from storage/commands.json
	json_cmds = {}

	def docs(self, source, args):
		if len(args) > 0:
			search = ' '.join(args)
			return docs_cmd(search)
		else:
			return 'http://laravel.com/docs'

	def api(self, source, args):
		if len(args) > 0:
			search = ' '.join(args)
			return apidocs_cmd(search)
		else:
			return 'http://laravel.com/api/4.1'

	def gh(self, source, args):
		if len(args) > 0:
			search = ' '.join(args)
			return ghsearch_cmd(search)
		else:
			return 'https://github.com/laravel/framework'

	def pkg(self, source, args):
		if len(args) > 0:
			search = ' '.join(args)
			return pkg_search(search)

	def hello(self, source, message):
		match = "hello " + self.bot.nick
		if match in message.lower():
			return 'Hello!'

	def pastebin(self, source, message):
		if 'http://pastebin.com/' in message:
			return ('Please avoid using pastebin.com as it is slow and forces'
				'others to look at ads. Please use http://paste.laravel.com or'
				'http://gist.github.com. Thanks!')

	def greetme(self, source, message):
		check = self.bot.nick + ': i speak'
		offset = len(check)
		if message[:offset].lower() == check:
			nick = source.split('!')[0]
			return addgreet(nick, message[(offset+1):].lower())

	##################################################################

	def __init__(self, bot):
		self.bot = bot
		self._load_commands()

	def handle(self, event):
		source = event.source
		target = event.target
		message = event.arguments[0]

		return self._map_method(source, target, message)

	def _load_commands(self):
		storpath = os.path.dirname(os.path.realpath(__file__)) + '/storage/commands.json'
		try:
			with open(storpath, 'r') as f:
				self.json_cmds = json.load(f)
		except:
			pass

	def _add_command(self, command, response):
		if command in self.commands or command in self.json_cmds:
			return False

		self.json_cmds[command] = response
		storpath = os.path.dirname(os.path.realpath(__file__)) + '/storage/commands.json'
		with open(storpath, 'w+') as f:
			json.dump(self.json_cmds, f)

	def _map_method(self, source, target, message):
		if self._is_cmd(message):
			msgparts = message.split(' ')
			cmd = msgparts[0][1:]
			args = msgparts[1:]
			return self._get_cmd_method(cmd, source, args)
		elif self._is_aimed_cmd(message):
			split = message.split(':')
			msgparts = split[1].strip().split(' ')
			cmd = msgparts[0][1:]
			args = msgparts[1:]
			return split[0] + ': ' + self._get_cmd_method(cmd, source, args)
		else:
			return self._loop_reply_methods(source, message)

	def _is_cmd(self, message):
		return message[0] == '!'

	def _is_aimed_cmd(self, message):
		split = message.split(':')
		if len(split) == 1:
			return False
		return self._is_cmd(split[1].strip())

	def _get_cmd_method(self, cmd, source, args):
		if cmd in self.json_cmds:
			return self.json_cmds[cmd]
		
		if (cmd in self.commands):
			method = getattr(self, cmd)
		elif cmd == '41upgrade':
			method = getattr(self, 'fourone')
		else:
			return
		return method(source, args)	

	def _loop_reply_methods(self, source, message):
		for reply in self.replies:
			method = getattr(self, reply)
			result = method(source, message)
			if result is not None:
				return result