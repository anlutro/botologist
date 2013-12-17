from mods.rss import LioRssChecker, StackRssChecker
import time

class Ticker():
	checks = ['lio_rss', 'so_rss']

	def lio_rss(self):
		self.lio.update()
		if self.lio.has_news():
			for news in self.lio.get_news():
				self.bot.msg_chan(news)

	def so_rss(self):
		self.so.update()
		if self.so.has_news():
			for news in self.so.get_news():
				self.bot.msg_chan(news)

	###############################################

	def __init__(self, bot):
		self.bot = bot
		self.stopped = False
		self.lio = LioRssChecker()
		self.so = StackRssChecker()

	def run(self, sleepfor):
		while self.stopped is not True:
			for check in self.checks:
				method = getattr(self, check)
				method()
			time.sleep(sleepfor)

	def stop(self):
		self.stopped = True