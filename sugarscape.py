#! /usr/bin/python

import agent
import cell
import environment
import gui

import getopt
import json
import math
import random
import sys
#import time
import uuid

class Sugarscape:
    def __init__(self, configuration):
        self.__configuration = configuration
        self.__timestep = 0
        self.__environment = environment.Environment(configuration["environmentHeight"], configuration["environmentWidth"], self, configuration["environmentMaxSugar"], configuration["environmentSugarRegrowRate"],
                                                     configuration["environmentSeasonInterval"], configuration["environmentSeasonalGrowbackDelay"], configuration["environmentConsumptionPollutionRate"],
                                                     configuration["environmentProductionPollutionRate"], configuration["environmentPollutionDiffusionDelay"])
        self.__environmentHeight = configuration["environmentHeight"]
        self.__environmentWidth = configuration["environmentWidth"]
        self.configureEnvironment(configuration["environmentMaxSugar"])
        self.__agents = []
        self.configureAgents(configuration["startingAgents"])
        self.__gui = gui.GUI(self) if configuration["headlessMode"] == False else None
        self.__run = False # Simulation start flag
        self.__end = False # Simulation end flag
        self.__runtimeStats = {"timestep": 0, "agents": 0, "meanMetabolism": 0, "meanVision": 0, "meanWealth": 0, "meanAge": 0, "giniCoefficient": 0,
                               "meanTradePrice": 0, "meanTradeVolume": 0, "totalTradeVolume": 0, "totalWealth": 0, "maxWealth": 0, "minWealth": 0}
        self.__lastLoggedTimestep = 0
        self.__log = open(configuration["logfile"], 'a') if configuration["logfile"] != None else None

    def addAgent(self, agent):
        self.__agents.append(agent)

    # TODO: Make more consistent with book, dispersion more tightly concentrated than in book (ref: pg. 22)
    def addSugarPeak(self, startX, startY, radius, maxCapacity):
        height = self.__environment.getHeight()
        width = self.__environment.getWidth()
        radialDispersion = math.sqrt(max(startX, width - startX)**2 + max(startY, height - startY)**2) * (radius / width)
        seasons = True if self.__configuration["environmentSeasonInterval"] > 0 else False
        for i in range(height):
            for j in range(width):
                if self.__environment.getCell(i, j) == None:
                    newCell = cell.Cell(i, j, self.__environment)
                    if seasons == True:
                        if j >= self.__environment.getEquator():
                            newCell.setSeason("summer")
                        else:
                            newCell.setSeason("winter")
                    self.__environment.setCell(newCell, i, j)
                euclideanDistanceToStart = math.sqrt((startX - i)**2 + (startY - j)**2)
                currDispersion = 1 + maxCapacity * (1 - euclideanDistanceToStart / radialDispersion)
                cellMaxCapacity = min(currDispersion, maxCapacity)
                cellMaxCapacity = math.ceil(cellMaxCapacity)
                if cellMaxCapacity > self.__environment.getCell(i, j).getMaxSugar():
                    self.__environment.getCell(i, j).setMaxSugar(cellMaxCapacity)
                    self.__environment.getCell(i, j).setCurrSugar(cellMaxCapacity)
 
    def configureAgents(self, numAgents):
        configs = self.__configuration
        startingAgents = configs["startingAgents"]
        metabolism = configs["agentMetabolism"]
        vision = configs["agentVision"]
        startingWealth = configs["agentStartingWealth"]
        maxAge = configs["agentMaxAge"]
        maleToFemaleRatio = configs["agentMaleToFemaleRatio"]
        femaleFertilityAge = configs["agentFemaleFertilityAge"]
        maleFertilityAge = configs["agentMaleFertilityAge"]
        femaleInfertilityAge = configs["agentFemaleInfertilityAge"]
        maleInfertilityAge = configs["agentMaleInfertilityAge"]
        tagStringLength = configs["agentTagStringLength"]

        if self.__environment == None:
            return
        totalCells = self.__environmentHeight * self.__environmentWidth
        if numAgents > totalCells:
            print("Could not allocate {0} agents. Allocating maximum of {1}.".format(numAgents, totalCells))
            numAgents = totalCells
        # Ensure infinitely-lived agents are properly initialized
        if maxAge[0] < 0 or maxAge[1] < 0:
            maxAge[0] = -1
            maxAge[1] = -1
        # Ensure agent endowments are randomized across initial agent count to make replacements follow same distributions
        agentEndowments = self.randomizeAgentEndowments(startingAgents, metabolism, vision, startingWealth, maxAge, maleToFemaleRatio,
                                                        femaleFertilityAge, maleFertilityAge, femaleInfertilityAge, maleInfertilityAge,
                                                        tagStringLength)
        for i in range(numAgents):
            randX = random.randrange(self.__environmentHeight)
            randY = random.randrange(self.__environmentWidth)
            while self.__environment.getCell(randX, randY).getAgent() != None and len(self.__agents) <= (self.__environmentHeight * self.__environmentWidth):
                randX = random.randrange(self.__environment.getHeight())
                randY = random.randrange(self.__environment.getWidth())
            c = self.__environment.getCell(randX, randY)
            currMetabolism = agentEndowments[i][0]
            currVision = agentEndowments[i][1]
            currMaxAge = agentEndowments[i][2]
            currWealth = agentEndowments[i][3]
            currSex = agentEndowments[i][4]
            currFertilityAge = agentEndowments[i][5]
            currInfertilityAge = agentEndowments[i][6]
            currTags = agentEndowments[i][7]
            # Generate random UUID for agent identification
            agentID = str(uuid.uuid4())
            a = agent.Agent(agentID, self.__timestep, c, currMetabolism, currVision, currMaxAge, currWealth, currSex, currFertilityAge, currInfertilityAge, currTags)
            c.setAgent(a)
            self.__agents.append(a)

    def configureEnvironment(self, maxCapacity):
        height = self.__environment.getHeight()
        width = self.__environment.getWidth()
        startX1 = math.ceil(height * 0.7)
        startX2 = math.ceil(height * 0.3)
        startY1 = math.ceil(width * 0.3)
        startY2 = math.ceil(width * 0.7)
        radius = math.ceil(math.sqrt(2 * (height + width)))
        self.addSugarPeak(startX1, startY1, radius, maxCapacity)
        self.addSugarPeak(startX2, startY2, radius, maxCapacity)
        self.__environment.setCellNeighbors()

    def doTimestep(self):
        if self.__end == True or len(self.__agents) == 0:
            self.endSimulation()
        self.replaceDeadAgents()
        self.updateRuntimeStats()
        self.writeToLog()
        self.__environment.doTimestep()
        for a in self.__agents:
            if a.isAlive() == False:
                self.__agents.remove(a)
        if self.__gui != None:
            self.__gui.doTimestep()
        print("Timestep: {0}".format(self.__timestep))
        self.__timestep += 1

    def endLog(self):
        if self.__log == None:
            return
        logString = '\t' + json.dumps(self.__runtimeStats) + "\n]"
        self.__log.write(logString)
        self.__log.flush()
        self.__log.close()

    # TODO: Simulation does not terminate when stepping through to end condition (no living agents)
    def endSimulation(self):
        self.endLog()
        print(str(self))
        exit(0)

    def getAgents(self):
        return self.__agents

    def getConfiguration(self):
        return self.__configuration

    def getEnd(self):
        return self.__end

    def getEnvironment(self):
        return self.__environment
 
    def getEnvironmentHeight(self):
        return self.__environmentHeight

    def getEnvironmentWidth(self):
        return self.__environmentWidth

    def getGUI(self):
        return self.__gui

    def getRun(self):
        return self.__run

    def getRuntimeStats(self):
        return self.__runtimeStats

    def getSeed(self):
        return self.__configuration["seed"]

    def getTimestep(self):
        return self.__timestep

    def pauseSimulation(self):
        while self.__run == False:
            if self.__end == True:
                self.endSimulation()
            if self.__gui != None:
                self.__gui.getWindow().update()

    def randomizeAgentEndowments(self, numAgents, metabolism, vision, startingWealth, maxAge, maleToFemaleRatio,
                                 femaleFertilityAge, maleFertilityAge, femaleInfertilityAge, maleInfertilityAge,
                                 tagStringLength):
        endowments = []
        metabolisms = []
        visions = []
        ages = []
        startingWealths = []
        sexes = []
        femaleFertilityAges = []
        maleFertilityAges = []
        femaleInfertilityAges = []
        maleInfertilityAges = []
        tags = []
        
        minMetabolism = metabolism[0]
        minVision = vision[0]
        minWealth = startingWealth[0]
        minFemaleFertilityAge = femaleFertilityAge[0]
        minMaleFertilityAge = maleFertilityAge[0]
        minFemaleInfertilityAge = femaleInfertilityAge[0]
        minMaleInfertilityAge = maleInfertilityAge[0]
        minStartingWealth = startingWealth[0]
        minAge = maxAge[0]

        maxMetabolism = metabolism[1]
        maxVision = vision[1]
        maxWealth = startingWealth[1]
        maxFemaleFertilityAge = femaleFertilityAge[1]
        maxMaleFertilityAge = maleFertilityAge[1]
        maxFemaleInfertilityAge = femaleInfertilityAge[1]
        maxMaleInfertilityAge = maleInfertilityAge[1]
        maxStartingWealth = startingWealth[1]
        maxAge = maxAge[1]

        currMetabolism = random.randrange(minMetabolism, maxMetabolism + 1)
        currVision = random.randrange(minVision, maxVision + 1)
        currWealth = random.randrange(minWealth, maxStartingWealth + 1)
        currMaxAge = minAge
        currFemaleFertilityAge = minFemaleFertilityAge
        currMaleFertilityAge = minMaleFertilityAge
        currFemaleInfertilityAge = minFemaleInfertilityAge
        currMaleInfertilityAge = minMaleInfertilityAge

        sexDistributionCountdown = numAgents
        # Determine count of male agents and set as switch for agent generation
        if maleToFemaleRatio != None and maleToFemaleRatio != 0:
            sexDistributionCountdown = math.floor(sexDistributionCountdown / (maleToFemaleRatio + 1)) * maleToFemaleRatio
        
        for i in range(numAgents):
            metabolisms.append(currMetabolism)
            visions.append(currVision)
            ages.append(currMaxAge)
            startingWealths.append(currWealth)
            femaleFertilityAges.append(currFemaleFertilityAge)
            maleFertilityAges.append(currMaleFertilityAge)
            femaleInfertilityAges.append(currFemaleInfertilityAge)
            maleInfertilityAges.append(currMaleInfertilityAge)
            tags.append([random.randrange(2) for i in range(tagStringLength)])
            currMetabolism += 1
            currVision += 1
            currMaxAge += 1
            currWealth += 1
            currFemaleFertilityAge += 1
            currMaleFertilityAge += 1
            currFemaleInfertilityAge += 1
            currMaleInfertilityAge += 1

            if maleToFemaleRatio != None and maleToFemaleRatio != 0:
                if sexDistributionCountdown == 0:
                    sexes.append("female")
                else:
                    sexes.append("male")
                    sexDistributionCountdown -= 1
            else:
                sexes.append(None)

            if currMetabolism > maxMetabolism:
                currMetabolism = minMetabolism
            if currVision > maxVision:
                currVision = minVision
            if currMaxAge > maxAge:
                currMaxAge = minAge
            if currWealth > maxStartingWealth:
                currWealth = minWealth
            if currFemaleFertilityAge > maxFemaleFertilityAge:
                currFemaleFertilityAge = minFemaleFertilityAge
            if currMaleFertilityAge > maxMaleFertilityAge:
                currMaleFertilityAge = minMaleFertilityAge
            if currFemaleInfertilityAge > maxFemaleInfertilityAge:
                currFemaleInfertilityAge = minFemaleInfertilityAge
            if currMaleInfertilityAge > maxMaleInfertilityAge:
                currMaleInfertilityAge = minMaleInfertilityAge
        
        random.shuffle(metabolisms)
        random.shuffle(visions)
        random.shuffle(ages)
        random.shuffle(startingWealths)
        random.shuffle(sexes)
        random.shuffle(femaleFertilityAges)
        random.shuffle(maleFertilityAges)
        random.shuffle(femaleInfertilityAges)
        random.shuffle(maleInfertilityAges)
        for i in range(numAgents):
            if sexes[i] == "female":
                endowments.append([metabolisms.pop(), visions.pop(), ages.pop(), startingWealths.pop(), sexes[i], femaleFertilityAges.pop(), femaleInfertilityAges.pop(), tags.pop()])
            elif sexes[i] == "male":
                endowments.append([metabolisms.pop(), visions.pop(), ages.pop(), startingWealths.pop(), sexes[i], maleFertilityAges.pop(), maleInfertilityAges.pop(), tags.pop()])
            else:
                endowments.append([metabolisms.pop(), visions.pop(), ages.pop(), startingWealths.pop(), sexes[i], 0, 0, tags.pop()])
        return endowments

    def replaceDeadAgents(self):
        if self.__configuration["agentReplacement"] == True and len(self.__agents) < self.__configuration["startingAgents"]:
            numReplacements = self.__configuration["startingAgents"] - len(self.__agents)
            self.configureAgents(numReplacements)
            if self.__gui != None:
                self.__gui.doTimestep()

    def runSimulation(self, timesteps=5):
        self.startLog()
        if self.__gui != None:
            self.pauseSimulation() # Simulation begins paused until start button in GUI pressed
        t = 0
        timesteps = timesteps - self.__timestep
        while t <= timesteps:
            self.doTimestep()
            t += 1
            if self.__gui != None and self.__run == False:
                self.pauseSimulation()
        self.endSimulation()

    def setAgents(self, agents):
        self.__agents = agents

    def setEnd(self):
        self.__end = not self.__end

    def setEnvironment(self, environment):
        self.__environment = environment

    def setEnvironmentHeight(self, environmentHeight):
        self.__environmentHeight = environmentHeight

    def setEnvironmentWidth(self, environmentWidth):
        self.__environmentWidth = environmentWidth

    def setGUI(self, gui):
        self.__gui = gui

    def setTimestep(self, timestep):
        self.__timestep = timestep
  
    def setRun(self):
        self.__run = not self.__run
  
    def setRuntimeStats(self, runtimeStats):
        self.__runtimeStats = runtimeStats

    def startLog(self):
        if self.__log == None:
            return
        self.__log.write("[\n")

    def updateGiniCoefficient(self):
        agentWealths = sorted([agent.getSugar() for agent in self.__agents])
        # Calculate area between line of equality and Lorenz curve of agent wealths
        height = 0
        area = 0
        for wealth in agentWealths:
            height += wealth
            area += (height - wealth) / 2
        lineOfEquality = (height * len(agentWealths)) / 2
        giniCoefficient = (lineOfEquality - area) / lineOfEquality
        return giniCoefficient

    def updateRuntimeStats(self):
        numAgents = len(self.__agents)
        meanMetabolism = 0
        meanVision = 0
        meanWealth = 0
        meanAge = 0
        meanTradePrice = 0
        meanTradeVolume = 0
        totalTradeVolume = 0
        totalWealth = 0
        maxWealth = 0
        minWealth = sys.maxsize
        for agent in self.__agents:
            agentWealth = agent.getSugar()
            meanMetabolism += agent.getMetabolism()
            meanVision += agent.getVision()
            meanAge += agent.getAge()
            meanWealth += agentWealth
            totalWealth += agentWealth
            if agentWealth < minWealth:
                minWealth = agentWealth
            if agentWealth > maxWealth:
                maxWealth = agentWealth
        meanMetabolism = meanMetabolism / numAgents
        meanVision = meanVision / numAgents
        meanAge = meanAge / numAgents
        meanWealth = meanWealth / numAgents
        self.__runtimeStats["timestep"] = self.__timestep
        self.__runtimeStats["agents"] = numAgents
        self.__runtimeStats["meanMetabolism"] = meanMetabolism
        self.__runtimeStats["meanVision"] = meanVision
        self.__runtimeStats["meanAge"] = meanAge
        self.__runtimeStats["meanWealth"] = meanWealth
        self.__runtimeStats["minWealth"] = minWealth
        self.__runtimeStats["maxWealth"] = maxWealth
        self.__runtimeStats["giniCoefficient"] = self.updateGiniCoefficient() if len(self.__agents) > 1 else 0

    def writeToLog(self):
        if self.__log == None:
            return
        self.__lastLoggedTimestep = self.__timestep
        logString = '\t' + json.dumps(self.__runtimeStats) + ",\n"
        self.__log.write(logString)

    def __str__(self):
        string = "{0}Timestep: {1}\nLiving Agents: {2}".format(str(self.__environment), self.__lastLoggedTimestep, len(self.__agents))
        return string

def parseConfigFile(configFile, configuration):
    file = open(configFile)
    options = json.loads(file.read())
    for opt in configuration:
        if opt in options:
            configuration[opt] = options[opt]
    return configuration

def parseOptions(configuration):
    commandLineArgs = sys.argv[1:]
    shortOptions = "ch:"
    longOptions = ["conf=", "help"]
    try:
        args, vals = getopt.getopt(commandLineArgs, shortOptions, longOptions)
    except getopt.GetoptError as err:
        print(err)
        printHelp()
    for currArg, currVal in args:
        # TODO: Passing short option -c requires instead passing --c to grab config file name
        if currArg in ("-c", "--conf"):
            if currVal == "":
                print("No config file provided.")
                printHelp()
            parseConfigFile(currVal, configuration)
        elif currArg in ("-h", "--help"):
            printHelp()
    return configuration

def printHelp():
    print("Usage:\n\tpython sugarscape.py --conf config.json\n\nOptions:\n\t-c,--conf\tUse specified config file for simulation settings.\n\t-h,--help\tDisplay this message.")
    exit(0)

if __name__ == "__main__":
    # Set default values for simulation configuration
    configuration = {"agentVision": [1, 6], "agentMetabolism": [1, 4], "agentStartingWealth": [1, 5], "startingAgents": 250, "agentReplacement": False,
                     "agentMaxAge": [60, 100], "agentMaleToFemaleRatio": 1, "agentFemaleFertilityAge": [12, 15], "agentMaleFertilityAge": [12, 15],
                     "agentFemaleInfertilityAge": [40, 50], "agentMaleInfertilityAge": [50, 60], "agentTagStringLength": 11,
                     "environmentHeight": 50, "environmentWidth": 50, "environmentMaxSugar": 4, "environmentSugarRegrowRate": 1,
                     "environmentSeasonInterval": 20, "environmentSeasonalGrowbackDelay": 2, "environmentConsumptionPollutionRate": 1,
                     "environmentProductionPollutionRate": 1, "environmentPollutionDiffusionDelay": 10,
                     "logfile": None, "seed": 12345, "headlessMode": False}
    configuration = parseOptions(configuration)
    random.seed(configuration["seed"])
    S = Sugarscape(configuration)
    print(str(S))
    S.runSimulation(1000)
    #print(str(S))
    exit(0)
