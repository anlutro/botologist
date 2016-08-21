import logging
log = logging.getLogger(__name__)

import re
import html

try:
	unescape_html = html.unescape # pylint: disable=no-member
except AttributeError:
	import html.parser
	unescape_html = html.parser.HTMLParser().unescape


# https://github.com/myano/jenni/wiki/IRC-String-Formatting
irc_format_pattern = re.compile(r'(\x03\d{1,2}(,\d{1,2})?)|[\x02\x03\x0F\x16\x1D\x1F]')
def strip_irc_formatting(string):
	return irc_format_pattern.sub('', string)


def decode(bytestring):
	try:
		return bytestring.decode('utf-8').strip()
	except UnicodeDecodeError:
		try:
			return bytestring.decode('iso-8859-1').strip()
		except:
			log.error('Could not decode string: %r', bytestring)
			return None


def decode_lines(bytestring):
	for substring in bytestring.split(b'\r\n'):
		line = decode(substring)
		if line:
			yield line
