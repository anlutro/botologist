import logging
log = logging.getLogger(__name__)

import os
import sqlite3
import dota2api
import datetime
import botologist.plugin


class DotaPlugin(botologist.plugin.Plugin):
    def __init__(self, bot, channel):
        super().__init__(bot, channel)
        api_key = self.bot.config.get('dota2_apikey')
        self.api = dota2api.Initialise(api_key)
        db = os.path.join(self.bot.storage_dir, 'dota2.db')
        self.conn = sqlite3.connect(db, check_same_thread=False)
        self.cur = self.conn.cursor()

    def get_our_scores(self, match):
        ret = ''
        accounts = self._all_accounts()
        print(accounts)
        for p in match['players']:
            for user, steamid in accounts:
                if p['account_id'] == steamid:
                    ret += '{player_name} ({team}) ({hero_name}, level {level}) kda:{kills}/{deaths}/{assists} xpm:{xpm} gpm:{gpm}. '.format(
                        hero_name=p['hero_name'],
                        player_name=user,
                        level=p['level'],
                        kills=p['kills'],
                        deaths=p['deaths'],
                        assists=p['assists'],
                        gpm=p['gold_per_min'],
                        xpm=p['xp_per_min'],
                        team='R' if p['player_slot'] <= 5 else 'D',
                    )
                    # Don't print out duplicates if we have multiple nicknames
                    # associated with the same Steam ID
                    break
        return ret

    def get_match_str(self, match_id):
        if not isinstance(match_id, int):
            return "Game not found."
        m = self.api.get_match_details(match_id)
        return "Dota 2 {match_id} {time}, score: {radiant_score}-{dire_score}, {winner} victory, duration {duration}m. {our_scores} {dotabuff}".format(
            time=datetime.datetime.fromtimestamp(m['start_time']).strftime('%b %d'),
            match_id=match_id,
            duration=m['duration']//60,
            dotabuff="http://www.dotabuff.com/matches/{}".format(match_id),
            radiant_score=m['radiant_score'],
            dire_score=m['dire_score'],
            winner="Radiant" if m['radiant_win'] else "Dire",
            our_scores=self.get_our_scores(m),
        )

    @botologist.plugin.command('dota')
    def dota(self, cmd):
        if not self._nick_exists(cmd.user.nick):
            return "Steam ID not found for {user}.".format(
                user=str(cmd.user.nick)
            )
        account_id = self._get_steam_id(cmd.user.nick)
        if not account_id:
            return "Invalid Steam ID."
        matches = self.api.get_match_history(account_id)
        latest_match = {'match_id': 'Not found.'}
        if 'total_results' in matches and matches['total_results'] > 0:
            latest_match = matches['matches'][0]
        return self.get_match_str(latest_match['match_id'])

    @botologist.plugin.command('steamid')
    def steamid(self, cmd):
        if len(cmd.args) != 1:
            return "Usage: !steamid 13371337"
        try:
            steamid = int(cmd.args[0])
        except ValueError:
            return "That's not a valid Steam ID."
        if not self._add_steamid(cmd.user.nick, steamid):
            return "Steam ID for {user} is now {steamid}.".format(
                steamid=steamid,
                user=cmd.user.nick
            )
        return "Failed to update Steam ID."

    # SQL helper functions, the joy
    def _nick_exists(self, user):
        self.cur.execute('''SELECT id FROM d2_users WHERE user = (?)''', (str(user),))
        return self.cur.fetchone()

    def _get_steam_id(self, user):
        self.cur.execute('''SELECT steamid FROM d2_users WHERE user = (?)''', (str(user),))
        ret = self.cur.fetchone()
        if not ret:
            return 0
        return ret[0]

    def _all_accounts(self):
        self.cur.execute('''SELECT user, steamid FROM d2_users ORDER BY id''')
        return self.cur.fetchall()

    def _remove_user(self, user):
        self.cur.execute('''delete from d2_users where user = (?)''', (user,))

    def _add_steamid(self, user, steamid):
        user = str(user)
        steamid = int(steamid)
        if self._nick_exists(user):
            self._remove_user(user)
        self.cur.execute('''insert into d2_users (user, steamid) values (?, ?)''', (user, steamid))
        self.conn.commit()
