import logging

log = logging.getLogger(__name__)

import json
import requests
import requests.exceptions
import botologist.plugin

BASE_URL = "https://qdb.lutro.me"


def _get_quote_url(quote):
    return BASE_URL + "/" + str(quote["id"])


def _get_qdb_data(url, query_params):
    response = requests.get(
        url, query_params, headers={"accept": "application/json"}, timeout=4
    )
    response.raise_for_status()
    return response.json()


def _search_for_quote(quote):
    search = False
    query_params = None
    if isinstance(quote, int):
        url = BASE_URL + "/" + str(quote)
        single_quote = True
    else:
        single_quote = False
        if quote == "random":
            url = BASE_URL + "/random"
        elif quote == "latest":
            url = BASE_URL
        else:
            search = str(quote)
            url = BASE_URL + "/random"
            query_params = {"s": search}

    try:
        data = _get_qdb_data(url, query_params=query_params)
    except requests.exceptions.RequestException:
        log.warning("QDB request caused an exception", exc_info=True)
        return "HTTP error!"

    if single_quote:
        quote = data["quote"]
        if not quote["approved"]:
            return "No quote with that ID found!"
    else:
        quotes = data["quotes"]
        if "items" in quotes:
            quotes = quotes["items"]
        if len(quotes) < 1:
            return "No quotes found!"
        quote = quotes[0]

    url = BASE_URL + "/" + str(quote["id"])

    if len(quote["body"]) > 400:
        body = quote["body"]
        if search:
            try:
                body_len = len(body)
                substr_pos = body.lower().index(search.lower())
                start = body.rfind("\n", 0, substr_pos) + 1
                while body_len - start < 300:
                    substr_pos = body.rfind("\n", 0, start - 1) + 1
                    if body_len - substr_pos < 300:
                        start = substr_pos
                    else:
                        break
                end = start + 350 - len(search)
            except ValueError:
                start = 0
                end = 300
        else:
            start = 0
            end = 300

        body = body.replace("\r", "").replace("\n", " ").replace("\t", " ")
        excerpt = body[start:end]

        if start > 0:
            excerpt = "[...] " + excerpt
        if end < len(quote["body"]):
            excerpt = excerpt + " [...]"
        body = excerpt
    else:
        body = quote["body"].replace("\r", "").replace("\n", " ").replace("\t", " ")

    return url + " - " + body


class QdbPlugin(botologist.plugin.Plugin):
    @botologist.plugin.command("qdb")
    def search(self, cmd):
        """
        Search for a quote, or show a specific quote.

        Examples: !qdb search for this - !qdb #220
        """
        if len(cmd.args) < 1:
            arg = "random"
        elif cmd.args[0][0] == "#":
            try:
                arg = int(cmd.args[0][1:])
            except ValueError:
                arg = " ".join(cmd.args)
        else:
            arg = " ".join(cmd.args)

        return _search_for_quote(arg)

    @botologist.plugin.http_handler(method="POST", path="/qdb-update")
    def quote_updated(self, body, headers):
        data = json.loads(body)
        quote = data["quote"]
        if quote["approved"]:
            return "New quote approved! " + _get_quote_url(quote)
        return "Quote pending approval!"
