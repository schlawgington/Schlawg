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

class player:
    def __init__(self, player_name):
        self.player_name = player_name
        self.acs_arr = 0
        self.acs_mean = 0
        self._acs_std = 0
    
    def player_analyzer(self):
        i = 1
        player_acs = []
        while True:
            url = requests.get(f'{player_file[self.player_name]} + /?page={i}')
            if url.status_code != 200:
                break
            current_page = BeautifulSoup(url.text, 'lxml')
            i += 1

            link_html = current_page.find_all('a', class_ = 'wf-card fc-flex m-item', href = True)
            links = [j.get('href') for j in link_html]

            for link in links:
                acs_page = BeautifulSoup(geturl("https://www.vlr.gg" + link), 'lxml')
                rlvnt_data = acs_page.find('div', class_ = 'vm-stats-game mod-active')
                player_tables = rlvnt_data.find_all('tbody')

                for table in player_tables:
                    player_tr = table.find_all('tr')
                    for player_instance in player_tr:
                        if player_instance.find('div', class_ = 'text-of').text.strip() == self.player_name:
                            player_instance_stats = player_instance.find_all('td', class_ = 'mod-stat')
                            per_game_acs = player_instance_stats[1].text.strip().replace('\n', ' ')
                            acs_list = per_game_acs.split(' ')
                            for acs in acs_list:
                                if acs.isdigit():
                                    player_acs.append(int(acs))
        
        self.acs_arr = np.array(player_acs)
        self.acs_mean = np.mean(self.acs_arr)
        self.acs_std = np.std(self.acs_arr)

    def make_hist(self, data):
        plt.hist(data)
        plt.show()

zekken = player("Shondex")
zekken.player_analyzer()
print(zekken.acs_arr, zekken.acs_mean, zekken.acs_std)
zekken.make_hist(zekken.acs_arr)

end = time.time() - start
print(f'Elapsed: {end}')