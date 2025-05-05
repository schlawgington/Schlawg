import os
import requests
from bs4 import BeautifulSoup
import re
import json

#defines html_file
html_file = 'valorant_teams.html'

if os.path.exists(html_file):
    with open(html_file, 'r', encoding='utf-8') as f:
        page_content = f.read()
else:
    url = "https://www.vlr.gg/rankings"
    response = requests.get(url)
    
    if response.status_code == 200:
        page_content = response.text
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(page_content)
    else:
        print("Failed to download results", response.status_code)
        page_content = None

if page_content:
    soup = BeautifulSoup(page_content, 'html.parser')

#all regions(NA, EU, KR, etc.)
regions = soup.find_all('tr', class_ = "wf-card mod-hover")
team_names = []
for i in regions:
    x = i.find('td', class_ = 'rank-item-team')
    team_names.append(x)

text = []
pattern = re.compile(r'\t|\n|Europe|Turkey|United States|Brazil|Thailand|Indonesia|Singapore|South Korea|China|Japan|Colombia|Mexico|Dominican Republic|Ecuador|Australia|Saudi Arabia|Egypt|Kuwait|Canada|Chile|Argentina')
for i in team_names:
    cleaned = pattern.sub('', i.text)
    text.append(cleaned)

json_file = 'team_matches.json'

team_links = []
all_matches = {}
for i in regions:
    x = i.find('a', href = True)
    y = x.get('href')
    z = y.replace('/team/', '')
    team_links.append(z)

if os.path.exists(json_file):
    with open(json_file, 'r', encoding = 'utf-8') as f:
        all_matches = json.load(f)
else:
    for j in team_links:
        matchpages = requests.get("https://www.vlr.gg/team/matches/" + str(j))
        if matchpages.status_code == 200:
            all_matches[j] = matchpages.text
        else:
            print("Failure code:", matchpages.status_code)
    with open(json_file, 'w', encoding = 'utf-8') as f:
        json.dump(all_matches, f)

matchlinks = []

for match, html in all_matches.items():
    obj = BeautifulSoup(html, 'html.parser')
    links = obj.find_all('a', class_ = 'wf-card fc-flex m-item', href = True)
    for i in links:
        matchlinks.append(i.get('href'))

all_teams = {}
match_names = {}

for i in text:
    all_teams[i] = {
        "matches": {}
    }