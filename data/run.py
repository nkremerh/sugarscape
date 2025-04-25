import csv
import getopt
import json
import multiprocessing
import os
import random
import sys
import time

def createConfigurations(config, path, mode="json"):
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
                if mode == "json":
                    simOpts["logfile"] = f"{path}{modelString}{seed}.json"
                    simOpts["logfileFormat"] = "json"
                else:
                    simOpts["logfile"] = f"{path}{modelString}{seed}.csv"
                    simOpts["logfileFormat"] = "csv"
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

def finishSimulations():
    # Sleep to prevent printing from occurring out of order with final job submission
    time.sleep(1)
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
    simOpts = config["sugarscapeOptions"]
    configs = []
    for file in os.listdir(encodedDir):
        filename = os.fsdecode(file)
        if not filename.endswith(".config"):
            continue
        filePath = path + filename
        configs.append(filePath)
    completedRuns = []
    for config in configs:
        configFile = open(config)
        rawConf = json.loads(configFile.read())
        log = rawConf["logfile"]
        configFile.close()
        if os.path.exists(log) == False:
            print(f"Configuration file {config} has no matching log. Adding it to be rerun.")
            continue
        try:
            logFile = open(log)
            lastEntry = None
            if log.endswith(".json"):
                lastEntry = json.loads(logFile.read())[-1]
            else:
                lastEntry = list(csv.DictReader(logFile))[-1]
            logFile.close()
            if int(lastEntry["timestep"]) == int(rawConf["timesteps"]) or int(lastEntry["population"]) == 0:
                completedRuns.append(config)
            else:
                print(f"Existing log {log} is incomplete. Adding it to be rerun.")
                os.remove(log)
        except:
            print(f"Existing log {log} is incomplete. Adding it to be rerun.")
            os.remove(log)
            continue
    for run in completedRuns:
        configs.remove(run)
    if len(configs) == 0:
        print("No incomplete logs found.")
    return configs

def parseOptions():
    commandLineArgs = sys.argv[1:]
    shortOptions = "c:m:p:s:t:h"
    longOptions = ("conf=", "mode=", "path=", "seeds", "help")
    options = {"config": None, "mode": "json", "path": None, "seeds": False}
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
        elif currArg in ("-m", "--mode"):
            options["mode"] = currVal
            if currVal == "":
                print("No log mode provided.")
                printHelp()
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
    print("Usage:\n\tpython run.py --conf /path/to/config\n\nOptions:\n\t-c,--conf\tUse the specified path to configurable settings file.\n\t-m,--mode\tUse the specified file format for simulation logs.\n\t-p,--path\tUse the specified directory path to store dataset JSON files.\n\t-h,--help\tDisplay this message.")
    exit(0)

def runSimulation(configFile, pythonAlias, jobNumber, totalJobs):
    print(f"Running decision model {configFile} ({jobNumber}/{totalJobs})")
    os.system(f"{pythonAlias} ../sugarscape.py --conf {configFile} &> /dev/null")

def runSimulations(config, configFiles):
    dataOpts = config["dataCollectionOptions"]
    pythonAlias = dataOpts["pythonAlias"]
    totalSimJobs = len(configFiles)
    jobUpdateFrequency = dataOpts["jobUpdateFrequency"]

    # Submit simulation jobs to local worker pool
    pool = multiprocessing.Pool(processes = dataOpts["numParallelSimJobs"])
    results = [pool.apply_async(runSimulation, args = (configFile, pythonAlias, i + 1, totalSimJobs)) for i, configFile in enumerate(configFiles)]

    # Wait for jobs to finish
    pool.apply(finishSimulations)
    lastUpdate = 0
    while len(results) > 0:
        waitingResults = []
        for result in results:
            ready = result.ready()
            if ready == False:
                waitingResults.append(result)
        outstanding = len(waitingResults)
        if outstanding != 0 and outstanding != lastUpdate and outstanding % jobUpdateFrequency == 0:
            print(f"{outstanding} jobs remaining.")
            lastUpdate = outstanding
        results = waitingResults

    # Clean up job pool
    pool.close()
    pool.join()

def verifyConfiguration(configuration):
    # Check if number of parallel jobs is greater than number of CPU cores
    cores = os.cpu_count()
    if configuration["dataCollectionOptions"]["numParallelSimJobs"] > cores:
        configuration["dataCollectionOptions"]["numParallelSimJobs"] = cores
    return configuration

if __name__ == "__main__":
    options = parseOptions()
    seedsOnly = options["seeds"]
    mode = options["mode"]
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

    config = verifyConfiguration(config)
    configFiles = createConfigurations(config, path, mode)
    if seedsOnly == False:
        runSimulations(config, configFiles)

    exit(0)
