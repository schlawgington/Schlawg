import os
import requests
from bs4 import BeautifulSoup
import json
import hashlib
import re
import numpy as np
from datetime import datetime
import math
import time

TEAM_NAME_NORMALIZATION = {
    "VISA KRÜ(KRÜ Esports)": "KRÜ Esports",
    "M80": "Chet's Pets",
    "Vila do Zana": "DIRETORIA",
    "Guangzhou Huadu Bilibili Gaming(Bilibili Gaming)": "Bilibili Gaming",
    "JD Mall JDG Esports(JDG Esports)": "JDG Esports"
}

start = time.time()

os.makedirs('cache', exist_ok = True)
os.makedirs('schedule', exist_ok = True)

teams_json = 'teams.json'
tbd_json = 'tbd.json'
match_json = 'match.json'
ranking_json = 'ranking.json'
error_json = 'error.json'

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

def getmatch(url, force_refresh = False):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    hash = hashlib.md5(url.encode('utf-8')).hexdigest()
    file = os.path.join('schedule', hash)
    if os.path.exists(file) and not force_refresh:
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

def prob(r1, r2):
    return 1.0 / (1 + math.pow(10, (r1 - r2) / 400))

def create_team_list():
    teams = set()
    
    region_list = ['north-america', 'europe', 'brazil', 'asia-pacific', 'korea', 'china', 'japan', 'la-s', 'la-n', 'oceania', 'mena', 'gc']
    link = 'https://www.vlr.gg/rankings/'
    for region in region_list:
        region_page_html = BeautifulSoup(requests.get(link + region).text, 'lxml')
        team_container_html = region_page_html.find('div', class_ = 'mod-scroll')
        team_list_html = team_container_html.find_all('div', class_ = 'rank-item wf-card fc-flex')
        for team in team_list_html:
            ge_text = team.find('div', class_ = 'ge-text')
            teamname = ge_text.find(string = True, recursive = False)
            team_rating = team.find('div', class_ = 'rank-item-rating').text
            team_string = f'{teamname.strip()}: {team_rating.strip()}'
            
            teams.add(team_string)
    
    return list(teams)

def get_history_links():
    links = set()
    for page in range(1, 33):
        soup = BeautifulSoup(geturl(f"https://www.vlr.gg/matches/results/?page={page}"), 'lxml')
        matches = soup.find_all('a', href=True)        
        for match in matches:
            href = match.get('href')
            if re.match(r'^/\d+/', href):
                links.add(href)
    return list(links)

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

        if soup.find('div', class_ = 'match-header-vs-score').find('div', class_ = 'match-header-vs-score') is None:
            continue
        match_header_score_unclipped = soup.find('div', class_ = 'match-header-vs-score').find('div', class_ = 'match-header-vs-score').text.replace('\n', '').replace('\t', '')
        match_header_score = re.match(r'\d:\d', match_header_score_unclipped).group()

        match_header_team_names = soup.find_all('div', class_ = 'wf-title-med')
        team1 = match_header_team_names[0].text.replace('\n', '').replace('\t', '')
        team2 = match_header_team_names[1].text.replace('\n', '').replace('\t', '')

        if team1 in TEAM_NAME_NORMALIZATION:
            team1 = TEAM_NAME_NORMALIZATION[team1]
        if team2 in TEAM_NAME_NORMALIZATION:
            team2 = TEAM_NAME_NORMALIZATION[team2]
        
        match_string = f'{team1} {match_header_score} {team2}'
        
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
                'Total Round diff': f'{team1_tot_rounds} - {team2_tot_rounds} = {team1_tot_rounds - team2_tot_rounds}',
                'Match Link': f'{i}'
            }
    return match_dict

def create_team_rankings():
    teams = {}
    
    for team in team_list:
        teamname = team.split(': ')[0]
        team_elo = int(team.split(': ')[1])
        if team not in teams:
            teams[teamname] = team_elo
    for match in match_history.keys():
        match_team_and_score = match_history[match]['Match Score']
        match_info = re.match(r'^(.*)\s(\d:\d)\s(.*)$', match_team_and_score)

        if not match_info:
            continue
        
        score = match_info.group(2).split(':')
        map_win_diff = int(score[0]) - int(score[1])
        round_win_diff = int(match_history[match]['Total Round diff'].rsplit(' ', 1)[1])
        
        team1_name = match_info.group(1)
        team2_name = match_info.group(3)

        if team1_name not in teams or team2_name not in teams:
            continue
        
        team1_elo = teams[team1_name]
        team2_elo = teams[team2_name]

        prob_team1_win = prob(team2_elo, team1_elo)
        prob_team2_win = prob(team1_elo, team2_elo)
        
        K = 20 + abs(round_win_diff)
        if map_win_diff > 0:
            teams[team1_name] += round(K*(1-prob_team1_win), 1)
            teams[team2_name] += round(K*(0-prob_team2_win), 1)
        elif map_win_diff < 0:
            teams[team1_name] += round(K*(0-prob_team1_win), 1)
            teams[team2_name] += round(K*(1-prob_team2_win), 1)
        else:
            continue

    return dict(sorted(teams.items(), key=lambda x: x[1], reverse=True))


def get_schedule_links(force_refresh = False):
    schedule = [BeautifulSoup(requests.get("https://www.vlr.gg/matches").text, 'lxml'), BeautifulSoup(requests.get("https://www.vlr.gg/matches/?page=2").text, 'lxml')]
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

def create_schedule(schedule_links):
    tbd_teams = {}
    
    for link in schedule_links:
        link = "https://www.vlr.gg" + link
        
        soup2 = BeautifulSoup(getmatch(link), 'lxml')
        teamnames = soup2.find_all('div', 'wf-title-med')
        
        team1 = teamnames[0].text.replace("\n", "").replace("\t", "")
        team2 = teamnames[1].text.replace("\n", "").replace("\t", "")


        if team1 in TEAM_NAME_NORMALIZATION:
            team1 = TEAM_NAME_NORMALIZATION[team1]
        if team2 in TEAM_NAME_NORMALIZATION:
            team2 = TEAM_NAME_NORMALIZATION[team2]

        elo.setdefault(team1, 1500)
        elo.setdefault(team2, 1500)

        real_team1 = f'{team1} [{elo[team1]}]'
        real_team2 = f'{team2} [{elo[team2]}]'

        table = soup2.find_all('table', class_ = 'wf-table-inset mod-overview')

        player_set = set()
        for tab in table:
            players = tab.find_all('div', class_ = 'text-of')
            for player in players:
                player_set.add(player.text.strip())
        
        player_list = list(player_set)
        
        matchname = hashlib.md5(link.encode('utf-8')).hexdigest()
        match_datetime = soup2.find('div', class_ = 'match-header-date').find_all('div', class_ = 'moment-tz-convert')
        if len(match_datetime) < 2:
            continue
        date = ', '.join([match_datetime[0].text.strip(), match_datetime[1].text.strip()])
        
        if matchname not in tbd_teams:
            tbd_teams[matchname] = {
                'Team 1': f'{real_team1}: {round(100*prob(elo[team2], elo[team1]), 2)}%',
                'Team 2': f'{real_team2}: {round(100*prob(elo[team1], elo[team2]), 2)}%',
                'Time': date,
                'Link': link,
                'Players': player_list
            }
    return tbd_teams

def cache_update():   
    now = datetime.now()
    update_matches_links = []
    update_match_hash = []
    for match in list(tbd.keys()):
        match_time_str = tbd[match]['Time']
        cleaned_time_str = re.sub(r'(\d{1,2})(st|nd|rd|th)', r'\1', match_time_str).rsplit(' ', 1)[0]
        format_str = "%A, %B %d, %I:%M %p"
        match_time = datetime.strptime(cleaned_time_str, format_str)
        match_time = match_time.replace(year=now.year)
        
        if match_time < now:
            update_match_hash.append(match)
            update_matches_links.append(tbd[match]["Link"])
            schedule_match = os.path.join('schedule', match)
            if os.path.exists(schedule_match):
                os.remove(schedule_match)
    
    for url in update_matches_links:
        geturl(url, force_refresh=True)

    update_match = create_match_history(update_matches_links)
    match_history.update(update_match)
    make_json(match_history, match_json)

    error_dict = {}
    for match in update_match_hash:
        if match not in error_dict:
            error_dict[match] = {
                'Result': [match_history[match]["Match Score"], match_history[match]["Total Round diff"]],
                'Prediction': [tbd[match]['Team 1'], tbd[match]['Team 2']]
            }
    if error is None:
        make_json(error_dict, error_json)
    else:
        error.update(error_dict)
        make_json(error, error_json)

    new_elo = {}
    for match in update_match_hash:
        match_team_and_score = match_history[match]['Match Score']
        match_info = re.search(r'^(.*?)\s+(\d:\d)\s+(.*)$', match_team_and_score)

        if not match_info:
            continue
        
        score = match_info.group(2).split(':')
        map_win_diff = int(score[0]) - int(score[1])
        round_win_diff = int(match_history[match]['Total Round diff'].rsplit(' ', 1)[1])
        
        team1_name = match_info.group(1)
        team2_name = match_info.group(3)

        if team1_name not in elo:
            elo[team1_name] = 1500
        if team2_name not in elo:
            elo[team2_name] = 1500

        if team1_name or team2_name not in new_elo:
            new_elo[team1_name] = elo[team1_name]
            new_elo[team2_name] = elo[team2_name]

        prob_team1_win = prob(new_elo[team2_name], new_elo[team1_name])
        prob_team2_win = prob(new_elo[team1_name], new_elo[team2_name])
        
        K = 20 + abs(round_win_diff)
        if map_win_diff > 0:
            new_elo[team1_name] += round(K*(1-prob_team1_win), 1)
            new_elo[team2_name] += round(K*(0-prob_team2_win), 1)
        elif map_win_diff < 0:
            new_elo[team1_name] += round(K*(0-prob_team1_win), 1)
            new_elo[team2_name] += round(K*(1-prob_team2_win), 1)
        else:
            continue
        
    elo.update(new_elo)
    make_json(elo, ranking_json)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }

    new_links = get_schedule_links()
    new_tbd = create_schedule(new_links)
    make_json(new_tbd, tbd_json)


def main():
    global team_list
    global match_history
    global elo
    global tbd
    global error
    
    team_list = loadfile(teams_json)
    tbd = loadfile(tbd_json)
    match_history = loadfile(match_json)
    elo = loadfile(ranking_json)
    error = loadfile(error_json)
    
    if team_list is None:
        teams = create_team_list()
        make_json(teams, teams_json)
    
    if match_history is None:
        links = get_history_links()
        match_history = create_match_history(links)
        make_json(match_history, match_json)
    
    if elo is None:
        rankings = create_team_rankings()
        make_json(rankings, ranking_json)
    
    if tbd is None:
        schedule_links = get_schedule_links()
        tbd_sched = create_schedule(schedule_links)
        make_json(tbd_sched, tbd_json)
    
    cache_update()

main()

print('Elapsed', time.time() - start)