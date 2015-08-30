import unittest

from botologist.util import strip_irc_formatting


class UtilTest(unittest.TestCase):
	def test_strip_irc_formatting(self):
		self.assertEqual('foo bar', strip_irc_formatting('\x0301,02foo\x03 bar'))
		self.assertEqual('foo bar', strip_irc_formatting('\x0301,02foo\x0F bar'))
		self.assertEqual('foo bar', strip_irc_formatting('\x02foo\x0F \x16bar\x0F'))
