import threading


class ErrorProneThread(threading.Thread):
	def __init__(self, *args, error_handler=None, **kwargs):
		self.error_handler = error_handler
		super().__init__(*args, **kwargs)

	def run(self):
		try:
			super().run()
		except Exception as exception:
			if self.error_handler:
				self.error_handler(exception)
			else:
				raise
