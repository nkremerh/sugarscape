import csv
import getopt
import json
import math
import matplotlib.pyplot
import matplotlib.ticker
import os
import re
import sys

def findMeans(dataset):
    print(f"Finding mean values across {totalTimesteps} timesteps")
    for model in dataset:
        for column in dataset[model]["metrics"]:
            for i in range(len(dataset[model]["metrics"][column])):
                if column not in dataset[model]["aggregates"]:
                    dataset[model]["aggregates"][column] = [0 for j in range(totalTimesteps + 1)]
                dataset[model]["aggregates"][column][i] = dataset[model]["metrics"][column][i] / dataset[model]["runs"]
    return dataset

def findMedians(dataset):
    print(f"Finding median values across {totalTimesteps} timesteps")
    for model in dataset:
        for column in dataset[model]["metrics"]:
            for i in range(len(dataset[model]["metrics"][column])):
                sortedColumn = sorted(dataset[model]["metrics"][column][i])
                columnLength = len(sortedColumn)
                midpoint = math.floor(columnLength / 2)
                median = sortedColumn[midpoint]
                quartile = math.floor(columnLength / 4)
                firstQuartile = sortedColumn[quartile]
                thirdQuartile = sortedColumn[midpoint + quartile]
                if columnLength % 2 == 0:
                    median = round((sortedColumn[midpoint - 1] + median) / 2, 2)
                    firstQuartile = round((sortedColumn[quartile - 1] + firstQuartile) / 2, 2)
                    thirdQuartile = round((sortedColumn[(midpoint + quartile) - 1] + thirdQuartile) / 2, 2)
                if column not in dataset[model]["aggregates"]:
                    dataset[model]["aggregates"][column] = [0 for j in range(totalTimesteps + 1)]
                    dataset[model]["firstQuartiles"][column] = [0 for j in range(totalTimesteps + 1)]
                    dataset[model]["thirdQuartiles"][column] = [0 for j in range(totalTimesteps + 1)]
                dataset[model]["aggregates"][column][i] = median
    return dataset

def generatePlots(config, models, totalTimesteps, dataset, statistic, experimentalGroup=None):
    titleStatistic = statistic.title()
    if "conflictHappiness" in config["plots"]:
        print(f"Generating {statistic} conflict happiness plot")
        generateSimpleLinePlot(models, dataset, totalTimesteps, f"{statistic}_conflict_happiness.pdf", "meanConflictHappiness", f"{titleStatistic} Conflict Happiness", "center right", percentage=False, experimentalGroup=experimentalGroup)
    if "deaths" in config["plots"]:
        print(f"Generating {statistic} deaths plot")
        generateSimpleLinePlot(models, dataset, totalTimesteps, f"{statistic}_deaths.pdf", "meanDeathsPercentage", f"{titleStatistic} Deaths", "center right", percentage=True, experimentalGroup=experimentalGroup)
    if "familyHappiness" in config["plots"]:
        print(f"Generating {statistic} family happiness plot")
        generateSimpleLinePlot(models, dataset, totalTimesteps, f"{statistic}_family_happiness.pdf", "meanFamilyHappiness", f"{titleStatistic} Family Happiness", "center right", percentage=False, experimentalGroup=experimentalGroup)
    if "giniCoefficient" in config["plots"]:
        print(f"Generating {statistic} Gini coefficient plot")
        generateSimpleLinePlot(models, dataset, totalTimesteps, f"{statistic}_gini.pdf", "giniCoefficient", f"{titleStatistic} Gini Coefficient", "center right", percentage=False, experimentalGroup=experimentalGroup)
    if "happiness" in config["plots"]:
        print(f"Generating {statistic} happiness plot")
        generateSimpleLinePlot(models, dataset, totalTimesteps, f"{statistic}_happiness.pdf", "meanHappiness", f"{titleStatistic} Happiness", "center right", percentage=False, experimentalGroup=experimentalGroup)
    if "healthHappiness" in config["plots"]:
        print(f"Generating {statistic} health happiness plot")
        generateSimpleLinePlot(models, dataset, totalTimesteps, f"{statistic}_health_happiness.pdf", "meanHealthHappiness", f"{titleStatistic} Health Happiness", "center right", percentage=False, experimentalGroup=experimentalGroup)
    if "lifeExpectancy" in config["plots"]:
        print(f"Generating {statistic} life expectancy plot")
        generateSimpleLinePlot(models, dataset, totalTimesteps, f"{statistic}_life_expectancy.pdf", "meanAgeAtDeath", f"{titleStatistic} Life Expectancy", "lower right", percentage=False, experimentalGroup=experimentalGroup)
    if "population" in config["plots"]:
        print(f"Generating {statistic} population plot")
        generateSimpleLinePlot(models, dataset, totalTimesteps, f"{statistic}_population.pdf", "population", f"{titleStatistic} Population", "lower right", percentage=False, experimentalGroup=experimentalGroup)
    if "selfishness" in config["plots"]:
        print(f"Generating {statistic} selfishness plot")
        generateSimpleLinePlot(models, dataset, totalTimesteps, f"{statistic}_selfishness.pdf", "meanSelfishness", f"{titleStatistic} Selfishness Factor", "lower center", percentage=False, experimentalGroup=experimentalGroup)
    if "sickness" in config["plots"]:
        print(f"Generating {statistic} sick percentage plot")
        generateSimpleLinePlot(models, dataset, totalTimesteps, f"{statistic}_sickness.pdf", "sickAgentsPercentage", f"{titleStatistic} Diseased Agents", "center right", percentage=True, experimentalGroup=experimentalGroup)
    if "socialHappiness" in config["plots"]:
        print(f"Generating {statistic} social happiness plot")
        generateSimpleLinePlot(models, dataset, totalTimesteps, f"{statistic}_social_happiness.pdf", "meanSocialHappiness", f"{titleStatistic} Social Happiness", "center right", percentage=False, experimentalGroup=experimentalGroup)
    if "totalWealth" in config["plots"]:
        print(f"Generating {statistic} total wealth plot")
        generateSimpleLinePlot(models, dataset, totalTimesteps, f"{statistic}_wealth.pdf", "agentWealthTotal", f"{titleStatistic} Total Wealth", "center right", percentage=False, experimentalGroup=experimentalGroup)
    if "tradeVolume" in config["plots"]:
        print(f"Generating {statistic} trade volume plot")
        generateSimpleLinePlot(models, dataset, totalTimesteps, f"{statistic}_trades.pdf", "tradeVolume", f"{titleStatistic} Trade Volume", "center right", percentage=False, experimentalGroup=experimentalGroup)
    if "ttl" in config["plots"]:
        print(f"Generating {statistic} time to live plot")
        generateSimpleLinePlot(models, dataset, totalTimesteps, f"{statistic}_ttl.pdf", "agentMeanTimeToLive", f"{titleStatistic} Time to Live", "upper right", percentage=False, experimentalGroup=experimentalGroup)
    if "wealth" in config["plots"]:
        print(f"Generating {statistic} wealth plot")
        generateSimpleLinePlot(models, dataset, totalTimesteps, f"{statistic}_wealth.pdf", "meanWealth", f"{titleStatistic} Wealth", "center right", percentage=False, experimentalGroup=experimentalGroup)
    if "wealthHappiness" in config["plots"]:
        print(f"Generating {statistic} wealth happiness plot")
        generateSimpleLinePlot(models, dataset, totalTimesteps, f"{statistic}_total_wealth_happiness.pdf", "meanWealthHappiness", f"{titleStatistic} Wealth Happiness", "center right", percentage=False, experimentalGroup=experimentalGroup)

def generateSimpleLinePlot(models, dataset, totalTimesteps, outfile, column, label, positioning, percentage=False, experimentalGroup=None):
    matplotlib.pyplot.rcParams["font.family"] = "serif"
    matplotlib.pyplot.rcParams["font.size"] = 18
    figure, axes = matplotlib.pyplot.subplots()
    axes.set(xlabel = "Timestep", ylabel = label, xlim = [0, totalTimesteps])
    x = [i for i in range(totalTimesteps + 1)]
    y = [0 for i in range(totalTimesteps + 1)]
    lines = []
    modelStrings = {"asimov": "Asimov's Robot", "bentham": "Utilitarian", "egoist": "Egoist", "altruist": "Altruist", "none": "Raw Sugarscape", "rawSugarscape": "Raw Sugarscape",
                    "temperance": "Simple Temperance", "temperancePECS": "Complex Temperance", "multiple": "Multiple", "unknown": "Unknown"}
    colors = {"asimov": "blue", "bentham": "magenta", "egoist": "cyan", "altruist": "gold", "none": "black", "rawSugarscape": "black ", "temperance": "blue", "temperancePECS": "purple", "multiple": "red", "unknown": "green"}
    for model in dataset:
        modelString = model
        if '_' in model:
            modelString = "multiple"
        elif model not in modelStrings:
            modelString = "unknown"
        if experimentalGroup != None:
            controlGroupColumn = "control" + column[0].upper() + column[1:]
            controlGroupLabel = f"Control {modelStrings[modelString]}"
            experimentalGroupColumn = experimentalGroup + column[0].upper() + column[1:]
            experimentalGroupLabel = experimentalGroup[0].upper() + experimentalGroup[1:] + f" {modelStrings[modelString]}"
            # Prevent key error if all seeds went extinct for model
            if column in dataset[model]["aggregates"]:
                y = [dataset[model]["aggregates"][controlGroupColumn][i] for i in range(totalTimesteps + 1)]
                axes.plot(x, y, color=colors[modelString], label=controlGroupLabel)
                y = [dataset[model]["aggregates"][experimentalGroupColumn][i] for i in range(totalTimesteps + 1)]
                axes.plot(x, y, color=colors[modelString], label=experimentalGroupLabel, linestyle="dotted")
        # Prevent key error if all seeds went extinct for model
        elif column in dataset[model]["aggregates"]:
            y = [dataset[model]["aggregates"][column][i] for i in range(totalTimesteps + 1)]
            axes.plot(x, y, color=colors[modelString], label=modelStrings[modelString])
        axes.legend(loc=positioning, labelspacing=0.1, frameon=False, fontsize=16)
    if percentage == True:
        axes.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter())
    figure.savefig(outfile, format="pdf", bbox_inches="tight")

def parseDataset(path, dataset, totalTimesteps, statistic, skipExtinct=False):
    encodedDir = os.fsencode(path)
    files = [f for f in os.listdir(encodedDir) if os.fsdecode(f).endswith("json") or os.fsdecode(f).endswith(".csv")]
    printFileLength = len(max(files, key=len))
    fileCount = 1
    totalFiles = len(files)
    for file in files:
        filename = os.fsdecode(file)
        filePath = path + filename
        fileDecisionModel = re.compile(r"^([A-z]*)(\d*)\.(json|csv)")
        fileSearch = re.search(fileDecisionModel, filename)
        if fileSearch == None:
            continue
        model = fileSearch.group(1)
        if model not in dataset:
            continue
        seed = fileSearch.group(2)
        log = open(filePath)
        printProgress(filename, fileCount, totalFiles, printFileLength)
        fileCount += 1
        rawData = None
        if filename.endswith(".json"):
            rawData = json.loads(log.read())
        else:
            rawData = list(csv.DictReader(log))

        if int(rawData[-1]["population"]) == 0:
            dataset[model]["extinct"] += 1
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
                if entry not in dataset[model]["metrics"]:
                    if statistic == "mean":
                        dataset[model]["metrics"][entry] = [0 for j in range(totalTimesteps + 1)]
                    elif statistic == "median":
                        dataset[model]["metrics"][entry] = [[] for j in range(totalTimesteps + 1)]
                if item[entry] == "None":
                    item[entry] = 0
                if statistic == "mean":
                    dataset[model]["metrics"][entry][i-1] += float(item[entry])
                elif statistic == "median":
                    dataset[model]["metrics"][entry][i-1].append(float(item[entry]))
            i += 1
    print(f"\r{' ' * os.get_terminal_size().columns}", end='\r')
    for model in dataset:
        if dataset[model]["runs"] == 0:
            print(f"No simulation runs found for the {model} decision model")
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
    print("Usage:\n\tpython plot.py --path /path/to/data --conf /path/to/config > results.dat\n\nOptions:\n\t-c,--conf\tUse the specified path to configurable settings file.\n\t-p,--path\tUse the specified path to find dataset JSON files.\n\t-s,--skip\tSkip including extinct societies in produced graphs.\n\t-h,--help\tDisplay this message.")
    exit(0)

def printProgress(filename, filesParsed, totalFiles, fileLength, decimals=2):
    barLength = os.get_terminal_size().columns // 2
    progress = round(((filesParsed / totalFiles) * 100), decimals)
    filledLength = (barLength * filesParsed) // totalFiles
    bar = '█' * filledLength + '-' * (barLength - filledLength)
    printString = f"\rParsing {filename:>{fileLength}}: |{bar}| {filesParsed} / {totalFiles} ({progress}%)"
    if filesParsed == totalFiles:
        print(f"\r{' ' * os.get_terminal_size().columns}", end='\r')
    else:
        print(f"\r{printString}", end='\r')

def printSummaryStats(dataset):
    print(f"Model population performance:\n{'Decision Model':^30} {'Extinct':^5} {'Worse':^5} {'Better':^5}")
    for model in dataset:
        print(f"{model:^30} {dataset[model]['extinct']:^5} {dataset[model]['worse']:^5} {dataset[model]['better']:^5}")

if __name__ == "__main__":
    options = parseOptions()
    path = options["path"]
    config = options["config"]
    skipExtinct = options["skip"]
    configFile = open(config)
    config = json.loads(configFile.read())
    configFile.close()
    experimentalGroup = config["sugarscapeOptions"]["experimentalGroup"] if "experimentalGroup" in config["sugarscapeOptions"] else None
    config = config["dataCollectionOptions"]
    totalTimesteps = config["plotTimesteps"]
    models = config["decisionModels"]
    statistic = config["plotStatistic"]
    dataset = {}
    for model in models:
        modelString = model
        if type(model) == list:
            modelString = '_'.join(model)
        dataset[modelString] = {"runs": 0, "extinct": 0, "worse": 0, "better": 0, "timesteps": 0, "aggregates": {}, "firstQuartiles": {}, "thirdQuartiles": {}, "metrics": {}}

    if not os.path.exists(path):
        print(f"Path {path} not recognized.")
        printHelp()

    dataset = parseDataset(path, dataset, totalTimesteps, statistic, skipExtinct)
    if statistic == "mean":
        dataset = findMeans(dataset)
    elif statistic == "median":
        dataset = findMedians(dataset)
    else:
        print(f"Plotting statistic {statistic} not recognized.")
        printHelp()

    generatePlots(config, models, totalTimesteps, dataset, statistic, experimentalGroup)
    printSummaryStats(dataset)
    exit(0)
