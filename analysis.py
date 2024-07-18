import csv
import sys

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
        logFile = open(fileName)
        log = csv.DictReader(logFile)

    analyzeTribalAssimilation(log)