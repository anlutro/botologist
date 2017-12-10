from datetime import datetime, tzinfo
import logging
import re
import html
try:
	unescape_html = html.unescape # pylint: disable=no-member
except AttributeError:
	import html.parser
	unescape_html = html.parser.HTMLParser().unescape

import dateutil.parser
import pytz

log = logging.getLogger(__name__)


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


def parse_dt(dt, tz=None):
	if not isinstance(dt, datetime):
		dt = dateutil.parser.parse(dt)
	if tz:
		if not isinstance(tz, tzinfo):
			tz = pytz.timezone(tz)
		dt = dt.astimezone(tz=tz)
	return dt


def time_until(dt: datetime):
	if not isinstance(dt, datetime):
		dt = dateutil.parser.parse(dt)
	now = datetime.now(dt.tzinfo)
	if dt > now:
		time_left = dt - now
		if time_left.days > 0:
			time_left_str = '%dd %dh' % (
				time_left.days,
				round(time_left.seconds / 3600),
			)
		elif time_left.seconds > 3600:
			time_left_str = '%dh %dm' % (
				round(time_left.seconds / 3600),
				round((time_left.seconds % 3600) / 60),
			)
		else:
			time_left_str = '%dm' % round(time_left.seconds / 60)
		return time_left_str
