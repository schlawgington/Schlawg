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

hth_json = 'hth.json'
wl_stats = loadfile(hth_json)

stats_json = 'stats.json'
stats = loadfile(stats_json)

class logisticregressionmodel:
    def __init__(self):
        self.b0 = np.random.uniform(-0.001, 0.001)
        self.b1 = np.random.uniform(-0.001, 0.001)
        self.b2 = np.random.uniform(-0.001, 0.001)
        self.b3 = np.random.uniform(-0.001, 0.001)

    def probabilities_yay(self):
        match_scores = [re.search(r'\d:\d', avg_stats[match]["Score"]).group(0) for match in avg_stats.keys()]
        winloss = []
        for i in match_scores:
            splitlist = i.split(":")
            if int(splitlist[0]) > int(splitlist[1]):
                winloss.append(1)
            else:
                winloss.append(0)

        team = [re.match(r"^(.*)\s\d+:\d+$", avg_stats[match]["Score"]).group(1) for match in avg_stats.keys()]

        deltas = np.array(
            [
                [avg_stats[match]["Stat Diff"]['delta acs'] for match in avg_stats.keys()],
                [avg_stats[match]["Stat Diff"]['delta kast'] for match in avg_stats.keys()],
                [avg_stats[match]["Stat Diff"]['delta adr'] for match in avg_stats.keys()]
            ]
        )

        results = np.array(
            [i for i in winloss]
        )

        def sigmoid(z):
            if z >= 0:
                return 1 / (1 + np.exp(-z))
            else:
                exp_z = np.exp(z)
                return exp_z / (1 + exp_z)

        for j in range(100):
            z = np.array(
                [self.b0 + self.b1*deltas[0][i] + self.b2*deltas[1][i] + self.b3*deltas[2][i] for i in range(len(deltas[0]))]
            )

            unclippedprob = [sigmoid(i) for i in z]
            epsilon = 1e-10
            prob = np.clip(unclippedprob, epsilon, 1 - epsilon)

            acsloss = sum([prob[i] - winloss[i]*deltas[0][i] for i in range(len(winloss))]) / len(winloss)
            kastloss = sum([prob[i] - winloss[i]*deltas[1][i] for i in range(len(winloss))]) / len(winloss)
            adrloss = sum([prob[i] - winloss[i]*deltas[2][i] for i in range(len(winloss))]) / len(winloss)
            loss = sum([winloss[i]*np.log(prob[i]) + (1 - winloss[i])*np.log(1-prob[i]) for i in range(len(winloss))]) / len(winloss)

            learn_rate = 0.0001
            self.b0 = self.b0 - learn_rate*loss
            self.b1 = self.b1 - learn_rate*acsloss
            self.b2 = self.b2 - learn_rate*kastloss
            self.b3 = self.b3 - learn_rate*adrloss

        pretty = [f"{team[i]}: {100*prob[i]:.2f}% to {100*(1-prob[i]):.2f}" for i in range(len(team))]

        return self.b0, self.b1, self.b2, self.b3
    
log = logisticregressionmodel()
coeff = log.probabilities_yay()
print(coeff)