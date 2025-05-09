import os
import requests
from bs4 import BeautifulSoup
import json
import hashlib
import re
import numpy as np

os.makedirs('cache', exist_ok = True)
os.makedirs('schedule', exist_ok = True)

stat_json = 'stat.json'
tbd_json = 'tbd.json'
avg_json = 'avg.json'

def geturl(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    hash = hashlib.md5(url.encode('utf-8')).hexdigest()
    file = os.path.join('cache', hash)
    if os.path.exists(file):
        with open(file, 'r', encoding = 'utf-8') as f:
            contents = f.read()
        return contents
    contents = requests.get(url, headers = headers).text
    with open(file, 'w', encoding = 'utf-8') as f:
        f.write(contents)
    return contents

def getmatch(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    hash = hashlib.md5(url.encode('utf-8')).hexdigest()
    file = os.path.join('schedule', hash)
    if os.path.exists(file):
        with open(file, 'r', encoding = 'utf-8') as f:
            contents = f.read()
        return contents
    contents = requests.get(url, headers = headers).text
    with open(file, 'w', encoding = 'utf-8') as f:
        f.write(contents)
    return contents

def loadfile(file):
    if os.path.exists(file):
        with open(file, 'r', encoding = 'utf-8') as f:
            raw_content = json.load(f)
            if not raw_content:
                return none
            return raw_content
    else:
        return None

def averager(strlist):
    x = []
    for k in strlist:
        if '%' in k:
            k = k.replace('%', '')
        if '\xa0' in k:
            k = k.replace('\xa0', '')
        if k == '':
            continue
        x.append(int(k))
    if not x:
        return 0
    y = sum(x) / len(x)
    return y

stats = loadfile(stat_json)
tbd = loadfile(tbd_json)
avg_stats = loadfile(avg_json)

if stats:
    print("Stats loaded")
else:
    results = []
    for i in range(1,3):
        if i == 1:
            results.append(BeautifulSoup(geturl("https://www.vlr.gg/matches/results/"), 'html.parser'))
        results.append(BeautifulSoup(geturl("https://www.vlr.gg/matches/results/?page=" + str(i)), 'html.parser'))
    links = []
    for k in results:
        bigclass = k.find('div', class_ = 'col-container')
        smallerclass = k.find_all('div', class_= 'wf-card')
        for i in smallerclass:
            x = i.find_all('a', href = True)
            for j in x:
                href = j.get('href')
                if '/matches' in href or '/results' in href:
                    continue
                links.append(href)
    team_stats = {}
    for i in links:
        soup = BeautifulSoup(geturl("https://www.vlr.gg" + i), 'html.parser')
        
        match_name = hashlib.md5(i.encode('utf-8')).hexdigest()
        match_data = soup.find('div', class_ = 'vm-stats-game mod-active')
        team_data = match_data.find_all('tbody')

        Score_html = soup.find('div', class_ = 'match-header-vs')

        team1_html = Score_html.find('div', class_ = 'match-header-link-name mod-1')
        team1 = [i.text.strip() for i in team1_html]

        team2_html = Score_html.find('div', class_ = 'match-header-link-name mod-2')
        team2 = [i.text.strip() for i in team2_html]

        Score = [Score_html.find('div', class_ = 'match-header-vs-score').find('div', class_ = 'match-header-vs-score').find('span', class_ = 'match-header-vs-score-winner').text.strip(), Score_html.find('div', class_ = 'match-header-vs-score').find('div', class_ = 'match-header-vs-score').find('span', class_ = 'match-header-vs-score-loser').text.strip()]

        for team in team_data:
            player_row = team.find_all('tr')
            for row in player_row:
                name_td = row.find('td' , class_ = 'mod-player')
                notname = name_td.text.replace('\n', '').replace('\t', '')
                nameteam = notname.rsplit(' ', 1)
                name = nameteam[0]
                teamname = nameteam[1]

                stat_tds = row.find_all('td')
                ACS = stat_tds[3].text.strip().replace('\n', ',').split(',')
                KAST = stat_tds[8].text.strip().replace('\n', ',').split(',')
                ADR = stat_tds[9].text.strip().replace('\n', ',').split(',')

                if teamname not in team_stats:
                    team_stats[teamname] = {}

                if name not in team_stats[teamname]:
                    team_stats[teamname][name] = {}

                if match_name not in team_stats[teamname][name]:
                    team_stats[teamname][name][match_name] = {}

                team_stats[teamname][name][match_name] = {
                    'ACS': averager(ACS),
                    'KAST': averager(KAST),
                    'ADR': averager(ADR),
                    'Score': f"{team1[1]}{team1[3]} {Score[0]}:{Score[1]} {team2[1]}{team2[3]}"
                }
    with open(stat_json, 'w', encoding = 'utf-8') as f:
        json.dump(team_stats, f, indent = 4)

if tbd:
    print("Scheduled matches loaded")
else:
    schedule = [BeautifulSoup(getmatch("https://www.vlr.gg/matches"), 'html.parser'), BeautifulSoup(getmatch("https://www.vlr.gg/matches/?page=2"), 'html.parser')]
    schedulelinks = []
    tbd_teams = {}
    for card in schedule:
        cardclass = card.find_all('div', class_ = 'wf-card')
        for links in cardclass:
            linkclass = links.find_all('a', href = True)
            for link in linkclass:
                if '/matches' in link.get('href') or 'tbd' in link.get('href'):
                    continue
                schedulelinks.append(link.get('href'))
    for link in schedulelinks:
        soup2 = BeautifulSoup(getmatch("https://www.vlr.gg" + link), 'html.parser')
        table = soup2.find_all('table', class_ = 'wf-table-inset mod-overview')
        matchname = hashlib.md5(link.encode('utf-8')).hexdigest()
        players = []
        for body in table:
            names = body.find_all('td', class_ = 'mod-player')
            for name in names:
                if len(players) > 9:
                    break
                player_name = name.text.replace('\t', '').replace('\n', '')
                players.append(player_name)
        tbd_teams[matchname] = players
    with open(tbd_json, 'w', encoding = 'utf-8') as f:
        json.dump(tbd_teams, f, indent = 4)

if avg_stats:
    print("Have stats")
else:
    matches = {}
    breakpoint()
    for player in stats.keys():
        if ' ' in player:
            teamname = player.rsplit(" ", 1)[1]
        else:
            teamname = re.search(r"[^a-z]$", player).group(0)
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