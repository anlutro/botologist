import unittest
from unittest import mock
from botologist import error

class ErrorHandlerTest(unittest.TestCase):
	def test_exception_is_formatted_correctly(self):
		try:
			raise RuntimeError('test')
		except:
			medium_msg, long_msg = error.format_error()

		self.assertEqual('Uncaught exception - RuntimeError: test', medium_msg)
		self.assertEqual('Traceback (most recent call last):\n'
			'  File "'+__file__+'", line 8, in test_exception_is_formatted_correctly\n'
			'    raise RuntimeError(\'test\')\nRuntimeError: test', long_msg)

	def test_error_message_is_formatted_correctly(self):
		try:
			raise RuntimeError('test')
		except:
			medium_msg, long_msg = error.format_error('doing stuff')

		self.assertEqual('doing stuff - RuntimeError: test', medium_msg)
		self.assertEqual('Traceback (most recent call last):\n'
			'  File "'+__file__+'", line 19, in test_error_message_is_formatted_correctly\n'
			'    raise RuntimeError(\'test\')\nRuntimeError: test', long_msg)
