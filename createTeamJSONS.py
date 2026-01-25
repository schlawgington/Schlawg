import os
import json
import time
import csv
import pprint

TeamDataJson = "Team Data JSON"
MatchDataJsonFolder = "Match Data JSON"

def extractMatchID(matchPath):
    return os.path.splitext(os.path.basename(matchPath))[0]

def normalizePlayer(name):
    return " ".join(name.split())

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

        # Open match data json
        try: 
            with open(matchPath, 'r', encoding='utf-8') as dataFile:
                matchData = json.load(dataFile)
        except FileNotFoundError:
            continue

        TeamNames = list(matchData["Aggregate Stats"].keys())

        for teamName in TeamNames:
            # Shorthand for team stats from match data json
            Shorthand = matchData["Aggregate Stats"][teamName]

            filePath = os.path.join(TeamDataJson, f"{teamName}.json")

            if os.path.exists(filePath):
                with open(filePath, 'r', encoding='utf-8') as teamFile:
                    teamDict = json.load(teamFile)

                processedMatchID = extractMatchID(matchPath)
                if processedMatchID in teamDict["Processed Matches"]:
                    continue

                for player, stats in Shorthand.items():
                    player = normalizePlayer(player)

                    if player not in teamDict["Players"]:
                        teamDict["Players"][player] = stats
                        continue

                    if player == "Match Counter" or player == "Round Counter" or player == "Processed Matches" or player in MapList:
                        continue

                    for stat in teamDict["Players"][player].keys():
                        if not teamDict["Players"][player][stat]:
                            teamDict["Players"][player][stat] = Shorthand[player][stat]
                            continue

                        if not Shorthand[player][stat]:
                            continue
                        
                        # Accumulate Kills, Deaths, and Assists and average all other stats
                        if stat == "R" or stat == "ACS" or stat == "KAST" or stat == "ADR" or stat == "HS%" or stat == "delta FK FD" or stat == "delta KD":
                            teamDict["Players"][player][stat] = ((teamDict["Players"][player][stat] * teamDict["Match Counter"]) + Shorthand[player][stat]) / (teamDict["Match Counter"] + 1)
                        elif stat == "K" or stat == "D" or stat == "A" or stat == "FK" or stat == "FD":
                            teamDict["Players"][player][stat] += Shorthand[player][stat]
                        else:
                            continue
            else:
                playerList = list(matchData["Aggregate Stats"][teamName].keys())

                # JSON object construction
                teamDict = {"Players": {
                    player: {
                    "R": Shorthand[player]["R"],
                    "ACS": Shorthand[player]["ACS"],
                    "K": Shorthand[player]["K"],
                    "D": Shorthand[player]["D"],
                    "A": Shorthand[player]["A"],
                    "delta KD": Shorthand[player]["delta KD"],
                    "KAST": Shorthand[player]["KAST"],
                    "ADR": Shorthand[player]["ADR"],
                    "HS%": Shorthand[player]["HS%"],
                    "FK": Shorthand[player]["FK"],
                    "FD": Shorthand[player]["FD"],
                    "delta FK FD": Shorthand[player]["delta FK FD"]
                } for player in playerList}}

                teamDict.update({Map: {
                    "Win": 0,
                    "Loss": 0,
                    "Rounds Won": 0,
                    "Rounds Lost": 0,
                    "Win%": 0,
                    "Round Win%": 0
                } for Map in MapList})

                teamDict.update({"Match Counter": 0, 
                                "Processed Matches": []
                            })

            # Increments for num of matches, num of rounds, and calculations for match and round win %
            for Map in matchData["Match Results"].keys():
                currentTeamScore = 0
                oppositeTeamScore = 0
                for team, value in  matchData["Match Results"][Map].items():
                    if team == teamName:
                        teamDict[Map]["Rounds Won"] += int(value)
                        currentTeamScore = int(value)
                    else:
                        teamDict[Map]["Rounds Lost"] += int(value)
                        oppositeTeamScore = int(value)

                if currentTeamScore > oppositeTeamScore:
                    teamDict[Map]["Win"] += 1
                else:
                    teamDict[Map]["Loss"] += 1

                teamDict[Map]["Win%"] = teamDict[Map]["Win"] / (teamDict[Map]["Win"] + teamDict[Map]["Loss"])
                teamDict[Map]["Round Win%"] = teamDict[Map]["Rounds Won"] / (teamDict[Map]["Rounds Won"] + teamDict[Map]["Rounds Lost"])

            teamDict["Match Counter"] += 1
            teamDict["Processed Matches"].append(extractMatchID(matchPath))

            with open(filePath, 'w', encoding='utf-8') as dumpFile:
                json.dump(teamDict, dumpFile, indent=4)