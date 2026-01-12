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
    for match in Hashes:
        with open(match, 'r', encoding='utf-8') as dataFile:
            matchData = json.load(dataFile)

        for Map in matchData.keys():
            if Map == "Match Link":
                continue

            for Team in matchData[Map].keys():
                TeamDict = {"Maps": {
                            "Bind": 0,
                            "Haven": 0,
                            "Split": 0,
                            "Ascent": 0,
                            "Icebox": 0,
                            "Breeze": 0,
                            "Fracture": 0,
                            "Pearl": 0,
                            "Lotus": 0,
                            "Sunset": 0,
                            "Abyss": 0
                        }, 
                        "Players": {}}

                for player in matchData[Map][Team]:
                    if player not in TeamDict["Players"]:
                        TeamDict["Players"][player] = matchData[Map][Team][player]

                teamFilePath = os.path.join(TeamDataJson, f"{Team}.json")
                
                if not os.path.exists(teamFilePath):
                    with open(teamFilePath, 'w', encoding='utf-8') as TeamDataFile:
                        json.dump(TeamDict, TeamDataFile, indent=4)
                else:
                    with open(teamFilePath, 'r', encoding='utf-8') as ReadTeamDataFile:
                        oldData = json.load(ReadTeamDataFile)

                    #i dont wanna do it right now
                    #load old data, for each player: iterate through stats and * multiply stat by number of matches played, then add new data value and divide by number of matches played + 1

createTeamJsons(testCase)