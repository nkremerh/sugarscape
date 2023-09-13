import getopt
import json
import os
import sys

def parseOptions():
    commandLineArgs = sys.argv[1:]
    shortOptions = "ch:"
    longOptions = ["conf=", "help"]
    try:
        args, vals = getopt.getopt(commandLineArgs, shortOptions, longOptions)
    except getopt.GetoptError as err:
        print(err)
        printHelp()
    nextArg = 0
    configuration = None
    for currArg, currVal in args:
        nextArg += 1
        if currArg in("-c", "--conf"):
            if currArg == "-c" and nextArg < len(commandLineArgs):
                currVal = commandLineArgs[nextArg]
            if currVal == "":
                print("No config file provided.")
                printHelp()
            configuration = currVal
        elif currArg in ("-h", "--help"):
            printHelp()
        elif currArg in ("-p", "--profile"):
            configuration["profileMode"] = True
    return configuration

def printHelp():
    print("Usage:\n\tpython setup.py --conf config.json\n\nOptions:\n\t-c,--conf\tUse specified config file for simulation settings.\n\t-h,--help\tDisplay this message.")
    exit(0)

def replaceMakefileSettings(settings, currPython):
    if settings["pathToPython"] != currPython:
        print("The setting for the Python path is replaced in the Makefile.\nYou will be prompted to allow in-file replacement if you changed this setting.\nDenying the change will cause the given option to be reverted to its previous value.")
        replace = input("Replace Python setting in the Makefile to {0} (currently: {1}) [Y/n]: ".format(settings["pathToPython"], currPython))
        if replace.upper() == 'Y':
            os.system("sed -i 's/PYTHON = {0}/PYTHON = {1}/g' Makefile".format(currPython, settings["pathToPython"]))
        else:
            settings["pathToPython"] = currPython

def selectSettings(settings, mode=None):
    newSettings = {}
    settingKey = "top-level"
    if mode == "sugarscape":
        settingKey = "Sugarscape simulation"
    print("You will be prompted with each configurable {0} setting in the software.\nFor each setting, enter the value(s) you would like.\nMulti-value settings should be comma-separated (with no spaces).\nNote: Given value will overwrite current value, not add to it.\nSimply hit enter for no change.".format(settingKey))
    i = 1
    settingsLen = len(settings) if mode == "sugarscape" else len(settings) - 1
    for setting in settings:
        if mode != "sugarscape" and setting == "sugarscapeOptions":
            continue
        value = input("{0}/{1} {2} (currently: {3}): ".format(i, settingsLen, setting, settings[setting]))
        if value != "":
            if isinstance(settings[setting], list):
                valType = None
                listValues = list(value.split(','))
                if isinstance(value[0], float):
                    value = list(map(float, listValues))
                elif isinstance(value[0], int):
                    value = list(map(int, listValues))
                elif isinstance(value[0], bool):
                    value = list(map(bool, listValues))
                elif isinstance(value[0], str):
                    value = listValues
            elif isinstance(settings[setting], float):
                value = float(value)
            elif isinstance(settings[setting], int):
                value = int(value)
            elif isinstance(value[0], bool):
                value = list(map(bool, listValues))
        else:
            value = settings[setting]
        newSettings[setting] = value
        i += 1
    return newSettings

if __name__ == "__main__":
    configuration = parseOptions()
    if configuration == None:
        configuration = "config.json"
    configFile = open(configuration)
    settings = json.loads(configFile.read())
    configFile.close()
    makefilePython = settings["pathToPython"]
    newSettings = selectSettings(settings)
    newSettings["sugarscapeOptions"] = selectSettings(settings["sugarscapeOptions"], "sugarscape")
    replaceMakefileSettings(newSettings, makefilePython)

    outfile = open("setup.json", 'w')
    outfile.write(json.dumps(newSettings, sort_keys=True))
    outfile.close()
    exit(0)
