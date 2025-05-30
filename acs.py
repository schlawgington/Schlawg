import numpy as np
import math
import time
import json
import os
import requests
from bs4 import BeautifulSoup
import re
import hashlib
import matplotlib.pyplot as plt
import pandas as pd

start = time.time()

match_json = 'match.json'
player_json = 'player.json'
mean_json = 'mean.json'
match_data = 'match_data.json'
tbd_json = 'tbd.json'

def loadfile(file):
    if os.path.exists(file):
        with open(file, 'r', encoding = 'utf-8') as f:
            raw_content = json.load(f)
            if not raw_content:
                return None
            return raw_content
    else:
        return None

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

matches = loadfile(match_json)
player_file = loadfile(player_json)
means_stds = loadfile(mean_json)
match_data_file = loadfile(match_data)
tbd = loadfile(tbd_json)

if not player_file:
    players = []
    player_names = []

    for match in matches.keys():
        match_page_html = BeautifulSoup(geturl(matches[match]["Match Link"]), 'lxml')
        player_container = match_page_html.find('div', class_ = 'vm-stats-container')
        team_players = player_container.find_all('table', class_ = 'wf-table-inset mod-overview')
        for team in team_players:
            player_info = team.find_all('td', class_ = 'mod-player')
            for player in player_info:
                player_name = player.find('div', class_ = 'text-of').text.strip()
                if player_name in player_names or player.find('a', href = True) is None:
                    continue
                player_names.append(player_name)
                
                link = player.find('a', href = True)
                new_link = link.get('href').replace('/player/', '')
                players.append('https://www.vlr.gg/player/matches/' + new_link)

    player_dict = {}

    for indiv, player in zip(players, player_names):
        if player not in player_dict:
            player_dict[player] = indiv

    with open (player_json, 'w', encoding='utf-8') as f:
        json.dump(player_dict, f, indent=4)

if not match_data_file:
    match_player_dict = {}
    already_parsed = set()
    for player in player_file.keys():
        i = 1
        while True:
            url = requests.get(f'{player_file[player]}/?page={i}')
            if url.status_code != 200:
                break
            current_page = BeautifulSoup(url.text, 'lxml')
            i += 1

            link_html = current_page.find_all('a', class_ = 'wf-card fc-flex m-item', href = True)
            links = [j.get('href') for j in link_html]

            for link in links:
                match_url = "https://www.vlr.gg" + link
                match_hash = hashlib.md5(match_url.encode('utf-8')).hexdigest()
                
                if match_hash in already_parsed:
                    continue
                already_parsed.add(match_hash)
                
                if match_hash not in match_player_dict:
                    match_player_dict[match_hash] = {}
                
                acs_page = BeautifulSoup(geturl(match_url), 'lxml')
                rlvnt_data = acs_page.find('div', class_ = 'vm-stats-game mod-active')
                if not rlvnt_data:
                    continue
                player_tables = rlvnt_data.find_all('tbody')

                for table in player_tables:
                    player_tr = table.find_all('tr')
                    for player_instance in player_tr:
                        player_name = player_instance.find('div', class_ = 'text-of').text.strip()
                        
                        player_instance_stats = player_instance.find_all('td', class_ = 'mod-stat')
                        per_game_acs = player_instance_stats[1].text.strip().replace('\n', ' ')
                        acs_str_list = per_game_acs.split(' ')
                        acs_list = []
                        for acs in acs_str_list:
                            if acs.isdigit():
                                acs_list.append(int(acs))
                        avg_acs = sum(acs_list) / len(acs_list) if len(acs_list) > 0 else None
                        
                        if player_name not in match_player_dict[match_hash]:
                            match_player_dict[match_hash][player_name] = avg_acs
    
    with open (match_data, 'w', encoding='utf-8') as f:
        json.dump(match_player_dict, f, indent=4)

class player:
    def __init__(self, player_name):
        self.player_name = player_name
        self.acs_arr = 0
        self.acs_mean = 0
        self.acs_std = 0
    
    def player_analyzer(self):
        acs_list = []
        for match_file in match_data_file.keys():
            if self.player_name in match_data_file[match_file]:
                acs_list.append(match_data_file[match_file][self.player_name])

        cleaned_acs_list = [round(acs, 2) for acs in acs_list if acs is not None]

        self.acs_arr = np.array(cleaned_acs_list)
        self.acs_mean = np.mean(self.acs_arr) if len(self.acs_arr) > 0 else 150
        self.acs_std = np.std(self.acs_arr) if len(self.acs_arr) > 0 else 150

    def make_hist(self):
        plt.hist(self.acs_arr)
        plt.show()

def match_analyzer(match_link):
    match_hash = hashlib.md5(match_link.encode('utf-8')).hexdigest()
    player_list = tbd[match_hash]["Players"]
    player_class_dict = {}

    for player_instance in player_list:
        obj_player_instance = player(player_instance)
        obj_player_instance.player_analyzer()  
        if obj_player_instance.player_name not in player_class_dict:
            player_class_dict[obj_player_instance.player_name] = [obj_player_instance.acs_mean, obj_player_instance.acs_std]

    return player_class_dict

test = match_analyzer("https://www.vlr.gg/491470/tbk-esports-vs-f4tality-gamers-club-challengers-league-2025-brazil-split-2-r1")
print(test)

end = time.time() - start
print(f'Elapsed: {end}')