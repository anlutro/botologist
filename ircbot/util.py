import logging
log = logging.getLogger(__name__)

import threading

import html
try:
	unescape_html = html.unescape
except AttributeError:
	import html.parser
	html = html.parser.HTMLParser()
	unescape_html = html.unescape


def decode(bytestring):
	"""Attempt to decode a byte string into a UTF-8 string.

	Because IRC doesn't enforce any particular encoding, we have to either guess
	what encoding is being used, or keep trying until it works. UTF-8 and
	ISO-8859-1 (Windows) are the most common, so we just try those two.
	"""
	try:
		return bytestring.decode('utf-8').strip()
	except UnicodeDecodeError:
		try:
			return bytestring.decode('iso-8859-1').strip()
		except:
			log.error('Could not decode string: '+repr(bytestring))
			return None


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
