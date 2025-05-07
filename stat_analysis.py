import json
import os
from collections import defaultdict
import hashlib
import numpy as np
import re

def loadfile(file):
    if os.path.exists(file):
        with open(file, 'r', encoding = 'utf-8') as f:
            content = json.load(f)
            return content
    else:
        return None
    
avg_json = 'avg.json'
avg_stats = loadfile(avg_json)

hth_json = 'hth.json'
wl_stats = loadfile(hth_json)

stats_json = 'stats.json'
stats = loadfile(stats_json)

def averager(list):
    arr = np.array(list)
    avg_stat = sum(arr) / len(arr)
    return avg_stat

if avg_stats:
    print("Have stats")
else:
    matches = {}
    for player in stats.keys():
        teamname = player.rsplit(" ", 1)[1]
        for match in stats[player].keys():
            if match in matches:
                if teamname in matches[match]["Teams"]:
                    matches[match]["Teams"][teamname]['acs'].append(stats[player][match]['ACS'])
                    matches[match]["Teams"][teamname]['kast'].append(stats[player][match]['KAST'])
                    matches[match]["Teams"][teamname]['k'].append(stats[player][match]['K'])
                    matches[match]["Teams"][teamname]['d'].append(stats[player][match]['D'])
                    matches[match]["Teams"][teamname]['a'].append(stats[player][match]['A'])
                    matches[match]["Teams"][teamname]['adr'].append(stats[player][match]['ADR'])
                else:
                    matches[match]["Teams"][teamname] = {
                        'acs': [stats[player][match]['ACS']],
                        'kast': [stats[player][match]['KAST']],
                        'k': [stats[player][match]['K']],
                        'd': [stats[player][match]['D']],
                        'a': [stats[player][match]['A']],
                        'adr': [stats[player][match]['ADR']]
                        } 
            else:
                matches[match] = {
                    "Score": f"{wl_stats[match]['Team 1']} vs {wl_stats[match]['Team 2']} {wl_stats[match]['Score:']}",
                    "Teams": {
                        teamname: {
                            'acs': [stats[player][match]['ACS']],
                            'kast': [stats[player][match]['KAST']],
                            'k': [stats[player][match]['K']],
                            'd': [stats[player][match]['D']],
                            'a': [stats[player][match]['A']],
                            'adr': [stats[player][match]['ADR']]
                            }
                        },
                    "Stat Diff": {
                        'delta acs': 0,
                        'delta kast': 0,
                        'delta k': 0,
                        'delta d': 0,
                        'delta a': 0,
                        'delta adr': 0,
                    }
                }

    for match in matches.keys():
        teamname = list(matches[match]["Teams"].keys())
        matches[match]["Stat Diff"]['delta acs'] = averager(matches[match]["Teams"][teamname[0]]['acs']) - averager(matches[match]["Teams"][teamname[1]]['acs'])
        matches[match]["Stat Diff"]['delta kast'] = averager(matches[match]["Teams"][teamname[0]]['kast']) - averager(matches[match]["Teams"][teamname[1]]['kast'])
        matches[match]["Stat Diff"]['delta k'] = averager(matches[match]["Teams"][teamname[0]]['k']) - averager(matches[match]["Teams"][teamname[1]]['k'])
        matches[match]["Stat Diff"]['delta d'] = averager(matches[match]["Teams"][teamname[0]]['d']) - averager(matches[match]["Teams"][teamname[1]]['d'])
        matches[match]["Stat Diff"]['delta a'] = averager(matches[match]["Teams"][teamname[0]]['a']) - averager(matches[match]["Teams"][teamname[1]]['a'])
        matches[match]["Stat Diff"]['delta adr'] =  averager(matches[match]["Teams"][teamname[0]]['adr']) - averager(matches[match]["Teams"][teamname[1]]['adr'])

    with open(avg_json, 'w', encoding = 'utf-8') as f:
        json.dump(matches, f, indent = 4)

class logisticregressionmodel:
    def __init__(self):
        self.b0 = -0.0081
        self.b1 = -0.0044
        self.b2 = -0.0031
        self.b3 = 0.0079

    def probabilities_yay(self):
        match_scores = [re.search(r'\d:\d', avg_stats[match]["Score"]).group(0) for match in avg_stats.keys()]
        winloss = []
        for i in match_scores:
            splitlist = i.split(":")
            if int(splitlist[0]) > int(splitlist[1]):
                winloss.append(1)
            else:
                winloss.append(0)

        team = [re.match(r"^(.*)\s\d+:\d+$", avg_stats[match]["Score"]).group(1) for match in avg_stats.keys()]

        deltas = np.array(
            [
                [avg_stats[match]["Stat Diff"]['delta acs'] for match in avg_stats.keys()],
                [avg_stats[match]["Stat Diff"]['delta kast'] for match in avg_stats.keys()],
                [avg_stats[match]["Stat Diff"]['delta adr'] for match in avg_stats.keys()]
            ]
        )

        results = np.array(
            [i for i in winloss]
        )

        z = np.array(
            [self.b0 + self.b1*deltas[0][i] + self.b2*deltas[1][i] + self.b3*deltas[2][i] for i in range(len(deltas[0]))]
        )

        prob = [1 / (1 + np.exp(-1*i)) for i in z]
        probarr = np.array(prob)

        pretty = [f"{team[i]}: {prob[i]}" for i in range(len(team))]

        return pretty

x = logisticregressionmodel()
print(x.probabilities_yay())