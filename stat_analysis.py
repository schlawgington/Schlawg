import json
import os
from collections import defaultdict
import hashlib
import numpy as np

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
                        }
                    }
    for match in matches.keys():
        for teamname in matches[match]["Teams"].keys():
            matches[match]["Teams"][teamname]['acs'] = averager(matches[match]["Teams"][teamname]['acs'])
            matches[match]["Teams"][teamname]['kast'] = averager(matches[match]["Teams"][teamname]['kast'])
            matches[match]["Teams"][teamname]['k'] = averager(matches[match]["Teams"][teamname]['k'])
            matches[match]["Teams"][teamname]['d'] = averager(matches[match]["Teams"][teamname]['d'])
            matches[match]["Teams"][teamname]['a'] = averager(matches[match]["Teams"][teamname]['a'])
            matches[match]["Teams"][teamname]['adr'] = averager(matches[match]["Teams"][teamname]['adr'])
    with open(avg_json, 'w', encoding = 'utf-8') as f:
        json.dump(matches, f, indent = 4)