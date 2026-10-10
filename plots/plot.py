import csv
import getopt
import json
import math
import matplotlib.pyplot
import matplotlib.ticker
import os
import re
import statistics
import sys

COLORS = {"asimov": "blue", "bentham": "magenta", "egoist": "cyan", "altruist": "gold", "none": "black", "rawSugarscape": "black", "temperance": "blue",
          "temperancePECS": "purple", "multiple": "red", "unknown": "green"}
FILLCOLORS = {"asimov": "blue", "bentham": "#FF99FF", "egoist": "#99FFFF", "altruist": "#FFFF99", "none": "#999999", "rawSugarscape": "#999999", "temperance": "blue",
          "temperancePECS": "purple", "multiple": "red", "unknown": "green"}
LABELS = {"asimov": "Asimov's Robot", "bentham": "Utilitarian", "egoist": "Egoist", "altruist": "Altruist", "none": "Raw Sugarscape", "rawSugarscape": "Raw Sugarscape",
          "temperance": "Simple Temperance", "temperancePECS": "Complex Temperance", "multiple": "Multiple", "unknown": "Unknown"}
HATCHES = {"asimov": 'O', "bentham": 'o', "egoist": 'o', "altruist": 'o', "none": '.', "rawSugarscape": '.',
           "temperance": 'x', "temperancePECS": 'x', "multiple": '*', "unknown": '*'}

def findMeans(dataset, totalTimesteps, parameter=None, parameterRange=None):
    meanString = f"Finding mean values across {totalTimesteps} timesteps"
    meanRange = range(totalTimesteps + 1)
    if parameter != None:
        meanString = f"Finding mean values across {parameterRange[1]} values for {parameter} parameter"
        meanRange = range(parameterRange[1] + 1)
    print(meanString)
    for model in dataset:
        for column in dataset[model]["metrics"]:
            for i in range(len(dataset[model]["metrics"][column])):
                if column not in dataset[model]["aggregates"]:
                    dataset[model]["aggregates"][column] = [0 for j in meanRange]
                    dataset[model]["standardDeviations"][column] = [0 for j in meanRange]
                dataset[model]["standardDeviations"][column][i] = statistics.stdev(dataset[model]["metrics"][column][i]) if len(dataset[model]["metrics"][column][i]) > 1 else 0
                dataset[model]["aggregates"][column][i] = sum(dataset[model]["metrics"][column][i]) / dataset[model]["runs"]
    return dataset

def findMedians(dataset, totalTimesteps, parameter=None, parameterRange=None):
    medianString = f"Finding median values across {totalTimesteps} timesteps"
    medianRange = range(totalTimesteps + 1)
    if parameter != None:
        medianString = f"Finding median values across {parameterRange[1]} values for {parameter} parameter"
        medianRange = range(parameterRange[1] + 1)
    print(medianString)
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
                    dataset[model]["aggregates"][column] = [0 for j in medianRange]
                    dataset[model]["firstQuartiles"][column] = [0 for j in medianRange]
                    dataset[model]["thirdQuartiles"][column] = [0 for j in medianRange]
                dataset[model]["aggregates"][column][i] = median
                dataset[model]["firstQuartiles"][column][i] = firstQuartile
                dataset[model]["thirdQuartiles"][column][i] = thirdQuartile
    return dataset

def generatePlots(config, models, totalTimesteps, dataset, statistic, experimentalGroup=None, plotGroups=False, fill=False, plotType="line", parameter=None, parameterRange=None, parameterPercentage=False):
    titleStatistic = statistic.title()
    generatePlot = generateSimpleLinePlot
    if plotType == "bar":
        generatePlot = generateSimpleBarPlot

    if "conflictHappiness" in config["plots"]:
        print(f"Generating {statistic} conflict happiness plot")
        generatePlot(models, dataset, totalTimesteps, statistic, f"{statistic}_conflict_happiness.pdf", "meanConflictHappiness", f"{titleStatistic} Conflict Happiness", "center right", percentage=False, experimentalGroup=experimentalGroup, plotGroups=plotGroups, fill=fill, parameter=parameter, parameterRange=parameterRange, parameterPercentage=parameterPercentage)
    if "deaths" in config["plots"]:
        print(f"Generating {statistic} deaths plot")
        generatePlot(models, dataset, totalTimesteps, statistic, f"{statistic}_deaths.pdf", "meanDeathsPercentage", f"{titleStatistic} Deaths", "center right", percentage=True, experimentalGroup=experimentalGroup, plotGroups=plotGroups, fill=fill, parameter=parameter, parameterRange=parameterRange, parameterPercentage=parameterPercentage)
    if "familyHappiness" in config["plots"]:
        print(f"Generating {statistic} family happiness plot")
        generatePlot(models, dataset, totalTimesteps, statistic, f"{statistic}_family_happiness.pdf", "meanFamilyHappiness", f"{titleStatistic} Family Happiness", "center right", percentage=False, experimentalGroup=experimentalGroup, plotGroups=plotGroups, fill=fill, parameter=parameter, parameterRange=parameterRange, parameterPercentage=parameterPercentage)
    if "giniCoefficient" in config["plots"]:
        print(f"Generating {statistic} Gini coefficient plot")
        generatePlot(models, dataset, totalTimesteps, statistic, f"{statistic}_gini.pdf", "giniCoefficient", f"{titleStatistic} Gini Coefficient", "center right", percentage=False, experimentalGroup=experimentalGroup, plotGroups=plotGroups, fill=fill, parameter=parameter, parameterRange=parameterRange, parameterPercentage=parameterPercentage)
    if "happiness" in config["plots"]:
        print(f"Generating {statistic} happiness plot")
        generatePlot(models, dataset, totalTimesteps, statistic, f"{statistic}_happiness.pdf", "meanHappiness", f"{titleStatistic} Happiness", "center right", percentage=False, experimentalGroup=experimentalGroup, plotGroups=plotGroups, fill=fill, parameter=parameter, parameterRange=parameterRange, parameterPercentage=parameterPercentage)
    if "healthHappiness" in config["plots"]:
        print(f"Generating {statistic} health happiness plot")
        generatePlot(models, dataset, totalTimesteps, statistic, f"{statistic}_health_happiness.pdf", "meanHealthHappiness", f"{titleStatistic} Health Happiness", "center right", percentage=False, experimentalGroup=experimentalGroup, plotGroups=plotGroups, fill=fill, parameter=parameter, parameterRange=parameterRange, parameterPercentage=parameterPercentage)
    if "lifeExpectancy" in config["plots"]:
        print(f"Generating {statistic} life expectancy plot")
        generatePlot(models, dataset, totalTimesteps, statistic, f"{statistic}_life_expectancy.pdf", "meanAgeAtDeath", f"{titleStatistic} Life Expectancy", "lower right", percentage=False, experimentalGroup=experimentalGroup, plotGroups=plotGroups, fill=fill, parameter=parameter, parameterRange=parameterRange, parameterPercentage=parameterPercentage)
    if "population" in config["plots"]:
        print(f"Generating {statistic} population plot")
        generatePlot(models, dataset, totalTimesteps, statistic, f"{statistic}_population.pdf", "population", f"{titleStatistic} Population", "lower right", percentage=False, experimentalGroup=experimentalGroup, plotGroups=plotGroups, fill=fill, parameter=parameter, parameterRange=parameterRange, parameterPercentage=parameterPercentage)
    if "selfishness" in config["plots"]:
        print(f"Generating {statistic} selfishness plot")
        generatePlot(models, dataset, totalTimesteps, statistic, f"{statistic}_selfishness.pdf", "meanSelfishness", f"{titleStatistic} Selfishness Factor", "lower center", percentage=False, experimentalGroup=experimentalGroup, plotGroups=plotGroups, fill=fill, parameter=parameter, parameterRange=parameterRange, parameterPercentage=parameterPercentage)
    if "sickness" in config["plots"]:
        print(f"Generating {statistic} sick percentage plot")
        generatePlot(models, dataset, totalTimesteps, statistic, f"{statistic}_sickness.pdf", "sickAgentsPercentage", f"{titleStatistic} Diseased Agents", "center right", percentage=True, experimentalGroup=experimentalGroup, plotGroups=plotGroups, fill=fill, parameter=parameter, parameterRange=parameterRange, parameterPercentage=parameterPercentage)
    if "socialHappiness" in config["plots"]:
        print(f"Generating {statistic} social happiness plot")
        generatePlot(models, dataset, totalTimesteps, statistic, f"{statistic}_social_happiness.pdf", "meanSocialHappiness", f"{titleStatistic} Social Happiness", "center right", percentage=False, experimentalGroup=experimentalGroup, plotGroups=plotGroups, fill=fill, parameter=parameter, parameterRange=parameterRange, parameterPercentage=parameterPercentage)
    if "totalWealth" in config["plots"]:
        print(f"Generating {statistic} total wealth plot")
        generatePlot(models, dataset, totalTimesteps, statistic, f"{statistic}_wealth.pdf", "agentWealthTotal", f"{titleStatistic} Total Wealth", "center right", percentage=False, experimentalGroup=experimentalGroup, plotGroups=plotGroups, fill=fill, parameter=parameter, parameterRange=parameterRange, parameterPercentage=parameterPercentage)
    if "tradeVolume" in config["plots"]:
        print(f"Generating {statistic} trade volume plot")
        generatePlot(models, dataset, totalTimesteps, statistic, f"{statistic}_trades.pdf", "tradeVolume", f"{titleStatistic} Trade Volume", "center right", percentage=False, experimentalGroup=experimentalGroup, plotGroups=plotGroups, fill=fill, parameter=parameter, parameterRange=parameterRange, parameterPercentage=parameterPercentage)
    if "ttl" in config["plots"]:
        print(f"Generating {statistic} time to live plot")
        generatePlot(models, dataset, totalTimesteps, statistic, f"{statistic}_ttl.pdf", "agentMeanTimeToLive", f"{titleStatistic} Time to Live", "upper right", percentage=False, experimentalGroup=experimentalGroup, plotGroups=plotGroups, fill=fill, parameter=parameter, parameterRange=parameterRange, parameterPercentage=parameterPercentage)
    if "wealth" in config["plots"]:
        print(f"Generating {statistic} wealth plot")
        generatePlot(models, dataset, totalTimesteps, statistic, f"{statistic}_wealth.pdf", "meanWealth", f"{titleStatistic} Wealth", "center right", percentage=False, experimentalGroup=experimentalGroup, plotGroups=plotGroups, fill=fill, parameter=parameter, parameterRange=parameterRange, parameterPercentage=parameterPercentage)
    if "wealthHappiness" in config["plots"]:
        print(f"Generating {statistic} wealth happiness plot")
        generatePlot(models, dataset, totalTimesteps, statistic, f"{statistic}_total_wealth_happiness.pdf", "meanWealthHappiness", f"{titleStatistic} Wealth Happiness", "center right", percentage=False, experimentalGroup=experimentalGroup, plotGroups=plotGroups, fill=fill, parameter=parameter, parameterRange=parameterRange, parameterPercentage=parameterPercentage)

def generateSimpleBarPlot(models, dataset, totalTimesteps, statistic, outfile, column, label, positioning, percentage=False, experimentalGroup=None, plotGroups=False, fill=False, parameter=None, parameterRange=None, parameterPercentage=False):
    matplotlib.pyplot.rcParams["font.family"] = "serif"
    matplotlib.pyplot.rcParams["font.size"] = 14
    figure, axes = matplotlib.pyplot.subplots()
    colors = []
    errors = []
    hatches = []
    labels = []
    values = []

    for model in dataset:
        modelString = model
        if '_' in model:
            modelString = "multiple"
        elif model not in LABELS:
            modelString = "unknown"
        if experimentalGroup != None and plotGroups == True:
            controlGroupColumn = "control" + column[0].upper() + column[1:]
            controlGroupLabel = f"Control {LABELS[modelString]}"
            experimentalGroupColumn = experimentalGroup + column[0].upper() + column[1:]
            experimentalGroupLabel = experimentalGroup[0].upper() + experimentalGroup[1:] + f" {LABELS[modelString]}"
            # Prevent key error if all seeds went extinct for model
            if column in dataset[model]["aggregates"]:
                colors.append(COLORS[modelString])
                errors.append(dataset[model]["standardDeviations"][controlGroupColumn][-1])
                hatches.append(HATCHES[modelString])
                labels.append(controlGroupLabel)
                values.append(dataset[model]["aggregates"][controlGroupColumn][-1])
                colors.append("white")
                errors.append(dataset[model]["standardDeviations"][experimentalGroupColumn][-1])
                hatches.append(HATCHES[modelString])
                labels.append(experimentalGroupLabel)
                values.append(dataset[model]["aggregates"][experimentalGroupColumn][-1])
            matplotlib.pyplot.xticks(rotation=-90, fontsize=12)
        # Prevent key error if all seeds went extinct for model
        elif column in dataset[model]["aggregates"]:
            colors.append(COLORS[modelString])
            errors.append(dataset[model]["standardDeviations"][column][-1])
            hatches.append(HATCHES[modelString])
            labels.append(LABELS[modelString])
            values.append(dataset[model]["aggregates"][column][-1])

    edgeColors = [colors[i] if colors[i] != "white" else colors[i - 1] for i in range(len(colors))]
    yMax =  max(values) + max(errors)
    yMax = math.ceil(yMax * 1.05) if yMax > 0 else yMax + 1
    axes.set(xlabel="Decision Models", ylabel=label, ylim=[0, yMax])
    axes.bar(labels, values, capsize=8, color=colors, ecolor="gray", edgecolor=edgeColors, hatch=hatches, yerr=errors)
    if percentage == True:
        axes.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter())
    figure.savefig(outfile, format="pdf", bbox_inches="tight")

def generateSimpleLinePlot(models, dataset, totalTimesteps, statistic, outfile, column, label, positioning, percentage=False, experimentalGroup=None, plotGroups=False, fill=False, parameter=None, parameterRange=None, parameterPercentage=False):
    matplotlib.pyplot.rcParams["font.family"] = "serif"
    matplotlib.pyplot.rcParams["font.size"] = 18
    figure, axes = matplotlib.pyplot.subplots()
    xRange = range(totalTimesteps + 1)
    yRange = range(totalTimesteps + 1)
    if parameter != None:
        xRange = [param for param in range(parameterRange[0], parameterRange[1] + 1, parameterRange[2])]
        yRange = range(((parameterRange[1] - parameterRange[0]) // parameterRange[2]) + 1)
        # Undo integer conversions from dataset parsing
        if parameterPercentage == True:
            parameterRange = [i / 100.0 for i in parameterRange]
            xRange = [x / 100.0 for x in xRange]
        axes.set(xlabel=parameter, ylabel=label, xlim=[parameterRange[0], parameterRange[1]])
        matplotlib.pyplot.xticks(ticks=xRange)
    else:
        axes.set(xlabel="Timestep", ylabel=label, xlim=[0, totalTimesteps])
    x = [i for i in xRange]
    y = [0 for i in yRange]
    lines = []

    for model in dataset:
        modelString = model
        if '_' in model:
            modelString = "multiple"
        elif model not in LABELS:
            modelString = "unknown"
        if experimentalGroup != None and plotGroups == True:
            controlGroupColumn = "control" + column[0].upper() + column[1:]
            controlGroupLabel = f"Control {LABELS[modelString]}"
            experimentalGroupColumn = experimentalGroup + column[0].upper() + column[1:]
            experimentalGroupLabel = experimentalGroup[0].upper() + experimentalGroup[1:] + f" {LABELS[modelString]}"
            # Prevent key error if all seeds went extinct for model
            if column in dataset[model]["aggregates"]:
                yControl = [dataset[model]["aggregates"][controlGroupColumn][i] for i in yRange]
                axes.plot(x, yControl, color=COLORS[modelString], label=controlGroupLabel)
                yExperimental = [dataset[model]["aggregates"][experimentalGroupColumn][i] for i in yRange]
                axes.plot(x, yExperimental, color=COLORS[modelString], label=experimentalGroupLabel, linestyle="dotted")
                if fill == True and statistic == "mean":
                    fillAboveControl = [yControl[i] + dataset[model]["standardDeviations"][controlGroupColumn][i] for i in yRange]
                    fillBelowControl = [max(0, yControl[i] - dataset[model]["standardDeviations"][controlGroupColumn][i]) for i in yRange]
                    axes.fill_between(x, fillBelowControl, fillAboveControl, color=FILLCOLORS[modelString], alpha=0.75)
                    fillAboveExperimental = [yExperimental[i] + dataset[model]["standardDeviations"][experimentalGroupColumn][i] for i in yRange]
                    fillBelowExperimental = [max(0, yExperimental[i] - dataset[model]["standardDeviations"][experimentalGroupColumn][i]) for i in yRange]
                    axes.fill_between(x, fillBelowExperimental, fillAboveExperimental, color=FILLCOLORS[modelString], alpha=0.25)
                elif fill == True and statistic == "median":
                    fillAboveControl = [dataset[model]["thirdQuartiles"][controlGroupColumn][i] for i in yRange]
                    fillBelowControl = [dataset[model]["firstQuartiles"][controlGroupColumn][i] for i in yRange]
                    fillAboveExperimental = [dataset[model]["thirdQuartiles"][experimentalGroupColumn][i] for i in yRange]
                    fillBelowExperimental = [dataset[model]["firstQuartiles"][experimentalGroupColumn][i] for i in yRange]
                    axes.fill_between(x, fillBelowControl, fillAboveControl, color=FILLCOLORS[modelString], alpha=0.75)
                    axes.fill_between(x, fillBelowExperimental, fillAboveExperimental, color=FILLCOLORS[modelString], alpha=0.25)
        # Prevent key error if all seeds went extinct for model
        elif column in dataset[model]["aggregates"]:
            y = [dataset[model]["aggregates"][column][i] for i in yRange]
            axes.plot(x, y, color=COLORS[modelString], label=LABELS[modelString])
            if fill == True and statistic == "mean":
                fillAbove = [y[i] + dataset[model]["standardDeviations"][column][i] for i in yRange]
                fillBelow = [max(0, y[i] - dataset[model]["standardDeviations"][column][i]) for i in yRange]
                axes.fill_between(x, fillBelow, fillAbove, color=FILLCOLORS[modelString], alpha=0.75)
            elif fill == True and statistic == "median":
                fillAbove = [dataset[model]["thirdQuartiles"][column][i] for i in yRange]
                fillBelow = [dataset[model]["firstQuartiles"][column][i] for i in yRange]
                axes.fill_between(x, fillBelow, fillAbove, color=FILLCOLORS[modelString], alpha=0.75)
        axes.set_ylim(bottom=0)
        axes.legend(loc=positioning, labelspacing=0.1, frameon=False, fontsize=16)
    if percentage == True:
        axes.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter())
    figure.savefig(outfile, format="pdf", bbox_inches="tight")

def parseDataset(path, dataset, totalTimesteps, statistic, skipExtinct=False, parameter=None, parameterRange=None):
    encodedDir = os.fsencode(path)
    files = [f for f in os.listdir(encodedDir) if os.fsdecode(f).endswith("json") or os.fsdecode(f).endswith(".csv")]
    printFileLength = len(max(files, key=len))
    fileCount = 1
    totalFiles = len(files)
    datasetRange = range(parameterRange[1] + 1) if parameter != None else range(totalTimesteps + 1)
    for file in files:
        filename = os.fsdecode(file)
        filePath = path + filename
        fileDecisionModel = re.compile(r"^([A-z]*)\.?(\d+[A-z]+)?\.(\d*)\.(json|csv)")
        fileSearch = re.search(fileDecisionModel, filename)
        if fileSearch == None:
            continue
        model = fileSearch.group(1)
        if model not in dataset:
            continue
        param = fileSearch.group(2)
        paramValue = 0
        paramPresent = parameter != None and param != None
        if paramPresent == True:
            paramExpr = re.compile(r"(\d+)([A-z]+)")
            paramSearch = re.search(paramExpr, param)
            paramString = paramSearch.group(1)
            paramValue = int(paramString)
            param = paramSearch.group(2)
            if param != parameter:
                continue
        seed = fileSearch.group(3)
        log = open(filePath)
        printProgress(filename, fileCount, totalFiles, printFileLength)
        fileCount += 1
        rawData = None
        if filename.endswith(".json"):
            rawData = json.loads(log.read())
        else:
            rawData = list(csv.DictReader(log))

        if parameter != None and paramString not in dataset[model][parameter]:
            dataset[model][parameter][paramString] = {"extinct": 0, "worse": 0, "better": 0}

        if int(rawData[-1]["population"]) == 0:
            dataset[model]["extinct"] += 1
            if parameter != None:
                dataset[model][parameter][paramString]["extinct"] += 1
            if skipExtinct == True:
                continue
        elif int(rawData[-1]["population"]) <= int(rawData[0]["population"]):
            dataset[model]["worse"] += 1
            if parameter != None:
                dataset[model][parameter][paramString]["worse"] += 1
        else:
            dataset[model]["better"] += 1
            if parameter != None:
                dataset[model][parameter][paramString]["better"] += 1
        dataset[model]["runs"] += 1

        if paramPresent == True:
            i = len(rawData) - 1
            item = rawData[i]
            while int(item["timestep"]) > totalTimesteps:
                i -= 1
                item = rawData[i]
            for entry in item:
                if entry in ["agentWealths", "agentTimesToLive", "agentTimesToLiveAgeLimited", "agentTotalMetabolism"]:
                        continue
                if entry not in dataset[model]["metrics"]:
                    dataset[model]["metrics"][entry] = [[] for j in datasetRange]
                if item[entry] == "None":
                    item[entry] = 0
                dataset[model]["metrics"][entry][paramValue].append(float(item[entry]))
        else:
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
                        dataset[model]["metrics"][entry] = [[] for j in datasetRange]
                    if item[entry] == "None":
                        item[entry] = 0
                    dataset[model]["metrics"][entry][i - 1].append(float(item[entry]))
                i += 1

    if paramPresent == True:
        for model in dataset:
            for column in dataset[model]["metrics"]:
                clippedColumn = []
                for i in range(len(dataset[model]["metrics"][column])):
                    inParameterRange = i >= parameterRange[0] and i <= parameterRange[1] and i % parameterRange[2] == 0
                    if inParameterRange == True:
                        clippedColumn.append(dataset[model]["metrics"][column][i])
                dataset[model]["metrics"][column] = clippedColumn

    print(f"\r{' ' * os.get_terminal_size().columns}", end='\r')
    for model in dataset:
        if dataset[model]["runs"] == 0:
            print(f"No simulation runs found for the {model} decision model")
    return dataset

def parseOptions():
    commandLineArgs = sys.argv[1:]
    shortOptions = "c:p:s:t:h"
    longOptions = ("conf=", "groups", "path=", "help", "skip", "type=")
    options = {"config": None, "path": None, "plotGroups": False, "plotType": "line", "skip": False}
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
        elif currArg in ("-g", "--groups"):
            options["plotGroups"] = True
        elif currArg in ("-p", "--path"):
            options["path"] = currVal
            if currVal == "":
                print("No dataset path provided.")
                printHelp()
        elif currArg in ("-h", "--help"):
            printHelp()
        elif currArg in ("-s", "--skip"):
            options["skip"] = True
        elif currArg in ("-t", "--type"):
            if currVal == "":
                print("No plot type provided.")
                printHelp()
            options["plotType"] = currVal
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
    print("Usage:\n\tpython plot.py --path /path/to/data --conf /path/to/config > results.dat\n\nOptions:\n\t-c,--conf\tUse the specified path to configurable settings file.\n\t-p,--path\tUse the specified path to find dataset JSON files.\n\t-s,--skip\tSkip including extinct societies in produced graphs.\n\t-t,--type\tUse the specified plot type when generating plots.\n\t-h,--help\tDisplay this message.")
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

def printSummaryStats(dataset, parameter=None):
    summaryString = f"Model population performance:\n{'Decision Model':^30} {'Extinct':^5} {'Worse':^5} {'Better':^5}\n"
    parameterSummaryString = f"Model population performance per parameter:\n{'Decision Model':^30} {'Extinct':^5} {'Worse':^5} {'Better':^5}\n"
    for model in dataset:
        summaryString += f"{model:^30} {dataset[model]['extinct']:^5} {dataset[model]['worse']:^5} {dataset[model]['better']:^5}\n"
        if parameter != None:
            for value in dataset[model][parameter]:
                parameterSummaryString += f"{model + '.' + value:^30} {dataset[model][parameter][value]['extinct']:^5} {dataset[model][parameter][value]['worse']:^5} {dataset[model][parameter][value]['better']:^5}\n"

    print(summaryString)
    if parameter != None:
        print(parameterSummaryString)

if __name__ == "__main__":
    options = parseOptions()
    path = options["path"]
    plotGroups = options["plotGroups"]
    plotType = options["plotType"]
    config = options["config"]
    skipExtinct = options["skip"]
    configFile = open(config)
    config = json.loads(configFile.read())
    configFile.close()
    experimentalGroup = config["sugarscapeOptions"]["experimentalGroup"] if "experimentalGroup" in config["sugarscapeOptions"] else None
    config = config["dataCollectionOptions"]
    parameter = config["parameterSweep"] if "parameterSweep" in config else None
    parameterPercentage = config["parameterPercentage"] if "parameterPercentage" in config else False
    parameterRange = config["parameterRange"] if "parameterRange" in config else None
    # Ensure plotting by parameter only happens if both the parameter and its range are fully specified
    if parameter == None or parameterRange == None or len(parameterRange) < 2:
        parameter = None
        parameterPercentage = False
        parameterRange = None
    # Convert percentage-based parameters to integers for easy parsing
    if parameterPercentage == True and parameterRange != None:
        parameterRange = [int(i * 100) for i in parameterRange]

    plotGroups = config["plotGroups"] if "plotGroups" in config else plotGroups
    plotType = config["plotType"] if "plotType" in config else plotType
    fill = config["plotFill"] if "plotFill" in config else False
    totalTimesteps = config["plotTimesteps"]
    models = config["decisionModels"]
    statistic = config["plotStatistic"]
    dataset = {}
    for model in models:
        modelString = model
        if type(model) == list:
            modelString = '_'.join(model)
        dataset[modelString] = {"runs": 0, "extinct": 0, "worse": 0, "better": 0, "timesteps": 0, "aggregates": {}, "firstQuartiles": {}, "thirdQuartiles": {}, "standardDeviations": {}, "metrics": {}}
        if parameter != None:
            dataset[modelString][parameter] = {}

    if not os.path.exists(path):
        print(f"Path {path} not recognized.")
        printHelp()

    dataset = parseDataset(path, dataset, totalTimesteps, statistic, skipExtinct, parameter, parameterRange)
    if statistic == "mean":
        dataset = findMeans(dataset, totalTimesteps, parameter, parameterRange)
    elif statistic == "median":
        dataset = findMedians(dataset, totalTimesteps, parameter, parameterRange)
    else:
        print(f"Plotting statistic {statistic} not recognized.")
        printHelp()

    generatePlots(config, models, totalTimesteps, dataset, statistic, experimentalGroup, plotGroups, fill, plotType, parameter, parameterRange, parameterPercentage)
    printSummaryStats(dataset, parameter)
    exit(0)
