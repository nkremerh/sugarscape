import csv
import json
import sys

# Will only produce results for the first run in a CSV file
def analyzeTribalAssimilation(log):
    tribeSummary = {}
    numTribes = 0
    for day in log:
        numTribes = int(day["totalTribes"])
        populationPercent = float(day["tribePopulationPercentage"])
        if isTribeDominant(numTribes, populationPercent) == True:
            tribeSummary["dominantTribe"] = day["majorityTribe"]
            tribeSummary["timestep"] = day["timestep"]
            break
    print(f"Tribe {tribeSummary['dominantTribe']} is at least {int(100 / (numTribes - 1))}% of the population at timestep {tribeSummary['timestep']}")

def isTribeDominant(numTribes, percent):
    dominantPercent = (100 / (numTribes - 1)) / 100
    if percent > dominantPercent:
        return True
    return False

def loadCSVFile(fileName):
    logFile = open(fileName)
    log = csv.DictReader(logFile)
    return log

# Will only parse if there is only one run logged in the file
def loadJSONFile(filename):
    logFile = open(fileName)
    log = json.load(logFile)
    return log

def parseFile(filename):
    split = filename.split(".")
    format = split[-1]
    return format

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: analysis.py [logfile]")
        exit(1)

    fileName = sys.argv[-1]
    fileFormat = parseFile(fileName)

    log = None

    if fileFormat == "csv":
        log = loadCSVFile(fileName)
    elif fileFormat == "json":
        log = loadJSONFile(fileName)
    else:
        print("Unsupported file format.")
        exit(1)

    analyzeTribalAssimilation(log)

    exit(0)