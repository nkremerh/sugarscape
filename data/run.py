import getopt
import json
import os
import random
import re
import sys

def createConfigurations(config, path):
    print("Generating configurations for random seeds.")
    if path[-1] != '/':
        path = path + '/'
    seeds = []
    for i in range(config["numSeeds"]):
        seed = random.randint(0, sys.maxsize)
        while seed in seeds:
            seed = random.randint(0, sys.maxsize)
        seeds.append(seed)
    for seed in seeds:
        for model in config["decisionModels"]:
            simOpts = config["sugarscapeOptions"]
            simOpts["agentEthicalTheory"] = model
            simOpts["seed"] = seed
            simOpts["logfile"] = "{0}{1}{2}.json".format(path, model, seed)
            # Enforce noninteractive, no-output mode
            simOpts["headlessMode"] = True
            simOpts["debugMode"] = ["none"]
            conf = open("{0}{1}{2}.config".format(path, model, seed), 'w')
            conf.write(json.dumps(simOpts))
            conf.close()

def parseOptions():
    commandLineArgs = sys.argv[1:]
    shortOptions = "c:p:t:h"
    longOptions = ("conf=", "path=", "help")
    options = {"config": None, "path": None}
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
                print("No path provided.")
                printHelp()
        elif currArg in ("-h", "--help"):
            printHelp()
    if options["config"] == None:
        print("Configuration file path required.")
        printHelp()
    return options

def printHelp():
    print("Usage:\n\tpython run.py --conf /path/to/config\n\nOptions:\n\t-c,--conf\tUse the specified path to configurable settings file.\n\t-p,--path\tUse the specified directory path to store dataset JSON files.\n\t-h,--help\tDisplay this message.")
    exit(0)

def runSimulations(config, path):
    encodedDir = os.fsencode(path) 
    configs = []
    for file in os.listdir(encodedDir):
        filename = os.fsdecode(file)
        if not filename.endswith('.config'):
            continue
        filePath = path + filename
        fileDecisionModel = re.compile(r"([A-z]*)\d*\.config")
        model = re.search(fileDecisionModel, filename).group(1)
        if model not in config["decisionModels"]:
            continue
        configs.append(filePath)

    shell = "files=("
    for conf in configs:
        shell += " {0}".format(conf)
    shell += " )\n\n"
    shell += "# Number of parallel processes to run\nN={0}\n\n".format(config["numParallelSimJobs"])
    shell += "i=1\nj=${#files[@]}\nfor f in \"${files[@]}\"\ndo\n"
    shell += "echo \"Running decision model $f ($i/$j)\"\n# Run simulation for config\n"
    shell += "{0} ../sugarscape.py --conf $f &\n\n".format(config["pathToPython"])
    shell += "if [[ $(jobs -r -p | wc -l) -ge $N ]]; then\nwait -n\nfi\ni=$((i+1))\ndone\n\n"
    shell += "sem=0\necho \"Waiting for jobs to finish up.\"\nwhile [[ $(jobs -r -p | wc -l) -gt 0 ]];\ndo\n"
    shell += "sem=$(((sem+1)%{0}))\nif [[ $sem -eq 0 ]]; then\n".format(config["jobUpdateFrequency"])
    shell += "status=$( ps -AF | grep 'sugarscape' | wc -l )\nstatus=$((status-1))\n"
    shell += "echo -n $status\necho ' jobs remaining.'\nfi\nwait -n\ndone\n"

    sh = open("temp.sh", 'w')
    sh.write(shell)
    sh.close()
    os.system("{0} temp.sh".format(config["pathToBash"]))
    os.remove("temp.sh")

    for config in configs:
        os.remove(config)

if __name__ == "__main__":
    options = parseOptions()
    path = options["path"]
    if path == None:
        path = "./"
    if not os.path.exists(path):
        print("Path {0} not recognized.".format(path))
        printHelp()

    config = options["config"]
    configFile = open(config)
    config = json.loads(configFile.read())
    configFile.close()

    createConfigurations(config, path)
    runSimulations(config, path)

    exit(0)
