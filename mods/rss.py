from urllib.request import urlopen
import xml.etree.ElementTree as etree

class RssChecker:
	last_items = []
	new_items = []

	def update(self):
		f = urlopen(self.url)
		tree = etree.parse(f)
		entries = tree.findall('{http://www.w3.org/2005/Atom}entry')

		self.new_items = []
		for entry in entries:
			item = self._parse_element(entry)
			self.new_items.append(item)

	def has_news(self):
		if not self.last_items:
			self.last_items = self.new_items
			return False
		return self.new_items != self.last_items

	def get_news(self):
		new = []
		for post in self.new_items:
			if post == self.last_items[-1] or post == self.last_items[0]:
				break
			new.append(post)
		self.last_items = self.new_items
		return new

class LioRssChecker(RssChecker):
	url = 'http://forums.laravel.io/extern.php?action=feed&type=atom'

	def _parse_element(self, entry):
		title = entry.find('{http://www.w3.org/2005/Atom}title').text
		link = entry.find('{http://www.w3.org/2005/Atom}link').attrib['href']
		return 'Forum post: ' + title + ' - ' + link

class StackRssChecker(RssChecker):
	url = 'http://stackoverflow.com/feeds/tag?tagnames=laravel-4&sort=newest'

	def _parse_element(self, entry):
		title = entry.find('{http://www.w3.org/2005/Atom}title').text
		link = entry.find('{http://www.w3.org/2005/Atom}link').attrib['href']
		return 'Stack Overflow: ' + title + ' - ' + link
