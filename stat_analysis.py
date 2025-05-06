import json
import os
from collections import defaultdict
import hashlib

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

if avg_stats:
    print("Have stats")
else:
    matches = {}
    for player in stats.keys():
        teamname = player.rsplit(" ", 1)[1]
        for match in stats[player].keys():
            if match in matches:
                if teamname in matches[match]:
                    matches[match][teamname]['acs'].append(stats[player][match]['ACS'])
                    matches[match][teamname]['kast'].append(stats[player][match]['KAST'])
                    matches[match][teamname]['k'].append(stats[player][match]['K'])
                    matches[match][teamname]['d'].append(stats[player][match]['D'])
                    matches[match][teamname]['a'].append(stats[player][match]['A'])
                    matches[match][teamname]['adr'].append(stats[player][match]['ADR'])
                else:
                    matches[match][teamname] = {
                        'acs': [stats[player][match]['ACS']],
                        'kast': [stats[player][match]['KAST']],
                        'k': [stats[player][match]['K']],
                        'd': [stats[player][match]['D']],
                        'a': [stats[player][match]['A']],
                        'adr': [stats[player][match]['ADR']]
                    } 
            else:
                matches[match] = {
                    teamname: {
                        'acs': [stats[player][match]['ACS']],
                        'kast': [stats[player][match]['KAST']],
                        'k': [stats[player][match]['K']],
                        'd': [stats[player][match]['D']],
                        'a': [stats[player][match]['A']],
                        'adr': [stats[player][match]['ADR']]
                    }
                }
    with open(avg_json, 'w', encoding = 'utf-8') as f:
        json.dump(matches, f, indent = 4)