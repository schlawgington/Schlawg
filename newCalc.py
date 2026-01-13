import os
import json
import time
import csv
import pprint

print = pprint.pprint

start = time.time()

TeamDataJson = "Team Data JSON"
MatchDataJsonFolder = "Match Data JSON"

os.makedirs(TeamDataJson, exist_ok=True)

def getmatchHashes():
    matchHashes = []

    with open("Hashes.csv", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            matchHashes.extend(row)

    fullFilePaths = []

    for match in matchHashes:
        filePath = os.path.join(MatchDataJsonFolder, match)
        fullFilePaths.append(f"{filePath}.json")

    return fullFilePaths

testCase = [getmatchHashes()[0]]

def createTeamJsons(Hashes: list):
    MapList = ["Bind", "Haven", "Split", "Ascent", "Icebox", "Breeze", "Fracture", "Pearl", "Lotus", "Sunset", "Abyss"]

    for match in Hashes:
        with open(match, 'r', encoding='utf-8') as dataFile:
            matchData = json.load(dataFile)

        for Map in matchData.keys():
            if Map == "Match Link":
                continue

            for Team in matchData[Map].keys():
                teamFilePath = os.path.join(TeamDataJson, f"{Team}.json")

                if not os.path.exists(teamFilePath):
                    TeamDict = {
                            "Match Counter": 0,
                            "Maps": {mapName: {
                                "Total Wins": 0,
                                "Total Losses": 0,
                                "Win%": TeamDict["Maps"]["Total Wins"] / TeamDict["Maps"]["Total Losses"] if TeamDict["Maps"]["Total Losses"] else 1,
                            } for mapName in MapList}, 
                            "Players": {}}

                    for player in matchData[Map][Team]:
                        if player not in TeamDict["Players"]:
                            TeamDict["Players"][player] = matchData[Map][Team][player]

                    with open(teamFilePath, 'w', encoding='utf-8') as TeamDataFile:
                        json.dump(TeamDict, TeamDataFile, indent=4)
                
                else:
                    with open(teamFilePath, 'r', encoding='utf-8') as ReadTeamDataFile:
                        oldData = json.load(ReadTeamDataFile)

                    #i dont wanna do it right now
                    #load old data, for each player: iterate through stats and * multiply stat by number of matches played, then add new data value and divide by number of matches played + 1
                    #Just make update cache function, put the fries in the bag

createTeamJsons(testCase)