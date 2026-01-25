from createMatchJSONS import getURL
from createMatchJSONS import normalizePlayer
from createMatchJSONS import HTMLToText
import os
import json
from bs4 import BeautifulSoup
import pprint
import hashlib
import re

print = pprint.pprint

matchScheduleCache = "Match Schedule Cache"
matchScheduleJSONCache = "Match Schedule JSON Cache"

def getMatchSchedule():
    vlrSchedulePage = "https://www.vlr.gg/matches"

    schedulePageHtml = BeautifulSoup(getURL(vlrSchedulePage, matchScheduleCache, True), 'lxml')
    allAnchors = schedulePageHtml.find_all("a", href=True)

    scheduleLinks = []

    for match in allAnchors:
            href = match.get('href')
            if re.match(r'^/\d+/', href):
                scheduleLinks.append(href)

    for link in scheduleLinks:
        fullLink = "https://www.vlr.gg" + link

        matchPage = BeautifulSoup(getURL(fullLink, matchScheduleCache, force_refresh = True), 'lxml')
        matchName = hashlib.md5(fullLink.encode()).hexdigest()

        TeamNames = [HTMLToText(team) for team in matchPage.find_all("div", class_="wf-title-med")]

        matchInfoDict = {Team: [] for Team in TeamNames}

        if not matchPage:
            continue

        tables = matchPage.find("div", class_ = "vm-stats-game mod-active").find_all("tbody")

        for i, table in enumerate(tables):
            tableRows = table.find_all("tr")
            currentTeam = TeamNames[i]

            for player in tableRows:
                playerName = normalizePlayer(player.find("td", class_ = "mod-player").text.strip())
                matchInfoDict[currentTeam].append(playerName)

        filePath = os.path.join(matchScheduleJSONCache, matchName)
        with open(f"{filePath}.json", 'w', encoding='utf-8') as matchFile:
            json.dump(matchInfoDict, matchFile, indent=2)