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
import csv

start = time.time()

os.makedirs('event_cache', exist_ok=True)
os.makedirs('upcoming', exist_ok=True)

event_json = 'event.json'

def make_json(info, file):
    with open (file, 'w', encoding = 'utf-8') as f:
        json.dump(info, f, indent = 4)

def geturl(url, force_refresh = False):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    hash = hashlib.md5(url.encode('utf-8')).hexdigest()
    file = os.path.join('event_cache', hash)
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
    file = os.path.join('upcoming', hash)
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

events = loadfile(event_json)

def get_event_info():
    all_events = {}

    for page_number in range(1, 3):
        current_page = BeautifulSoup(requests.get(f"https://www.vlr.gg/events/?page={page_number}").text, 'lxml')
        upcoming_and_completed = current_page.find_all('div', class_ = 'events-container-col')
        
        upcoming_events = upcoming_and_completed[0]
        completed_events_html = upcoming_and_completed[1]

        if page_number == 1:
            upcoming_event_info = upcoming_events.find_all('a', class_ = 'wf-card mod-flex event-item')
            for event in upcoming_event_info:
                event_status_holder = event.find('div', class_ = 'event-item-desc-item')
                event_status = event_status_holder.find('span').text

                if event_status not in all_events:
                    all_events[event_status] = {}

                event_template_link = event.get('href')
                event_matches_link = event_template_link.replace('/event', '/event/matches')

                event_name = event.find('div', class_ = 'event-item-title').text.replace('\n', '').replace('\t', '')

                if event_name not in all_events:
                    all_events[event_status][event_name] = {
                        "Event Overview Link": f'https://vlr.gg{event_template_link}',
                        "Event Matches Link": f'https://vlr.gg{event_matches_link}'
                    }
            
            completed_event_info = completed_events_html.find_all('a', class_ = 'wf-card mod-flex event-item')
            for event in completed_event_info:
                event_status_holder = event.find('div', class_ = 'event-item-desc-item')
                event_status = event_status_holder.find('span').text

                if event_status not in all_events:
                    all_events[event_status] = {}

                event_template_link = event.get('href')
                event_matches_link = event_template_link.replace('/event', '/event/matches')

                event_name = event.find('div', class_ = 'event-item-title').text.replace('\n', '').replace('\t', '')

                if event_name not in all_events:
                    all_events[event_status][event_name] = {
                        "Event Overview Link": f'https://vlr.gg{event_template_link}',
                        "Event Matches Link": f'https://vlr.gg{event_matches_link}'
                    }
        
        else:
            completed_event_info = completed_events_html.find_all('a', class_ = 'wf-card mod-flex event-item')
            for event in completed_event_info:
                event_status_holder = event.find('div', class_ = 'event-item-desc-item')
                event_status = event_status_holder.find('span').text

                event_template_link = event.get('href')
                event_matches_link = event_template_link.replace('/event', '/event/matches')

                event_name = event.find('div', class_ = 'event-item-title').text.replace('\n', '').replace('\t', '')

                if event_name not in all_events:
                    all_events[event_status][event_name] = {
                        "Event Overview Link": f'https://vlr.gg{event_template_link}',
                        "Event Matches Link": f'https://vlr.gg{event_matches_link}'
                    }

    return all_events

def get_match_links():
    match_links = set()

    for event in events["completed"].keys():
        match_page_link = events["completed"][event]["Event Matches Link"]
        html = BeautifulSoup(requests.get(match_page_link).text, 'lxml')

        wf_card = html.find_all('div', class_ = 'wf-card')

        for card in wf_card:
            links = card.find_all('a', href = True)
            for link in links:
                match_status = link.find('div', class_ = 'ml_status')
                
                if not match_status:
                    continue
                
                rl_link = link.get('href')
                link_str = f'https://vlr.gg{rl_link}'
                match_links.add(link_str)

    for event in events["ongoing"].keys():
        match_page_link = events["ongoing"][event]["Event Matches Link"]
        html = BeautifulSoup(requests.get(match_page_link).text, 'lxml')

        wf_card = html.find_all('div', class_ = 'wf-card')

        for card in wf_card:
            links = card.find_all('a', href = True)
            for link in links:
                match_status_html = link.find('div', class_ = 'ml-status')
                
                if not match_status_html:
                    continue
                match_status = match_status_html.text
                
                if match_status == "Completed":
                    rl_link = link.get('href')
                    link_str = f'https://vlr.gg{rl_link}'
                    match_links.add(link_str)

    with open('links.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        for link in match_links:
            writer.writerow([link])

def create_team_map_dict():
    links = []
    team_dict = {}
    with open ('links.csv', 'r', newline='') as f:
        reader = csv.reader(f)
        for link in reader:
            str_link_unclipped = str(link)
            str_link = str_link_unclipped.replace('[\'', '').replace('\']', '')
            links.append(str_link)

    for match in links:
        match_html = BeautifulSoup(geturl(match), 'lxml')
        team_links = []

        match_time = match_html.find('div', class_ = 'moment-tz-convert').text.strip()

        team_link_cont = match_html.find('div', class_ = 'match-header-vs')
        team_link_html = team_link_cont.find_all('a', href = True)
        team_name_list = team_link_cont.find_all('div', class_ = 'wf-title-med')

        team1 = team_name_list[0].text.strip()
        team2 = team_name_list[1].text.strip()

        match_name = f'{team1} v {team2} on {match_time}'

        match_score = team_link_cont.find('div', class_ = 'js-spoiler').text.replace('\n', '').replace('\t', '')

        data_container = match_html.find('div', class_ = 'vm-stats-container')
        all_maps = data_container.find_all('div', class_ = 'vm-stats-game-header')
        
        for partial in team_link_html:
            i = partial.get('href')
            full_str = f'https://vlr.gg{i}'
            team_links.append(full_str)

        for team_page in team_links:
            current_page = BeautifulSoup(requests.get(team_page).text, 'lxml')

            current_team_name = current_page.find('h1', class_ = 'wf-title').text.strip()

            if current_team_name not in team_dict:
                team_dict[current_team_name] = {}

            if team_page not in team_dict:
                team_dict[current_team_name]["Team Link"] = team_page

            if match_name not in team_dict[current_team_name]:
                team_dict[current_team_name][match_name] = {}

            if match_score not in team_dict[current_team_name][match_name]:
                team_dict[current_team_name][match_name]["Match Score"] = match_score

            for map_instance in all_maps:
                map_name_html = map_instance.find('div', class_ = 'map')
                map_name = map_name_html.find('div', style = True).text

                if "PICK" in map_name:
                    map_name = map_name.replace("PICK", "").strip()
                else:
                    map_name = map_name.strip()
                
                left_team = map_instance.find('div', class_ = 'team')
                right_team = map_instance.find('div', class_ = 'team mod-right')

                left_team_name = left_team.find('div', class_ = 'team-name').text.strip()
                right_team_name = right_team.find('div', class_ = 'team-name').text.strip()

                if not left_team.find('div', class_ = 'score mod-win'):
                    left_team_score = left_team.find('div', class_ = 'score').text.strip()
                    right_team_score = right_team.find('div', class_ = 'score mod-win').text.strip()
                else:
                    left_team_score = left_team.find('div', class_ = 'score mod-win').text.strip()
                    right_team_score = right_team.find('div', class_ = 'score').text.strip()

                score_str = f'{left_team_name} {left_team_score}:{right_team_score} {right_team_name}'

                if map_name not in team_dict[current_team_name][match_name]:
                    team_dict[current_team_name][match_name][map_name] = score_str

    return team_dict

team_dict_json = loadfile('team_dict.json')

def team_map_elo_constructor():
    team_map_elo = {}

    for team in team_dict_json.keys():
        team_page_html = BeautifulSoup(requests.get(team_dict_json[team]["Team Link"]).text, 'lxml')
        rating_cont = team_page_html.find("div", class_ = 'core-rating-block mod-active')

        rating_html = rating_cont.find_all('div', class_ = 'team-rating-info-section mod-rating')
        rating_num = 0

        if rating_html:
            streak_html = rating_cont.find_all('div', class_ = 'team-rating-info-section mod-streak')

            tot_match = 0

            for streak_instance, rating_instance in zip(streak_html, rating_html):
                streak_num = streak_instance.find('div', class_ = 'rating-num')
                streak_num = streak_instance.text.replace('\n', '').replace('\t', '')

                record = re.search(r'(\d+)W(\d+)L', streak_num)
                wins = record.group(1)
                loss = record.group(2)

                current_match_num = int(wins) + int(loss)

                if current_match_num > tot_match:
                    tot_match = current_match_num
                    rating_num = int(rating_instance.find('div', class_ = 'rating-num').text.strip())
        else:
            rating_html = rating_cont.find('div', class_ = 'team-rating-info-section mod-rating')
            rating_num = int(rating_html.find('div', class_ = 'rating-num').text.strip())

        if team not in team_map_elo:
            team_map_elo[team] = {
                "Bind": rating_num,
                "Haven": rating_num,
                "Split": rating_num,
                "Ascent": rating_num,
                "Icebox": rating_num,
                "Breeze": rating_num,
                "Fracture": rating_num,
                "Pearl": rating_num,
                "Lotus": rating_num,
                "Sunset": rating_num,
                "Abyss": rating_num
            }

    match_set = set()



end = time.time()
print(f'{round(end - start, 2)}s')