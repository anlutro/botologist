import logging
import requests
from botologist.util import parse_dt, time_until
import botologist.plugin

log = logging.getLogger(__name__)


def get_next_episode_info(show, tz="UTC"):
    query = {"q": show, "embed": "nextepisode"}
    try:
        response = requests.get(
            "http://api.tvmaze.com/singlesearch/shows", query, timeout=4
        )
        response.raise_for_status()
    except requests.exceptions.RequestException:
        log.warning("TVMaze request caused an exception", exc_info=True)
        return None

    try:
        data = response.json()
    except ValueError:
        log.warning("TVMaze returned invalid JSON: %r", response.text, exc_info=True)
        return None

    info = data["name"]
    nextepisode = data.get("_embedded", {}).get("nextepisode")
    if nextepisode:
        log.debug("next episode data: %r", nextepisode)
        dt = parse_dt(nextepisode["airstamp"], tz)
        info += " - season %d, episode %d airs at %s" % (
            nextepisode["season"],
            nextepisode["number"],
            dt.strftime("%Y-%m-%d %H:%M %z"),
        )
        time_until_str = time_until(dt)
        if time_until_str:
            info += " (in %s)" % time_until_str
    else:
        status = data["status"]
        if status == "Ended":
            info += " - cancelled :("
        else:
            info += " - next episode not announced yet"

    return info


class TvseriesPlugin(botologist.plugin.Plugin):
    def __init__(self, bot, channel):
        super().__init__(bot, channel)
        self.tz = self.bot.config.get("output_timezone", "UTC")

    @botologist.plugin.command("nextepisode")
    def nextepisode(self, msg):
        info = get_next_episode_info(" ".join(msg.args), self.tz)
        return info or "No show with that name found!"
