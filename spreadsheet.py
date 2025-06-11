import json
import csv

with open('tbd.json') as f:
    data = json.load(f)

with open('tbd_matches.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Match Hash', 'Team 1', '% Team 1', 'Team 2', '% Team 2'])

    for match_hash, details in data.items():
        t1_raw = details['Team 1']
        t2_raw = details['Team 2']
        t1_name, t1_pct = t1_raw.split(': ')
        t2_name, t2_pct = t2_raw.split(': ')
        writer.writerow([match_hash, t1_name.split(' [')[0], t1_pct, t2_name.split(' [')[0], t2_pct])