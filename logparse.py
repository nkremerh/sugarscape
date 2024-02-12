#! /usr/bin/python

import getopt
import json
import sys

def parseLog(logFile):
    file = open(logFile)
    entries = json.loads(file.read())
    timesteps = -1

    data = {"population": 0, "agentWealthCollected": 0, "agentWealthTotal": 0,
            "environmentWealthCreated": 0, "environmentWealthTotal": 0, "meanHappiness": 0, "meanWealthHappiness": 0, 
            "meanHealthHappiness": 0, "meanSocialHappiness": 0, "meanFamilyHappiness": 0, "meanConflictHappiness": 0,
            "agentStarvationDeaths": 0, "agentMeanTimeToLive": 0,
            "agentMeanTimeToLiveAgeLimited": 0, "agentReproduced": 0}

    print(data.keys())
    for entry in entries:
        dataStr = ""
        for datum in data:
            data[datum] = entry[datum]
            print(data[datum], end=',')
        print("")

def parseOptions():
    commandLineArgs = sys.argv[1:]
    shortOptions = "lh:"
    longOptions = ["log=", "help"]
    logFile = None
    try:
        args, vals = getopt.getopt(commandLineArgs, shortOptions, longOptions)
    except getopt.GetoptError as err:
        print(err)
        printHelp()
    nextArg = 0
    for currArg, currVal in args:
        nextArg += 1
        if currArg in("-l", "--log"):
            if currArg == "-l" and nextArg < len(commandLineArgs):
                currVal = commandLineArgs[nextArg]
            if currVal == "":
                print("No log file provided.")
                printHelp()
            logFile = currVal
        elif currArg in ("-h", "--help"):
            printHelp()
    return logFile

def printHelp():
    print("Usage:\n\tpython logparse.py --log log.json\n\nOptions:\n\t-l,--log\tUse specified log file for parsing and summarizing.\n\t-h,--help\tDisplay this message.")
    exit(0)

if __name__ == "__main__":
    logFile = parseOptions()
    if logFile == None:
        print("No log file provided.")
        printHelp()
    summary = parseLog(logFile)
    exit(0)