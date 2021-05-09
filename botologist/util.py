from datetime import datetime, tzinfo
import logging
import math
import html

try:
    unescape_html = html.unescape  # pylint: disable=no-member
except AttributeError:
    import html.parser

    unescape_html = html.parser.HTMLParser().unescape  # pylint: disable=no-member

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
        return timedelta_human_readable(dt - now)


def timedelta_human_readable(timedelta):
    seconds = timedelta.total_seconds()
    days = max(0, math.floor(seconds / (3600 * 24)))
    seconds -= 3600 * 24 * days
    hours = max(0, math.floor(seconds / 3600))
    seconds -= 3600 * hours
    minutes = max(0, math.floor(seconds / 60))
    seconds -= 60 * minutes

    parts = []
    if days > 0:
        parts.append("%dd" % days)
    if hours > 0:
        parts.append("%dh" % hours)
    if days == 0 and minutes > 0:
        parts.append("%dm" % minutes)
    if hours == 0 and minutes < 10 and seconds > 0:
        parts.append("%ds" % seconds)
    if parts:
        return " ".join(parts)
