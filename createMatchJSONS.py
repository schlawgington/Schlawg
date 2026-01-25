import os
import requests
from bs4 import BeautifulSoup
import json
import hashlib
import re
import time
import csv
import pprint

matchPageCache = "Match Results Pages" #Holds html for pages that hold links to actual match pages
matchDataCache = "Match Data" #Holds html for match data
matchDataJsonCache = "Match Data JSON" #Holds parsed data in JSON format for later calculations
vlrLink = "https://www.vlr.gg"

#headers for web requests
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}

def normalizePlayer(name):
    return " ".join(name.split())

def getURL(url, cache, force_refresh = False):
    hash = hashlib.md5(url.encode('utf-8')).hexdigest()

    #if file exists get from cache else create and put in cache
    filePath = os.path.join(cache, hash)
    if os.path.exists(filePath) and not force_refresh:
        with open(filePath, 'r', encoding='utf-8') as f:
            return f.read()
    
    contents = requests.get(url, headers=headers, timeout=(5, 10)).text

    with open(filePath, 'w', encoding='utf-8') as f:
        f.write(contents)

    return contents

#Get all matches from page 1 to numPages
def getHistoryLinks(startPage, endPages, forceRefresh: bool, inputURL):
    links = set()

    for page in range(startPage, endPages):
        soup = BeautifulSoup(getURL(f"{inputURL}{page}", matchPageCache, force_refresh=forceRefresh), 'lxml')
        matches = soup.find_all('a', href=True)        

        for match in matches:
            href = match.get('href')
            if re.match(r'^/\d+/', href):
                links.add(href)

    return list(links)

def HTMLToText(HTML):
    return HTML.text.strip()

def cleanData(data):
    cleanedData = data.strip().replace("\xa0", "")

    if not cleanedData:
        return None

    if "+" in cleanedData:
        return int(cleanedData.replace("+", ""))
    elif "%" in cleanedData:
        return int(cleanedData.replace("%", ""))/100
    else:
        try:
            return int(cleanedData)
        except ValueError:
            return float(cleanedData)

def createMatchToDataDict(links: list, forceRefresh = False):
    #Put data in json files in form of {match Hash: {Team: {Player Stats: }}}

    HashedMatchNames = []

    for link in links:
        fullLink = vlrLink + link

        matchPage = BeautifulSoup(getURL(fullLink, matchDataCache, force_refresh = forceRefresh), 'lxml')
        matchName = hashlib.md5(fullLink.encode()).hexdigest()
        HashedMatchNames.append(matchName)

        matchDataDict = {
            "Full Link": fullLink,
            "Match Results": {},
            "Aggregate Stats": {},
        }

        #If no data just continue
        try:
            TeamNames = [HTMLToText(team) for team in matchPage.find_all("div", class_="wf-title-med")]
            matchDataDict["Aggregate Stats"] = {teamName: {} for teamName in TeamNames}

            matchMapsHtml = matchPage.find_all("div", class_="vm-stats-gamesnav-item js-map-switch")
            matchMaps = [maps.text.split() for maps in matchMapsHtml]

            teamNametoResult = [HTMLToText(page) for page in matchPage.find_all(class_ = "team-name")]
            mapResults = [HTMLToText(score) for score in matchPage.find_all(class_ = "score")]
            
            #Occurs in BO1s
            if not matchMapsHtml:
                matchMaps = matchPage.find("div", class_ = "map").find("span").text.strip()
                matchDataDict["Match Results"] = {matchMaps: {teamNametoResult[i]: mapResults[i] for i in range(len(teamNametoResult))}}
            else:
                matchDataDict["Match Results"] = {Map[1]: {teamNametoResult[i]: mapResults[i] for i in range(len(teamNametoResult))} for Map in matchMaps}

            matchTableData = matchPage.find("div", class_ = "vm-stats-game mod-active").find_all("tbody")

        except AttributeError:
            continue

        for i, table in enumerate(matchTableData):
            playerList = table.find_all("tr")
            aggregateStats = "Aggregate Stats"

            for player in playerList:
                if not player:
                    continue

                Team = TeamNames[0] if i % 2 == 0 else TeamNames[1]

                playerData = [data.find("span", class_ = "mod-both") for data in player.find_all("td")]
                noFalsyData = [data.text for data in playerData if data]

                name = normalizePlayer(player.find("td", class_ = "mod-player").text.strip())
                R = cleanData(noFalsyData[0])
                ACS = cleanData(noFalsyData[1])
                K = cleanData(noFalsyData[2])
                D = cleanData(noFalsyData[3])
                A = cleanData(noFalsyData[4])
                deltaKD = cleanData(noFalsyData[5])
                KAST = cleanData(noFalsyData[6])
                ADR = cleanData(noFalsyData[7])
                HS_pct = cleanData(noFalsyData[8])
                FK = cleanData(noFalsyData[9])
                FD = cleanData(noFalsyData[10])
                deltaFKFD = cleanData(noFalsyData[11])

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

                if PlayerObject["Name"] not in matchDataDict[aggregateStats][Team]:
                    matchDataDict[aggregateStats][Team][PlayerObject["Name"]] = PlayerObject

        filePath = os.path.join(matchDataJsonCache, matchName)
        with open(f"{filePath}.json", 'w', encoding='utf-8') as f:
            json.dump(matchDataDict, f, indent=4)

    with open("Hashes.csv", 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows([[h] for h in HashedMatchNames])