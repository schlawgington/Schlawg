import math
import json
import os
import numpy as np
import hashlib
import pprint

print = pprint.pprint

def createAveragePlayer():
    cachePath = "Team Data JSON"

    dataHolder = {
        "R": [],
        "ACS": [],
        "delta KD": [],
        "KAST": [],
        "ADR": [],
        "delta FK FD": []
    }

    averagePlayer = {
        "Means": {
            "R": 0,
            "ACS": 0,
            "delta KD": 0,
            "KAST": 0,
            "ADR": 0,
            "delta FK FD": 0,
        },

        "Standard Deviations": {
            "R": 0,
            "ACS": 0,
            "delta KD": 0,
            "KAST": 0,
            "ADR": 0,
            "delta FK FD": 0,
        }
    }

    playerCount = 1

    for file in os.scandir(cachePath):
        if file.is_file():
            with open(file.path, 'r', encoding='utf-8') as teamFile:
                teamData = json.load(teamFile)
            
            # Add all values and average at end
            for player in teamData["Players"].keys():
                playerShorthand = teamData["Players"][player]

                for stat in averagePlayer["Means"].keys():
                    if not playerShorthand[stat]:
                        continue
                    else:
                        averagePlayer["Means"][stat] += playerShorthand[stat]
                        dataHolder[stat].append(playerShorthand[stat])

                playerCount += 1

    for key in averagePlayer["Means"].keys():
        averagePlayer["Means"][key] = round(averagePlayer["Means"][key]/playerCount, 2)
        averagePlayer["Standard Deviations"][key] = round(np.std(dataHolder[key], mean=averagePlayer["Means"][key]), 2)

    with open(f"Average Stats JSON.json", 'w', encoding='utf-8') as averageFile:
        json.dump(averagePlayer, averageFile, indent=2)

    return averagePlayer

def calculateZScores(player, playerName, averagePlayer):
    playerZScores = {
        "Name": playerName,
        "R": 0,
        "ACS": 0,
        "delta KD": 0,
        "KAST": 0,
        "ADR": 0,
        "delta FK FD": 0,
    }

    for stat in player.keys():
        if stat not in playerZScores.keys() or stat == "Name" or not player[stat]:
            continue

        playerZScores[stat] = (player[stat] - averagePlayer["Means"][stat]) / averagePlayer["Standard Deviations"][stat]

    return playerZScores

# Creates dict of z-scores for each player compared to average player
def getTeamZScores():
    inputLink = "https://www.vlr.gg/596409/loud-vs-100-thieves-vct-2026-americas-kickoff-mr1"
    matchName = hashlib.md5(inputLink.encode()).hexdigest()
    averagePlayer = createAveragePlayer()
    print("Run")

    try:
        scheduleCache = "Match Schedule JSON Cache"
        filePath = os.path.join(scheduleCache, matchName)
        with open(f"{filePath}.json", 'r') as matchFile:
            scheduledMatchDict = json.load(matchFile)
    except FileNotFoundError:
        print("Link is incorrect")
        exit()

    Teams = list(scheduledMatchDict.keys())

    teamZScores = {Team: {} for Team in Teams}

    teamDataCache = "Team Data JSON"
    for team in Teams:
        try:
            teamFilePath = os.path.join(teamDataCache, team)
            with open(f"{teamFilePath}.json", 'r') as teamFile:
                teamData = json.load(teamFile)
        except FileNotFoundError:
            print("No data on this team")
            exit()

        for player in teamData["Players"].keys():
            if player not in teamZScores[team]:
                teamZScores[team][player] = calculateZScores(teamData["Players"][player], player, averagePlayer)

    return teamZScores