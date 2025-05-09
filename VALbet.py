import os
import requests
from bs4 import BeautifulSoup
import json
import hashlib
from collections import defaultdict
import re
import numpy as np

def loadfile(file):
    if os.path.exists(file):
        with open(file, 'r', encoding = 'utf-8') as f:
            content = json.load(f)
            return content
    else:
        return None

stat_json = 'stats.json'
hth_json = 'hth.json'
tbd_json = 'tbd.json'

stats = loadfile(stat_json)
hth_stats = loadfile(hth_json)
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
            if player not in stats:
                continue
            for match in stats[player]:
                sum_acs += stats[player][match]['ACS']
                sum_kast += stats[player][match]['KAST']
                sum_adr += stats[player][match]['ADR']
                counter += 1
            team_name = player.split()[1]
            if team_name not in team_avg:
                team_avg[team_name] = {
                    'avg_acs': sum_acs/counter,
                    'avg_kast': sum_kast/counter,
                    'avg_adr': sum_adr/counter,
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
    
    def previous_matches():
        soup3 = BeautifulSoup(requests.get(matchlink).text, 'html.parser')
        header = soup3.find('div', class_ = 'match-header-vs')
        htmlnames = header.find_all('div', class_ = 'wf-title-med')
        teamnames = []
        for i in htmlnames:
            teamnames.append(i.text)
        teamnames.sort()
        for matches in hth_stats.keys():
            hth_sort = [hth_stats[matches]['Team 1'], hth_stats[matches]['Team 2']]
            hth_sort.sort()
            for j in teamnames:
                if hth_sort[0] == j and hth_sort[1] == j + 1:
                    x = hth_stats[matches]['Score'].split(':')
                    y = x[0] - x[1]
                else:
                    return 0
    
    def sigmoid(z):
        if z >= 0:
            return 1 / (1 + np.exp(-z))
        else:
            exp_z = np.exp(z)
            return exp_z / (1 + exp_z)
    
    team_stat = get_team_stats(matchhash)
    previous_match = previous_matches()

    keys = team_stat.keys()
    keys = [key for key in keys]

    acs_diff = team_stat[keys[0]]['avg_acs'] - team_stat[keys[1]]['avg_acs']
    kast_diff = team_stat[keys[0]]['avg_kast'] - team_stat[keys[1]]['avg_kast']
    adr_diff = team_stat[keys[0]]['avg_adr'] - team_stat[keys[1]]['avg_adr']

    z = b0 + b1*acs_diff + b2*kast_diff + b3*adr_diff
    prob = sigmoid(z)

    STATEMENT = f"{keys[0]}: {str(prob)}%\n{keys[1]}: {str(1-prob)}%"

    return STATEMENT

x = generateprobability("https://www.vlr.gg/485377/wolves-esports-vs-tyloo-china-evolution-series-act-2-x-asian-champions-league-qf")
print(x)