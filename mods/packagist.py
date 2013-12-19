from urllib.parse import quote_plus
from urllib.request import urlopen
from json import loads

def pkg_search(search):
	url = 'https://packagist.org/search.json?q=' + quote_plus(search)
	f = urlopen(url)
	result = f.read()
	f.close()
	data = loads(result.decode())

	if data['results']:
		result = data['results'][0]
		return result['name'] + ' - ' + result['url'] + ' (' + str(result['downloads']) + ' downloads)' 
	else:
		return 'No results!'