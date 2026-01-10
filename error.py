import os
import json
import re

error_json = 'error.json'

def loadfile(file):
    if os.path.exists(file):
        with open(file, 'r', encoding = 'utf-8') as f:
            raw_content = json.load(f)
            if not raw_content:
                return None
            return raw_content
    else:
        return None

error = loadfile(error_json)

correct_prediction = 0
incorrect_prediction = 0

for match in error.keys():
    result_str = error[match]["Result"][0]
    result = re.search(r'\d:\d', result_str).group()
    team_score_1 = int(result.split(':')[0])
    team_score_2 = int(result.split(':')[1])

    prediction = error[match]["Prediction"]
    team1_prediction_unclip = prediction[0].split(': ')[1]
    team2_prediction_unclip = prediction[1].split(': ')[1]
    team1_prediction = float(team1_prediction_unclip.replace('%', ''))
    team2_prediction =float(team2_prediction_unclip.replace('%', ''))

    if team_score_1 > team_score_2 and team1_prediction > team2_prediction:
        correct_prediction += 1
    elif team_score_1 < team_score_2 and team1_prediction < team2_prediction:
        correct_prediction += 1
    elif team_score_1 > team_score_2 and team1_prediction < team2_prediction:
        incorrect_prediction += 1
    elif team_score_1 < team_score_2 and team1_prediction > team2_prediction:
        incorrect_prediction += 1

print(correct_prediction, incorrect_prediction, round(100*correct_prediction/(correct_prediction + incorrect_prediction), 2))