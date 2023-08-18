import os
import sys
import getopt
import re
import json

popDescriptors = ("population", "agentWealthCollected", "agentWealthTotal",
                "environmentWealthCreated", "environmentWealthTotal",
                "agentStarvationDeaths", "agentMeanTimeToLive",
                "agentMeanTimeToLiveAgeLimited", "agentReproduced")

graphs = ("meanTimeToLive", "percentPopulationGrowth", "starvationDeaths", "totalWealth",
          "wealthCollected", "populationPerTimestep", "agentWealthCollected", "agentWealthTotal",
          "agentMeanTimeToLiveAgeLimited", "agentWealthTotalDivByPop", "agentWealthCollectedDivByPop",
          "agentTotMetDivByEnvWealthCreated")

models = ("benthamHalfLookaheadBinary", "benthamHalfLookaheadTop", "benthamNoLookaheadBinary",
          "egoisticHalfLookaheadTop", "rawSugarscape")

def parseOptions():
    commandLineArgs = sys.argv[1:]
    shortOptions = "l:p:h"
    longOptions = ("log", "path", "help")
    returnValues = {}
    try:
        args, vals = getopt.getopt(commandLineArgs, shortOptions, longOptions)
    except getopt.GetoptError as err:
        print(err)
        exit(0)
    for currArg, currVal in args:
        if (currArg in ("-l", "--log")):
            returnValues["logFile"] = currVal
        elif (currArg in ("-p", "--path")):
            returnValues["path"] = currVal
            returnValues["model"] = currVal
        elif (currArg in ("-h", "--help")):
            exit(0)
    return returnValues
        
def populatePercentPopulationGrowth(data, path):
    with open(path, 'r') as file:
        entries = json.loads(file.read())
        for entry in entries:
            if entry["timestep"] not in data.keys():
                data[entry["timestep"]] = {}
                data[entry["timestep"]]["populations"] = []
                data[entry["timestep"]]["growth"] = []
            data[entry["timestep"]]["populations"].append(entry["population"])

def calcPercentGrowth(data):
    for timestep in data:
        if timestep == 0:
            data[timestep]["growth"] = 0
        else:
            currAvgPop = sum(data[timestep]["populations"])/len(data[timestep]["populations"])
            prevAvgPop = sum(data[timestep-1]["populations"])/len(data[timestep-1]["populations"])
            percentGrowth = currAvgPop/prevAvgPop - 1
            data[timestep]["output"] = percentGrowth    
             
def populateNormalizedLinearData(data, numerator, denominator, path):
    with open(path, 'r') as file:
        entries = json.loads(file.read())
        for entry in entries:
            if entry["timestep"] not in data.keys():
                data[entry["timestep"]] = {}
                data[entry["timestep"]][numerator] = []
                data[entry["timestep"]][denominator] = []
            data[entry["timestep"]][numerator].append(entry[numerator])
            data[entry["timestep"]][denominator].append(entry[denominator])

def calcNormalizedLinearData(data, numerator, denominator):
    for timestep in data:
        if timestep == 0:
            data[timestep]["wealth"] = 0
        else:
            numeratorList = list(data[timestep][numerator])
            denominatorList = list(data[timestep][denominator])
            normalizedList = []
            for i in range(len(numeratorList)):
                normalizedValue = numeratorList[i]/denominatorList[i] if denominatorList[i] > 0 else 0
                normalizedList.append(normalizedValue)
            normalizedValue = sum(normalizedList)/len(normalizedList)
            data[timestep]["output"] = normalizedValue
            
def populateLinearData(data, path, desc):
    with open(path, 'r') as file:
        entries = json.loads(file.read())
        for entry in entries:
            if entry["timestep"] not in data.keys():
                data[entry["timestep"]] = {}
                data[entry["timestep"]]["values"] = []
                data[entry["timestep"]]["output"] = None
            data[entry["timestep"]]["values"].append(entry[desc])
            
def condenseLinearData(data):
    for timestep in data.keys():
        data[timestep]["output"] = sum(data[timestep]["values"])/len(data[timestep]["values"])

    
def logData(data, path):
    maxTimestep = 0
    for model in models:
        timesteps = list(data[graphs[0]][model].keys())
        timesteps.append(maxTimestep)
        maxTimestep = max(timesteps)
    with open(path, 'w') as file:
        file.write("timestep".ljust(95))
        for graph in graphs:
            for model in models:
                file.write("{}-{} ".format(graph, model).ljust(95))
        file.write("\n")
        for timestep in range(1, maxTimestep+1):
            file.write("{} ".format(timestep).ljust(95))
            for graph in graphs:
                for model in models:
                    if (timestep not in data[graph][model].keys()):
                        output = 0
                    else:
                        outputData = data[graph][model][timestep]["output"]
                    file.write("{} ".format(outputData).ljust(95))
            file.write("\n")
            
if __name__ == "__main__":
    parsedOptions = parseOptions()
    dirPath = parsedOptions["path"]
    if (not os.path.exists(dirPath)):
        raise Exception("Path not recognized")
    encodedDir = os.fsencode(dirPath) 
    data = {}
    for graph in graphs:
        data[graph] = {}
        for model in models:
            data[graph][model] = {}
    for file in os.listdir(encodedDir):
        filename = os.fsdecode(file)
        if not filename.endswith('.json'):
            continue
        filePath = dirPath + '/' + filename
        fileDecisionModel = re.compile(r"([A-z]*)\d*\.json")
        model = re.search(fileDecisionModel, filename).group(1)
        if model in models:
            populatePercentPopulationGrowth(data["percentPopulationGrowth"][model], filePath)
            populateNormalizedLinearData(data["agentTotMetDivByEnvWealthCreated"][model], "agentTotalMetabolism", "environmentWealthCreated", filePath)
            populateNormalizedLinearData(data["agentWealthCollectedDivByPop"][model], "agentWealthCollected", "population", filePath)
            populateNormalizedLinearData(data["agentWealthTotalDivByPop"][model], "agentWealthTotal", "population", filePath)
            populateNormalizedLinearData(data["totalWealth"][model], "agentWealthTotal", "environmentWealthTotal", filePath)
            populateNormalizedLinearData(data["wealthCollected"][model], "agentWealthCollected", "environmentWealthCreated", filePath)
            populateLinearData(data["meanTimeToLive"][model], filePath, "agentMeanTimeToLive")
            populateLinearData(data["starvationDeaths"][model], filePath, "agentStarvationDeaths")
            populateLinearData(data["populationPerTimestep"][model], filePath, "population")
            populateLinearData(data["agentWealthCollected"][model], filePath, "agentWealthCollected")
            populateLinearData(data["agentWealthTotal"][model], filePath, "agentWealthTotal")
            populateLinearData(data["agentMeanTimeToLiveAgeLimited"][model], filePath, "agentMeanTimeToLiveAgeLimited")
        else:
            if model == "benthamNoLookaheadTop": #bugged/bad model
                continue
            print("Iterated over an unkown model: {}".format(model))
    for model in models:
        calcPercentGrowth(data["percentPopulationGrowth"][model])
        calcNormalizedLinearData(data["agentTotMetDivByEnvWealthCreated"][model], "agentTotalMetabolism", "environmentWealthCreated")
        calcNormalizedLinearData(data["agentWealthCollectedDivByPop"][model], "agentWealthCollected", "population")
        calcNormalizedLinearData(data["agentWealthTotalDivByPop"][model], "agentWealthTotal", "population")
        calcNormalizedLinearData(data["totalWealth"][model], "agentWealthTotal", "environmentWealthTotal")
        calcNormalizedLinearData(data["wealthCollected"][model], "agentWealthCollected", "environmentWealthCreated")
        condenseLinearData(data["meanTimeToLive"][model])
        condenseLinearData(data["starvationDeaths"][model])
        condenseLinearData(data["populationPerTimestep"][model])
        condenseLinearData(data["agentWealthCollected"][model])
        condenseLinearData(data["agentWealthTotal"][model])
        condenseLinearData(data["agentMeanTimeToLiveAgeLimited"][model])
    logData(data, parsedOptions["logFile"])
    exit(0) 