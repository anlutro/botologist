from mods.docs import docs_cmd, apidocs_cmd, ghsearch_cmd

class MsgHandler():
	# commands are methods that reply to commands prefixed with an exclamation
	# mark, like '!help' or '!foo bar'
	commands = ['help', 'docs', 'api', 'gh']

	# replies are methods that scan a full message. if they return anything,
	# the return value will be the bot's reply in the channel
	replies = ['hello']

	def help(self, source, target, cmd, args):
		return ('Before asking for help, use paste.laravel.com to provide'
		        '1. Your Laravel version (3, 4.0 or 4.1) and ALL relevant code'
		        '(controllers, routes, models, views, anything) 2. Expected and'
		        'actual behaviour 3. Any error messages you\'re getting.'
		        'Thank you!')

	def docs(self, source, target, cmd, args):
		if len(args) > 0:
			search = ' '.join(args)
			return docs_cmd(search)
		else:
			return 'http://laravel.com/docs'

	def api(self, source, target, cmd, args):
		if len(args) > 0:
			search = ' '.join(args)
			return apidocs_cmd(search)
		else:
			return 'http://laravel.com/api/4.1'

	def gh(self, source, target, cmd, args):
		if len(args) > 0:
			search = ' '.join(args)
			return ghsearch_cmd(search)
		else:
			return 'https://github.com/laravel/framework'

	def hello(self, source, target, message):
		match = "hello " + self.bot.nick
		if match in message:
			return 'Hello!'

	##################################################################

	def __init__(self, bot):
		self.bot = bot

	def handle(self, event):
		source = event.source
		target = event.target
		message = event.arguments[0]

		return self._map_method(source, target, message)

	def _map_method(self, source, target, message):
		if self._is_cmd(message):
			msgparts = message.split(' ')
			cmd = msgparts[0][1:]
			args = msgparts[1:]
			return self._get_cmd_method(source, target, cmd, args)
		elif self._is_aimed_cmd(message):
			split = message.split(':')
			msgparts = split[1].strip().split(' ')
			cmd = msgparts[0][1:]
			args = msgparts[1:]
			return split[0] + ': ' + self._get_cmd_method(source, target, cmd, args)
		else:
			return self._loop_reply_methods(source, target, message)

	def _is_cmd(self, message):
		return message[0] == '!'

	def _is_aimed_cmd(self, message):
		split = message.split(':')
		if len(split) == 1:
			return False
		return self._is_cmd(split[1].strip())

	def _get_cmd_method(self, source, target, cmd, args):
		if (cmd in self.commands):
			method = getattr(self, cmd)
			return method(source, target, cmd, args)

	def _loop_reply_methods(self, source, target, message):
		for reply in self.replies:
			method = getattr(self, reply)
			result = method(source, target, message)
			if result is not None:
				return result