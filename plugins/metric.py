import botologist.plugin
import re


def handle_conversion(value, left, right):
	if 'meters' in left.lower() or 'metres' in left.lower():
		if 'feet' in right.lower():
			return float(value) * 3.2808
		if 'inches' in right.lower():
			return float(value) * 39.370
		if 'league' in right.lower():
			return float(value) * 0.000179985601
		if 'yard' in right.lower():
			return float(value) * 1.0936133
		if 'meters' in right.lower() or 'metres' in right.lower():
			return 'l2convert'

	if 'feet' in left.lower():
		if 'feet' in right.lower():
			return 'l2convert'
		if 'yard' in right.lower():
			return float(value) * 0.333333
		if 'meters' in right.lower() or 'metres' in right.lower():
			return float(value) * 0.3048

	if 'inches' in left.lower():
		if 'inches' in right.lower():
			return 'l2convert'
		if 'feet' in right.lower():
			return float(value) * 0.0833333
		if 'meters' in right.lower() or 'metres' in right.lower():
			return float(value) * 0.0254

	if 'yard' in left.lower():
		if 'yard' in right.lower():
			return 'l2convert'
		if 'feet' in right.lower():
			return float(value) * 3
		if 'inches' in right.lower():
			return float(value) * 36

	if 'miles' in left.lower():
		if 'miles' in right.lower():
			return 'l2convert'
		if 'kilometres' in right.lower() or 'kilometers' in right.lower():
			return float(value) * 1.609344

	if 'kilometres' in left.lower() or 'kilometers' in left.lower():
		if 'miles' in right.lower():
			return float(value) * 0.6213712
		if 'kilometres' in right.lower() or 'kilometers' in right.lower():
			return 'l2convert'

	return

class MetricPlugin(botologist.plugin.Plugin):
	@botologist.plugin.reply()
	def metric(self, msg):
		pattern = re.compile(r'([.\d]+[\s]+[a-z]+[\s]+[into|in|to]+[\s]+[a-z]+)')
		match = pattern.search(msg.message)
		if not match:
			return
		else:
			tokens = match.group().split(' ')
			value = handle_conversion(tokens[0], tokens[1], tokens[3])
			if not value:
				return
			return '{}'.format(value)
