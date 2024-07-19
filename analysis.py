import csv
import json
import sys

class Analysis:
    def __init__(self, log):
        self.log = log
        self.numTribes = int(self.log[0]["totalTribes"])
        self.assimilationPercentage = 100 / (self.numTribes - 1)
        self.tribeSummary = {"dominantTribe": -1, "timestep": -1}

    def analyzeTribalAssimilation(self):
        for day in log:
            majorityPercent = float(day["tribePopulationPercentage"])
            if self.isTribeDominant(majorityPercent) == True:
                self.tribeSummary["dominantTribe"] = int(day["majorityTribe"])
                self.tribeSummary["timestep"] = day["timestep"]
                break
        if self.tribeSummary["dominantTribe"] < 0:
            print("There was no clear dominant tribe during this run.")
        else:
            print(f"Tribe {self.tribeSummary['dominantTribe']} is over {int(self.assimilationPercentage)}% of the population at timestep {self.tribeSummary['timestep']}.")

    def isTribeDominant(self, percent):
        if percent > self.assimilationPercentage / 100:
            return True
        return False

    def __str__(self):
        return self.tribeSummary

def loadCSV(filename):
    file = open(filename)
    log = list(csv.DictReader(file))
    for day in log:
        if list(day.keys()) == list(day.values()):
            print("invalid log file. Cannot have more than one entry per log.")
            exit(1)
    return log

def loadJSON(filename):
    try:
        file = open(filename)
        log = json.load(file)
    except:
        print("Invalid log file. Cannot have more than one entry per log.")
        exit(1)
    return log

def parseFile(fileName):
    split = fileName.split(".")
    fileFormat = split[-1]
    return fileFormat

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python analysis.py [logfile]")
        exit(1)

    file = sys.argv[1]
    fileFormat = parseFile(file)
    log = None
    if fileFormat == "csv":
        log = loadCSV(file)
    elif fileFormat == "json":
        log = loadJSON(file)

    if log == None:
        print("No log found.")
        exit(1)
    else:
        A = Analysis(log)
        A.analyzeTribalAssimilation()