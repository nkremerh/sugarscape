import getopt
import json
import multiprocessing
import os
import random
import re
import sys

def createConfigurations(config, path):
    configs = getJobsToDo(config, path)
    if len(configs) == 0:
        print("Generating new configurations for random seeds.")
        if path[-1] != '/':
            path = path + '/'
        dataOpts = config["dataCollectionOptions"]
        seeds = generateSeeds(dataOpts)
        confFiles = []
        for seed in seeds:
            for model in dataOpts["decisionModels"]:
                modelString = model
                if type(model) == list:
                    modelString = '_'.join(model)
                simOpts = config["sugarscapeOptions"]
                simOpts["agentDecisionModels"] = model
                simOpts["seed"] = seed
                simOpts["logfile"] = f"{path}{modelString}{seed}.json"
                # Enforce noninteractive, no-output mode
                simOpts["headlessMode"] = True
                simOpts["debugMode"] = ["none"]
                confFilePath = f"{path}{modelString}{seed}.config"
                confFiles.append(confFilePath)
                conf = open(confFilePath, 'w')
                conf.write(json.dumps(simOpts))
                conf.close()
        return confFiles
    return configs

def finishRuns():
    print("Waiting for jobs to finish up.")

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
    dataOpts = config["dataCollectionOptions"]
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
                print(f"Existing log {log} is incomplete. Adding it to be rerun.")
            logFile.close()
        except:
            print(f"Existing log {log} is incomplete. Adding it to be rerun.")
            continue
    for run in completedRuns:
        configs.remove(run)
    for config in configs:
        print(f"Configuration file {config} has no matching log. Adding it to be rerun")
    if len(configs) == 0:
        print("No incomplete logs found.")
    return configs

def parseOptions():
    commandLineArgs = sys.argv[1:]
    shortOptions = "c:p:s:t:h"
    longOptions = ("conf=", "path=", "seeds", "help")
    options = {"config": None, "path": None, "seeds": False}
    try:
        args, vals = getopt.getopt(commandLineArgs, shortOptions, longOptions)
    except getopt.GetoptError as err:
        print(err)
        exit(0)
    for currArg, currVal in args:
        if currArg in ("-c", "--conf"):
            if currVal == "":
                print("No configuration file provided.")
                printHelp()
            options["config"] = currVal
        elif currArg in ("-p", "--path"):
            options["path"] = currVal
            if currVal == "":
                print("No path provided.")
                printHelp()
        elif currArg in ("-h", "--help"):
            printHelp()
        elif currArg in ("-s", "--seeds"):
            options["seeds"] = True
    if options["config"] == None:
        print("Configuration file path required.")
        printHelp()
    return options

def printHelp():
    print("Usage:\n\tpython run.py --conf /path/to/config\n\nOptions:\n\t-c,--conf\tUse the specified path to configurable settings file.\n\t-p,--path\tUse the specified directory path to store dataset JSON files.\n\t-h,--help\tDisplay this message.")
    exit(0)

def runSimulations(config, configFiles, path):
    dataOpts = config["dataCollectionOptions"]
    pythonAlias = dataOpts["pythonAlias"]
    totalSimJobs = len(configFiles)
    jobUpdateFrequency = dataOpts["jobUpdateFrequency"]

    with multiprocessing.Pool(processes = dataOpts["numParallelSimJobs"]) as pool:
        for i, configFile in enumerate(configFiles):
            pool.apply_async(runSimulation, args = (configFile, pythonAlias, i + 1, totalSimJobs, jobUpdateFrequency))
        pool.apply(finishRuns)
        pool.close()
        pool.join()

def runSimulation(configFile, pythonAlias, jobNumber, totalJobs, updateFrequency):
    if jobNumber == 1 or jobNumber % updateFrequency == 0 or jobNumber == totalJobs:
        print(f"Running decision model {configFile} ({jobNumber}/{totalJobs})")
    os.system(f"{pythonAlias} ../sugarscape.py --conf {configFile}")

if __name__ == "__main__":
    options = parseOptions()
    seedsOnly = options["seeds"]
    path = options["path"]
    if path == None:
        path = "./"
    if not os.path.exists(path):
        print(f"Path {path} not recognized.")
        printHelp()

    config = options["config"]
    configFile = open(config)
    config = json.loads(configFile.read())
    configFile.close()
    if "dataCollectionOptions" not in config:
        print("Configuration file must have specific data collection options in order to run automated data collection.")
        exit(1)

    configFiles = createConfigurations(config, path)
    if seedsOnly == False:
        runSimulations(config, configFiles, path)

    exit(0)
