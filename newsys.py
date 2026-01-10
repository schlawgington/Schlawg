import os
import requests
from bs4 import BeautifulSoup
import json
import re
import numpy as np
from datetime import datetime
import math
import time


start = time.time()

def make_json(info, file):
    with open (file, 'w', encoding = 'utf-8') as f:
        json.dump(info, f, indent = 4)

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

def get_team_elo(team_page_link):
    team_elo_page = BeautifulSoup(requests.get(team_page_link).text, 'lxml')
    rating_cont = team_elo_page.find("div", class_ = 'core-rating-block mod-active')

    flag = False

    if not rating_cont:
        return None

    rating_html = rating_cont.find_all('div', class_ = 'team-rating-info-section mod-rating')
            
    rating_num = 0

    if rating_html:
        streak_html = rating_cont.find_all('div', class_ = 'team-rating-info-section mod-streak')

        tot_match = 0

        for streak_instance, rating_instance in zip(streak_html, rating_html):
            streak_num = streak_instance.find('div', class_ = 'rating-num')
            streak_num = streak_instance.text.replace('\n', '').replace('\t', '')

            record = re.search(r'(\d+)W(\d+)L', streak_num)
                    
            if not record:
                flag = True
                continue
                    
            wins = record.group(1)
            loss = record.group(2)

            current_match_num = int(wins) + int(loss)

            if current_match_num > tot_match:
                tot_match = current_match_num
                rating_num = int(rating_instance.find('div', class_ = 'rating-num').text.strip())
    else:
        rating_html = rating_cont.find('div', class_ = 'team-rating-info-section mod-rating')
        rating_num = int(rating_html.find('div', class_ = 'rating-num').text.strip())

    if flag:
        return None

    return rating_num

def get_match_info(match_link):
    team_map_elo = {}

    html = BeautifulSoup(requests.get(match_link).text, 'lxml')

    header_html = html.find('div', class_ = 'match-header-vs')
    link_html = header_html.find_all('a', href = True)
    links = [f'https://vlr.gg{i.get('href')}' for i in link_html]

    for link in links:
        flag = False

        rating_num = get_team_elo(link)

        match_page_link = link.replace('/team', '/team/matches')
        team_match_page = BeautifulSoup(requests.get(match_page_link).text, 'lxml')

        team_name_html = team_match_page.find('h1', class_ = 'wf-title')
        team_name = team_name_html.text.replace('\n', '').replace('\t', '')

        if team_name not in team_map_elo:
            team_map_elo[team_name] = {
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

        match_history_link_cont = team_match_page.find('div', class_ = 'mod-dark')
        match_history_links = match_history_link_cont.find_all('a', href = True)

        for match in match_history_links:
            match_get = match.get('href')
            current_match_link = f'https://vlr.gg{match_get}'

            match_html = BeautifulSoup(requests.get(current_match_link).text, 'lxml')
            print(f"Got {current_match_link}")

            teams_in_match = match_html.find_all('a', class_ = 'match-header-link')
            for team in teams_in_match:
                if team.find('div', class_ = 'wf-title-med').text.replace('\n', '').replace('\t', '') != team_name:
                    enemy_elo_html = team.find('div', class_ = 'match-header-link-name-elo')
                    if not enemy_elo_html:
                        enemy_elo = 1500
                    enemy_elo = enemy_elo_html.text.strip().replace('[', '').replace(']', '')
                    if enemy_elo == '':
                        enemy_elo = 1500
            
            data_container = match_html.find('div', class_ = 'vm-stats-container')
            all_maps = data_container.find_all('div', class_ = 'vm-stats-game-header')

            for map_instance in all_maps:
                map_name_html = map_instance.find('div', class_ = 'map')
                map_name = map_name_html.find('div', style = True).text

                score_diff = 0

                if "PICK" in map_name:
                    map_name = map_name.replace("PICK", "").strip()
                else:
                    map_name = map_name.strip()

                if map_instance.find('div', class_ = 'team').find('div', class_ = 'team-name').text.replace('\n', '').replace('\t', '') == team_name and map_instance.find('div', class_ = 'score mod-win'):
                    rlvnt_team_score = map_instance.find('div', class_ = 'score mod-win').text.strip()
                    enemy_team_score = map_instance.find('div', class_ = 'score').text.strip()

                    score_diff = int(rlvnt_team_score) - int(enemy_team_score)
                else:
                    rlvnt_team_score = map_instance.find('div', class_ = 'score').text.strip()
                    enemy_team_score = map_instance.find('div', class_ = 'score mod-win').text.strip()

                    score_diff = int(rlvnt_team_score) - int(score_diff)

                prob_win = prob(int(enemy_elo), rating_num)
                
                K = 20 + abs(score_diff)

                if score_diff > 0:
                    team_map_elo[team_name][map_name] += round(K*(1-prob_win), 2)
                elif score_diff < 0:
                    team_map_elo[team_name][map_name] += round(K*(0-prob_win), 2)
                else:
                    continue

    return team_map_elo

glob = get_match_info("https://www.vlr.gg/498628/paper-rex-vs-fnatic-valorant-masters-toronto-2025-gf")
print(glob)

end = time.time()
print(f'{round(end - start, 2)}s')