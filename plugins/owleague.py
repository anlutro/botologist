import logging

import requests

from botologist.util import parse_dt, time_until
import botologist.plugin

log = logging.getLogger(__name__)


def get_owl_data():
    resp = requests.get(
        "https://api.overwatchleague.com/live-match",
        params={"locale": "en-gb"},
        headers={"Accept-Language": "en-GB", "Cache-Control": "no-cache"},
        timeout=4,
    )
    resp.raise_for_status()
    return resp.json().get("data", {})


class Team:
    def __init__(self, id, name):
        self.id = id
        self.name = name

    @classmethod
    def from_data(cls, data):
        return cls(data.get("id"), data["name"])

    def __str__(self):
        return self.name

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        if self.id and other.id:
            return self.id == other.id
        return self.name == other.name


class Match:
    LIVE = object()

    def __init__(self, team_a, team_b, time=None):
        self.team_a = team_a
        self.team_b = team_b
        self.time = time

    @property
    def time_until(self):
        return time_until(self.time)

    @classmethod
    def from_data(cls, data, tz=None):
        if not data:
            return None
        if data.get("liveStatus") == "LIVE":
            time = Match.LIVE
        else:
            time = parse_dt(data["startDate"], tz)
        teams = (Team.from_data(team_data) for team_data in data["competitors"])
        return cls(*teams, time=time)

    def __str__(self):
        s = "%s vs %s" % (self.team_a, self.team_b)
        if not self.time is Match.LIVE:
            time_until_str = time_until(self.time)
            if time_until_str:
                s += " at %s (in %s)" % (
                    self.time.strftime("%Y-%m-%d %H:%M %z"),
                    time_until_str,
                )
        return s

    def __hash__(self):
        return hash((self.team_a, self.team_b, self.time))

    def __eq__(self, other):
        if not isinstance(other, Match):
            return False
        return all(
            (
                self.team_a == other.team_a,
                self.team_b == other.team_b,
                self.time == other.time,
            )
        )


def get_owl_matches(tz=None):
    live_match = None
    next_match = None
    data = get_owl_data()
    if data.get("liveMatch", {}).get("liveStatus") == "LIVE":
        live_match = Match.from_data(data["liveMatch"])
        next_match = Match.from_data(data.get("nextMatch", {}))
    elif data.get("liveMatch", {}).get("liveStatus") == "UPCOMING":
        next_match = Match.from_data(data["liveMatch"])
    return live_match, next_match


class OwleaguePlugin(botologist.plugin.Plugin):
    def __init__(self, bot, channel):
        super().__init__(bot, channel)
        self.cur_state = None
        self.cur_match = None
        self.prev_match = None
        self.tz = self.bot.config.get("output_timezone", "UTC")

    def _get_info_str(self, ticker):
        try:
            cur_match, next_match = get_owl_matches(tz=self.tz)
        except requests.exceptions.RequestException as exc:
            log.warning("exception getting OWL data", exc_info=True)
            if ticker:
                return
            return "Problem fetching OWL data: %s" % exc

        skip = ticker and (
            cur_match == self.cur_state
            or cur_match == self.cur_match
            or cur_match == self.prev_match
            or not cur_match
        )

        if not skip:
            log.debug(
                "cur_state=%r; cur_match=%r; prev_match=%r",
                self.cur_state,
                self.cur_match,
                self.prev_match,
            )

        self.cur_state = cur_match
        if cur_match and cur_match != self.cur_match:
            self.prev_match = self.cur_match
            self.cur_match = cur_match
        elif not cur_match and cur_match != self.prev_match:
            self.cur_match = None
            self.prev_match = None

        if skip:
            return

        match_infos = []
        if cur_match:
            match_infos.append("Live now: %s" % cur_match)
        if next_match:
            match_infos.append("Next match: %s" % next_match)
        if not match_infos:
            match_infos = ["No matches live or scheduled"]
        return " -- ".join(match_infos + ["https://overwatchleague.com"])

    @botologist.plugin.ticker()
    def ticker(self):
        return self._get_info_str(ticker=True)

    @botologist.plugin.command("owl")
    def command(self, msg):
        return self._get_info_str(ticker=False)
