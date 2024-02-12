import getopt
import json
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
                if entry not in dataset[model]["meanMetrics"]:
                    dataset[model]["meanMetrics"][entry] = [0 for j in range(totalTimesteps + 1)]
                dataset[model]["meanMetrics"][entry][i-1] += item[entry]
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
            for i in range(len(dataset[model]["meanMetrics"][column])):
                dataset[model]["meanMetrics"][column][i] = dataset[model]["meanMetrics"][column][i] / dataset[model]["runs"]
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
    print("Model population performance:\n{0:^30} {1:^5} {2:^5} {3:^5}".format("Decision Model", "Died", "Worse", "Better"))
    for model in dataset:
        better = dataset[model]["runs"] - (dataset[model]["died"] + dataset[model]["worse"])
        print("{0:^30}: {1:^5} {2:^5} {3:^5}".format(model, dataset[model]["died"], dataset[model]["worse"], better))

def printRawData(dataset, totalTimesteps, outfile):
    file = open(outfile, 'w')
    columnHeads = "timestep"
    for model in dataset:
        for metric in ["pop", "mttl", "strv", "comd", "welt", "maad"]:
            columnHeads += " {0}_{1}".format(model, metric)
    columnHeads += '\n'
    file.write(columnHeads)

    for i in range(totalTimesteps + 1):
        line = str(i)
        for model in dataset:
            line += " {0} {1} {2} {3} {4} {5}".format(dataset[model]["meanMetrics"]["population"][i], dataset[model]["meanMetrics"]["agentMeanTimeToLive"][i],
                                                  dataset[model]["meanMetrics"]["agentStarvationDeaths"][i], dataset[model]["meanMetrics"]["agentCombatDeaths"][i],
                                                  dataset[model]["meanMetrics"]["agentWealthTotal"][i], dataset[model]["meanMetrics"]["meanAgeAtDeath"][i])
        line += '\n'
        file.write(line)
    file.close()

def generatePlots(config, models, outfile):
    if "population" in config["plots"]:
        generatePopulationPlot(models, outfile)
    if "meanttl" in config["plots"]:
        generateMeanTimeToLivePlot(models, outfile)
    if "wealth" in config["plots"]:
        generateTotalWealthPlot(models, outfile)
    if "wealthNormalized" in config["plots"]:
        generateTotalWealthNormalizedPlot(models, outfile)
    if "starvationCombat" in config["plots"]:
        generateStarvationAndCombatPlot(models, outfile)
    if "meanAgeAtDeath" in config["plots"]:
        generateMeanAgeAtDeathPlot(models, outfile)

def generatePopulationPlot(models, outfile):
    print("Generating population plot script")
    plot = open("population.plg", 'w')
    config = "set xlabel \"Timestep\"\nset ylabel \"Population\"\nset lt 1 lw 2 lc \"black\"\n"
    config += "set xtics nomirror\nset ytics nomirror\nset key fixed right bottom\nset term pdf font \"Times,20\"\nset output \"population.pdf\"\n\n"
    plot.write(config)
    i = 0
    j = len(models) - 1
    lines = ""
    for model in models:
        if i == 0:
            lines += "plot ARGV[1] using 'timestep':'{0}_pop' with linespoints pointinterval 100 pointsize 0.75  lc 'magenta' lt 1 dt 1 pt {1} title 'Utilitarian', \\\n".format(model, j)
        elif i < len(models) - 1:
            lines += "\t'' u 'timestep':'{0}_pop' with linespoints pointinterval 100 pointsize 0.75  lc 'cyan' lt 1 dt 1 pt {1} title 'Egoist', \\\n".format(model, j)
        else:
            lines += "\t'' u 'timestep':'{0}_pop' with linespoints pointinterval 100 pointsize 0.75  lc 'gold' lt 1 dt 1 pt {1} title 'Raw Sugarscape'".format(model, j)
        i += 1
        j -= 1
    plot.write(lines)
    plot.close()
    os.system("gnuplot -c population.plg {0}".format(outfile))

def generateMeanAgeAtDeathPlot(models, outfile):
    print("Generating mean age at death plot script")
    plot = open("mean_age_at_death.plg", 'w')
    config = "set xlabel \"Timestep\"\nset ylabel \"Mean Age at Death\"\nset lt 1 lw 2 lc \"black\"\n"
    config += "set xtics nomirror\nset ytics nomirror\nset key fixed right bottom\nset term pdf font \"Times,24\"\nset output \"mean_age_at_death.pdf\"\n\n"
    plot.write(config)
    i = 0
    j = len(models) - 1
    lines = ""
    for model in models:
        if i == 0:
            lines += "plot ARGV[1] using 'timestep':'{0}_maad' with linespoints pointinterval 100 pointsize 0.75  lc 'magenta' lt 1 dt 1 pt {1} title 'Utilitarian', \\\n".format(model, j)
        elif i < len(models) - 1:
            lines += "\t'' u 'timestep':'{0}_maad' with linespoints pointinterval 100 pointsize 0.75  lc 'cyan' lt 1 dt 1 pt {1} title 'Egoist', \\\n".format(model, j)
        else:
            lines += "\t'' u 'timestep':'{0}_maad' with linespoints pointinterval 100 pointsize 0.75  lc 'gold' lt 1 dt 1 pt {1} title 'Raw Sugarscape'".format(model, j)
        i += 1
        j -= 1
    plot.write(lines)
    plot.close()
    os.system("gnuplot -c mean_age_at_death.plg {0}".format(outfile))



def generateMeanTimeToLivePlot(models, outfile):
    print("Generating mean time to live plot script")
    plot = open("meanttl.plg", 'w')
    config = "set xlabel \"Timestep\"\nset ylabel \"Mean Time to Live\"\nset lt 1 lw 2 lc \"black\"\n"
    config += "set xtics nomirror\nset ytics nomirror\nset key fixed right top\nset term pdf font \"Times,20\"\nset output \"meanttl.pdf\"\n\n"
    plot.write(config)
    i = 0
    j = len(models) - 1
    lines = ""
    for model in models:
        if i == 0:
            lines += "plot ARGV[1] using 'timestep':'{0}_mttl' with linespoints pointinterval 100 pointsize 0.75  lc 'magenta' lt 1 dt 1 pt {1} title 'Utilitarian', \\\n".format(model, j)
        elif i < len(models) - 1:
            lines += "\t'' u 'timestep':'{0}_mttl' with linespoints pointinterval 100 pointsize 0.75  lc 'cyan' lt 1 dt 1 pt {1} title 'Egoist', \\\n".format(model, j)
        else:
            lines += "\t'' u 'timestep':'{0}_mttl' with linespoints pointinterval 100 pointsize 0.75  lc 'gold' lt 1 dt 1 pt {1} title 'Raw Sugarscape'".format(model, j)
        i += 1
        j -= 1
    plot.write(lines)
    plot.close()
    os.system("gnuplot -c meanttl.plg {0}".format(outfile))

def generateTotalWealthPlot(models, outfile):
    print("Generating total wealth plot script")
    plot = open("wealth.plg", 'w')
    config = "set xlabel \"Timestep\"\nset ylabel \"Total Wealth\"\nset lt 1 lw 2 lc \"black\"\n"
    config += "set xtics nomirror\nset ytics nomirror\nset key fixed right bottom\nset term pdf font \"Times,20\"\nset output \"wealth.pdf\"\n\n"
    plot.write(config)
    i = 0
    j = len(models) - 1
    lines = ""
    for model in models:
        if i == 0:
            lines += "plot ARGV[1] using 'timestep':'{0}_welt' with linespoints pointinterval 100 pointsize 0.75  lc 'magenta' lt 1 dt 1 pt {1} title 'Utilitarian', \\\n".format(model, j)
        elif i < len(models) - 1:
            lines += "\t'' u 'timestep':'{0}_welt' with linespoints pointinterval 100 pointsize 0.75  lc 'cyan' lt 1 dt 1 pt {1} title 'Egoist', \\\n".format(model, j)
        else:
            lines += "\t'' u 'timestep':'{0}_welt' with linespoints pointinterval 100 pointsize 0.75  lc 'gold' lt 1 dt 1 pt {1} title 'Raw Sugarscape'".format(model, j)
        i += 1
        j -= 1
    plot.write(lines)
    plot.close()
    os.system("gnuplot -c wealth.plg {0}".format(outfile))

def generateTotalWealthNormalizedPlot(models, outfile):
    print("Generating total wealth normalized plot script")
    plot = open("wealth_normalized.plg", 'w')
    config = "set xlabel \"Timestep\"\nset ylabel \"Total Wealth / Population\"\nset lt 1 lw 2 lc \"black\"\n"
    config += "set xtics nomirror\nset ytics nomirror\nset key fixed right bottom\nset term pdf font \"Times,20\"\nset output \"wealth_normalized.pdf\"\n\n"
    plot.write(config)
    i = 0
    j = len(models) - 1
    lines = ""
    for model in models:
        if i == 0:
            lines += "plot ARGV[1] using 'timestep':(column('{0}_welt')/column('{0}_pop')) with linespoints pointinterval 100 pointsize 0.75  lc 'magenta' lt 1 dt 1 pt {1} title 'Utilitarian', \\\n".format(model, j)
        elif i < len(models) - 1:
            lines += "\t'' u 'timestep':(column('{0}_welt')/column('{0}_pop')) with linespoints pointinterval 100 pointsize 0.75  lc 'cyan' lt 1 dt 1 pt {1} title 'Egoist', \\\n".format(model, j)
        else:
            lines += "\t'' u 'timestep':(column('{0}_welt')/column('{0}_pop')) with linespoints pointinterval 100 pointsize 0.75  lc 'gold' lt 1 dt 1 pt {1} title 'Raw Sugarscape'".format(model, j)
        i += 1
        j -= 1
    plot.write(lines)
    plot.close()
    os.system("gnuplot -c wealth_normalized.plg {0}".format(outfile))

def generateStarvationAndCombatPlot(models, outfile):
    print("Generating starvation and combat deaths plot script")
    plot = open("deaths.plg", 'w')
    config = "set xlabel \"Timestep\"\nset ylabel \"Deaths / Population\"\nset lt 1 lw 2 lc \"black\"\n"
    config += "set xtics nomirror\nset ytics nomirror\nset key fixed right top\nset term pdf font \"Times,24\"\nset output \"deaths.pdf\"\n\n"
    plot.write(config)
    i = 0
    j = len(models) - 1
    lines = ""
    for model in models:
        if i == 0:
            lines += "plot ARGV[1] using 'timestep':((column('{0}_strv') + column('{0}_comd'))/column('{0}_pop')) with linespoints pointinterval 100 pointsize 0.75  lc 'magenta' lt 1 dt 1 pt {1} title 'Utilitarian', \\\n".format(model, j)
        elif i < len(models) - 1:
            lines += "\t'' u 'timestep':((column('{0}_strv') + column('{0}_comd'))/column('{0}_pop')) with linespoints pointinterval 100 pointsize 0.75  lc 'cyan' lt 1 dt 1 pt {1} title 'Egoist', \\\n".format(model, j)
        else:
            lines += "\t'' u 'timestep':((column('{0}_strv') + column('{0}_comd'))/column('{0}_pop')) with linespoints pointinterval 100 pointsize 0.75  lc 'gold' lt 1 dt 1 pt {1} title 'Raw Sugarscape'".format(model, j)
        i += 1
        j -= 1
    plot.write(lines)
    plot.close()
    os.system("gnuplot -c deaths.plg {0}".format(outfile))

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
        dataset[model] = {"runs": 0, "died": 0, "worse": 0, "timesteps": 0, "meanMetrics": {}, "distributionMetrics": {}}

    if not os.path.exists(path):
        print("Path {0} not recognized.".format(path))
        printHelp()

    dataset = parseDataset(path, dataset, totalTimesteps)
    dataset = findMeans(dataset)
    printRawData(dataset, totalTimesteps, outfile)
    generatePlots(config, models, outfile)
    printSummaryStats(dataset)
    exit(0)
