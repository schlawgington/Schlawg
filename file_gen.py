import os
import requests
from bs4 import BeautifulSoup
import json
import hashlib
import re
from collections import defaultdict
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
        if isinstance(k, (int, float)):
            x.append(k)
            continue
        if '%' in k:
            k = k.replace('%', '')
        if '\xa0' in k:
            k = k.replace('\xa0', '')
        if k == '':
            continue
        x.append(float(k))
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
    for i in range(1,25):
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

        sep = ''

        team1_html = Score_html.find('div', class_ = 'match-header-link-name mod-1')
        team1_list = [i.text.strip() for i in team1_html if '' not in i]
        team1 = sep.join(team1_list).replace('\n', '').replace('\t', '')

        team2_html = Score_html.find('div', class_ = 'match-header-link-name mod-2')
        team2_list = [i.text.strip() for i in team2_html if '' not in i]
        team2 = sep.join(team2_list).replace('\n', '').replace('\t', '')

        if Score_html.find('div', class_ = 'match-header-vs-score').find('div', class_ = 'match-header-vs-score').find('span', class_ = 'match-header-vs-score-winner') is None or Score_html.find('div', class_ = 'match-header-vs-score').find('div', class_ = 'match-header-vs-score').find('span', class_ = 'match-header-vs-score-loser') is None:
            continue
        Score = [Score_html.find('div', class_ = 'match-header-vs-score').find('div', class_ = 'match-header-vs-score').find('span', class_ = 'match-header-vs-score-winner').text.strip(), Score_html.find('div', class_ = 'match-header-vs-score').find('div', class_ = 'match-header-vs-score').find('span', class_ = 'match-header-vs-score-loser').text.strip()]

        teamnames = [team1, team2]

        for teamname in teamnames:
            for team in team_data:
                player_row = team.find_all('tr')
                for row in player_row:
                    name_td = row.find('td' , class_ = 'mod-player')
                    notname = name_td.text.replace('\n', '').replace('\t', '')
                    nameteam = notname.rsplit(' ', 1)
                    name = nameteam[0]

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
                        'Score': f"{team1[0]}{team1[1]} {Score[0]}:{Score[1]} {team2[0]}{team2[1]}"
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
                bad_player_name = name.text.strip()
                player_name = bad_player_name.rsplit(" ", 1)[0]
                players.append(player_name)
        tbd_teams[matchname] = players
    with open(tbd_json, 'w', encoding = 'utf-8') as f:
        json.dump(tbd_teams, f, indent = 4)

if avg_stats:
    print("Have stats")
else:
    matches = defaultdict(lambda: defaultdict(dict))
    for team in stats.keys():
        for player in stats[team].keys():
            for match in stats[team][player].keys():
                if 'acs' not in matches[match][team]:
                    matches[match][team] = {
                        'acs': [],
                        'kast': [],
                        'adr': []
                    }
                if len(matches[match][team]['acs']) < 5:
                    matches[match][team]['acs'].append(stats[team][player][match]['ACS'])
                    matches[match][team]['kast'].append(stats[team][player][match]['KAST'])
                    matches[match][team]['adr'].append(stats[team][player][match]['ADR'])
                if "Match Score" not in matches[match]:
                    matches[match]["Match Score"] = stats[team][player][match]['Score']
    for match in matches.keys():
        for team in list(matches[match].keys()):
            if team in ["Match Score", "deltas"]:
                continue
            else:
                if "deltas" not in matches[match]:
                    matches[match]["deltas"] = {
                        'delta acs': averager(matches[match][team]['acs']),
                        'delta kast': averager(matches[match][team]['kast']),
                        'delta adr': averager(matches[match][team]['adr']),
                        'delta elo': 0
                    }
                else:
                    matches[match]["deltas"]['delta acs'] -= averager(matches[match][team]['acs'])
                    matches[match]["deltas"]['delta kast'] -= averager(matches[match][team]['kast'])
                    matches[match]["deltas"]['delta adr'] -= averager(matches[match][team]['adr'])

        elos = re.findall(r'\[(\d{3,4})\]', matches[match]["Match Score"])
        if len(elos) == 2:
            team1_elo = int(elos[0])
            team2_elo = int(elos[1])
            matches[match]["deltas"]['delta elo'] = team1_elo - team2_elo
        else:
            matches[match]["deltas"]['delta elo'] = 0

    with open(avg_json, 'w', encoding = 'utf-8') as f:
        json.dump(matches, f, indent = 4)