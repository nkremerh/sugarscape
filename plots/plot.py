import getopt
import json
import matplotlib.pyplot
import matplotlib.ticker
import os
import re
import sys

datacols = []

def parseDataset(path, dataset, totalTimesteps):
    encodedDir = os.fsencode(path) 
    for file in os.listdir(encodedDir):
        filename = os.fsdecode(file)
        if not filename.endswith('.json'):
            continue
        filePath = path + filename
        fileDecisionModel = re.compile(r"([A-z]*)\d*\.json")
        model = re.search(fileDecisionModel, filename).group(1)
        if model not in dataset:
            continue
        log = open(filePath)
        rawJson = json.loads(log.read())
        dataset[model]["runs"] += 1
        i = 1
        print("Reading log {0}".format(filePath))
        for item in rawJson:
            if item["timestep"] > totalTimesteps:
                break
            if item["timestep"] > dataset[model]["timesteps"]:
                dataset[model]["timesteps"] += 1

            for entry in item:
                if entry in ["agentWealths", "agentTimesToLive", "agentTimesToLiveAgeLimited", "agentTotalMetabolism"]:
                    continue
                if entry not in datacols:
                    datacols.append(entry)
                if entry not in dataset[model]["metrics"]:
                    dataset[model]["metrics"][entry] = [0 for j in range(totalTimesteps + 1)]
                dataset[model]["metrics"][entry][i-1] += item[entry]
            i += 1
        if rawJson[-1]["population"] == 0:
            dataset[model]["died"] += 1
        elif rawJson[-1]["population"] < rawJson[0]["population"]:
            dataset[model]["worse"] += 1
    return dataset

def findMeans(dataset):
    print("Finding mean values across {0} timesteps".format(totalTimesteps))
    for model in dataset:
        for column in datacols:
            for i in range(len(dataset[model]["metrics"][column])):
                dataset[model]["metrics"][column][i] = dataset[model]["metrics"][column][i] / dataset[model]["runs"]
        dataset[model]["metrics"]["meanWealth"] = []
        dataset[model]["metrics"]["meanDeaths"] = []
        for i in range(len(dataset[model]["metrics"]["population"])):
            deaths = dataset[model]["metrics"]["agentStarvationDeaths"][i] + dataset[model]["metrics"]["agentCombatDeaths"][i] + dataset[model]["metrics"]["agentAgingDeaths"][i]
            dataset[model]["metrics"]["meanWealth"].append(dataset[model]["metrics"]["agentWealthTotal"][i] / dataset[model]["metrics"]["population"][i])
            dataset[model]["metrics"]["meanDeaths"].append((deaths / dataset[model]["metrics"]["population"][i]) * 100)
    return dataset

def parseOptions():
    commandLineArgs = sys.argv[1:]
    shortOptions = "c:p:t:o:h"
    longOptions = ("conf=", "outf=", "path=", "help")
    options = {"config": None, "path": None, "outfile": None}
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
        elif currArg in ("-o", "--outf"):
            options["outfile"] = currVal
            if currVal == "":
                print("No data output file path provided.")
                printHelp()
        elif currArg in ("-p", "--path"):
            options["path"] = currVal
            if currVal == "":
                print("No dataset path provided.")
                printHelp()
        elif currArg in ("-h", "--help"):
            printHelp()
    flag = 0
    if options["path"] == None:
        print("Dataset path required.")
        flag = 1
    if options["config"] == None:
        print("Configuration file path required.")
        flag = 1
    if options["outfile"] == None:
        print("Data output file path required.")
        flag = 1
    if flag == 1:
        printHelp()
    return options

def printHelp():
    print("Usage:\n\tpython parselogs.py --path /path/to/data --conf /path/to/config > results.dat\n\nOptions:\n\t-c,--conf\tUse the specified path to configurable settings file.\n\t-o,--outf\tUse the specified path to data output file.\n\t-p,--path\tUse the specified path to find dataset JSON files.\n\t-h,--help\tDisplay this message.")
    exit(0)

def printSummaryStats(dataset):
    print("Model population performance:\n{0:^30} {1:^5} {2:^5} {3:^5}".format("Decision Model", "Extinct", "Worse", "Better"))
    for model in dataset:
        better = dataset[model]["runs"] - (dataset[model]["died"] + dataset[model]["worse"])
        print("{0:^30}: {1:^5} {2:^5} {3:^5}".format(model, dataset[model]["died"], dataset[model]["worse"], better))

def generatePlots(config, models, outfile, totalTimesteps, dataset):
    if "deaths" in config["plots"]:
        print("Generating deaths plot")
        generateSimpleLinePlot(models, dataset, totalTimesteps, "deaths.pdf", "meanDeaths", "Mean Deaths", True)
    if "meanAgeAtDeath" in config["plots"]:
        print("Generating mean age at death plot")
        generateSimpleLinePlot(models, dataset, totalTimesteps, "mean_age_at_death.pdf", "meanAgeAtDeath", "Mean Age at Death")
    if "meanttl" in config["plots"]:
        print("Generating mean time to live plot")
        generateSimpleLinePlot(models, dataset, totalTimesteps, "meanttl.pdf", "agentMeanTimeToLive", "Mean Time to Live")
    if "meanWealth" in config["plots"]:
        print("Generating mean wealth plot")
        generateSimpleLinePlot(models, dataset, totalTimesteps, "mean_wealth.pdf", "meanWealth", "Mean Wealth")
    if "population" in config["plots"]:
        print("Generating population plot")
        generateSimpleLinePlot(models, dataset, totalTimesteps, "population.pdf", "population", "Population")
    if "wealth" in config["plots"]:
        print("Generating total wealth plot")
        generateSimpleLinePlot(models, dataset, totalTimesteps, "wealth.pdf", "agentWealthTotal", "Total Wealth")

def generateSimpleLinePlot(models, dataset, totalTimesteps, outfile, column, label, percentage=False):
    matplotlib.pyplot.rcParams["font.family"] = "serif"
    matplotlib.pyplot.rcParams["font.serif"] = ["Times New Roman"]
    matplotlib.pyplot.rcParams["font.size"] = 20
    figure, axes = matplotlib.pyplot.subplots()
    axes.set(xlabel = "Timestep", ylabel = label, xlim = [0, totalTimesteps])
    x = [i for i in range(totalTimesteps + 1)]
    lines = []
    colors = ["magenta", "cyan", "gold", "black"]
    c = 0
    modelStrings = {"bentham": "Utilitarian", "egoist": "Egoist", "altruist": "Altruist", "none": "Raw Sugarscape"}
    for model in dataset:
        y = [dataset[model]["metrics"][column][i] for i in range(totalTimesteps + 1)]
        axes.plot(x, y, color = colors[c], label = modelStrings[model])
        axes.legend(loc = "center right", labelspacing = 0.1, frameon = False, fontsize = 16)
        c += 1
    if percentage == True:
        axes.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter())
    figure.savefig(outfile, format = "pdf", bbox_inches = "tight")

if __name__ == "__main__":
    options = parseOptions()
    path = options["path"]
    config = options["config"]
    outfile = options["outfile"]
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
        dataset[modelString] = {"runs": 0, "died": 0, "worse": 0, "timesteps": 0, "metrics": {}}

    if not os.path.exists(path):
        print("Path {0} not recognized.".format(path))
        printHelp()

    dataset = parseDataset(path, dataset, totalTimesteps)
    dataset = findMeans(dataset)
    generatePlots(config, models, outfile, totalTimesteps, dataset)
    printSummaryStats(dataset)
    exit(0)
