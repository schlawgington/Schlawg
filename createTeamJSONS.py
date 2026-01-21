import os
import json
import time
import csv
import pprint

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

def createTeamJsons(Hashes: list):
    MapList = ["Bind", "Haven", "Split", "Ascent", "Icebox", "Breeze", "Fracture", "Pearl", "Lotus", "Sunset", "Abyss", "Corrode"]

    for matchPath in Hashes:

        try: 
            with open(matchPath, 'r', encoding='utf-8') as dataFile:
                matchData = json.load(dataFile)
        except FileNotFoundError:
            continue

        matchResults = matchData.get("Match Results")

        for Map, mapData in matchData.items():
            if Map in ("Match Link", "Match Results", "All Maps"):
                continue

            for Team, players in mapData.items():
                teamFilePath = os.path.join(TeamDataJson, f"{Team}.json")

                if os.path.exists(teamFilePath):
                    with open(teamFilePath, 'r', encoding='utf-8') as f:
                        TeamDict = json.load(f)
                else:
                    TeamDict = {
                        "Match Counter": 0,
                        "Round Counter": 0,
                        "Maps": {
                            mapName: {
                                "Total Wins": 0,
                                "Total Losses": 0,
                                "Win%": None
                            } for mapName in MapList
                        },
                        "Players": {}
                    }

                TeamDict["Match Counter"] += 1

                for playerName, stats in players.items():
                    if playerName not in TeamDict["Players"]:
                        TeamDict["Players"][playerName] = stats

                    else:
                        currentPlayer = TeamDict["Players"][playerName]
                        for stat, statData in stats.items():
                            if stat == "Name":
                                continue

                            elif stat == "K" or stat == "D" or stat == "A" or stat == "FK" or stat == "FD":
                                currentPlayer[stat] += statData if statData else 0

                            elif stat == "delta KD":
                                currentPlayer[stat] = (currentPlayer["K"] - currentPlayer["D"])/TeamDict["Match Counter"]

                            elif stat == "KAST" or stat == "ADR" or stat == "ACS" or stat == "HS%":
                                currentPlayer[stat] = ((currentPlayer[stat] * TeamDict["Match Counter"] - 1)
                                                       + statData) / TeamDict["Match Counter"] if statData else currentPlayer[stat]
                                
                            elif stat == "delta FK FD":
                                currentPlayer[stat] = (currentPlayer["FK"] - currentPlayer["FD"]) / TeamDict["Match Counter"]

                with open(teamFilePath, 'w', encoding='utf-8') as f:
                    json.dump(TeamDict, f, indent=4)

if __name__ == "__main__":
    print = pprint.pprint
    start = time.time()
    matchHashes = getmatchHashes()
    createTeamJsons(matchHashes)
    end = time.time()
    print(f"{end - start}s")