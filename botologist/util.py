from datetime import datetime, tzinfo
import logging
import html
try:
	unescape_html = html.unescape # pylint: disable=no-member
except AttributeError:
	import html.parser
	unescape_html = html.parser.HTMLParser().unescape

import dateutil.parser
import pytz

log = logging.getLogger(__name__)


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
