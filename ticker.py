import time

class Ticker():
	checks = ['test']

	def test(self):
		self.bot.msg_chan('Ticker test!')

	def __init__(self, bot):
		self.bot = bot
		self.streamchecker = StreamChecker()
		self.stopped = False

	def run(self, sleepfor):
		while self.stopped is not True:
			for check in self.checks:
				method = getattr(self, check)
				method()
			time.sleep(sleepfor)

	def stop(self):
		self.stopped = True