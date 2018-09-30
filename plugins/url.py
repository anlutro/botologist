import html
import logging
import urllib.parse

import re
import requests
import requests.exceptions

import botologist.plugin

log = logging.getLogger(__name__)

url_shorteners = r"|".join(
    (
        r"https?://bit\.ly",
        r"https?://is\.gd",
        r"https?://redd\.it",
        r"https?://t\.co",
        r"https?://tinyurl\.com",
    )
)
short_url_regex = re.compile(r"((" + url_shorteners + r")\/[a-zA-Z0-9/]+)")


def find_shortened_urls(text):
    matches = short_url_regex.findall(text)
    return [match[0] for match in matches]


def get_location(url):
    response = requests.head(url, timeout=4)
    if response.status_code != 301 and response.status_code != 302:
        return response.url
    return response.headers["location"]


def unshorten_url(url):
    try:
        url = get_location(url)
    except requests.exceptions.RequestException:
        log.info("HTTP error while unshortening URL", exc_info=True)
        return None

    if len(url) > 300:
        log.info("Unshortened URL is too long (%d characters)", len(url))
        return None

    return url


def unshorten_urls(text):
    ret = []
    for url in find_shortened_urls(text):
        real_url = unshorten_url(url)
        if real_url:
            ret.append("{} => {}".format(url, real_url))
    return ret


titlazable_url_regex = re.compile(
    r"("
    + r"|".join(
        (
            r"https?:\/\/youtu\.be\/[a-zA-Z0-9_-]+",
            r"https?:\/\/(www\.)?youtube\.com\/watch[^\s]+",
        )
    )
    + r")"
)


def find_titlazible_urls(text):
    matches = titlazable_url_regex.findall(text)
    return [match[0] for match in matches]


def show_link_titles(text):
    titles = {}
    for url in find_titlazible_urls(text):
        resp = requests.get(url, timeout=3)
        match = re.search(r"\<title\>([^<]+)\<\/title\>", resp.text)
        if not match:
            continue
        title = match.group(1).strip()
        title = urllib.parse.unquote(title)
        title = html.unquote(title)
        titles[url] = title

    ret = []
    for url, title in titles.items():
        if title in text:
            continue
        s = title
        if len(titles) > 1:
            s += " (%s)" % url
        ret.append(s)
    return ret


class UrlPlugin(botologist.plugin.Plugin):
    @botologist.plugin.reply()
    def reply(self, msg):
        ret = []
        ret.extend(unshorten_urls(msg.message))
        ret.extend(show_link_titles(msg.message))
        if ret:
            return ret
