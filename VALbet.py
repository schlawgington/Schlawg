import os
import requests
from bs4 import BeautifulSoup
import json
import hashlib
from collections import defaultdict
import re
import numpy as np
from fuzzywuzzy import fuzz

def loadfile(file):
    if os.path.exists(file):
        with open(file, 'r', encoding = 'utf-8') as f:
            content = json.load(f)
            return content
    else:
        return None

stat_json = 'stat.json'
tbd_json = 'tbd.json'

stats = loadfile(stat_json)
tbd = loadfile(tbd_json)

b0 = 0.07968364919098547
b1 = -0.01538007314636117
b2 = -0.05652877597543738
b3 = 0.05407970916940718
b4 = -0.0031161344386801447

def generateprobability(matchlink):
    if 'https://www.vlr.gg/' in matchlink:
        matchinfo = matchlink.replace('https://www.vlr.gg', '')
        matchhash = hashlib.md5(matchinfo.encode('utf-8')).hexdigest()

    def get_team_stats(matchhash):
        playerlist = tbd[matchhash]
        team_avg = {}
        for player in playerlist:
            sum_acs = 0
            sum_kast = 0
            sum_adr = 0
            counter = 0
            for team in stats.keys():
                team_name = str(team)
                if player not in stats[team]['Players']:
                    continue
                for match in stats[team]['Players'][player].keys():
                    score_string = stats[team]['Players'][player][match]["Score"]
                    team_elo_thing = re.search(r'\d{3,4}', team)
                    team_elo = int(team_elo_thing.group()) if team_elo_thing is not None else 0

                    sum_acs += stats[team]['Players'][player][match]['ACS']
                    sum_kast += stats[team]['Players'][player][match]['KAST']
                    sum_adr += stats[team]['Players'][player][match]['ADR']
                    counter += 1
                if team_name not in team_avg:
                    team_avg[team_name] = {
                        'avg_acs': sum_acs/counter,
                        'avg_kast': sum_kast/counter,
                        'avg_adr': sum_adr/counter,
                        'elo': team_elo,
                        'count': 1
                    }
                else:
                    team_avg[team_name]['avg_acs'] += sum_acs/counter
                    team_avg[team_name]['avg_kast'] += sum_kast/counter
                    team_avg[team_name]['avg_adr'] += sum_adr/counter
                    team_avg[team_name]['count'] += 1
        for team in team_avg.keys():
            team_avg[team]['avg_acs'] /= team_avg[team]['count']
            team_avg[team]['avg_kast'] /= team_avg[team]['count']
            team_avg[team]['avg_adr'] /= team_avg[team]['count']
        return team_avg
    
    def sigmoid(z):
        if z >= 0:
            return 1 / (1 + np.exp(-z))
        else:
            exp_z = np.exp(z)
            return exp_z / (1 + exp_z)
    
    team_stat = get_team_stats(matchhash)

    keys = team_stat.keys()
    keys = [key for key in keys]

    acs_diff = team_stat[keys[0]]['avg_acs'] - team_stat[keys[1]]['avg_acs']
    kast_diff = team_stat[keys[0]]['avg_kast'] - team_stat[keys[1]]['avg_kast']
    adr_diff = team_stat[keys[0]]['avg_adr'] - team_stat[keys[1]]['avg_adr']
    elo_diff = team_stat[keys[0]]['elo'] - team_stat[keys[1]]['elo'] if team_stat[keys[0]]['elo'] or team_stat[keys[1]]['elo'] != 0 else 0

    z = b0 + b1*acs_diff + b2*kast_diff + b3*adr_diff + b4*elo_diff
    prob = sigmoid(z)

    def kelly(prob, odds, bankroll):
        return (prob*odds - 1) / (odds - 1)

    STATEMENT = f"{keys[0]}: {str(prob)}%\n{keys[1]}: {str(1-prob)}%"

    return STATEMENT

x = generateprobability("https://www.vlr.gg/482508/team-liquid-vs-fnatic-champions-tour-2025-emea-stage-1-playoffs-ubsf")
print(x)