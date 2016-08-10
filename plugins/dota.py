import logging
log = logging.getLogger(__name__)

import dota2api
import datetime
import botologist.plugin

dota_ids = {
    20714906: 'Naypalm',
    39594528: 'haiku',
    56467315: 'moop',
}

class DotaPlugin(botologist.plugin.Plugin):
    def __init__(self, bot, channel):
        super().__init__(bot, channel)
        api_key = self.bot.config.get('dota2_apikey')
        self.api = dota2api.Initialise(api_key)

    def get_our_scores(self, match):
        ret = ''
        for p in match['players']:
            if p['account_id'] in list(dota_ids.keys()):
                ret += '{player_name} ({team}) ({hero_name}, level {level}) kda:{kills}/{deaths}/{assists} xpm:{xpm} gpm:{gpm}. '.format(
                    hero_name=p['hero_name'],
                    player_name=dota_ids[p['account_id']],
                    level=p['level'],
                    kills=p['kills'],
                    deaths=p['deaths'],
                    assists=p['assists'],
                    gpm=p['gold_per_min'],
                    xpm=p['xp_per_min'],
                    team='R' if p['player_slot'] <= 5 else 'D',
                )
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

    def get_account_id(self, username):
        for aid, user in dota_ids.items():
            if user == username.name:
                return aid
        return 0

    @botologist.plugin.command('dota')
    def dota(self, cmd):
        account_id = self.get_account_id(cmd.user)
        if not account_id:
            return "Account not found."
        matches = self.api.get_match_history(account_id)
        latest_match = {'match_id': 'Not found.'}
        if 'total_results' in matches and matches['total_results'] > 0:
            latest_match = matches['matches'][0]
        return self.get_match_str(latest_match['match_id'])
