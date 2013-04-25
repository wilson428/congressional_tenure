#!/usr/bin/env python

import urllib2, yaml, json, datetime
from collections import defaultdict
from utils import write
import re

# convert the United States Project YAML files to JSON
# only runs if file is not detected
def yaml_to_json():
    historical = 'https://raw.github.com/unitedstates/congress-legislators/master/legislators-historical.yaml'
    current = 'https://raw.github.com/unitedstates/congress-legislators/master/legislators-current.yaml'

    print "Downloading current lawmaker file"    
    current = urllib2.urlopen(current)

    print "Downloading historical lawmaker file"
    historical = urllib2.urlopen(historical)
    
    print "Converting from YAML to JSON"
    current = yaml.load(current.read())
    historical = yaml.load(historical.read())

    print "Writing to disk"
    write(json.dumps(historical + current), "legislators.json")

# I don't feel like looking up the start/end dates for each session,
# so we'll impute them from the data
def impute_start_end(legislators):
    start = defaultdict(int)
    end = defaultdict(int)
    for legislator in legislators:
        for term in legislator["terms"]:
            start[term["start"]] += 1
            end[term["end"]] += 1

    start = [datetime.datetime.strptime(x, "%Y-%m-%d") for x,y in start.items() if y > 25]
    end = [datetime.datetime.strptime(x, "%Y-%m-%d") for x,y in end.items() if y > 25]

    return {
        "start_dates": sorted(start),
        "end_dates": sorted(end)
    }

# we need a function to receive a date and figure out which session it belongs to
# if direction == lower, finds nearest date less than input
# otherwise closest date greater than
def session_from_date(date, date_list, direction):
    date = datetime.datetime.strptime(date, "%Y-%m-%d")
    if date in date_list:
        return date_list.index(date) + 1
    if direction == "lower":
        closest = min(date_list, key=lambda x:1000 if (x-date).days > 0 else abs((x-date).days))
    else:
        closest = min(date_list, key=lambda x:1000 if (x-date).days < 0 else abs((x-date).days))
        
    return date_list.index(closest) + 1

# exclude these state abbreviations
DELEGATES = ["MP", "PI", "PR", "VI", "AS", "DC", "DK", "GU", "OL"]

# these dictionaries will map sessions to total days in congress of its members

data = {
    "rep": defaultdict(lambda: defaultdict(int)),
    "sen": defaultdict(lambda: defaultdict(int))
}

roster = {
    "rep": defaultdict(list),
    "sen": defaultdict(list)
}

try:
    legislators = json.load(open("data/legislators.json", "r"))
except:
    print ("Couldn't find file. Downloading from Github.")
    yaml_to_json()
    legislators = json.load(open("data/legislators.json", "r"))

print "Scanning %d legislators" % len(legislators)

dates = impute_start_end(legislators)

for legislator in legislators:
    sessions = {
        "rep": [],
        "sen": []
    }
    
    #count up each session in which this member served 
    for term in [x for x in legislator["terms"] if x["state"] not in DELEGATES]:
        start = session_from_date(term["start"], dates["start_dates"], "lower")
        end = session_from_date(term["end"], dates["end_dates"], "upper")
        for c in range(start, end+1):
            if c not in sessions[term["type"]]:
                if "party" not in term:
                    term["party"] = "None"
                sessions[term["type"]].append([c, term["party"]])

    # add to totals
    # note: totals reflect years in that chamber, not overall

    for chamber in ["rep", "sen"]:
        for c in range(0, len(sessions[chamber])):
            my_session = str(sessions[chamber][c][0])
            my_party = sessions[chamber][c][1]

            roster[chamber][my_session].append("%s (%s) - %d years" % (legislator["name"]["last"], ''.join([x[0] for x in re.split("\s|-", my_party)]), 2 * c))
            if c > 0:
                data[chamber][my_session][my_party] += 2 * c
                data[chamber][my_session]["total"] += 2 * c

# calculate averages
for chamber in data:
    for session in data[chamber]:
        data[chamber][session]["per"] = round(float(data[chamber][session]["total"]) / len(roster[chamber][session]), 2)

# add first session (which by definition has no tenure)
for chamber in data:
    if '114' in data[chamber]:
        del data[chamber]['114']
    if '115' in data[chamber]:
        del data[chamber]['115']
    data[chamber]["1"] = { "total": 0, "per": 0 }

for chamber in roster:
    if '114' in roster[chamber]:
        del roster[chamber]['114']
    if '115' in roster[chamber]:
        del roster[chamber]['115']
    roster[chamber]["1"] = []
    
write(json.dumps(data, sort_keys=True), "data.json")
write(json.dumps(roster, sort_keys=True), "roster.json")
