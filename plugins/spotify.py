import logging

log = logging.getLogger(__name__)

import re

import spotipy
import spotipy.client
from spotipy.oauth2 import SpotifyClientCredentials

import botologist.plugin


def _get_artist_str(artists):
    return ", ".join(artist["name"] for artist in artists)


class Spotify:
    def __init__(self, spotipy_instance=None):
        self.spotipy = spotipy_instance or spotipy.Spotify()

    def get_info_str(self, item_type, item_id):
        log.info("looking up spotify:%s:%s", item_type, item_id)
        try:
            if item_type == "artist":
                data = self.spotipy.artist(item_id)
                return "%s (%s)" % (data["name"], ", ".join(data["genres"]))
            elif item_type == "album":
                data = self.spotipy.album(item_id)
                return "%s - %s" % (_get_artist_str(data["artists"]), data["name"])
            elif item_type == "track":
                data = self.spotipy.track(item_id)
                return "%s - %s [album: %s]" % (
                    _get_artist_str(data["artists"]),
                    data["name"],
                    data["album"]["name"],
                )
            else:
                raise ValueError("unknown item type: %r" % item_type)
        except spotipy.client.SpotifyException:
            log.warning(
                "spotipy threw an exception while looking up spotify:%s:%s",
                item_type,
                item_id,
                exc_info=True,
            )
            return


class SpotifyPlugin(botologist.plugin.Plugin):
    pattern = re.compile(
        r"(open\.spotify\.com\/|spotify:)(artist|album|track)[:/](\w+)"
    )

    def __init__(self, bot, channel):
        super().__init__(bot, channel)
        ccm = None
        if bot.config.get("spotify_client_id"):
            ccm = SpotifyClientCredentials(
                client_id=bot.config.get("spotify_client_id"),
                client_secret=bot.config.get("spotify_client_secret"),
            )
        sp = spotipy.Spotify(client_credentials_manager=ccm)
        self.spotify = Spotify(sp)

    @botologist.plugin.reply(threaded=True)
    def convert(self, msg):
        ret = []

        for match in self.pattern.finditer(msg.message):
            info = self.spotify.get_info_str(match.group(2), match.group(3))
            if info:
                ret.append("[spotify] %s" % info)

        if len(ret) < 3:
            return ret
