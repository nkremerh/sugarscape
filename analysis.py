import csv
import getopt
import json
import sys

class Analysis:
    def __init__(self, log):
        self.log = log
        self.numTribes = int(self.log[0]["totalTribes"])
        self.assimilationPercentage = 100 / (self.numTribes - 1)
        self.tribeSummary = {"dominantTribe": -1, "timestep": -1}

    def analyzeTribalAssimilation(self):
        for day in self.log:
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
    if fileFormat == "csv":
        log = loadCSV(fileName)
    elif fileFormat == "json":
        log = loadJSON(fileName)
    return log

def parseOptions():
    commandLineArgs = sys.argv[1:]
    shortOptions = "l:h:"
    longOptions = ["log=", "help"]
    try:
        args, vals = getopt.getopt(commandLineArgs, shortOptions, longOptions)
    except getopt.GetoptError as err:
        print(err)
        printHelp()
    for currArg, currVal in args:
        if currArg in ("-l", "--log"):
            if currVal == "":
                print("No log file provided.")
                printHelp()
            logFile = parseFile(currVal)
        elif currArg in ("-h", "--help"):
            printHelp()
    return logFile

def printHelp():
    print("Usage:\n\tpython analysis.py --log [logfile]\n\nOptions:\n\t-l,--log\tAnalyze specified log file.\n\t-h,--help\tDisplay this message.")
    exit(0)

if __name__ == "__main__":
    log = parseOptions()
    A = Analysis(log)
    A.analyzeTribalAssimilation()
