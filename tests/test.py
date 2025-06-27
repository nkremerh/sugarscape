import getopt
import json
import multiprocessing
import os
import re
import sys
import time

def cleanup():
    encodedDir = os.fsencode('.')
    for file in os.listdir(encodedDir):
        filename = os.fsdecode(file)
        if not (filename.endswith(".config") or filename.endswith(".log")):
            continue
        os.remove(filename)

def createConfigurations(path):
    configs = []
    encodedDir = os.fsencode(path)
    for file in os.listdir(encodedDir):
        filename = os.fsdecode(file)
        if not filename.endswith(".json"):
            print(f"Skipping file {filename} in testing.")
            continue
        filePath = path + filename
        fileShortName = re.compile(r"^([A-z_]*)(\d*)\.json")
        fileSearch = re.search(fileShortName, filename)
        if fileSearch == None:
            continue
        fileShortName = fileSearch.group(1)
        configFile = open(filePath)
        config = json.loads(configFile.read())
        configFile.close()
        simOpts = config["sugarscapeOptions"] if "sugarscapeOptions" in config else config
        simOpts["debugMode"] = ["none"]
        simOpts["headlessMode"] = True
        simOpts["logfile"] = f"{fileShortName}_test.log"
        simOpts["timesteps"] = 200
        configFileName = f"{fileShortName}_test.config"
        configFile = open(configFileName, 'w')
        configFile.write(json.dumps(simOpts))
        configFile.close()
        configs.append(configFileName)
    return configs

def finishSimulations():
    # Sleep to prevent printing from occurring out of order with final job submission
    time.sleep(1)
    print("Waiting for jobs to finish up.")

def parseOptions():
    commandLineArgs = sys.argv[1:]
    shortOptions = "c:h"
    longOptions = ("conf=", "help")
    options = {"config": None}
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
        elif currArg in ("-h", "--help"):
            printHelp()
    if options["config"] == None:
        print("Configuration file path required.")
        printHelp()
    return options

def printHelp():
    print("Usage:\n\tpython test.py --conf /path/to/config\n\nOptions:\n\t-c,--conf\tUse the specified path to configurable settings file.\n\t-h,--help\tDisplay this message.")
    exit(0)

def runSimulation(configFile, pythonAlias, jobNumber, totalJobs, failures):
    print(f"Running test {configFile} ({jobNumber}/{totalJobs})")
    result = os.system(f"{pythonAlias} ../sugarscape.py --conf {configFile} &> /dev/null")
    if result != 0:
        print(f"Test {configFile} failed - {result}.")
        failures[configFile] = result

def runSimulations(config, configFiles):
    dataOpts = config["dataCollectionOptions"]
    pythonAlias = dataOpts["pythonAlias"]
    totalSimJobs = len(configFiles)
    jobUpdateFrequency = dataOpts["jobUpdateFrequency"]
    manager = multiprocessing.Manager()
    failures = manager.dict()

    # Submit simulation jobs to local worker pool
    pool = multiprocessing.Pool(processes = dataOpts["numParallelSimJobs"])
    results = [pool.apply_async(runSimulation, args = (configFile, pythonAlias, i + 1, totalSimJobs, failures)) for i, configFile in enumerate(configFiles)]

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
    return failures

def verifyConfiguration(configuration):
    # Check if number of parallel jobs is greater than number of CPU cores
    cores = os.cpu_count()
    if configuration["dataCollectionOptions"]["numParallelSimJobs"] > cores:
        configuration["dataCollectionOptions"]["numParallelSimJobs"] = cores
    return configuration

if __name__ == "__main__":
    options = parseOptions()
    path = "../examples/"
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
    configFiles = createConfigurations(path)
    failures = runSimulations(config, configFiles)
    if len(failures) == 0:
        cleanup()
    exit(0)
