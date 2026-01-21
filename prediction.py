from pathlib import Path
import math
import json
import os

matchCache = "Match Data JSON"
matchFolder = Path(matchCache)

def calculateWinProbability(TeamAElo, TeamBElo):
    return 1/(1 + math.pow(10, (TeamBElo - TeamAElo)/400))

def calculateEloChange(Elo, winProb, Result):
    maxEloChange = 100
    return Elo + maxEloChange*(Result - winProb)