import logging
log = logging.getLogger(__name__)

from email.mime.text import MIMEText
import os
import pwd
import subprocess
import traceback


def send_email(email, sendmail_bin, sendmail_args=None):
	if sendmail_args is None:
		sendmail_args = ['-t', '-oi']
	elif isinstance(sendmail_args, str):
		sendmail_args = sendmail_args.split()
	p = subprocess.Popen([sendmail_bin] + sendmail_args, stdin=subprocess.PIPE)
	p.communicate(email.as_string().encode('utf-8'))


def format_error(message=None):
	long_msg = traceback.format_exc().strip()
	# should get the exception type and message
	medium_msg = long_msg.split('\n')[-1]
	short_msg = 'Uncaught exception'

	if isinstance(message, str):
		short_msg = message.split('\n')[0]
	medium_msg = '{} - {}'.format(short_msg, medium_msg)

	return medium_msg, long_msg


class ErrorHandler:
	def __init__(self, bot):
		self.bot = bot

	def handle_error(self, message=None):
		medium_msg, long_msg = format_error(message)

		log.exception(medium_msg)

		self.bot._send_msg(medium_msg, self.bot.get_admin_nicks())

		if 'admin_email' in self.bot.config:
			email = MIMEText(long_msg)
			email['Subject'] = '[botologist] ' + medium_msg
			email['From'] = self.bot.config.get('email_from', 'botologist')

			if self.bot.config['admin_email'] is None:
				email['To'] = pwd.getpwuid(os.getuid())[0]
			else:
				email['To'] = self.bot.config['admin_email']

			sendmail_bin = self.bot.config.get('sendmail_bin', '/usr/sbin/sendmail')
			sendmail_args = self.bot.config.get('sendmail_args', None)
			send_email(email, sendmail_bin, sendmail_args)
			log.info('Sent email with exception information to %s', email['To'])

	def wrap(self, func):
		def wrapped(*args, **kwargs):
			try:
				func(*args, **kwargs)
			except:
				self.handle_error()
		return wrapped
