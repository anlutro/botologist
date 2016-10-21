import logging
log = logging.getLogger(__name__)

import os
import json
import sqlite3
import dota2api
import datetime
import botologist.plugin
import random
from time import sleep


class DotaPlugin(botologist.plugin.Plugin):

    def __init__(self, bot, channel):
        super().__init__(bot, channel)
        api_key = self.bot.config.get('dota2_apikey')
        self.api = dota2api.Initialise(api_key)
        db = os.path.join(self.bot.storage_dir, 'dota2.db')
        if not os.path.isfile(db):
            open(db, "w+")
        self.conn = sqlite3.connect(db, check_same_thread=False)
        self.cur = self.conn.cursor()
        self._create_table()
        self.colours = [
            "02",  # Blue
            "03",  # Green
            "04",  # Red
            "06",  # Purple
            "08",  # Yellow
        ]

    def _api_online(self):
        '''Checks if the API is actually working since it's down frequently.'''
        try:
            self.api.get_heroes()
        except:
            return False
        return True

    def get_our_scores(self, match):
        ret = ''
        accounts = self._all_accounts()
        players = []
        for p in match['players']:
            for user, steamid in accounts:
                if p['account_id'] == steamid:
                    players.append('{player_name} ({team}) {hero_name} {level} gpm:{gpm} kda:{kills}/{deaths}/{assists}'.format(
                        hero_name=p['hero_name'],
                        player_name=user,
                        level=p['level'],
                        kills=p['kills'],
                        deaths=p['deaths'],
                        assists=p['assists'],
                        gpm=p['gold_per_min'],
                        xpm=p['xp_per_min'],
                        team='R' if p['player_slot'] <= 5 else 'D',
                    ))
                    # Don't print out duplicates if we have multiple nicknames
                    # associated with the same Steam ID
                    break
        random.shuffle(self.colours)
        for idx, player in enumerate(players):
            player = "\x03{colour}{player_string}\x03 ".format(
                colour=self.colours[idx],
                player_string=player
            )
            ret += player
        return ret

    def get_match_str(self, match_id):
        if not isinstance(match_id, int):
            return "Problems with the Dota 2 API at the moment, try later."
        if match_id == 0:
            log.error("Invalid match ID.")
            return None
        log.debug("Attempting to fetch match_id: {match_id}".format(
            match_id=match_id
        ))
        try:
            m = self.api.get_match_details(match_id)
        except dota2api.exceptions.APITimeoutError:
            log.error("Dota2 API Timeout.")
            return None
        return "{mode}{ranked}: score: {radiant_score}-{dire_score}, {winner} victory, duration {duration}m. {our_scores} {dotabuff}".format(
            time=datetime.datetime.fromtimestamp(
                m['start_time']).strftime('%b %d'),
            match_id=match_id,
            duration=m['duration'] // 60,
            dotabuff="http://www.dotabuff.com/matches/{match_id}".format(
                match_id=match_id),
            radiant_score=m['radiant_score'],
            dire_score=m['dire_score'],
            winner="Radiant" if m['radiant_win'] else "Dire",
            our_scores=self.get_our_scores(m),
            mode=m['game_mode_name'],
            ranked=" RANKED!" if 'Rank' in m['lobby_name'] else ' CASUAL!'
        )

    def _get_latest_match_id(self, steamid):
        latest_match_id = 0
        try:
            matches = self.api.get_match_history(account_id=steamid)
            latest_match_id = matches['matches'][0]['match_id']
            log.debug("Returned latest_match: {latest_match}".format(
                latest_match=latest_match_id
            ))
            if 'total_results' in matches and matches['total_results'] > 0:
                self._update_latest_match_id(steamid, latest_match_id)
        except:
            log.error(
                "Failed to api.get_match_history. Steamid: {}".format(steamid))
        return latest_match_id

    @botologist.plugin.command('dota')
    def dota(self, cmd):
        '''
        Gets the latest dota match for the user requesting it.
        '''
        if not self._api_online():
            return "Dota 2 API is offline, try in a few minutes."
        if not self._nick_exists(cmd.user.nick):
            return "Steam ID not found for {user}.".format(
                user=str(cmd.user.nick)
            )
        steamid = self._get_steam_id(cmd.user.nick)
        if not steamid:
            return "Invalid Steam ID."
        latest_match_id = self._get_latest_match_id(steamid)
        return self.get_match_str(latest_match_id)

    def _steam_id_exists(self, steamid):
        '''Return boolean if steamid is API valid.'''
        try:
            self.api.get_match_history(account_id=int(steamid))
        except:
            return False
        return True

    @botologist.plugin.command('steamid')
    def steamid(self, cmd):
        '''
        Adds the user's steam id (dota version) to the sqlite db
        '''
        if len(cmd.args) != 1:
            existing_steam_id = self._get_steam_id(cmd.user.nick)
            if existing_steam_id:
                return "Your steam ID is: {existing}".format(
                    existing=existing_steam_id
                )
            return "Usage: !steamid 20000000"
        try:
            steamid = int(cmd.args[0])
        except ValueError:
            return "Your Dota 2 Steam id should be a number."
        if not self._steam_id_exists(steamid):
            return "That steam ID doesn't seem to match a real person."
        if not self._add_steamid(cmd.user.nick, steamid):
            return "Steam ID for {user} is now {steamid}.".format(
                steamid=steamid,
                user=cmd.user.nick
            )
        return "Failed to update Steam ID."

    @botologist.plugin.ticker()
    def real_time_dota(self):
        '''
        Check if player has a new game, if so plaster the channel with it.
        '''
        if not self._api_online():
            return False
        accts = self._all_accounts()
        steamids = [y for (x, y) in self._all_accounts()]
        old_matchids = self._get_all_matchids()  # From DB
        ret = []
        for sid in steamids:
            latest_match_id = self._get_latest_match_id(sid)  # From API
            sleep(1)
            log.debug("Latest: {}, Olds: [{}]".format(
                latest_match_id, old_matchids))
            if latest_match_id not in old_matchids:
                ret.append(self.get_match_str(latest_match_id))
                # If 2 players are in the same game we don't want double
                # messages
                old_matchids.append(latest_match_id)
        return ret

    # SQL helper functions, the joy
    def _nick_exists(self, user):
        self.cur.execute('''SELECT id FROM d2_users WHERE user = (?)''',
                         (str(user),)
                         )
        return self.cur.fetchone()

    def _get_steam_id(self, user):
        self.cur.execute('''SELECT steamid FROM d2_users WHERE user = (?)''',
                         (str(user),)
                         )
        ret = self.cur.fetchone()
        if not ret:
            return 0
        return ret[0]

    def _all_accounts(self):
        self.cur.execute('''SELECT user, steamid FROM d2_users ORDER BY id''')
        return self.cur.fetchall()

    def _remove_user(self, user):
        self.cur.execute('''delete from d2_users where user = (?)''',
                         (user,)
                         )

    def _add_steamid(self, user, steamid):
        user = str(user)
        steamid = int(steamid)
        if self._nick_exists(user):
            self._remove_user(user)
        self.cur.execute('''insert into d2_users (user, steamid) values (?, ?)''',
                         (user, steamid)
                         )
        self.conn.commit()

    def _get_all_matchids(self):
        self.cur.execute('''SELECT latest_match FROM d2_users''')
        return [x for (x,) in self.cur.fetchall()]

    def _update_latest_match_id(self, steamid, matchid):
        '''
        Update the latest_match field in the db.
        '''
        try:
            matchid = int(matchid)
        except ValueError:
            raise "Match ID not an integer."
        self.cur.execute('''SELECT id, steamid, user, latest_match FROM d2_users WHERE steamid = (?)''',
                         (steamid,)
                         )
        sql_ret = self.cur.fetchone()
        old_matchid = sql_ret[3]
        if not old_matchid or matchid != old_matchid:
            self.cur.execute('''UPDATE d2_users SET latest_match = (?) WHERE id = (?)''',
                             (matchid, sql_ret[0])
                             )
            self.conn.commit()
            log.debug("Updated {steamid}'s latest matchid to {matchid}".format(
                steamid=steamid,
                matchid=matchid)
            )

    def _create_table(self):
        '''
        Create d2_users table if it doesn't exist.
        '''
        self.cur.execute('''
            CREATE TABLE IF NOT EXISTS d2_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                steamid INTEGER,
                user TEXT,
                latest_match INTEGER)
        ''')
