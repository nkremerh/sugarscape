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

def printProgress(lastJob, jobsFinished, totalJobs, jobLength, decimals=2):
    barLength = os.get_terminal_size().columns // 2
    progress = round(((jobsFinished / totalJobs) * 100), decimals)
    filledLength = (barLength * jobsFinished) // totalJobs
    bar = '█' * filledLength + '-' * (barLength - filledLength)
    printString = f"\rRunning {lastJob:>{jobLength}}: |{bar}| {jobsFinished} / {totalJobs} ({progress}%)"
    print(f"\r{printString}", end='\r')

def runDeterminismTest(config, configFiles):
    failures = 0
    dataOpts = config["dataCollectionOptions"]
    pythonAlias = dataOpts["pythonAlias"]
    result1 = os.system(f"{pythonAlias} ../sugarscape.py --conf determinism_test.config &> /dev/null && mv determinism_test.log 1.log")
    result2 = os.system(f"{pythonAlias} ../sugarscape.py --conf determinism_test.config &> /dev/null && mv determinism_test.log 2.log")
    if result1 != 0:
        failures += 1
    if result2 != 0:
        failures += 1
    logfile1 = open("1.log")
    logfile2 = open("2.log")
    log1 = json.loads(logfile1.read())
    log2 = json.loads(logfile2.read())
    logfile1.close()
    logfile2.close()
    if log1 != log2:
        print("Simulation is not deterministic!")
        failures += 1
    return failures

def runSimulation(configFile, pythonAlias, jobNumber, totalJobs, count, printFileLength, failures):
    result = os.system(f"{pythonAlias} ../sugarscape.py --conf {configFile} &> /dev/null")
    if result != 0:
        failures[configFile] = result
    count.value += 1
    printProgress(configFile, count.value, totalJobs, printFileLength)

def runSimulations(config, configFiles):
    dataOpts = config["dataCollectionOptions"]
    pythonAlias = dataOpts["pythonAlias"]
    configFiles.remove("determinism_test.config")
    totalSimJobs = len(configFiles)

    # Submit simulation jobs to local worker pool
    manager = multiprocessing.Manager()
    counter = manager.Value('i', 0)
    failures = manager.dict()
    printFileLength = len(max(configFiles, key=len))
    pool = multiprocessing.Pool(processes = dataOpts["numParallelSimJobs"])
    results = [pool.apply_async(runSimulation, args=(configFile, pythonAlias, i + 1, totalSimJobs, counter, printFileLength, failures)) for i, configFile in enumerate(configFiles)]

    # Wait for jobs to finish
    while len(results) > 0:
        waitingResults = []
        for result in results:
            ready = result.ready()
            if ready == False:
                waitingResults.append(result)
        results = waitingResults

    # Clean up job pool
    pool.close()
    pool.join()
    print(f"\r{' ' * os.get_terminal_size().columns}", end='\r')
    for failure in failures:
        print(f"Test {failure} failed, got result {failures[failure]}.")
    return len(failures)

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
    failures += runDeterminismTest(config, configFiles)
    print("All tests completed.")
    if failures == 0:
        cleanup()
    exit(0)
