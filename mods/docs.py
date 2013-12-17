from urllib.parse import quote_plus
from urllib.request import urlopen
from json import loads

def docs_cmd(search):
	return get_res_url('laravel.com/docs', search)

def apidocs_cmd(search):
	return get_res_url('laravel.com/api', search)

def ghsearch_cmd(search):
	return get_res_url('github.com/laravel/framework/tree', search)

def get_res_url(site, search):
	site = '&q=site:' + site + '+'
	url = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0' + site
	url = url + quote_plus(search)

	response = urlopen(url)
	text = response.read()
	response.close()

	data = loads(text.decode())
	if data['responseData']['results']:
		return data['responseData']['results'][0]['url']
	else:
		return 'No results!'