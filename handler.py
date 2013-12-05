class MsgHandler():
	# commands are methods that reply to commands prefixed with an exclamation
	# mark, like '!help' or '!foo bar'
	commands = ['help']

	# replies are methods that scan a full message. if they return anything,
	# the return value will be the bot's reply in the channel
	replies = ['hello']

	def help(self, source, target, cmd, args):
		return 'No help for you! yet!'

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
		if (message[0] == '!'):
			msgparts = message.split(' ')
			cmd = msgparts[0][1:]
			args = msgparts[1:]
			return self._get_cmd_method(source, target, cmd, args)
		else:
			return self._loop_reply_methods(source, target, message)

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