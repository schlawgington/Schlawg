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
import math
import time

start = time.time()

os.makedirs('cache', exist_ok = True)
os.makedirs('schedule', exist_ok = True)

stat_json = 'stat.json'
tbd_json = 'tbd.json'
match_json = 'match.json'
team_json = 'team.json'

def make_json(info, file):
    with open (file, 'w', encoding = 'utf-8') as f:
        json.dump(info, f, indent = 4)

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

stats = loadfile(stat_json)
tbd = loadfile(tbd_json)
match_history = loadfile(match_json)
elo = loadfile(team_json)

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

def prob(r1, r2):
    return 1.0 / (1 + math.pow(10, (r1 - r2) / 400))

def get_history_links(max_pages = 33):
    links = set()
    for i in range(1, max_pages):
        soup = BeautifulSoup(geturl(f"https://www.vlr.gg/matches/results/?page={i}"), 'lxml')
        matches = soup.find_all('a', href=True)        
        for match in matches:
            href = match.get('href')
            if re.match(r'^/\d+/', href):
                links.add(href)
    return list(links)

#links = get_history_links()

def create_player_history(links):
    team_stats = {}
    if isinstance(links, list) is False:
        links = [links]
    
    for i in links:
        
        if "https://www.vlr.gg" in i:
            i = i.replace("https://www.vlr.gg", '')
        i = "https://www.vlr.gg" + i
        
        soup = BeautifulSoup(geturl(i), 'lxml')
        
        match_name = hashlib.md5(i.encode('utf-8')).hexdigest()
        match_data = soup.find('div', class_ = 'vm-stats')

        team_data = match_data.find_all('tbody')

        Score_html = soup.find('div', class_ = 'match-header-vs')

        team1_html = Score_html.find('div', class_ = 'match-header-link-name mod-1')
        team1_list = [j.text.replace('\n', '').replace('\t', '') for j in team1_html if '' not in j]

        team2_html = Score_html.find('div', class_ = 'match-header-link-name mod-2')
        team2_list = [j.text.replace('\n', '').replace('\t', '') for j in team2_html if '' not in j]

        if Score_html.find('div', class_ = 'match-header-vs-score').find('div', class_ = 'match-header-vs-score').find('span', class_ = 'match-header-vs-score-winner') is None or Score_html.find('div', class_ = 'match-header-vs-score').find('div', class_ = 'match-header-vs-score').find('span', class_ = 'match-header-vs-score-loser') is None:
            continue
        Score = [Score_html.find('div', class_ = 'match-header-vs-score').find('div', class_ = 'match-header-vs-score').find('span', class_ = 'match-header-vs-score-winner').text.strip(), Score_html.find('div', class_ = 'match-header-vs-score').find('div', class_ = 'match-header-vs-score').find('span', class_ = 'match-header-vs-score-loser').text.strip()]

        teamnames = [team1_list[0], team2_list[0]]

        for teamname, team in zip(teamnames,  team_data):
            player_row = team.find_all('tr')

            if teamname not in team_stats:
                team_stats[teamname] = {}

            for row in player_row:
                name_td = row.find('td' , class_ = 'mod-player')
                name = name_td.text.replace('\n', '').replace('\t', '')

                stat_tds = row.find_all('td')
                
                ACS = stat_tds[3].text.strip().replace('\n', ',').split(',')
                KAST = stat_tds[8].text.strip().replace('\n', ',').split(',')
                ADR = stat_tds[9].text.strip().replace('\n', ',').split(',')

                if name not in team_stats[teamname]:
                    team_stats[teamname][name] = {}

                team_stats[teamname][name] = {
                    'ACS': averager(ACS),
                    'KAST': averager(KAST),
                    'ADR': averager(ADR)
                }

    return team_stats

#player_history = create_player_history(links)
#make_json(player_history, stat_json)

def create_match_history(links):
    match_dict = {}
    
    if isinstance(links, list) is False:
        links = [links]
    
    for i in links:
        
        if "https://www.vlr.gg" in i:
            i = i.replace("https://www.vlr.gg", '')
        i = "https://www.vlr.gg" + i
        
        soup = BeautifulSoup(geturl(i), 'lxml')
        
        match_name = hashlib.md5(i.encode('utf-8')).hexdigest()
        match_data = soup.find('div', class_ = 'vm-stats')

        match_header_score_unclipped = soup.find('div', class_ = 'match-header-vs-score').find('div', class_ = 'match-header-vs-score').text.replace('\n', '').replace('\t', '')
        match_header_score = re.match(r'\d:\d', match_header_score_unclipped).group()

        match_header_team_names = soup.find_all('div', class_ = 'wf-title-med')
        
        match_string = f'{match_header_team_names[0].text.replace('\n', '').replace('\t', '')} {match_header_score} {match_header_team_names[1].text.replace('\n', '').replace('\t', '')}'
        
        big_match_data = match_data.find_all('div', class_ = 'vm-stats-game-header')
        
        map_strings = []
        team1_tot_rounds = 0
        team2_tot_rounds = 0
        
        for maps in big_match_data:
            team1_match_data = maps.find('div', class_ = 'team')
            team1_score = team1_match_data.find('div', class_ = 'score').text.strip()
            team1_tot_rounds += int(team1_score)

            map_name = maps.find('div', class_ = 'map').text.strip().split('\t', 1)[0]

            team2_match_data = maps.find('div', class_ = 'team mod-right')
            team2_score = team2_match_data.find('div', class_ = 'score').text.strip()
            team2_tot_rounds += int(team2_score)

            string = f'{map_name}: {team1_score}-{team2_score}'
            map_strings.append(string)

        
        if match_name not in match_dict:
            match_dict[match_name] = {
                'Match Score': match_string,
                'Map Scores': map_strings,
                'Total Round diff': f'{team1_tot_rounds} - {team2_tot_rounds} = {team1_tot_rounds - team2_tot_rounds}'
            }
    return match_dict

#match_history = create_match_history(links)
#make_json(match_history, match_json)

def create_team_rankings():
    teams = {}
    def get_elo(team_name): 
        return teams.setdefault(team_name, 1500) 
    
    for team in stats.keys():
        if team not in teams:
            teams[team] = 1500
    for match in match_history.keys():
        match_team_and_score = match_history[match]['Match Score']
        match_info = re.search(r'^(.*?)\s+(\d:\d)\s+(.*)$', match_team_and_score)

        if not match_info:
            continue
        
        score = match_info.group(2).split(':')
        map_win_diff = int(score[0]) - int(score[1])
        round_win_diff = int(match_history[match]['Total Round diff'].rsplit(' ', 1)[1])
        
        team1_name = match_info.group(1)
        team2_name = match_info.group(3)

        team1_elo = get_elo(team1_name)
        team2_elo = get_elo(team2_name)

        prob_team1_win = prob(team2_elo, team1_elo)
        prob_team2_win = prob(team1_elo, team2_elo)
        
        K = 30 + abs(round_win_diff)
        if map_win_diff > 0:
            teams[team1_name] += round(K*(1-prob_team1_win), 1)
            teams[team2_name] += round(K*(0-prob_team2_win), 1)
        else:
            teams[team1_name] += round(K*(0-prob_team1_win), 1)
            teams[team2_name] += round(K*(1-prob_team2_win), 1)

    return dict(sorted(teams.items(), key=lambda x: x[1], reverse=True))

#teams = create_team_rankings()
#make_json(teams, team_json)
    

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
        
        soup2 = BeautifulSoup(getmatch(link), 'lxml')
        teamnames = soup2.find_all('div', 'wf-title-med')
        
        team1 = teamnames[0].text.replace("\n", "").replace("\t", "")
        team2 = teamnames[1].text.replace("\n", "").replace("\t", "")

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
        
        if matchname not in tbd_teams:
            tbd_teams[matchname] = {
                team1: round(100*prob(elo[team2], elo[team1]), 2),
                team2: round(100*prob(elo[team1], elo[team2]), 2),
                'Players': players,
                'Time': date,
                'Link': link
            }
    with open(tbd_json, 'w', encoding = 'utf-8') as f:
        json.dump(tbd_teams, f, indent = 4)

create_schedule(schedule_links)

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
    update_player = create_player_history(update_matches_links)

    match_history.update(update_match)
    stats.update(update_player)

    make_json(match_history, match_json)
    make_json(stats, stat_json)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    new_sched_pages = [BeautifulSoup(requests.get("https://www.vlr.gg/matches", headers = headers).text, 'lxml'), BeautifulSoup(requests.get("https://www.vlr.gg/matches/?page=2", headers = headers).text, 'lxml')]
    
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

print('Elapsed', time.time() - start)