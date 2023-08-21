import os
import sys
import getopt
import re
import json

# Decision models each represented by a dictionary containing the mean of all seeds in the dataset
dataset = {"benthamHalfLookaheadBinary": {"runs": 0, "died": 0, "worse": 0, "timesteps": 0, "meanMetrics": {}, "distributionMetrics": {}},
           "benthamHalfLookaheadTop": {"runs": 0, "died": 0, "worse": 0, "timesteps": 0, "meanMetrics": {}, "distributionMetrics": {}},
           "benthamNoLookaheadBinary": {"runs": 0, "died": 0, "worse": 0, "timesteps": 0, "meanMetrics": {}, "distributionMetrics": {}},
           "benthamNoLookaheadTop": {"runs": 0, "died": 0, "worse": 0, "timesteps": 0, "meanMetrics": {}, "distributionMetrics": {}},
           "egoisticHalfLookaheadBinary": {"runs": 0, "died": 0, "worse": 0, "timesteps": 0, "meanMetrics": {}, "distributionMetrics": {}},
           "egoisticHalfLookaheadTop": {"runs": 0, "died": 0, "worse": 0, "timesteps": 0, "meanMetrics": {}, "distributionMetrics": {}},
           "egoisticNoLookaheadBinary": {"runs": 0, "died": 0, "worse": 0, "timesteps": 0, "meanMetrics": {}, "distributionMetrics": {}},
           "egoisticNoLookaheadTop": {"runs": 0, "died": 0, "worse": 0, "timesteps": 0, "meanMetrics": {}, "distributionMetrics": {}},
           "rawSugarscape": {"runs": 0, "died": 0, "worse": 0, "timesteps": 0, "meanMetrics": {}, "distributionMetrics": {}}
           }

datacols = []

def parseDataset(path, totalTimesteps):
    encodedDir = os.fsencode(path) 
    for file in os.listdir(encodedDir):
        filename = os.fsdecode(file)
        if not filename.endswith('.json'):
            continue
        filePath = path + filename
        fileDecisionModel = re.compile(r"([A-z]*)\d*\.json")
        model = re.search(fileDecisionModel, filename).group(1)
        log = open(filePath)
        rawJson = json.loads(log.read())
        dataset[model]["runs"] += 1
        i = 1
        print("Reading log {0}".format(filePath), file=sys.stderr)
        for item in rawJson:
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

def findMeans():
    print("Finding mean values across {0} timesteps".format(totalTimesteps), file=sys.stderr)
    for model in dataset:
        for column in datacols:
            for i in range(len(dataset[model]["meanMetrics"][column])):
                dataset[model]["meanMetrics"][column][i] = dataset[model]["meanMetrics"][column][i] / dataset[model]["runs"]

def parseOptions():
    commandLineArgs = sys.argv[1:]
    shortOptions = "p:t:h"
    longOptions = ("path", "help", "time")
    options = {"path": None, "timesteps": 1000}
    try:
        args, vals = getopt.getopt(commandLineArgs, shortOptions, longOptions)
    except getopt.GetoptError as err:
        print(err, file=sys.stderr)
        exit(0)
    for currArg, currVal in args:
        if currArg in ("-p", "--path"):
            options["path"] = currVal
        elif currArg in ("-t", "--time"):
            options["timesteps"] = int(currVal)
        elif currArg in ("-h", "--help"):
            printHelp()
    if options["path"] == None:
        print("No path specified.")
        printHelp()
    return options

def printHelp():
    print("Usage:\n\tpython parselogs.py --path /path/to/data > results.dat\n\nOptions:\n\t-p,--path\tUse the specified path to find dataset JSON files.\n\t-h,--help\tDisplay this message.")
    exit(0)

def printSummaryStats():
    print("Model population performance:\n{0:^30} {1:^5} {2:^5} {3:^5}".format("Decision Model", "Died", "Worse", "Better"), file=sys.stderr)
    for model in dataset:
        better = dataset[model]["runs"] - (dataset[model]["died"] + dataset[model]["worse"])
        print("{0:^30}: {1:^5} {2:^5} {3:^5}".format(model, dataset[model]["died"], dataset[model]["worse"], better), file=sys.stderr)

def printRawData(totalTimesteps):
    columnHeads = "timestep"
    for model in ["bhlb", "bhlt", "bnlb", "bnlt", "ehlb", "ehlt", "enlb", "enlt", "rs"]:
        for metric in ["pop", "mttl", "strv", "comd", "welt"]:
            columnHeads += " {0}_{1}".format(model, metric)
    print(columnHeads)
    bhlb = dataset["benthamHalfLookaheadBinary"]["meanMetrics"]
    bhlt = dataset["benthamHalfLookaheadTop"]["meanMetrics"]
    bnlb = dataset["benthamNoLookaheadBinary"]["meanMetrics"]
    bnlt = dataset["benthamNoLookaheadBinary"]["meanMetrics"]
    ehlb = dataset["egoisticHalfLookaheadBinary"]["meanMetrics"]
    ehlt = dataset["egoisticHalfLookaheadTop"]["meanMetrics"]
    enlb = dataset["egoisticNoLookaheadBinary"]["meanMetrics"]
    enlt = dataset["egoisticNoLookaheadBinary"]["meanMetrics"] 
    rs = dataset["rawSugarscape"]["meanMetrics"]

    models = [bhlb, bhlt, bnlb, bnlt, ehlb, ehlt, enlb, enlt, rs]
    for i in range(totalTimesteps + 1):
        line = str(i)
        for model in models:
            line += " {0} {1} {2} {3} {4}".format(model["population"][i], model["agentMeanTimeToLive"][i], model["agentStarvationDeaths"][i],
                                                  model["agentCombatDeaths"][i], model["agentWealthTotal"][i])
        print(line)

def generatePlots():
    generatePopulationPlot()
    generateMeanTimeToLivePlot()
    generateTotalWealthPlot()
    generateTotalWealthNormalizedPlot()
    generateStarvationAndCombatPlot()

def generatePopulationPlot():
    print("Generating population plot script", file=sys.stderr)
    plot = open("population.plg", 'w')
    config = "set title \"Population per Timestep\"\nset xlabel \"Timestep\"\nset ylabel \"Population\"\nset lt 1 lw 2 lc \"black\"\n"
    config += "set xtics nomirror\nset ytics nomirror\nset key fixed right bottom\nset term pdf mono\nset output \"population.pdf\"\n\n"
    plot.write(config)
    lines = "plot ARGV[1] using 'timestep':'bhlb_pop' with linespoints pointinterval 100 pointsize 0.75  lt 1 dt 1 pt 2 title 'Utilitarian', \\\n"
    lines += "\t'' u 'timestep':'ehlb_pop' with linespoints pointinterval 100 pointsize 0.75  lt 1 dt 1 pt 1 title 'Egoist', \\\n"
    lines += "\t'' u 'timestep':'rs_pop' with linespoints pointinterval 100 pointsize 0.75  lt 1 dt 1 pt 0 title 'Raw Sugarscape'"
    plot.write(lines)
    plot.close()

def generateMeanTimeToLivePlot():
    print("Generating mean time to live plot script", file=sys.stderr)
    plot = open("meanttl.plg", 'w')
    config = "set title \"Mean Time to Live per Timestep\"\nset xlabel \"Timestep\"\nset ylabel \"Mean Time to Live\"\nset lt 1 lw 2 lc \"black\"\n"
    config += "set xtics nomirror\nset ytics nomirror\nset key fixed right top\nset term pdf mono\nset output \"meanttl.pdf\"\n\n"
    plot.write(config)
    lines = "plot ARGV[1] using 'timestep':'bhlb_mttl' with linespoints pointinterval 100 pointsize 0.75  lt 1 dt 1 pt 2 title 'Utilitarian', \\\n"
    lines += "\t'' u 'timestep':'ehlb_mttl' with linespoints pointinterval 100 pointsize 0.75  lt 1 dt 1 pt 1 title 'Egoist', \\\n"
    lines += "\t'' u 'timestep':'rs_mttl' with linespoints pointinterval 100 pointsize 0.75  lt 1 dt 1 pt 0 title 'Raw Sugarscape'"
    plot.write(lines)
    plot.close()

def generateTotalWealthPlot():
    print("Generating total wealth plot script", file=sys.stderr)
    plot = open("wealth.plg", 'w')
    config = "set title \"Agent Total Wealth per Timestep\"\nset xlabel \"Timestep\"\nset ylabel \"Total Wealth\"\nset lt 1 lw 2 lc \"black\"\n"
    config += "set xtics nomirror\nset ytics nomirror\nset key fixed right bottom\nset term pdf mono\nset output \"wealth.pdf\"\n\n"
    plot.write(config)
    lines = "plot ARGV[1] using 'timestep':'bhlb_welt' with linespoints pointinterval 100 pointsize 0.75  lt 1 dt 1 pt 2 title 'Utilitarian', \\\n"
    lines += "\t'' u 'timestep':'ehlb_welt' with linespoints pointinterval 100 pointsize 0.75  lt 1 dt 1 pt 1 title 'Egoist', \\\n"
    lines += "\t'' u 'timestep':'rs_welt' with linespoints pointinterval 100 pointsize 0.75  lt 1 dt 1 pt 0 title 'Raw Sugarscape'"
    plot.write(lines)
    plot.close()

def generateTotalWealthNormalizedPlot():
    print("Generating total wealth normalized plot script", file=sys.stderr)
    plot = open("wealth_normalized.plg", 'w')
    config = "set title \"Agent Total Wealth per Timestep Normalized by Population\"\nset xlabel \"Timestep\"\nset ylabel \"Total Wealth / Population\"\nset lt 1 lw 2 lc \"black\"\n"
    config += "set xtics nomirror\nset ytics nomirror\nset key fixed right bottom\nset term pdf mono\nset output \"wealth_normalized.pdf\"\n\n"
    plot.write(config)
    lines = "plot ARGV[1] using 'timestep':(column('bhlb_welt')/column('bhlb_pop')) with linespoints pointinterval 100 pointsize 0.75  lt 1 dt 1 pt 2 title 'Utilitarian', \\\n"
    lines += "\t'' u 'timestep':(column('ehlb_welt')/column('ehlb_pop')) with linespoints pointinterval 100 pointsize 0.75  lt 1 dt 1 pt 1 title 'Egoist', \\\n"
    lines += "\t'' u 'timestep':(column('rs_welt')/column('rs_pop')) with linespoints pointinterval 100 pointsize 0.75  lt 1 dt 1 pt 0 title 'Raw Sugarscape'"
    plot.write(lines)
    plot.close()

def generateStarvationAndCombatPlot():
    print("Generating starvation and combat deaths plot script", file=sys.stderr)
    plot = open("starvation_combat.plg", 'w')
    config = "set title \"Starvation and Combat Deaths per Timestep Normalized by Population\"\nset xlabel \"Timestep\"\nset ylabel \"Deaths / Population\"\nset lt 1 lw 2 lc \"black\"\n"
    config += "set xtics nomirror\nset ytics nomirror\nset key fixed right top\nset term pdf mono\nset output \"starvation_combat.pdf\"\n\n"
    plot.write(config)
    lines = "plot ARGV[1] using 'timestep':((column('bhlb_strv') + column('bhlb_comd'))/column('bhlb_pop')) with linespoints pointinterval 100 pointsize 0.75  lt 1 dt 1 pt 2 title 'Utilitarian Starvation and Combat Death', \\\n"
    lines += "\t'' u 'timestep':((column('ehlb_strv') + column('ehlb_comd'))/column('ehlb_pop')) with linespoints pointinterval 100 pointsize 0.75  pt 2 title 'Egoist Starvation and Combat Death', \\\n"
    lines += "\t'' u 'timestep':((column('rs_strv') + column('rs_comd'))/column('rs_pop')) with linespoints pointinterval 100 pointsize 0.75  lt 1 dt 1 pt 1 title 'Raw Sugarscape Starvation and Combat Death'"
    plot.write(lines)
    plot.close()

if __name__ == "__main__":
    options = parseOptions()
    path = options["path"]
    totalTimesteps = options["timesteps"]
    if (not os.path.exists(path)):
        raise Exception("Path {0} not recognized".format(path))
    parseDataset(path, totalTimesteps)
    findMeans()
    printRawData(totalTimesteps)
    generatePlots()
    printSummaryStats()
    exit(0)
