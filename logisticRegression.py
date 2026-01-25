import json
import os
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
import prediction as pred
import hashlib

def loadMatchData():
    matchDataCache = "Match Data JSON"
    
    X = []
    y = []
    
    averagePlayer = pred.createAveragePlayer()
    
    for matchFile in os.scandir(matchDataCache):
        if not matchFile.is_file() or not matchFile.name.endswith('.json'):
            continue
            
        with open(matchFile.path, 'r', encoding='utf-8') as f:
            matchData = json.load(f)
        
        if not matchData.get("Aggregate Stats") or not matchData.get("Match Results"):
            continue
            
        teams = list(matchData["Aggregate Stats"].keys())
        if len(teams) != 2:
            continue
        
        teamZScores = {}
        for team in teams:
            playerStats = matchData["Aggregate Stats"][team]
            if not playerStats:
                continue
                
            teamZScoreList = []
            for player, stats in playerStats.items():
                if not isinstance(stats, dict):
                    continue
                    
                playerZScore = pred.calculateZScores(stats, player, averagePlayer)
                # Average the z-scores for this player (excluding name)
                zScoreValues = [v for k, v in playerZScore.items() if k != "Name" and isinstance(v, (int, float))]
                if zScoreValues:
                    avgZ = np.mean(zScoreValues)
                    teamZScoreList.append(avgZ)
            
            if teamZScoreList:
                teamZScores[team] = np.mean(teamZScoreList)
        
        if len(teamZScores) != 2:
            continue
        
        team1, team2 = teams[0], teams[1]
        team1Score = 0
        team2Score = 0
        
        for mapName, mapResult in matchData["Match Results"].items():
            for team, rounds in mapResult.items():
                if team == team1:
                    team1Score += int(rounds)
                elif team == team2:
                    team2Score += int(rounds)
        
        zScoreDiff = teamZScores.get(team1, 0) - teamZScores.get(team2, 0)
        
        # Label: 1 if team1 won, 0 if team2 won
        label = 1 if team1Score > team2Score else 0
        
        X.append([zScoreDiff])
        y.append(label)
    
    return np.array(X), np.array(y)

def trainModel(X, y):
    if len(X) == 0:
        print("No training data available")
        return None, None
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    model = LogisticRegression(random_state=42, max_iter=1000)
    model.fit(X_train, y_train)
    
    trainAccuracy = model.score(X_train, y_train)
    testAccuracy = model.score(X_test, y_test)
    
    print(f"Training Accuracy: {trainAccuracy:.2%}")
    print(f"Test Accuracy: {testAccuracy:.2%}")
    print(f"Total samples: {len(X)}")
    
    return model, None

def predictMatch(inputLink):
    # Predict match outcome from scheduled match link
    matchName = hashlib.md5(inputLink.encode()).hexdigest()
    averagePlayer = pred.createAveragePlayer()
    
    try:
        scheduleCache = "Match Schedule JSON Cache"
        filePath = os.path.join(scheduleCache, matchName)
        with open(f"{filePath}.json", 'r') as matchFile:
            scheduledMatchDict = json.load(matchFile)
    except FileNotFoundError:
        print("Match not found in schedule cache. Run createUpcomingMatchJSON first.")
        return None
    
    teams = list(scheduledMatchDict.keys())
    if len(teams) != 2:
        print("Invalid number of teams")
        return None
    
    # Calculate average z-scores for each team
    teamDataCache = "Team Data JSON"
    teamAvgZScores = {}
    
    for team in teams:
        try:
            teamFilePath = os.path.join(teamDataCache, team)
            with open(f"{teamFilePath}.json", 'r') as teamFile:
                teamData = json.load(teamFile)
        except FileNotFoundError:
            print(f"No data found for team: {team}")
            return None
        
        playerZScores = []
        for player, stats in teamData["Players"].items():

            if not isinstance(stats, dict):
                continue
                
            playerZScore = pred.calculateZScores(stats, player, averagePlayer)
            zScoreValues = [v for k, v in playerZScore.items() if k != "Name" and isinstance(v, (int, float))]
            if zScoreValues:
                avgZ = np.mean(zScoreValues)
                playerZScores.append(avgZ)
        
        teamAvgZScores[team] = np.mean(playerZScores)
    
    team1, team2 = teams[0], teams[1]
    zScoreDiff = teamAvgZScores[team1] - teamAvgZScores[team2]
    
    # Load and train model
    print("Training model on historical data...\n")
    X, y = loadMatchData()
    model, _ = trainModel(X, y)
    
    if model is None:
        return None
    
    X_pred = np.array([[zScoreDiff]])
    probabilities = model.predict_proba(X_pred)[0]
    
    print("\n" + "="*50)
    print("MATCH PREDICTION")
    print("="*50)
    print(f"\n{team1} vs {team2}\n")
    print(f"Average Team Z-Score:")
    print(f"  {team1}: {teamAvgZScores[team1]:.3f}")
    print(f"  {team2}: {teamAvgZScores[team2]:.3f}")
    print(f"  Difference: {zScoreDiff:.3f}")
    print(f"\nWin Probabilities:")
    print(f"  {team1}: {probabilities[1]:.2%}")
    print(f"  {team2}: {probabilities[0]:.2%}")
    print("="*50)
    
    return {
        "teams": teams,
        "z_scores": teamAvgZScores,
        "probabilities": {
            team1: probabilities[1],
            team2: probabilities[0]
        }
    }

if __name__ == "__main__":
    inputLink = "https://www.vlr.gg/596414/envy-vs-cloud9-vct-2026-americas-kickoff-mr2"
    
    result = predictMatch(inputLink)