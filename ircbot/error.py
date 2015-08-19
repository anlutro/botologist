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

	def handle_error(self, exception):
		log.exception(exception)

		short_msg = type(exception).__name__ + ' - ' + str(exception)
		long_msg = traceback.format_exc()

		self.bot._send_msg('An exception has occured: '+short_msg,
			self.bot.get_admin_nicks())

		email = MIMEText(traceback.format_exc(), _charset='utf-8')
		user = pwd.getpwuid(os.getuid())[0]
		email['From'] = user
		email['To'] = user
		email['Subject'] = 'IRC bot: Uncaught exception'

		p = subprocess.Popen(['/usr/sbin/sendmail', '-t', '-oi'],
			stdin=subprocess.PIPE)
		p.communicate(email.as_string().encode('utf-8'))
		log.info('Sent email with exception information to {}'.format(user))
