import json
import os
from collections import defaultdict
import hashlib
import numpy as np
import re
import matplotlib.pyplot as plt

def loadfile(file):
    if os.path.exists(file):
        with open(file, 'r', encoding = 'utf-8') as f:
            content = json.load(f)
            return content
    else:
        return None
    
avg_json = 'avg.json'
avg_stats = loadfile(avg_json)

stats_json = 'stat.json'
stats = loadfile(stats_json)

class logisticregressionmodel:
    def __init__(self):
        self.b0 = np.random.uniform(-0.1, 0.1)
        self.b1 = np.random.uniform(-0.1, 0.1)
        self.b2 = np.random.uniform(-0.1, 0.1)
        self.b3 = np.random.uniform(-0.1, 0.1)
        self.b4 = np.random.uniform(-0.1, 0.1)

    def probabilities_yay(self):
        match_scores_unclip = []
        teams = []
        for team in stats.keys():
            for player in stats[team]['Players'].keys():
                for match in avg_stats.keys():
                    if match not in stats[team]['Players'][player]:
                        continue
                    if stats[team]['Players'][player][match]["Score"] in match_scores_unclip:
                        continue
                    match_scores_unclip.append(stats[team]['Players'][player][match]["Score"])
                    teams.append(stats[team]['Players'][player][match]["Score"])
        match_scores = [re.search(r'\d:\d', score).group() for score in match_scores_unclip]
        winloss = []
        for i in match_scores:
            splitlist = i.split(":")
            if int(splitlist[0]) > int(splitlist[1]):
                winloss.append(1)
            else:
                winloss.append(0)

        deltas = np.array([
                [avg_stats[match]["deltas"]['delta_acs'],
                avg_stats[match]["deltas"]['delta_kast'],
                avg_stats[match]["deltas"]['delta_adr'],
                avg_stats[match]["deltas"]['delta_elo']]
                for match in avg_stats.keys()
            ])

        def sigmoid(z):
            if z >= 0:
                return 1 / (1 + np.exp(-z))
            else:
                exp_z = np.exp(z)
                return exp_z / (1 + exp_z)

        for j in range(1000):
            z = self.b0 + np.dot(deltas, np.array([self.b1, self.b2, self.b3, self.b4]))

            unclippedprob = [sigmoid(i) for i in z]
            epsilon = 1e-10
            prob = np.clip(unclippedprob, epsilon, 1 - epsilon)

            error = np.array(prob) - 1
            grads = np.mean(error[:, None] * deltas, axis=0)
            loss = np.mean(error)

            learn_rate = 0.0001
            self.b0 -= learn_rate*loss
            self.b1 -= learn_rate*grads[0]
            self.b2 -= learn_rate*grads[1]
            self.b3 -= learn_rate*grads[2]
            self.b4 -= learn_rate*grads[3]

        pretty = [f"{teams[i]}: {100*prob[i]:.2f}% to {100*(1-prob[i]):.2f}" for i in range(len(teams))]

        return pretty
    
log = logisticregressionmodel()
coeff = log.probabilities_yay()
print(coeff)