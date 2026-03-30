#!/usr/bin/python

import json

with open('saol14.txt') as inp:
    lines=inp.readlines()
ct=0
for line in lines:
    l=line.split('\n')[0]
    pobj=json.loads(l)
    toprint=pobj['normaliserat_ord'].split(' ')[0].lower()
    if ':' in toprint:
        continue
    print("%s:word_from_saol14_dump"%toprint)
