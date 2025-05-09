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

b0 = 0.0020489347393461647
b1 = 0.07228577070993243
b2 = 0.01969340959882133
b3 = 0.05427056700622877

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
                if player not in stats[team]:
                    continue
                for match in stats[team][player].keys():
                    score_string = stats[team][player][match]["Score"]
                    team_elo = int(re.search(r'\d{3,4}', team).group(0))

                    sum_acs += stats[team][player][match]['ACS']
                    sum_kast += stats[team][player][match]['KAST']
                    sum_adr += stats[team][player][match]['ADR']
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
    elo_diff = team_stat[keys[0]]['elo'] - team_stat[keys[1]]['elo']

    z = b0 + b1*acs_diff + b2*kast_diff + b3*adr_diff + b4*elo_diff
    prob = sigmoid(z)

    STATEMENT = f"{keys[0]}: {str(prob)}%\n{keys[1]}: {str(1-prob)}%"

    return team_stat

x = generateprobability("https://www.vlr.gg/485377/wolves-esports-vs-tyloo-china-evolution-series-act-2-x-asian-champions-league-qf")
print(x)