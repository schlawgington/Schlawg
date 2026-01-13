import os
import requests
from bs4 import BeautifulSoup
import json
import hashlib
import numpy as np
import re
import time
import csv
import pprint

print = pprint.pprint
start = time.time()

matchPageCache = "Match Results Pages" #Holds html for pages that hold links to actual match pages
matchDataCache = "Match Data" #Holds html for match data
matchDataJsonCache = "Match Data JSON" #Holds parsed data in JSON format for later calculations
vlrLink = "https://www.vlr.gg"

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
def getHistoryLinks(numPages, forceRefresh: bool):
    links = set()

    for page in range(1, numPages):
        soup = BeautifulSoup(getURL(f"https://www.vlr.gg/matches/results/?page={page}", matchPageCache, force_refresh=forceRefresh), 'lxml')
        matches = soup.find_all('a', href=True)        

        for match in matches:
            href = match.get('href')
            if re.match(r'^/\d+/', href):
                links.add(href)

    return list(links)

def getAggregateStat(td):
    both = td.find("span", class_="side mod-side mod-both")
    if both:
        return both.text.strip()

    values = [s.text.strip() for s in td.find_all("span", class_="side")]
    return values[-1] if values else td.text.strip()

#Convert html table to numpy
def tableToNumpy(table):
    rows = table.find_all('tr')
    data = []

    for row in rows:
        cols = row.find_all("td")
        data.append([getAggregateStat(col) for col in cols])

    return np.array(data, dtype=object)

def CleanData(data):

    if not any(x.strip() for x in data):
        return None

    if "%" in data:
        newData = data.replace("%", "")
        return int(newData)/100
    else:
        try:
            return float(data)
        except ValueError:
            return int(data)

    return

def HTMLToText(HTML):
    return HTML.text.strip()

def createMatchToDataDict(links: list):
    #Put data in json files in form of {match Hash: {Team: {Player Stats: }}}

    HashedMatchNames = []

    for link in links:
        fullLink = vlrLink + link

        matchPage = BeautifulSoup(getURL(fullLink, matchDataCache), 'lxml')
        matchName = hashlib.md5(fullLink.encode()).hexdigest()
        HashedMatchNames.append(matchName)

        #If no data just continue
        try:
            oneMapFlag = False

            TeamNames = [HTMLToText(team) for team in matchPage.find_all("div", class_="wf-title-med")]

            matchMapsHtml = matchPage.find_all("div", class_="vm-stats-gamesnav-item js-map-switch")
            matchMaps = [maps.text.split() for maps in matchMapsHtml]

            mapNametoResult = [HTMLToText(page) for page in matchPage.find_all(class_ = "team-name")]
            mapResults = [HTMLToText(score) for score in matchPage.find_all(class_ = "score")]
            
            matchDataDict = {}

            #Occurs in BO1s
            if not matchMapsHtml:
                matchMaps = matchPage.find("div", class_ = "map").find("span").text.strip()
                oneMapFlag = True

                matchDataDict.update({"Match Results": {
                                       HTMLToText(mapNametoResult[0]): HTMLToText(mapResults[0]),
                                       HTMLToText(mapNametoResult[1]): HTMLToText(mapResults[1])
                                    }})
                matchDataDict.update({matchMaps: {Team: {} for Team in TeamNames}})
            else:
                matchDataDict.update({"Match Results": {}})
                matchDataDict.update({"All Maps": {Team: {} for Team in TeamNames}})
                matchDataDict.update({Map[1]: {Team: {} for Team in TeamNames} for Map in matchMaps})

                for i, Map in enumerate(matchMaps):
                    start = i * 2
                    end = start + 2

                    matchDataDict["Match Results"][Map[1]] = {
                        team: result
                        for team, result in zip(
                            mapNametoResult[start:end],
                            mapResults[start:end]
                        )
                    }

            matchDataDict.update({"Match Link": fullLink})

            matchTableData = matchPage.find_all("table")

        except AttributeError:
            continue

        for i, table in enumerate(matchTableData):
            currentTable = tableToNumpy(table)

            #Handles edge case of BO1
            if (i == 0 or i == 1) and not oneMapFlag:
                currentMap = "All Maps"
            elif oneMapFlag:
                currentMap = matchMaps
            else:
                currentMap = matchMaps[i // 2 - 1][1]

            for player in currentTable:
                if not player:
                    continue
                
                Team = TeamNames[0] if i % 2 == 0 else TeamNames[1]

                name = player[0].replace("\n", "")
                R = CleanData(player[2])
                ACS = CleanData(player[3])
                K = CleanData(player[4])
                D = CleanData(player[5])
                A = CleanData(player[6])
                deltaKD = CleanData(player[7])
                KAST = CleanData(player[8])
                ADR = CleanData(player[9])
                HS_pct = CleanData(player[10])
                FK = CleanData(player[11])
                FD = CleanData(player[12])
                deltaFKFD = CleanData(player[13])

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

                if PlayerObject["Name"] not in matchDataDict[currentMap][Team]:
                    matchDataDict[currentMap][Team][PlayerObject["Name"]] = PlayerObject

        filePath = os.path.join(matchDataJsonCache, matchName)
        with open(f"{filePath}.json", 'w', encoding='utf-8') as f:
            json.dump(matchDataDict, f, indent=4)

    if not os.path.exists("Hashes.csv"):
        with open("Hashes.csv", 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows([[h] for h in HashedMatchNames])

def main():
    unHashedMatchNames = getHistoryLinks(2)
    createMatchToDataDict(unHashedMatchNames, forceRefresh = True)

if __name__ == "__main__":
    os.makedirs(matchPageCache, exist_ok=True)
    os.makedirs(matchDataCache, exist_ok=True)
    os.makedirs(matchDataJsonCache, exist_ok=True)
    main()

end = time.time()
print(f"{end - start}s")