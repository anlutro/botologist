import logging
log = logging.getLogger(__name__)

from email.mime.text import MIMEText
import os
import pwd
import subprocess
import traceback


class ErrorHandler:
	def __init__(self, bot):
		self.bot = bot

	def handle_error(self, exception=None):
		long_msg = traceback.format_exc()

		if isinstance(exception, str):
			short_msg = exception.split('\n')[0]
		elif isinstance(exception, Exception):
			short_msg = 'Uncaught exception - {}: {}'.format(
				type(exception).__name__, str(exception))
		else:
			short_msg = long_msg.split('\n')[-1]

		log.exception(short_msg)

		self.bot._send_msg(short_msg, self.bot.get_admin_nicks())

		email = MIMEText(long_msg)
		user = pwd.getpwuid(os.getuid())[0]
		email['From'] = user
		email['To'] = user
		email['Subject'] = '[botologist] ' + short_msg

		p = subprocess.Popen(['/usr/sbin/sendmail', '-t', '-oi'],
			stdin=subprocess.PIPE)
		p.communicate(email.as_string().encode('utf-8'))
		log.info('Sent email with exception information to {}'.format(user))
