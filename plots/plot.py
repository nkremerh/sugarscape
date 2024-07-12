import csv
import getopt
import json
import matplotlib.pyplot
import matplotlib.ticker
import os
import re
import sys

datacols = []

def parseDataset(path, dataset, totalTimesteps, skipExtinct=False):
    encodedDir = os.fsencode(path) 
    for file in os.listdir(encodedDir):
        filename = os.fsdecode(file)
        if not (filename.endswith(".json") or filename.endswith(".csv")):
            continue
        filePath = path + filename
        fileDecisionModel = re.compile(r"([A-z]*)\d*\.(json|csv)")
        model = re.search(fileDecisionModel, filename).group(1)
        if model not in dataset:
            continue
        log = open(filePath)
        print("Reading log {0}".format(filePath))
        rawData = None
        if filename.endswith(".json"):
            rawData = json.loads(log.read())
        else:
            rawData = list(csv.DictReader(log))

        if int(rawData[-1]["population"]) == 0:
            dataset[model]["died"] += 1
            if skipExtinct == True:
                continue
        elif int(rawData[-1]["population"]) <= int(rawData[0]["population"]):
            dataset[model]["worse"] += 1
        else:
            dataset[model]["better"] += 1

        dataset[model]["runs"] += 1
        i = 1
        for item in rawData:
            if int(item["timestep"]) > totalTimesteps:
                break
            if int(item["timestep"]) > dataset[model]["timesteps"]:
                dataset[model]["timesteps"] += 1

            for entry in item:
                if entry in ["agentWealths", "agentTimesToLive", "agentTimesToLiveAgeLimited", "agentTotalMetabolism"]:
                    continue
                if entry not in datacols:
                    datacols.append(entry)
                if entry not in dataset[model]["metrics"]:
                    dataset[model]["metrics"][entry] = [0 for j in range(totalTimesteps + 1)]
                dataset[model]["metrics"][entry][i-1] += float(item[entry])
            i += 1
    for model in dataset:
        if dataset[model]["runs"] == 0:
            print(f"No simulation runs found for the {model} decision model")
    return dataset

def findMeans(dataset):
    print("Finding mean values across {0} timesteps".format(totalTimesteps))
    for model in dataset:
        for column in datacols:
            for i in range(len(dataset[model]["metrics"][column])):
                if column not in dataset[model]["means"]:
                    dataset[model]["means"][column] = [0 for j in range(totalTimesteps + 1)]
                dataset[model]["means"][column][i] = dataset[model]["metrics"][column][i] / dataset[model]["runs"]
        dataset[model]["means"]["meanWealth"] = []
        dataset[model]["means"]["meanDeaths"] = []
        for i in range(len(dataset[model]["metrics"]["population"])):
            deaths = dataset[model]["metrics"]["agentStarvationDeaths"][i] + dataset[model]["metrics"]["agentCombatDeaths"][i] + dataset[model]["metrics"]["agentAgingDeaths"][i]
            dataset[model]["means"]["meanWealth"].append(dataset[model]["metrics"]["agentWealthTotal"][i] / dataset[model]["metrics"]["population"][i])
            dataset[model]["means"]["meanDeaths"].append((deaths / dataset[model]["metrics"]["population"][i]) * 100)
    return dataset

def parseOptions():
    commandLineArgs = sys.argv[1:]
    shortOptions = "c:p:s:t:h"
    longOptions = ("conf=", "path=", "help", "skip")
    options = {"config": None, "path": None, "skip": False}
    try:
        args, vals = getopt.getopt(commandLineArgs, shortOptions, longOptions)
    except getopt.GetoptError as err:
        print(err)
        exit(0)
    for currArg, currVal in args:
        if currArg in ("-c", "--conf"):
            if currVal == "":
                print("No config file provided.")
                printHelp()
            options["config"] = currVal
        elif currArg in ("-p", "--path"):
            options["path"] = currVal
            if currVal == "":
                print("No dataset path provided.")
                printHelp()
        elif currArg in ("-h", "--help"):
            printHelp()
        elif currArg in ("-s", "--skip"):
            options["skip"] = True
    flag = 0
    if options["path"] == None:
        print("Dataset path required.")
        flag = 1
    if options["config"] == None:
        print("Configuration file path required.")
        flag = 1
    if flag == 1:
        printHelp()
    return options

def printHelp():
    print("Usage:\n\tpython parselogs.py --path /path/to/data --conf /path/to/config > results.dat\n\nOptions:\n\t-c,--conf\tUse the specified path to configurable settings file.\n\t-p,--path\tUse the specified path to find dataset JSON files.\n\t-s,--skip\tSkip including extinct societies in produced graphs.\n\t-h,--help\tDisplay this message.")
    exit(0)

def printSummaryStats(dataset):
    print("Model population performance:\n{0:^30} {1:^5} {2:^5} {3:^5}".format("Decision Model", "Extinct", "Worse", "Better"))
    for model in dataset:
        print("{0:^30}: {1:^5} {2:^5} {3:^5}".format(model, dataset[model]["died"], dataset[model]["worse"], dataset[model]["better"]))

def generatePlots(config, models, totalTimesteps, dataset):
    if "deaths" in config["plots"]:
        print("Generating deaths plot")
        generateSimpleLinePlot(models, dataset, totalTimesteps, "deaths.pdf", "meanDeaths", "Mean Deaths", "center right", True)
    if "meanAgeAtDeath" in config["plots"]:
        print("Generating mean age at death plot")
        generateSimpleLinePlot(models, dataset, totalTimesteps, "mean_age_at_death.pdf", "meanAgeAtDeath", "Mean Age at Death", "center right")
    if "meanttl" in config["plots"]:
        print("Generating mean time to live plot")
        generateSimpleLinePlot(models, dataset, totalTimesteps, "meanttl.pdf", "agentMeanTimeToLive", "Mean Time to Live", "center right")
    if "meanWealth" in config["plots"]:
        print("Generating mean wealth plot")
        generateSimpleLinePlot(models, dataset, totalTimesteps, "mean_wealth.pdf", "meanWealth", "Mean Wealth", "center right")
    if "population" in config["plots"]:
        print("Generating population plot")
        generateSimpleLinePlot(models, dataset, totalTimesteps, "population.pdf", "population", "Population", "center right")
    if "wealth" in config["plots"]:
        print("Generating total wealth plot")
        generateSimpleLinePlot(models, dataset, totalTimesteps, "wealth.pdf", "agentWealthTotal", "Total Wealth", "center right")

def generateSimpleLinePlot(models, dataset, totalTimesteps, outfile, column, label, positioning, percentage=False):
    matplotlib.pyplot.rcParams["font.family"] = "serif"
    matplotlib.pyplot.rcParams["font.serif"] = ["Times New Roman"]
    matplotlib.pyplot.rcParams["font.size"] = 20
    figure, axes = matplotlib.pyplot.subplots()
    axes.set(xlabel = "Timestep", ylabel = label, xlim = [0, totalTimesteps])
    x = [i for i in range(totalTimesteps + 1)]
    lines = []
    modelStrings = {"bentham": "Utilitarian", "egoist": "Egoist", "altruist": "Altruist", "none": "Raw Sugarscape", "rawSugarscape": "Raw Sugarscape", "multiple": "Multiple", "unknown": "Unknown"}
    colors = {"bentham": "magenta", "egoist": "cyan", "altruist": "gold", "none": "black", "rawSugarscape": "black ", "multiple": "red", "unknown": "green"}
    for model in dataset:
        y = [dataset[model]["means"][column][i] for i in range(totalTimesteps + 1)]
        if '_' in model:
            model = "multiple"
        elif model not in modelStrings:
            model = "unknown"
        axes.plot(x, y, color=colors[model], label=modelStrings[model])
        axes.legend(loc=positioning, labelspacing=0.1, frameon=False, fontsize=16)
    if percentage == True:
        axes.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter())
    figure.savefig(outfile, format="pdf", bbox_inches="tight")

if __name__ == "__main__":
    options = parseOptions()
    path = options["path"]
    config = options["config"]
    skipExtinct = options["skip"]
    configFile = open(config)
    config = json.loads(configFile.read())["dataCollectionOptions"]
    configFile.close()
    totalTimesteps = config["plotTimesteps"]
    models = config["decisionModels"]
    dataset = {}
    for model in models:
        modelString = model
        if type(model) == list:
            modelString = '_'.join(model)
        dataset[modelString] = {"runs": 0, "died": 0, "worse": 0, "better": 0, "timesteps": 0, "means": {}, "metrics": {}}

    if not os.path.exists(path):
        print("Path {0} not recognized.".format(path))
        printHelp()

    dataset = parseDataset(path, dataset, totalTimesteps, skipExtinct)
    dataset = findMeans(dataset)
    generatePlots(config, models, totalTimesteps, dataset)
    printSummaryStats(dataset)
    exit(0)
