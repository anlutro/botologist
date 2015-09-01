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

	def handle_error(self, error=None):
		short_msg = 'Uncaught exception'
		long_msg = traceback.format_exc()

		if isinstance(error, Exception):
			medium_msg = 'Uncaught exception - {}: {}'.format(
				type(error).__name__, str(error))
		else:
			# should get the exception type and message
			medium_msg = long_msg.strip().split('\n')[-1]
			if isinstance(error, str):
				short_msg = error.strip().split('\n')[0]
				medium_msg = '{} - {}'.format(short_msg, medium_msg)

		log.exception(medium_msg)

		self.bot._send_msg(medium_msg, self.bot.get_admin_nicks())

		email = MIMEText(long_msg)
		user = pwd.getpwuid(os.getuid())[0]
		email['From'] = user
		email['To'] = user
		email['Subject'] = '[botologist] ' + medium_msg

		p = subprocess.Popen(['/usr/sbin/sendmail', '-t', '-oi'],
			stdin=subprocess.PIPE)
		p.communicate(email.as_string().encode('utf-8'))
		log.info('Sent email with exception information to {}'.format(user))
