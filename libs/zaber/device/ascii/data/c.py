import json
import csv
import pprint

rec = {}
with open('ascii-settings.csv') as f:
    c = csv.reader(f)
    for l in list(c)[1:]:
        rec.setdefault(l[1],{}).setdefault(l[0],0)

pprint.pprint(rec)

