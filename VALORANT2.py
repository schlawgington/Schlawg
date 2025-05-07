import os
import requests
from bs4 import BeautifulSoup
import json
import hashlib
from collections import defaultdict
import re
import numpy as np

#makes directory called cache
os.makedirs('cache', exist_ok = True)
os.makedirs('schedule', exist_ok = True)

def geturl(url):
    #Mimic normal browser when requesting, so don't get ip banned
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    #give file a hash name
    hash = hashlib.md5(url.encode('utf-8')).hexdigest()
    #give file path in cache
    file = os.path.join('cache', hash)
    #if path to file exists, read file
    if os.path.exists(file):
        with open(file, 'r', encoding = 'utf-8') as f:
            contents = f.read()
        return contents
    #if path doesn't exist, write contents of url to it as txt
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

def averager(strlist):
    x = []
    for k in strlist:
        if '%' in k:
            k = k.replace('%', '').replace('\xa0', '')
        if k == '':
            continue
        x.append(int(k))
    if not x:
        return 0
    y = sum(x) / len(x)
    return y

def loadfile(file):
    if os.path.exists(file):
        with open(file, 'r', encoding = 'utf-8') as f:
            content = json.load(f)
            return content
    else:
        return None

stat_json = 'stats.json'
hth_json = 'hth.json'

stats = loadfile(stat_json)
hth_stats = loadfile(hth_json)

if stats and hth_stats:
    print("Stats loaded")
else:
    results = []
    for i in range(1,11):
        if i == 1:
            results.append(BeautifulSoup(geturl("https://www.vlr.gg/matches/results/"), 'html.parser'))
        results.append(BeautifulSoup(geturl("https://www.vlr.gg/matches/results/?page=" + str(i)), 'html.parser'))
    links = []
    player_stats = defaultdict(dict)
    hth = {}
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
    for i in links:
        soup = BeautifulSoup(geturl("https://www.vlr.gg" + i), 'html.parser')
        match_name = hashlib.md5(i.encode('utf-8')).hexdigest()
        match_data = soup.find('div', class_ = 'vm-stats-game mod-active')
        team_data = match_data.find_all('tbody')
        for team in team_data:
            player_row = team.find_all('tr')
            for row in player_row:
                name_td = row.find('td' , class_ = 'mod-player')
                name = name_td.text.replace('\n', '').replace('\t', '')

                stat_tds = row.find_all('td')
                ACS = stat_tds[3].text.strip().replace('\n', ',').split(',')
                K = stat_tds[4].text.strip().replace('\n', ',').split(',')
                D = stat_tds[5].text.replace('/', '').strip().replace('\n', ',').split(',')
                A = stat_tds[6].text.strip().replace('\n', ',').split(',')
                KAST = stat_tds[8].text.strip().replace('\n', ',').split(',')
                ADR = stat_tds[9].text.strip().replace('\n', ',').split(',')

                player_stats[name][match_name] = {
                    'ACS': averager(ACS),
                    'K': averager(K),
                    'D': averager(D),
                    'A': averager(A),
                    'KAST': averager(KAST),
                    'ADR': averager(ADR)
                }
        hth_html = soup.find('div', class_ = 'match-header-vs-score').text.replace('\n', '').replace('\t', '')
        hth_score = re.search(r'\d:\d', hth_html).group()
        team1 = soup.find('a', 'match-header-link wf-link-hover mod-1')
        team2 = soup.find('a', 'match-header-link wf-link-hover mod-2')
        namegob = team1.text.strip().replace('\n', '').replace('\t', '')
        namegoob = team2.text.strip().replace('\n', '').replace('\t', '')
        name1 = re.sub(r'\[\d+\]', '', namegob)
        name2 = re.sub(r'\[\d+\]', '', namegoob)
        hth[match_name] = {
            'Team 1': name1,
            'Team 2': name2,
            'Score:': hth_score
        }
    with open(stat_json, 'w', encoding = 'utf-8') as f:
        json.dump(player_stats, f, indent = 4)
    with open(hth_json, 'w', encoding = 'utf-8') as k:
        json.dump(hth, k, indent = 4)

tbd_json = 'tbd.json'
tbd = loadfile(tbd_json)

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
    
    team_stat = get_team_stats(matchhash)
    previous_match = previous_matches()

    keys = team_stat.keys()
    keys = [key for key in keys]

    team1 = 1.429*(team_stat[keys[0]]['avg_acs']) + team_stat[keys[0]]['avg_kast'] + team_stat[keys[0]]['avg_adr'] + previous_matches()
    team2 = 1.429*(team_stat[keys[1]]['avg_acs']) + team_stat[keys[1]]['avg_kast'] + team_stat[keys[1]]['avg_adr'] + previous_matches()

    values = np.array([team1, team2])
    
    probabilities = values/ sum(values)
    probabilities = 100*probabilities

    STATEMENT = f"{keys[0]}: {str(probabilities[0])}% \n{keys[1]}: {str(probabilities[1])}%"

    return STATEMENT

PREDICTION = generateprobability("https://www.vlr.gg/481897/funhavers-vs-winthrop-university-challengers-league-2025-north-america-ace-stage-2-r6")
print(PREDICTION)