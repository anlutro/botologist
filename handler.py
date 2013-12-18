from mods.docs import docs_cmd, apidocs_cmd, ghsearch_cmd
from mods.paste import repaste

class MsgHandler():
	# commands are methods that reply to commands prefixed with an exclamation
	# mark, like '!help' or '!foo bar'
	commands = ['help', 'helpme', 'dataja', 'ugt', 'nick', 'welcome', 'docscontrib',
		'paste', 'docs', 'api', 'gh', 'no', 'massassign', 'xy', 'tableflip']

	# replies are methods that scan a full message. if they return anything,
	# the return value will be the bot's reply in the channel
	replies = ['hello', 'pastebin']

	def help(self, source, args):
		return ('Before asking for help, use paste.laravel.com to provide 1.'
			'Your Laravel version (3, 4.0 or 4.1) and ALL relevant code'
			'(controllers, routes, models, views, anything) 2. Expected and'
			'actual behaviour 3. Any error messages you\'re getting.'
			'Thank you!')

	def helpme(self, source, args):
		return ('Before asking for help, use http://help.laravel.io to provide'
			'us the information we need to help you - Laravel version, '
			'expected/actual behavior, and all relevant code. Paste the link'
			'here when done. Thanks!')

	def dataja(self, source, args):
		return 'Don\'t ask to ask, Just ask!'

	def ugt(self, source, args):
		return ('It is always morning when someone comes into a channel. We call that'
			'Universal Greeting Time http://www.total-knowledge.com/~ilya/mips/ugt.html')

	def nick(self, source, args):
		return ('Hello! You\'re currently using a nick that\'s difficult to distinguish.'
			'Please type in "/nick your_name" so we can easily identify you. Thanks!')

	def welcome(self, source, args):
		return ('Hello, I\'m Rommie, the Laravel IRC Bot!  Welcome to Laravel :).'
			'If you have any questions, type !help to see how to best ask for assistance.'
			'If you need to paste code, check !paste for more info.  Thanks!')

	def docscontrib(self, source, args):
		return ('Want to contribute to the documentation? Awesome! Fork and'
			'submit a pull request at http://github.com/laravel/docs')

	def no(self, source, args):
		return 'NOOOOOOOOO! http://www.youtube.com/watch?v=umDr0mPuyQc'

	def massassign(self, source, args):
		return ('Getting a MassAssignmentException? Find out how to protect your'
			'input at: http://wiki.laravel.io/FAQ_(Laravel_4)#MassAssignmentException')

	def tableflip(self, source, args):
		return '(╯°□°)╯︵ ┻━┻'

	def xy(self, source, args):
		return ('It\'s difficult to discuss a solution without first understanding'
			'the problem. Please, explain the problem itself and not the solution'
			'that you have in mind. For more info on presenting your problem see'
			'!help. Thanks! Also see http://mywiki.wooledge.org/XyProblem')

	def fourone(self, source, args):
		return 'Upgrading from 4.0 to 4.1: http://laravel.com/docs/upgrade'

	def paste(self, source, args):
		return 'You may paste your code at http://paste.laravel.com'

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

	def hello(self, source, message):
		match = "hello " + self.bot.nick
		if match in message.lower():
			return 'Hello!'

	def pastebin(self, source, message):
		if 'http://pastebin.com/' in message:
			return ('Please avoid using pastebin.com as it is slow and forces'
				'others to look at ads. Please use http://paste.laravel.com or'
				'http://gist.github.com. Thanks!')

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