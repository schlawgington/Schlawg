import createMatchJSONS as CMJ
import createTeamJSONS as CTJ
import createUpcomingMatchJSON as CUMJ
import prediction as calc
import time
import os

if __name__ == "__main__":
    start = time.time()

    # Make folders
    os.makedirs(CMJ.matchPageCache, exist_ok=True)
    os.makedirs(CMJ.matchDataCache, exist_ok=True)
    os.makedirs(CMJ.matchDataJsonCache, exist_ok=True)
    os.makedirs(CTJ.TeamDataJson, exist_ok=True)
    os.makedirs(CUMJ.matchScheduleCache, exist_ok=True)
    os.makedirs(CUMJ.matchScheduleJSONCache, exist_ok=True)

    # Create Match data json files
    forceRefresh = True
    ResultsURL = "https://www.vlr.gg/matches/results/?page="
    unHashedMatchNames = CMJ.getHistoryLinks(1, 7, forceRefresh, ResultsURL)
    CMJ.createMatchToDataDict(unHashedMatchNames, forceRefresh = forceRefresh)

    # Create Team data json files
    matchHashes = CTJ.getmatchHashes()
    CTJ.createTeamJsons(matchHashes)

    # Create schedule files
    CUMJ.getMatchSchedule()

    # Z score calculation
    averagePlayer = calc.createAveragePlayer()

    end = time.time()