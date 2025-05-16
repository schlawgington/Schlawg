import os
import requests
from bs4 import BeautifulSoup
import json
import hashlib
import re
from collections import defaultdict
import numpy as np
from datetime import datetime
import shutil

os.makedirs('cache', exist_ok = True)
os.makedirs('schedule', exist_ok = True)

stat_json = 'stat.json'
tbd_json = 'tbd.json'
avg_json = 'avg.json'

def geturl(url, force_refresh = False):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    hash = hashlib.md5(url.encode('utf-8')).hexdigest()
    file = os.path.join('cache', hash)
    if os.path.exists(file) and not force_refresh:
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
                return None
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

def get_history_links():
    results = []
    for i in range(1,3):
        results.append(BeautifulSoup(geturl(f"https://www.vlr.gg/matches/results/?page={i}"), 'html.parser'))
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
    return links

links = get_history_links()

def create_match_history(links):
    team_stats = {}
    if isinstance(links, list) is False:
        links = [links]
    for i in links:
        if "https://www.vlr.gg" in i:
            i = i.replace("https://www.vlr.gg", '')
        i = "https://www.vlr.gg" + i
        soup = BeautifulSoup(geturl(i), 'html.parser')
        
        match_name = hashlib.md5(i.encode('utf-8')).hexdigest()
        match_data = soup.find('div', class_ = 'vm-stats-game mod-active')
        team_data = match_data.find_all('tbody')

        Score_html = soup.find('div', class_ = 'match-header-vs')

        team1_html = Score_html.find('div', class_ = 'match-header-link-name mod-1')
        team1_list = [j.text.strip() for j in team1_html if '' not in j]

        team2_html = Score_html.find('div', class_ = 'match-header-link-name mod-2')
        team2_list = [j.text.strip() for j in team2_html if '' not in j]

        if Score_html.find('div', class_ = 'match-header-vs-score').find('div', class_ = 'match-header-vs-score').find('span', class_ = 'match-header-vs-score-winner') is None or Score_html.find('div', class_ = 'match-header-vs-score').find('div', class_ = 'match-header-vs-score').find('span', class_ = 'match-header-vs-score-loser') is None:
            continue
        Score = [Score_html.find('div', class_ = 'match-header-vs-score').find('div', class_ = 'match-header-vs-score').find('span', class_ = 'match-header-vs-score-winner').text.strip(), Score_html.find('div', class_ = 'match-header-vs-score').find('div', class_ = 'match-header-vs-score').find('span', class_ = 'match-header-vs-score-loser').text.strip()]

        teamnames = [team1_list[0], team2_list[0]]
        teamelo = [team1_list[1], team2_list[1]]

        for teamname, elo, team in zip(teamnames, teamelo, team_data):
            player_row = team.find_all('tr')

            if teamname not in team_stats:
                team_stats[teamname] = {
                    'ELO': None,
                    'Players': {}
                }

            team_stats[teamname]['ELO'] = elo

            for row in player_row:
                name_td = row.find('td' , class_ = 'mod-player')
                name = name_td.text.replace('\n', '').replace('\t', '')

                stat_tds = row.find_all('td')
                ACS = stat_tds[3].text.strip().replace('\n', ',').split(',')
                KAST = stat_tds[8].text.strip().replace('\n', ',').split(',')
                ADR = stat_tds[9].text.strip().replace('\n', ',').split(',')

                if name not in team_stats[teamname]['Players']:
                    team_stats[teamname]['Players'][name] = {}

                if match_name not in team_stats[teamname]['Players'][name]:
                    team_stats[teamname]['Players'][name][match_name] = {}

                team_stats[teamname]['Players'][name][match_name] = {
                    'ACS': averager(ACS),
                    'KAST': averager(KAST),
                    'ADR': averager(ADR),
                    'Score': f"{team1_list[0]}{team1_list[1]} {Score[0]}:{Score[1]} {team2_list[0]}{team2_list[1]}"
                }
    return team_stats

def make_stat_json(team_stats):
    with open (stat_json, 'w', encoding = 'utf-8') as f:
        json.dump(team_stats, f, indent = 4)

def get_schedule_links():
    schedule = [BeautifulSoup(getmatch("https://www.vlr.gg/matches"), 'html.parser'), BeautifulSoup(getmatch("https://www.vlr.gg/matches/?page=2"), 'html.parser')]
    schedulelinks = []
    for card in schedule:
        cardclass = card.find_all('div', class_ = 'wf-card')
        for links in cardclass:
            linkclass = links.find_all('a', href = True)
            for link in linkclass:
                if '/matches' in link.get('href') or 'tbd' in link.get('href'):
                    continue
                schedulelinks.append(link.get('href'))
    return schedulelinks
    
schedule_links = get_schedule_links()

def create_schedule(schedule_links):
    tbd_teams = {}
    for link in schedule_links:
        link = "https://www.vlr.gg" + link
        soup2 = BeautifulSoup(getmatch(link), 'html.parser')
        table = soup2.find_all('table', class_ = 'wf-table-inset mod-overview')
        matchname = hashlib.md5(link.encode('utf-8')).hexdigest()
        match_datetime = soup2.find('div', class_ = 'match-header-date')
        date = ', '.join([match_datetime.find_all('div', class_ = 'moment-tz-convert')[0].text.strip(), match_datetime.find_all('div', class_ = 'moment-tz-convert')[1].text.strip()])
        players = []
        for body in table:
            names = body.find_all('td', class_ = 'mod-player')
            for name in names:
                if len(players) > 9:
                    break
                player_name = name.text.strip().replace("\n", "").replace("\t", "")
                players.append(player_name)
        tbd_teams[matchname] = {
            'Players': players,
            'Time': date,
            'Link': link
        }
    with open(tbd_json, 'w', encoding = 'utf-8') as f:
        json.dump(tbd_teams, f, indent = 4)

def create_avgs():
    matches = defaultdict(lambda: defaultdict(dict))

    for team in stats.keys():
        players = list(stats[team]['Players'].keys())
        for player in players:
            if len(player.rsplit(" ", 1)) == 2:
                teamname = player.rsplit(" ", 1)[1]
                break
            else:
                continue
       
        elo = int(re.search(r'\d+', stats[team]['ELO']).group()) if stats[team]['ELO'] else 0

        all_matches= set()
        for player in stats[team]['Players'].keys():
            all_matches.update(stats[team]['Players'][player].keys())

        for match in all_matches:
            if match not in matches:
                matches[match]: {
                    'teams': {},
                }
        
            if teamname not in matches[match]['teams']:
                matches[match]['teams'][teamname] = {
                    'acs': [],
                    'kast': [],
                    'adr': [],
                    'elo': elo
                }

            for player in stats[team]['Players'].keys():
                if match in stats[team]['Players'][player]:
                    if len(player.rsplit(" ", 1)) != 2:
                        continue
                    if len(matches[match]['teams'][teamname]['acs']) < 5:
                        matches[match]['teams'][teamname]['acs'].append(stats[team]['Players'][player][match]['ACS'])
                        matches[match]['teams'][teamname]['kast'].append(stats[team]['Players'][player][match]['KAST'])
                        matches[match]['teams'][teamname]['adr'].append(stats[team]['Players'][player][match]['ADR'])

    for match in matches.keys():
        teamnames = list(matches[match]['teams'].keys())
        if len(teamnames) != 2:
            continue
        team1 = teamnames[0]
        team2 = teamnames[1]

        team1_acs = averager(matches[match]['teams'][team1]['acs'])
        team2_acs = averager(matches[match]['teams'][team2]['acs'])

        team1_kast = averager(matches[match]['teams'][team1]['kast'])
        team2_kast = averager(matches[match]['teams'][team2]['kast'])

        team1_adr = averager(matches[match]['teams'][team1]['adr'])
        team2_adr = averager(matches[match]['teams'][team2]['adr'])

        team1_elo = int(matches[match]['teams'][team1]['elo'])
        team2_elo = int(matches[match]['teams'][team2]['elo'])

        matches[match]['deltas'] = {
            'delta_acs': team1_acs - team2_acs,
            'delta_kast': team1_kast - team2_kast,
            'delta_adr': team1_adr - team2_adr,
            'delta_elo': team1_elo - team2_elo if team1_elo != 0 and team2_elo != 0 else 0
        }

    to_delete = []
    for match in matches:
        if len(matches[match]['teams']) < 2:
            to_delete.append(match)
        elif 'deltas' not in matches[match]:
            to_delete.append(match)
        elif matches[match]['deltas']['delta_acs'] == 0:
            to_delete.append(match)
    for match in to_delete:
        del matches[match]

    with open(avg_json, 'w', encoding = 'utf-8') as f:
        json.dump(matches, f, indent = 4)

def cache_update():
    now = datetime.now()
    update_matches_links = []
    for match in list(tbd.keys()):
        match_link = tbd[match]["Link"]
        
        match_time_str = tbd[match]['Time']
        cleaned_time_str = re.sub(r'(\d{1,2})(st|nd|rd|th)', r'\1', match_time_str).rsplit(' ', 1)[0]
        format_str = "%A, %B %d, %I:%M %p"
        match_time = datetime.strptime(cleaned_time_str, format_str)
        match_time = match_time.replace(year=now.year)
        
        if match_time < now:
            update_matches_links.append(match_link)
            schedule_match = os.path.join('schedule', match)
            if os.path.exists(schedule_match):
                os.remove(schedule_match)
    
    for url in update_matches_links:
        geturl(url, force_refresh=True)
    
    update_match = create_match_history(update_matches_links)
    stats.update(update_match)
    make_stat_json(stats)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    new_sched_pages = [BeautifulSoup(requests.get("https://www.vlr.gg/matches", headers = headers).text, 'html.parser'), BeautifulSoup(requests.get("https://www.vlr.gg/matches/?page=2", headers = headers).text, 'html.parser')]
    
    new_links = []
    for page in new_sched_pages:
        cardclass = page.find_all('div', class_ = 'wf-card')
        for links in cardclass:
            linkclass = links.find_all('a', href = True)
            for link in linkclass:
                if '/matches' in link.get('href') or 'tbd' in link.get('href'):
                    continue
                new_links.append(link.get('href'))
    create_schedule(new_links)

#create_match_history(links)
#create_schedule(schedule_links)
cache_update()