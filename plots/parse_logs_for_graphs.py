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
          "agentMeanTimeToLiveAgeLimited", "agentWealthTotalDivByPop", "agentWealthCollectedDivByPop")

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

def populateMeanTimeToLive(data, path):
    with open(path, 'r') as file:
        entries = json.loads(file.read())
        for entry in entries:
            if entry["timestep"] not in data.keys():
                data[entry["timestep"]] = []
            data[entry["timestep"]].append(entry["agentMeanTimeToLive"])

def condenseMeanTimeToLiveData(data):
    for timestep in data.keys():
        data[timestep] = sum(data[timestep])/len(data[timestep])
        
def populatepercentPopulationGrowth(data, path):
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
            data[timestep]["growth"] = percentGrowth
                    
def populateTotalWealthData(data, path):
    with open(path, 'r') as file:
        entries = json.loads(file.read())
        for entry in entries:
            if entry["timestep"] not in data.keys():
                data[entry["timestep"]] = {}
                data[entry["timestep"]]["agentWealth"] = []
                data[entry["timestep"]]["environmentWealth"] = []
            data[entry["timestep"]]["agentWealth"].append(entry["agentWealthTotal"])
            data[entry["timestep"]]["environmentWealth"].append(entry["environmentWealthTotal"])
            
def calcTotalWealth(data):
    for timestep in data:
        if timestep == 0:
            data[timestep]["wealth"] = 0
        else:
            agentWealthList = list(data[timestep]["agentWealth"])
            envrionmentWealthList = list(data[timestep]["environmentWealth"])
            normalizedList = []
            for i in range(len(agentWealthList)):
                normalizedList.append(agentWealthList[i]/envrionmentWealthList[i])
            normalizedWealth = sum(normalizedList)/len(normalizedList)
            data[timestep]["wealth"] = normalizedWealth
            
def populateWealthCollectedData(data, path):
    with open(path, 'r') as file:
        entries = json.loads(file.read())
        for entry in entries:
            if entry["timestep"] not in data.keys():
                data[entry["timestep"]] = {}
                data[entry["timestep"]]["agentWealth"] = []
                data[entry["timestep"]]["environmentWealth"] = []
            data[entry["timestep"]]["agentWealth"].append(entry["agentWealthCollected"])
            data[entry["timestep"]]["environmentWealth"].append(entry["environmentWealthCreated"])
            
def calcWealthCollected(data):
    for timestep in data:
        if timestep == 0:
            data[timestep]["wealth"] = 0
        else:
            agentWealthList = list(data[timestep]["agentWealth"])
            envrionmentWealthList = list(data[timestep]["environmentWealth"])
            normalizedList = []
            for i in range(len(agentWealthList)):
                normalizedList.append(agentWealthList[i]/envrionmentWealthList[i])
            normalizedWealth = sum(normalizedList)/len(normalizedList)
            data[timestep]["wealth"] = normalizedWealth
            
def populateAgentWealthTotalDivByPop(data, path):
    with open(path, 'r') as file:
        entries = json.loads(file.read())
        for entry in entries:
            if entry["timestep"] not in data.keys():
                data[entry["timestep"]] = {}
                data[entry["timestep"]]["agentWealthTotal"] = []
                data[entry["timestep"]]["population"] = []
            data[entry["timestep"]]["agentWealthTotal"].append(entry["agentWealthTotal"])
            data[entry["timestep"]]["population"].append(entry["population"])
            
def calcAgentWealthTotalDivByPop(data):
    for timestep in data:
        if timestep == 0:
            data[timestep]["wealth"] = 0
        else:
            agentWealthList = list(data[timestep]["agentWealthTotal"])
            populationList = list(data[timestep]["population"])
            normalizedList = []
            for i in range(len(agentWealthList)):
                normalizedWealth = agentWealthList[i]/populationList[i] if populationList[i] > 0 else 0
                normalizedList.append(normalizedWealth)
            normalizedWealth = sum(normalizedList)/len(normalizedList)
            data[timestep]["wealth"] = normalizedWealth
            
def populateAgentWealthCollectedDivByPop(data, path):
    with open(path, 'r') as file:
        entries = json.loads(file.read())
        for entry in entries:
            if entry["timestep"] not in data.keys():
                data[entry["timestep"]] = {}
                data[entry["timestep"]]["agentWealthCollected"] = []
                data[entry["timestep"]]["population"] = []
            data[entry["timestep"]]["agentWealthCollected"].append(entry["agentWealthCollected"])
            data[entry["timestep"]]["population"].append(entry["population"])

def calcAgentWealthCollectedDivByPop(data):
    for timestep in data:
        if timestep == 0:
            data[timestep]["wealth"] = 0
        else:
            agentWealthList = list(data[timestep]["agentWealthCollected"])
            populationList = list(data[timestep]["population"])
            normalizedList = []
            for i in range(len(agentWealthList)):
                normalizedWealth = agentWealthList[i]/populationList[i] if populationList[i] > 0 else 0
                normalizedList.append(normalizedWealth)
            normalizedWealth = sum(normalizedList)/len(normalizedList)
            data[timestep]["wealth"] = normalizedWealth
            
def populateLinearData(data, path, desc):
    with open(path, 'r') as file:
        entries = json.loads(file.read())
        for entry in entries:
            if entry["timestep"] not in data.keys():
                data[entry["timestep"]] = []
            data[entry["timestep"]].append(entry[desc])
            
def condenseLinearData(data):
    for timestep in data.keys():
        data[timestep] = sum(data[timestep])/len(data[timestep])
    
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
                    if graph == "meanTimeToLive":
                        outputData = data[graph][model][timestep]
                    elif graph == "percentPopulationGrowth":
                        outputData = data[graph][model][timestep]["growth"]
                    elif graph == "starvationDeaths":
                        outputData = data[graph][model][timestep]
                    elif graph == "totalWealth":
                        outputData = data[graph][model][timestep]["wealth"]
                    elif graph == "wealthCollected":
                        outputData = data[graph][model][timestep]["wealth"]
                    elif graph == "agentMeanTimeToLiveAgeLimited":
                        outputData = data[graph][model][timestep]
                    elif graph == "agentWealthCollected":
                        outputData = data[graph][model][timestep]
                    elif graph == "agentWealthTotal":
                        outputData = data[graph][model][timestep]
                    elif graph == "populationPerTimestep":
                        outputData = data[graph][model][timestep]
                    elif graph == "agentWealthTotalDivByPop":
                        outputData = data[graph][model][timestep]["wealth"]
                    elif graph == "agentWealthCollectedDivByPop":
                        outputData = data[graph][model][timestep]["wealth"]
                    else:
                        raise Exception("Graph not recognized: {}".format(graph))
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
            populateAgentWealthCollectedDivByPop(data["agentWealthCollectedDivByPop"][model], filePath)
            populateAgentWealthTotalDivByPop(data["agentWealthTotalDivByPop"][model], filePath)
            populateLinearData(data["meanTimeToLive"][model], filePath, "agentMeanTimeToLive")
            populatepercentPopulationGrowth(data["percentPopulationGrowth"][model], filePath)
            populateLinearData(data["starvationDeaths"][model], filePath, "agentStarvationDeaths")
            populateTotalWealthData(data["totalWealth"][model], filePath)
            populateWealthCollectedData(data["wealthCollected"][model], filePath)
            populateLinearData(data["populationPerTimestep"][model], filePath, "population")
            populateLinearData(data["agentWealthCollected"][model], filePath, "agentWealthCollected")
            populateLinearData(data["agentWealthTotal"][model], filePath, "agentWealthTotal")
            populateLinearData(data["agentMeanTimeToLiveAgeLimited"][model], filePath, "agentMeanTimeToLiveAgeLimited")
        else:
            if model == "benthamNoLookaheadTop": #bugged/bad model
                continue
            print("Iterated over an unkown model: {}".format(model))
    for model in models:
        calcAgentWealthCollectedDivByPop(data["agentWealthCollectedDivByPop"][model])
        calcAgentWealthTotalDivByPop(data["agentWealthTotalDivByPop"][model])
        condenseLinearData(data["meanTimeToLive"][model])
        calcPercentGrowth(data["percentPopulationGrowth"][model])
        condenseLinearData(data["starvationDeaths"][model])
        calcTotalWealth(data["totalWealth"][model])
        calcWealthCollected(data["wealthCollected"][model])
        condenseLinearData(data["populationPerTimestep"][model])
        condenseLinearData(data["agentWealthCollected"][model])
        condenseLinearData(data["agentWealthTotal"][model])
        condenseLinearData(data["agentMeanTimeToLiveAgeLimited"][model])
    logData(data, parsedOptions["logFile"])
    exit(0) 