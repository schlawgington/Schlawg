import os
import requests
from bs4 import BeautifulSoup
import json
import hashlib
import numpy as np
import re
import time

start = time.time()

matchPageCache = "match page cache"
matchDataCache = "match data cache"
vlrLink = "https://www.vlr.gg"
os.makedirs(matchPageCache, exist_ok=True)
os.makedirs(matchDataCache, exist_ok=True)

#headers for web requests
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}

def getURL(url, cache, force_refresh = False):
    hash = hashlib.md5(url.encode('utf-8')).hexdigest()

    #if file exists get from cache else create and put in cache
    filePath = os.path.join(cache, hash)
    if os.path.exists(filePath) and not force_refresh:
        with open(filePath, 'r', encoding='utf-8') as f:
            return f.read()
        
    contents = requests.get(url, headers=headers).text

    with open(filePath, 'w', encoding='utf-8') as f:
        f.write(contents)

    return contents

#Get all matches from page 1 to numPages
def getHistoryLinks(numPages):
    links = set()

    for page in range(1, numPages):
        soup = BeautifulSoup(getURL(f"https://www.vlr.gg/matches/results/?page={page}", matchPageCache), 'lxml')
        matches = soup.find_all('a', href=True)        

        for match in matches:
            href = match.get('href')
            if re.match(r'^/\d+/', href):
                links.add(href)

    return list(links)

def tableToNumpy(table):
    rows = table.find_all('tr')
    data = []

    for row in rows:
        cols = row.find_all("td")
        data.append([col.get_text(strip=False).strip().replace('\t', '') for col in cols])

    return np.array(data, dtype=object)

def createMatchToDataDict(links: list):
    #Put data in json files in form of {match Hash: {Team: {Player Stats: }}}
    for link in links:
        fullLink = vlrLink + link

        matchPage = BeautifulSoup(getURL(fullLink, matchDataCache), 'lxml')
        matchName = hashlib.md5(fullLink.encode()).hexdigest()

        TeamNames = [team.text.strip() for team in matchPage.find_all("div", class_ = "wf-title-med")]

        matchTableData = matchPage.find('div', class_ = "vm-stats-game mod-active").find_all("table")

        matchDataDict = {team: {} for team in TeamNames}
        for i, table in enumerate(matchTableData):
            currentTable = tableToNumpy(table)

            for player in currentTable:
                if not player:
                    continue
                
                Team = TeamNames[0] if i == 0 else TeamNames[1]

                name = player[0].replace("\n", "")
                R = player[2].replace("\n", " ")
                ACS = player[3].replace("\n", " ")
                K = player[4].replace("\n", " ")
                D = player[5].strip().replace("\n", " ")
                A = player[6].replace("\n", " ")
                deltaKD = player[7].replace("\n", " ")
                KAST = player[8].replace("\n", " ")
                ADR = player[9].replace("\n", " ")
                HS_pct = player[10].replace("\n", " ")
                FK = player[11].replace("\n", " ")
                FD = player[12].replace("\n", " ")
                deltaFKFD = player[13].replace("\n", " ")

                PlayerObject = {
                    "Name": name,
                    "R": R,
                    "ACS": ACS,
                    "K": K,
                    "D": D,
                    "A": A,
                    "delta KD": deltaKD,
                    "KAST": KAST,
                    "ADR": ADR,
                    "HS%": HS_pct,
                    "FK": FK,
                    "FD": FD,
                    "delta FK FD": deltaFKFD
                }

                if PlayerObject["Name"] not in matchDataDict[Team]:
                    matchDataDict[Team][PlayerObject["Name"]] = PlayerObject

        filePath = os.path.join(matchDataCache, matchName)
        with open(f"{filePath}.json", 'w', encoding='utf-8') as f:
            json.dump(matchDataDict, f, indent=4)


createMatchToDataDict(["/600370/f9-eicar-vs-erah-esport-challengers-2026-france-revolution-split-1-w1"])

end = time.time()
print(f"{end - start}s")