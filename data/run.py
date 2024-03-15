import getopt
import json
import os
import os.path
import random
import re
import sys

def createConfigurations(config, path):
    configs = getJobsToDo(config, path)
    if len(configs) == 0:
        print("Generating new configurations for random seeds.")
        if path[-1] != '/':
            path = path + '/'
        dataOpts = config["configurationOptions"]
        variableOpts = config["dataCollectionOptions"]
        seeds = generateSeeds(dataOpts)
        confFiles = []

        if len(variableOpts) == 1:
            for seed in seeds:
                for variable in variableOpts:
                    for val in variableOpts[variable]:
                        simOpts = config["sugarscapeOptions"]
                        simOpts[variable] = val
                        simOpts["seed"] = seed
                        if type(val) is list:
                            simOpts["logfile"] = "{0}{1}{2}.json".format(path, variable, val[0], seed)
                        else:
                            simOpts["logfile"] = "{0}{1}{2}.json".format(path, variable, val, seed)                   
                        # Enforce noninteractive, no-output mode
                        simOpts["headlessMode"] = True
                        simOpts["debugMode"] = ["none"]
                        if type(val) is list:
                            confFilePath = "{0}{1}{2}.config".format(path, variable, val[0], seed)
                        else:
                            confFilePath = "{0}{1}{2}.config".format(path, variable, val, seed)                            
                        confFiles.append(confFilePath)
                        conf = open(confFilePath, 'w')
                        conf.write(json.dumps(simOpts))
                        conf.close()
        else:
            for seed in seeds:
                innerList = variableOpts.copy()
                for variable in variableOpts:
                    #if len(innerList) == 0:
                    #    continue
                    if variable in innerList:
                        del innerList[variable]
                    for val in variableOpts[variable]:
                        for variable2 in innerList:
                            for val2 in innerList[variable2]:
                                print(variable, " ", val, " ", variable2, " ", val2)
                                simOpts = config["sugarscapeOptions"]
                                simOpts[variable] = val
                                simOpts[variable2] = val2
                                simOpts["seed"] = seed
                                if type(val) is list and type(val2) is list:
                                    simOpts["logfile"] = "{0}{1}{2}.json".format(path, val[0], val2[0], seed)
                                else:
                                    simOpts["logfile"] = "{0}{1}{2}.json".format(path,variable, val, variable2, seed)                   
                                # Enforce noninteractive, no-output mode
                                simOpts["headlessMode"] = True
                                simOpts["debugMode"] = ["none"]
                                if type(val) is list and type(val2) is list:
                                    confFilePath = "{0}{1}{2}.config".format(path, val[0], val2[0], seed)
                                else:
                                    confFilePath = "{0}{1}{2}.config".format(path,variable, val, variable2, seed)
                                confFiles.append(confFilePath)
                                conf = open(confFilePath, 'w')
                                conf.write(json.dumps(simOpts))
                                conf.close()
        return confFiles
    return configs

def generateSeeds(config):
    seeds = []
    for i in range(config["numSeeds"]):
        seed = random.randint(0, sys.maxsize)
        while seed in seeds:
            seed = random.randint(0, sys.maxsize)
        seeds.append(seed)
    return seeds

def getJobsToDo(config, path):
    print("Searching for incomplete logs from previously created seeds.")
    encodedDir = os.fsencode(path)
    dataOpts = config["configurationOptions"]
    simOpts = config["sugarscapeOptions"]
    configs = []
    for file in os.listdir(encodedDir):
        filename = os.fsdecode(file)
        if not filename.endswith('.config'):
            continue
        filePath = path + filename
        fileDecisionModel = re.compile(r"([A-z]*)\d*\.config")
        model = re.search(fileDecisionModel, filename).group(1)
        if model not in dataOpts["decisionModels"]:
            continue
        configs.append(filePath)
    completedRuns = []
    for config in configs:
        configFile = open(config)
        log = json.loads(configFile.read())["logfile"]
        configFile.close()
        if os.path.exists(log) == False:
            continue
        try:
            logFile = open(log)
            lastEntry = json.loads(logFile.read())[-1]
            if lastEntry["timestep"] == simOpts["timesteps"] or lastEntry["population"] == 0:
                completedRuns.append(config)
            else:
                print("Existing log {0} is incomplete. Adding it to be rerun.".format(log))
            logFile.close()
        except:
            print("Existing log {0} is incomplete. Adding it to be rerun.".format(log))
            continue
    for run in completedRuns:
        configs.remove(run)
    for config in configs:
        print("Configuration file {0} has no matching log. Adding it to be rerun".format(config))
    if len(configs) == 0:
        print("No incomplete logs found.")
    return configs

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

def runSimulations(config, configFiles, path):
    dataOpts = config["configurationOptions"]

    shell = "files=("
    for conf in configFiles:
        shell += " {0}".format(conf)
    shell += " )\n\n"
    shell += "# Number of parallel processes to run\nN={0}\n\n".format(dataOpts["numParallelSimJobs"])
    shell += "i=1\nj=${#files[@]}\nfor f in \"${files[@]}\"\ndo\n"
    shell += "echo \"Running decision model $f ($i/$j)\"\n# Run simulation for config\n"
    shell += "{0} ../sugarscape.py --conf $f &\n\n".format(dataOpts["pathToPython"])
    shell += "if [[ $(jobs -r -p | wc -l) -ge $N ]]; then\nwait -n\nfi\ni=$((i+1))\ndone\n\n"
    shell += "sem=0\necho \"Waiting for jobs to finish up.\"\nwhile [[ $(jobs -r -p | wc -l) -gt 0 ]];\ndo\n"
    shell += "sem=$(((sem+1)%{0}))\nif [[ $sem -eq 0 ]]; then\n".format(dataOpts["jobUpdateFrequency"])
    shell += "status=$( ps -AF | grep 'sugarscape' | wc -l )\nstatus=$((status-1))\n"
    shell += "echo -n $status\necho ' jobs remaining.'\nfi\nwait -n\ndone\n"

    sh = open("temp.sh", 'w')
    sh.write(shell)
    sh.close()
    os.system("{0} temp.sh".format(dataOpts["pathToBash"]))
    os.remove("temp.sh")

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

    if "configurationOptions" not in config:
        print("Configuration file must have specific data collection options in order to run automated data collection.")
        exit(1)

    configFiles = createConfigurations(config, path)
    runSimulations(config, configFiles, path)

    exit(0)
