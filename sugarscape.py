#! /usr/bin/python

import agent
import cell
import disease
import environment
import ethics

import getopt
import hashlib
import json
import math
import random
import sys

class Sugarscape:
    def __init__(self, configuration):
        self.diseaseConfigHashes = None
        self.agentConfigHashes = None
        self.configuration = configuration
        self.maxTimestep = configuration["timesteps"]
        self.timestep = 0
        self.nextAgentID = 0
        self.nextDiseaseID = 0
        environmentConfiguration = {"globalMaxSugar": configuration["environmentMaxSugar"], "sugarRegrowRate": configuration["environmentSugarRegrowRate"],
                                    "seasonInterval": configuration["environmentSeasonInterval"], "seasonalGrowbackDelay": configuration["environmentSeasonalGrowbackDelay"],
                                    "spiceConsumptionPollutionFactor": configuration["environmentSpiceConsumptionPollutionFactor"],
                                    "sugarConsumptionPollutionFactor": configuration["environmentSugarConsumptionPollutionFactor"],
                                    "spiceProductionPollutionFactor": configuration["environmentSpiceProductionPollutionFactor"],
                                    "sugarProductionPollutionFactor": configuration["environmentSugarProductionPollutionFactor"],
                                    "pollutionDiffusionDelay": configuration["environmentPollutionDiffusionDelay"], "maxCombatLoot": configuration["environmentMaxCombatLoot"],
                                    "globalMaxSpice": configuration["environmentMaxSpice"], "spiceRegrowRate": configuration["environmentSpiceRegrowRate"],
                                    "universalSpiceIncomeInterval": configuration["environmentUniversalSpiceIncomeInterval"],
                                    "universalSugarIncomeInterval": configuration["environmentUniversalSugarIncomeInterval"],
                                    "sugarscapeSeed": configuration["seed"]}
        self.seed = configuration["seed"]
        self.environment = environment.Environment(configuration["environmentHeight"], configuration["environmentWidth"], self, environmentConfiguration)
        self.environmentHeight = configuration["environmentHeight"]
        self.environmentWidth = configuration["environmentWidth"]
        self.configureEnvironment(configuration["environmentMaxSugar"], configuration["environmentMaxSpice"])
        self.debug = configuration["debugMode"]
        self.agents = []
        self.deadAgents = []
        self.diseases = []
        self.configureAgents(configuration["startingAgents"])
        self.configureDiseases(configuration["startingDiseases"])
        self.gui = gui.GUI(self, self.configuration["interfaceHeight"], self.configuration["interfaceWidth"]) if configuration["headlessMode"] == False else None
        self.run = False # Simulation start flag
        self.end = False # Simulation end flag
        # TODO: Remove redundant metrics
        self.runtimeStats = {"timestep": 0, "population": 0, "meanMetabolism": 0, "meanMovement": 0, "meanVision": 0, "meanWealth": 0, "meanAge": 0, "giniCoefficient": 0,
                             "meanTradePrice": 0, "tradeVolume": 0, "maxWealth": 0, "minWealth": 0, "meanHappiness": 0, "meanWealthHappiness": 0, "meanHealthHappiness": 0,
                             "meanSocialHappiness": 0, "meanFamilyHappiness": 0, "meanConflictHappiness": 0, "meanAgeAtDeath": 0, "seed": self.seed, "totalWealthLost": 0,
                             "totalMetabolismCost": 0, "agentReproduced": 0, "agentStarvationDeaths": 0, "agentDiseaseDeaths": 0, "environmentWealthCreated": 0,
                             "agentWealthTotal": 0, "environmentWealthTotal": 0, "agentWealthCollected": 0, "agentWealthBurnRate": 0, "agentMeanTimeToLive": 0, "agentWealths": [],
                             "agentTimesToLive": [], "agentTimesToLiveAgeLimited": [], "agentTotalMetabolism": 0}
        self.log = open(configuration["logfile"], 'a') if configuration["logfile"] != None else None

    def addAgent(self, agent):
        self.agents.append(agent)

    def addDisease(self, oldDisease, agent):
        diseaseID = oldDisease.ID
        diseaseConfig = oldDisease.configuration
        newDisease = disease.Disease(diseaseID, diseaseConfig)
        agent.catchDisease(newDisease)

    def addSpicePeak(self, startX, startY, radius, maxSpice):
        height = self.environment.height
        width = self.environment.width
        radialDispersion = math.sqrt(max(startX, width - startX)**2 + max(startY, height - startY)**2) * (radius / width)
        for i in range(height):
            for j in range(width):
                euclideanDistanceToStart = math.sqrt((startX - i)**2 + (startY - j)**2)
                currDispersion = 1 + maxSpice * (1 - euclideanDistanceToStart / radialDispersion)
                cellMaxCapacity = min(currDispersion, maxSpice)
                cellMaxCapacity = math.ceil(cellMaxCapacity)
                if cellMaxCapacity > self.environment.findCell(i, j).maxSpice:
                    self.environment.findCell(i, j).maxSpice = cellMaxCapacity
                    self.environment.findCell(i, j).spice = cellMaxCapacity

    def addSugarPeak(self, startX, startY, radius, maxSugar):
        height = self.environment.height
        width = self.environment.width
        radialDispersion = math.sqrt(max(startX, width - startX)**2 + max(startY, height - startY)**2) * (radius / width)
        for i in range(height):
            for j in range(width):
                euclideanDistanceToStart = math.sqrt((startX - i)**2 + (startY - j)**2)
                currDispersion = 1 + maxSugar * (1 - euclideanDistanceToStart / radialDispersion)
                cellMaxCapacity = min(currDispersion, maxSugar)
                cellMaxCapacity = math.ceil(cellMaxCapacity)
                if cellMaxCapacity > self.environment.findCell(i, j).maxSugar:
                    self.environment.findCell(i, j).maxSugar = cellMaxCapacity
                    self.environment.findCell(i, j).sugar = cellMaxCapacity

    def configureAgents(self, numAgents):
        if self.environment == None:
            return

        activeCells = self.findActiveQuadrants()
        if len(activeCells) == 0:
            return

        totalCells = len(activeCells)
        if len(self.agents) + numAgents > totalCells:
            if "all" in self.debug or "sugarscape" in self.debug:
                print("Could not allocate {0} agents. Allocating maximum of {1}.".format(numAgents, totalCells))
            numAgents = totalCells

        # Ensure agent endowments are randomized across initial agent count to make replacements follow same distributions
        agentEndowments = self.randomizeAgentEndowments(numAgents)
        randCoords = activeCells
        random.shuffle(randCoords)

        for i in range(numAgents):
            randCoord = randCoords.pop()
            randCellX = randCoord[0]
            randCellY = randCoord[1]
            c = self.environment.findCell(randCellX, randCellY)
            agentConfiguration = agentEndowments[i]
            agentID = self.generateAgentID()
            a = agent.Agent(agentID, self.timestep, c, agentConfiguration)
            # If using a different decision model, replace new agent with instance of child class
            if "altruisticHalfLookahead" in agentConfiguration["decisionModel"]:
                a = ethics.Bentham(agentID, self.timestep, c, agentConfiguration, "halfLookahead")
                a.selfishnessFactor = 0
            elif "altruisticNoLookahead" in agentConfiguration["decisionModel"]:
                a = ethics.Bentham(agentID, self.timestep, c, agentConfiguration)
                a.selfishnessFactor = 0
            elif "benthamHalfLookahead" in agentConfiguration["decisionModel"]:
                a = ethics.Bentham(agentID, self.timestep, c, agentConfiguration, "halfLookahead")
            elif "benthamNoLookahead" in agentConfiguration["decisionModel"]:
                a = ethics.Bentham(agentID, self.timestep, c, agentConfiguration)
            elif "egoisticHalfLookahead" in agentConfiguration["decisionModel"]:
                a = ethics.Bentham(agentID, self.timestep, c, agentConfiguration, "halfLookahead")
                a.selfishnessFactor = 1
            elif "egoisticNoLookahead" in agentConfiguration["decisionModel"]:
                a = ethics.Bentham(agentID, self.timestep, c, agentConfiguration)
                a.selfishnessFactor = 1
            c.agent = a
            self.agents.append(a)

    def configureDiseases(self, numDiseases):
        numAgents = len(self.agents)
        if numAgents == 0:
            return
        elif numAgents < numDiseases:
            numDiseases = numAgents

        diseaseEndowments = self.randomizeDiseaseEndowments(numDiseases)
        random.shuffle(self.agents)
        diseases = []
        for i in range(numDiseases):
            diseaseID = self.generateDiseaseID()
            diseaseConfiguration = diseaseEndowments[i]
            newDisease = disease.Disease(diseaseID, diseaseConfiguration)
            diseases.append(newDisease)

        unplacedDisease = 0
        for agent in self.agents:
            for newDisease in diseases:
                hammingDistance = agent.findNearestHammingDistanceInDisease(newDisease)["distance"]
                if hammingDistance != 0:
                    agent.catchDisease(newDisease)
                    self.diseases.append(newDisease)
                    diseases.remove(newDisease)
                    break
        if len(diseases) > 0 and ("all" in self.debug or "sugarscape" in self.debug):
            print("Could not place {0} diseases.".format(len(diseases)))

    def configureEnvironment(self, maxSugar, maxSpice):
        height = self.environment.height
        width = self.environment.width
        for i in range(height):
            for j in range(width):
                newCell = cell.Cell(i, j, self.environment)
                self.environment.setCell(newCell, i, j)

        startX1 = math.ceil(height * 0.7)
        startX2 = math.ceil(height * 0.3)
        startY1 = math.ceil(width * 0.3)
        startY2 = math.ceil(width * 0.7)
        sugarRadiusScale = 2
        radius = math.ceil(math.sqrt(sugarRadiusScale * (height + width)))
        self.addSugarPeak(startX1, startY1, radius, maxSugar)
        self.addSugarPeak(startX2, startY2, radius, maxSugar)

        startX1 = math.ceil(height * 0.7)
        startX2 = math.ceil(height * 0.3)
        startY1 = math.ceil(width * 0.7)
        startY2 = math.ceil(width * 0.3)
        spiceRadiusScale = 2
        radius = math.ceil(math.sqrt(spiceRadiusScale * (height + width)))
        self.addSpicePeak(startX1, startY1, radius, maxSpice)
        self.addSpicePeak(startX2, startY2, radius, maxSpice)
        self.environment.findCellNeighbors()

    def doTimestep(self):
        self.removeDeadAgents()
        self.replaceDeadAgents()
        if self.timestep >= self.maxTimestep:
            self.toggleEnd()
            return
        if "all" in self.debug or "sugarscape" in self.debug:
            print("Timestep: {0}\nLiving Agents: {1}".format(self.timestep, len(self.agents)))
        self.timestep += 1
        if self.end == True or len(self.agents) == 0:
            self.toggleEnd()
        else:
            self.environment.doTimestep(self.timestep)
            random.shuffle(self.agents)
            for agent in self.agents:
                agent.doTimestep(self.timestep)
            if self.gui != None:
                self.gui.doTimestep()
            self.removeDeadAgents()
            self.updateRuntimeStats()
            # If final timestep, do not write to log to cleanly close JSON array log structure
            if self.timestep != self.maxTimestep and len(self.agents) > 0:
                self.writeToLog()

    def endLog(self):
        if self.log == None:
            return
        # Update total wealth accumulation to include still living agents at simulation end
        for agent in self.agents:
            self.runtimeStats["totalMetabolismCost"] += agent.sugarMetabolism + agent.spiceMetabolism
        environmentWealthCreated = 0
        environmentWealthTotal = 0
        for i in range(self.environment.height):
            for j in range(self.environment.width):
                environmentWealthCreated += self.environment.grid[i][j].sugarLastProduced + self.environment.grid[i][j].spiceLastProduced
                environmentWealthTotal += self.environment.grid[i][j].sugar + self.environment.grid[i][j].spice
        self.runtimeStats["environmentWealthCreated"] = environmentWealthCreated
        self.runtimeStats["environmentWealthTotal"] = environmentWealthTotal
        logString = '\t' + json.dumps(self.runtimeStats) + "\n]"
        self.log.write(logString)
        self.log.flush()
        self.log.close()

    def endSimulation(self):
        self.removeDeadAgents()
        self.endLog()
        if "all" in self.debug or "sugarscape" in self.debug:
            print(str(self))
        exit(0)

    def findActiveQuadrants(self):
        quadrants = self.configuration["agentStartingQuadrants"]
        cellRange = []
        halfWidth = math.floor(self.environmentWidth / 2)
        halfHeight = math.floor(self.environmentHeight / 2)
        # Quadrant I at origin in top left corner, other quadrants in clockwise order
        if 1 in quadrants:
            quadRange = [[(i, j) for j in range(halfHeight)] for i in range(halfWidth)]
            for i in range(halfWidth):
                for j in range(halfHeight):
                    cellRange.append([i, j])
        if 2 in quadrants:
            quadRange = [[(i, j) for j in range(halfHeight)] for i in range(halfWidth, self.environmentWidth)]
            for i in range(halfWidth, self.environmentWidth):
                for j in range(halfHeight):
                    cellRange.append([i, j])
        if 3 in quadrants:
            quadRange = [[(i, j) for j in range(halfHeight, self.environmentHeight)] for i in range(halfWidth, self.environmentWidth)]
            for i in range(halfWidth, self.environmentWidth):
                for j in range(halfHeight, self.environmentHeight):
                    cellRange.append([i, j])
        if 4 in quadrants:
            quadRange = [[(i, j) for j in range(halfHeight, self.environmentHeight)] for i in range(halfWidth)]
            for i in range(halfWidth):
                for j in range(halfHeight, self.environmentHeight):
                    cellRange.append([i, j])
        return cellRange

    def generateAgentID(self):
        agentID = self.nextAgentID
        self.nextAgentID += 1
        return agentID

    def generateDiseaseID(self):
        diseaseID = self.nextDiseaseID
        self.nextDiseaseID += 1
        return diseaseID

    def pauseSimulation(self):
        while self.run == False:
            if self.gui != None and self.end == False:
                self.gui.window.update()
            if self.end == True:
                self.endSimulation()

    def randomizeDiseaseEndowments(self, numDiseases):
        configs = self.configuration
        sugarMetabolismPenalty = configs["diseaseSugarMetabolismPenalty"]
        spiceMetabolismPenalty = configs["diseaseSpiceMetabolismPenalty"]
        movementPenalty = configs["diseaseMovementPenalty"]
        visionPenalty = configs["diseaseVisionPenalty"]
        fertilityPenalty = configs["diseaseFertilityPenalty"]
        aggressionPenalty = configs["diseaseAggressionPenalty"]
        tagLengths = configs["diseaseTagStringLength"]

        minSugarMetabolismPenalty = sugarMetabolismPenalty[0]
        minSpiceMetabolismPenalty = spiceMetabolismPenalty[0]
        minMovementPenalty = movementPenalty[0]
        minVisionPenalty = visionPenalty[0]
        minFertilityPenalty = fertilityPenalty[0]
        minAggressionPenalty = aggressionPenalty[0]
        minTagLength = tagLengths[0]

        maxSugarMetabolismPenalty = sugarMetabolismPenalty[1]
        maxSpiceMetabolismPenalty = spiceMetabolismPenalty[1]
        maxMovementPenalty = movementPenalty[1]
        maxVisionPenalty = visionPenalty[1]
        maxFertilityPenalty = fertilityPenalty[1]
        maxAggressionPenalty = aggressionPenalty[1]
        maxTagLength = tagLengths[1]

        endowments = []
        sugarMetabolismPenalties = []
        spiceMetabolismPenalties = []
        movementPenalties = []
        visionPenalties = []
        fertilityPenalties = []
        aggressionPenalties = []
        diseaseTags = []

        currSugarMetabolismPenalty = minSugarMetabolismPenalty
        currSpiceMetabolismPenalty = minSpiceMetabolismPenalty
        currMovementPenalty = minMovementPenalty
        currVisionPenalty = minVisionPenalty
        currFertilityPenalty = minFertilityPenalty
        currAggressionPenalty = minAggressionPenalty
        currTagLength = minTagLength

        for i in range(numDiseases):
            sugarMetabolismPenalties.append(currSugarMetabolismPenalty)
            spiceMetabolismPenalties.append(currSpiceMetabolismPenalty)
            movementPenalties.append(currMovementPenalty)
            visionPenalties.append(currVisionPenalty)
            fertilityPenalties.append(currFertilityPenalty)
            aggressionPenalties.append(currAggressionPenalty)
            diseaseTags.append([random.randrange(2) for i in range(currTagLength)])

            currSugarMetabolismPenalty += 1
            currSpiceMetabolismPenalty += 1
            currMovementPenalty += 1
            currVisionPenalty += 1
            currFertilityPenalty += 1
            currAggressionPenalty += 1
            currTagLength += 1

            if currSugarMetabolismPenalty > maxSugarMetabolismPenalty:
                currSugarMetabolismPenalty = minSugarMetabolismPenalty
            if currSpiceMetabolismPenalty > maxSpiceMetabolismPenalty:
                currSpiceMetabolismPenalty = minSpiceMetabolismPenalty
            if currMovementPenalty > maxMovementPenalty:
                currMovementPenalty = minMovementPenalty
            if currVisionPenalty > maxVisionPenalty:
                currVisionPenalty = minVisionPenalty
            if currFertilityPenalty > maxFertilityPenalty:
                currFertilityPenalty = minFertilityPenalty
            if currAggressionPenalty > maxAggressionPenalty:
                currAggressionPenalty = minAggressionPenalty
            if currTagLength > maxTagLength:
                currTagLength = minTagLength

        randomDiseaseEndowment = {"sugarMetabolismPenalties": sugarMetabolismPenalties,
                     "spiceMetabolismPenalties": spiceMetabolismPenalties,
                     "movementPenalties": movementPenalties,
                     "visionPenalties": visionPenalties,
                     "fertilityPenalties": fertilityPenalties,
                     "aggressionPenalties": aggressionPenalties,
                     "diseaseTags": diseaseTags}

        # Map configuration to a random number via hash to make random number generation independent of iteration order
        if (self.diseaseConfigHashes == None):
            self.diseaseConfigHashes = {}
            for penalty in randomDiseaseEndowment:
                hashed = hashlib.md5(penalty.encode())
                self.diseaseConfigHashes[penalty] = int(hashed.hexdigest(), 16)

        # Keep state of random numbers to allow extending agent endowments without altering original random object state
        randomNumberReset = random.getstate()
        for endowment in randomDiseaseEndowment.keys():
            random.seed(self.diseaseConfigHashes[endowment] + self.timestep)
            random.shuffle(randomDiseaseEndowment[endowment])
        random.setstate(randomNumberReset)

        for i in range(numDiseases):
            diseaseEndowment = {"aggressionPenalty": aggressionPenalties.pop(),
                                "fertilityPenalty": fertilityPenalties.pop(),
                                "movementPenalty": movementPenalties.pop(),
                                "sugarMetabolismPenalty": sugarMetabolismPenalties.pop(),
                                "spiceMetabolismPenalty": spiceMetabolismPenalties.pop(),
                                "tags": diseaseTags.pop(),
                                "visionPenalty": visionPenalties.pop()}
            endowments.append(diseaseEndowment)
        return endowments

    def randomizeAgentEndowments(self, numAgents):
        configs = self.configuration
        spiceMetabolism = configs["agentSpiceMetabolism"]
        sugarMetabolism = configs["agentSugarMetabolism"]
        movement = configs["agentMovement"]
        vision = configs["agentVision"]
        startingSugar = configs["agentStartingSugar"]
        startingSpice = configs["agentStartingSpice"]
        maxAge = configs["agentMaxAge"]
        maleToFemaleRatio = configs["agentMaleToFemaleRatio"]
        femaleFertilityAge = configs["agentFemaleFertilityAge"]
        maleFertilityAge = configs["agentMaleFertilityAge"]
        femaleInfertilityAge = configs["agentFemaleInfertilityAge"]
        maleInfertilityAge = configs["agentMaleInfertilityAge"]
        tagStringLength = configs["agentTagStringLength"]
        immuneSystemLength = configs["agentImmuneSystemLength"]
        aggressionFactor = configs["agentAggressionFactor"]
        tradeFactor = configs["agentTradeFactor"]
        lookaheadFactor = configs["agentLookaheadFactor"]
        lendingFactor = configs["agentLendingFactor"]
        fertilityFactor = configs["agentFertilityFactor"]
        loanDuration = configs["agentLoanDuration"]
        baseInterestRate = configs["agentBaseInterestRate"]
        maxFriends = configs["agentMaxFriends"]
        inheritancePolicy = configs["agentInheritancePolicy"]
        decisionModelFactor = configs["agentDecisionModelFactor"]
        selfishnessFactor = configs["agentSelfishnessFactor"]
        decisionModel = configs["agentDecisionModel"]
        # Convert clever name for default behavior
        if decisionModel == "rawSugarscape":
            decisionModel = "none"
        universalSpice = configs["agentUniversalSpice"]
        universalSugar = configs["agentUniversalSugar"]
        movementMode = configs["agentMovementMode"]
        visionMode = configs["agentVisionMode"]

        configurations = {"aggressionFactor": {"endowments": [], "curr": aggressionFactor[0], "min": aggressionFactor[0], "max": aggressionFactor[1]},
                          "baseInterestRate": {"endowments": [], "curr": baseInterestRate[0], "min": baseInterestRate[0], "max": baseInterestRate[1]},
                          "decisionModelFactor": {"endowments": [], "curr": decisionModelFactor[0], "min": decisionModelFactor[0], "max": decisionModelFactor[1]},
                          "selfishnessFactor": {"endowments": [], "curr": selfishnessFactor[0], "min": selfishnessFactor[0], "max": selfishnessFactor[1]},
                          "femaleInfertilityAge": {"endowments": [], "curr": femaleInfertilityAge[0], "min": femaleInfertilityAge[0], "max": femaleInfertilityAge[1]},
                          "femaleFertilityAge": {"endowments": [], "curr": femaleFertilityAge[0], "min": femaleFertilityAge[0], "max": femaleFertilityAge[1]},
                          "fertilityFactor": {"endowments": [], "curr": fertilityFactor[0], "min": fertilityFactor[0], "max": fertilityFactor[1]},
                          "lendingFactor": {"endowments": [], "curr": lendingFactor[0], "min": lendingFactor[0], "max": lendingFactor[1]},
                          "loanDuration": {"endowments": [], "curr": loanDuration[0], "min": loanDuration[0], "max": loanDuration[1]},
                          "lookaheadFactor": {"endowments": [], "curr": lookaheadFactor[0], "min": lookaheadFactor[0], "max": lookaheadFactor[1]},
                          "maleInfertilityAge": {"endowments": [], "curr": maleInfertilityAge[0], "min": maleInfertilityAge[0], "max": maleInfertilityAge[1]},
                          "maleFertilityAge": {"endowments": [], "curr": maleFertilityAge[0], "min": maleFertilityAge[0], "max": maleFertilityAge[1]},
                          "maxAge": {"endowments": [], "curr": maxAge[0], "min": maxAge[0], "max": maxAge[1]},
                          "maxFriends": {"endowments": [], "curr": maxFriends[0], "min": maxFriends[0], "max": maxFriends[1]},
                          "movement": {"endowments": [], "curr": movement[0], "min": movement[0], "max": movement[1]},
                          "spice": {"endowments": [], "curr": startingSpice[0], "min": startingSpice[0], "max": startingSpice[1]},
                          "spiceMetabolism": {"endowments": [], "curr": spiceMetabolism[0], "min": spiceMetabolism[0], "max": spiceMetabolism[1]},
                          "sugar": {"endowments": [], "curr": startingSugar[0], "min": startingSugar[0], "max": startingSugar[1]},
                          "sugarMetabolism": {"endowments": [], "curr": sugarMetabolism[0], "min": sugarMetabolism[0], "max": sugarMetabolism[1]},
                          "tradeFactor": {"endowments": [], "curr": tradeFactor[0], "min": tradeFactor[0], "max": tradeFactor[1]},
                          "vision": {"endowments": [], "curr": vision[0], "min": vision[0], "max": vision[1]},
                          "universalSpice": {"endowments": [], "curr": universalSpice[0], "min": universalSpice[0], "max": universalSugar[1]},
                          "universalSugar": {"endowments": [], "curr": universalSugar[0], "min": universalSugar[0], "max": universalSugar[1]}
                          }

        if self.agentConfigHashes == None:
            self.agentConfigHashes = {}
            # Map configuration to a random number via hash to make random number generation independent of iteration order
            for config in configurations.keys():
                hashed = hashlib.md5(config.encode())
                hashNum = int(hashed.hexdigest(), 16)
                self.agentConfigHashes[config] = hashNum

        for config in configurations:
            configMin = configurations[config]["min"]
            configMax = configurations[config]["max"]
            configMinDecimals = str(configMin).split('.')
            configMaxDecimals = str(configMax).split('.')
            decimalRange = []
            if len(configMinDecimals) == 2:
                configMinDecimals = len(configMinDecimals[1])
                decimalRange.append(configMinDecimals)
            if len(configMaxDecimals) == 2:
                configMaxDecimals = len(configMaxDecimals[1])
                decimalRange.append(configMaxDecimals)
            # If no fractional component to configuration item, assume increment of 1
            decimals = max(decimalRange) if len(decimalRange) > 0 else 0
            increment = 10 ** (-1 * decimals)
            configurations[config]["inc"] = increment
            configurations[config]["decimals"] = decimals

        endowments = []
        sexes = []
        tags = []
        immuneSystems = []

        sexDistributionCountdown = numAgents
        # Determine count of male agents and set as switch for agent generation
        if maleToFemaleRatio != None and maleToFemaleRatio != 0:
            sexDistributionCountdown = math.floor(sexDistributionCountdown / (maleToFemaleRatio + 1)) * maleToFemaleRatio

        for i in range(numAgents):
            for config in configurations:
                configurations[config]["endowments"].append(configurations[config]["curr"])
                configurations[config]["curr"] += configurations[config]["inc"]
                configurations[config]["curr"] = round(configurations[config]["curr"], configurations[config]["decimals"])
                if configurations[config]["curr"] > configurations[config]["max"]:
                    configurations[config]["curr"] = configurations[config]["min"]

            if tagStringLength > 0:
                tags.append([random.randrange(2) for i in range(tagStringLength)])
            else:
                tags.append(None)
            if immuneSystemLength > 0:
                immuneSystems.append([random.randrange(2) for i in range(immuneSystemLength)])
            else:
                immuneSystems.append(None)

            if maleToFemaleRatio != None and maleToFemaleRatio != 0:
                if sexDistributionCountdown == 0:
                    sexes.append("female")
                else:
                    sexes.append("male")
                    sexDistributionCountdown -= 1
            else:
                sexes.append(None)

        # Keep state of random numbers to allow extending agent endowments without altering original random object state
        randomNumberReset = random.getstate()
        for config in configurations:
            random.seed(self.agentConfigHashes[config] + self.timestep)
            random.shuffle(configurations[config]["endowments"])
        random.setstate(randomNumberReset)
        random.shuffle(sexes)
        for i in range(numAgents):
            agentEndowment = {"seed": self.seed, "sex": sexes[i], "tags": tags.pop(),
                              "immuneSystem": immuneSystems.pop(), "inheritancePolicy": inheritancePolicy,
                              "decisionModel": decisionModel, "movementMode": movementMode,
                              "visionMode": visionMode}
            for config in configurations:
                # If sexes are enabled, ensure proper fertility and infertility ages are set
                if sexes[i] == "female" and config == "femaleFertilityAge":
                    agentEndowment["fertilityAge"] = configurations["femaleFertilityAge"]["endowments"].pop()
                elif sexes[i] == "female" and config == "femaleInfertilityAge":
                    agentEndowment["infertilityAge"] = configurations["femaleInfertilityAge"]["endowments"].pop()
                elif sexes[i] == "male" and config == "maleFertilityAge":
                    agentEndowment["fertilityAge"] = configurations["maleFertilityAge"]["endowments"].pop()
                elif sexes[i] == "male" and config == "maleInfertilityAge":
                    agentEndowment["infertilityAge"] = configurations["maleInfertilityAge"]["endowments"].pop()
                elif sexes[i] == None and (config == "femaleInfertilityAge" or config == "femaleFertilityAge" or
                                           config == "maleInfertilityAge" or config == "maleFertilityAge"):
                    continue
                else:
                    agentEndowment[config] = configurations[config]["endowments"].pop()

            if sexes[i] == None:
                agentEndowment["fertilityAge"] = 0
                agentEndowment["infertilityAge"] = 0
            endowments.append(agentEndowment)
        return endowments

    def removeDeadAgents(self):
        deadAgents = []
        for agent in self.agents:
            if agent.isAlive() == False:
                deadAgents.append(agent)
            elif agent.cell == None:
                deadAgents.append(agent)
        self.deadAgents += deadAgents
        for agent in deadAgents:
            self.agents.remove(agent)

    def replaceDeadAgents(self):
        numAgents = len(self.agents)
        if numAgents < self.configuration["agentReplacements"]:
            numReplacements = self.configuration["agentReplacements"] - numAgents
            self.configureAgents(numReplacements)
            if self.gui != None:
                self.gui.doTimestep()

    def runSimulation(self, timesteps=5):
        self.startLog()
        if self.gui != None:
            # Simulation begins paused until start button in GUI pressed
            self.pauseSimulation()
        t = 1
        timesteps = timesteps - self.timestep
        screenshots = 0
        while t <= timesteps and len(self.agents) > 0:
            if self.configuration["screenshots"] == True:
                self.gui.canvas.postscript(file="screenshot{0}.ps".format(psacc), colormode="color")
                screenshots += 1
            self.doTimestep()
            t += 1
            if self.gui != None and self.run == False:
                self.pauseSimulation()
        self.endSimulation()

    def startLog(self):
        if self.log == None:
            return
        self.log.write("[\n")
        self.updateRuntimeStats()
        self.writeToLog()

    def toggleEnd(self):
        self.end = True

    def toggleRun(self):
        self.run = not self.run

    def updateGiniCoefficient(self):
        agentWealths = sorted([agent.wealth for agent in self.agents])
        # Calculate area between line of equality and Lorenz curve of agent wealths
        height = 0
        area = 0
        for wealth in agentWealths:
            height += wealth
            area += (height - wealth) / 2
        lineOfEquality = (height * len(agentWealths)) / 2
        giniCoefficient = round((lineOfEquality - area) / max(1, lineOfEquality), 2)
        return giniCoefficient

    def updateRuntimeStats(self):
        numAgents = len(self.agents)
        meanSugarMetabolism = 0
        meanSpiceMetabolism = 0
        meanMetabolism = 0
        meanMovement = 0
        meanVision = 0
        meanWealth = 0
        meanAge = 0
        meanTradePrice = 0
        tradeVolume = 0
        maxWealth = 0
        minWealth = sys.maxsize
        meanHappiness = 0
        meanHealthHappiness = 0
        meanWealthHappiness = 0
        meanSocialHappiness = 0
        meanFamilyHappiness = 0
        meanConflictHappiness = 0
        numTraders = 0
        totalWealthLost = 0
        totalMetabolismCost = 0

        # Log per-agent stats every quarter of the total runtime
        perAgentStatsInterval = self.maxTimestep / 4
        perAgentStatsCheck = self.timestep % perAgentStatsInterval
        wealths = []
        timesToLive = []
        timesToLiveAgeLimited = []
        sugarMetabolisms = []
        spiceMetabolisms = []

        environmentWealthCreated = 0
        environmentWealthTotal = 0
        for i in range(self.environment.height):
            for j in range(self.environment.width):
                environmentWealthCreated += self.environment.grid[i][j].sugarLastProduced + self.environment.grid[i][j].spiceLastProduced
                environmentWealthTotal += self.environment.grid[i][j].sugar + self.environment.grid[i][j].spice
                if self.timestep == 1:
                    environmentWealthCreated += self.environment.grid[i][j].maxSugar + self.environment.grid[i][j].maxSpice

        agentWealthCollected = 0
        agentWealthTotal = 0
        agentStarvationDeaths = 0
        agentDiseaseDeaths = 0
        agentCombatDeaths = 0
        agentAgingDeaths = 0
        agentWealthBurnRate = 0
        agentMeanTimeToLive = 0
        agentReproduced = 0
        agentTotalMetabolism = 0

        for agent in self.agents:
            agentTimeToLive = agent.findTimeToLive()
            agentTimeToLiveAgeLimited = agent.findTimeToLive(True)
            meanSugarMetabolism += agent.sugarMetabolism
            meanSpiceMetabolism += agent.spiceMetabolism
            meanMovement += agent.movement
            meanVision += agent.vision
            meanAge += agent.age
            meanWealth += agent.wealth
            meanHappiness += agent.happiness
            meanWealthHappiness += agent.wealthHappiness
            meanHealthHappiness += agent.healthHappiness
            meanFamilyHappiness += agent.familyHappiness
            meanSocialHappiness += agent.socialHappiness
            meanConflictHappiness += agent.conflictHappiness
            if agent.tradeVolume > 0:
                meanTradePrice += max(agent.spicePrice, agent.sugarPrice)
                tradeVolume += agent.tradeVolume
                numTraders += 1
            agentWealthTotal += agent.wealth
            agentWealthCollected += agent.wealth - (agent.lastSugar + agent.lastSpice)
            agentWealthBurnRate += agentTimeToLive
            agentMeanTimeToLive += agentTimeToLiveAgeLimited
            agentReproduced += agent.lastReproduced
            agentTotalMetabolism += agent.sugarMetabolism + agent.spiceMetabolism

            if agent.wealth < minWealth:
                minWealth = agent.wealth
            if agent.wealth > maxWealth:
                maxWealth = agent.wealth
            totalMetabolismCost += agent.sugarMetabolism + agent.spiceMetabolism

            if perAgentStatsCheck == 0 and self.timestep != 0:
                wealths.append(agent.wealth)
                timesToLive.append(agentTimeToLive)
                timesToLiveAgeLimited.append(agentTimeToLiveAgeLimited)
                sugarMetabolisms.append(agent.sugarMetabolism)
                spiceMetabolisms.append(agent.spiceMetabolism)

        if numAgents > 0:
            combinedMetabolism = meanSugarMetabolism + meanSpiceMetabolism
            if meanSugarMetabolism > 0 and meanSpiceMetabolism > 0:
                combinedMetabolism = round(combinedMetabolism / 2, 2)
            meanMetabolism = round(combinedMetabolism / numAgents, 2)
            meanMovement = round(meanMovement / numAgents, 2)
            meanVision = round(meanVision / numAgents, 2)
            meanAge = round(meanAge / numAgents, 2)
            meanWealth = round(meanWealth / numAgents, 2)
            meanTradePrice = round(meanTradePrice / numTraders, 2) if numTraders > 0 else 0
            tradeVolume = round(tradeVolume, 2)
            agentWealthTotal = round(agentWealthTotal, 2)
            minWealth = round(minWealth, 2)
            maxWealth = round(maxWealth, 2)
            meanHappiness = round(meanHappiness / numAgents, 2)
            meanWealthHappiness = round(meanWealthHappiness / numAgents, 2)
            meanHealthHappiness = round(meanHealthHappiness / numAgents, 2)
            meanFamilyHappiness = round(meanFamilyHappiness / numAgents, 2)
            meanSocialHappiness = round(meanSocialHappiness / numAgents, 2)
            meanConflictHappiness = round(meanConflictHappiness / numAgents, 2)
            agentWealthBurnRate = round(agentWealthBurnRate / numAgents, 2)
            agentMeanTimeToLive = round(agentMeanTimeToLive / numAgents, 2)
        else:
            meanMetabolism = 0
            meanMovement = 0
            meanVision = 0
            meanAge = 0
            meanWealth = 0
            minWealth = 0
            maxWealth = 0
            meanHappiness = 0
            meanWealthHappiness = 0
            meanHealthHappiness = 0
            meanFamilyHappiness = 0
            meanSocialHappiness = 0
            meanConflictHappiness = 0
            tradeVolume = 0
            agentWealthBurnRate = 0
            agentMeanTimeToLive = 0

        numDeadAgents = len(self.deadAgents)
        meanAgeAtDeath = 0
        for agent in self.deadAgents:
            meanAgeAtDeath += agent.age
            agentWealthCollected += agent.wealth - (agent.lastSugar + agent.lastSpice)
            totalWealthLost += agent.sugar + agent.spice
            agentReproduced += agent.lastReproduced
            agentStarvationDeaths += 1 if agent.causeOfDeath == "starvation" else 0
            agentDiseaseDeaths += 1 if agent.causeOfDeath == "disease" else 0
            agentCombatDeaths += 1 if agent.causeOfDeath == "combat" else 0
            agentAgingDeaths += 1 if agent.causeOfDeath == "aging" else 0
        meanAgeAtDeath = round(meanAgeAtDeath / numDeadAgents, 2) if numDeadAgents > 0 else 0
        self.deadAgents = []

        self.runtimeStats["timestep"] = self.timestep
        self.runtimeStats["population"] = numAgents
        self.runtimeStats["meanMetabolism"] = meanMetabolism
        self.runtimeStats["meanMovement"] = meanMovement
        self.runtimeStats["meanVision"] = meanVision
        self.runtimeStats["meanAge"] = meanAge

        # TODO: make clear whether agent or environment calculation
        self.runtimeStats["meanWealth"] = meanWealth
        self.runtimeStats["minWealth"] = minWealth
        self.runtimeStats["maxWealth"] = maxWealth
        self.runtimeStats["meanHappiness"] = meanHappiness
        self.runtimeStats["meanWealthHappiness"] = meanWealthHappiness
        self.runtimeStats["meanHealthHappiness"] = meanHealthHappiness
        self.runtimeStats["meanFamilyHappiness"] = meanFamilyHappiness
        self.runtimeStats["meanSocialHappiness"] = meanSocialHappiness
        self.runtimeStats["meanConflictHappiness"] = meanConflictHappiness
        self.runtimeStats["meanTradePrice"] = meanTradePrice
        self.runtimeStats["tradeVolume"] = tradeVolume
        self.runtimeStats["giniCoefficient"] = self.updateGiniCoefficient() if len(self.agents) > 1 else 0
        self.runtimeStats["meanAgeAtDeath"] = meanAgeAtDeath
        self.runtimeStats["totalWealthLost"] += totalWealthLost
        self.runtimeStats["totalMetabolismCost"] += totalMetabolismCost

        self.runtimeStats["agentStarvationDeaths"] = agentStarvationDeaths
        self.runtimeStats["agentDiseaseDeaths"] = agentDiseaseDeaths
        self.runtimeStats["agentCombatDeaths"] = agentCombatDeaths
        self.runtimeStats["agentAgingDeaths"] = agentAgingDeaths
        self.runtimeStats["agentReproduced"] = agentReproduced
        self.runtimeStats["agentWealthCollected"] = agentWealthCollected
        self.runtimeStats["agentWealthTotal"] = agentWealthTotal
        self.runtimeStats["agentWealthBurnRate"] = agentWealthBurnRate
        self.runtimeStats["agentMeanTimeToLive"] = agentMeanTimeToLive
        self.runtimeStats["environmentWealthCreated"] = environmentWealthCreated
        self.runtimeStats["environmentWealthTotal"] = environmentWealthTotal

        self.runtimeStats["agentWealths"] = wealths
        self.runtimeStats["agentTimesToLive"] = timesToLive
        self.runtimeStats["agentTimesToLiveAgeLimited"] = timesToLiveAgeLimited
        self.runtimeStats["agentTotalMetabolism"] = agentTotalMetabolism

    def writeToLog(self):
        if self.log == None:
            return
        logString = '\t' + json.dumps(self.runtimeStats) + ",\n"
        self.log.write(logString)

    def __str__(self):
        string = "{0}Seed: {1}\nTimestep: {2}\nLiving Agents: {3}".format(str(self.environment), self.seed, self.timestep, len(self.agents))
        return string

def parseConfiguration(configFile, configuration):
    file = open(configFile)
    options = json.loads(file.read())
    # If using the top-level config file, access correct JSON object
    if "sugarscapeOptions" in options:
        options = options["sugarscapeOptions"]

    # Keep compatibility with outdated configuration files
    optkeys = options.keys()
    if "agentEthicalTheory" in optkeys:
        options["agentDecisionModel"] = options["agentEthicalTheory"]
    if "agentEthicalFactor" in optkeys:
        options["agentDecisionModelFactor"] = options["agentEthicalFactor"]

    for opt in configuration:
        if opt in options:
            configuration[opt] = options[opt]
    return configuration

def parseOptions(configuration):
    commandLineArgs = sys.argv[1:]
    shortOptions = "c:h:"
    longOptions = ["conf=", "help"]
    try:
        args, vals = getopt.getopt(commandLineArgs, shortOptions, longOptions)
    except getopt.GetoptError as err:
        print(err)
        printHelp()
    nextArg = 0
    for currArg, currVal in args:
        nextArg += 1
        if currArg in("-c", "--conf"):
            if currVal == "":
                print("No config file provided.")
                printHelp()
            parseConfiguration(currVal, configuration)
        elif currArg in ("-h", "--help"):
            printHelp()
    return configuration

def printHelp():
    print("Usage:\n\tpython sugarscape.py --conf config.json\n\nOptions:\n\t-c,--conf\tUse specified config file for simulation settings.\n\t-h,--help\tDisplay this message.")
    exit(0)

def verifyConfiguration(configuration):
    # Ensure starting agents are not larger than available cells
    totalCells = configuration["environmentHeight"] * configuration["environmentWidth"]
    if configuration["startingAgents"] > totalCells:
        if "all" in configuration["debugMode"] or "sugarscape" in configuration["debugMode"]:
            print("Could not allocate {0} agents. Allocating maximum of {1}.".format(configuration["startingAgents"], totalCells))
        configuration["startingAgents"] = totalCells

    # Ensure infinitely-lived agents are properly initialized
    if configuration["agentMaxAge"][0] < 0 or configuration["agentMaxAge"][1] < 0:
        configuration["agentMaxAge"][0] = -1
        configuration["agentMaxAge"][1] = -1

    # Ensure at most number of tribes equal to agent tag string length
    if configuration["agentTagStringLength"] > 0 and configuration["environmentMaxTribes"] > configuration["agentTagStringLength"]:
        configuration["environmentMaxTribes"] = configuration["agentTagStringLength"]
    if configuration["environmentMaxTribes"] > 11:
        configuration["environmentMaxTribes"] = 11

    # Keep compatibility with outdated configuration files
    if configuration["agentDecisionModel"] == "rawSugarscape":
        configuration["agentDecisionModel"] = "none"

    if len(configuration["agentStartingQuadrants"]) == 0:
        configuration["agentStartingQuadrants"] = [1, 2, 3, 4]

    # Set timesteps to (seemingly) unlimited runtime
    if configuration["timesteps"] < 0:
        configuration["timesteps"] = sys.maxsize

    if configuration["seed"] == -1:
        configuration["seed"] = random.randrange(sys.maxsize)

    if configuration["logfile"] == "":
        configuration["logfile"] = None

    recognizedDebugModes = ["agent", "all", "cell", "disease", "environment", "ethics", "none", "sugarscape"]
    validModes = True
    for mode in configuration["debugMode"]:
        if mode not in recognizedDebugModes:
            print("Debug mode {0} not recognized".format(mode))
            validModes = False
    if validModes == False:
        printHelp()

    if "all" in configuration["debugMode"] and "none" in configuration["debugMode"]:
        print("Cannot have \"all\" and \"none\" debug modes enabled at the same time")
        printHelp()
    elif "all" in configuration["debugMode"] and len(configuration["debugMode"]) > 1:
        configuration["debugMode"] = "all"
    elif "none" in configuration["debugMode"] and len(configuration["debugMode"]) > 1:
        configuration["debugMode"] = "none"

    return configuration

if __name__ == "__main__":
    # Set default values for simulation configuration
    configuration = {"agentAggressionFactor": [0, 0],
                     "agentBaseInterestRate": [0.0, 0.0],
                     "agentDecisionModel": "none",
                     "agentDecisionModelFactor": [0, 0],
                     "agentFemaleInfertilityAge": [0, 0],
                     "agentFemaleFertilityAge": [0, 0],
                     "agentFertilityFactor": [0, 0],
                     "agentImmuneSystemLength": 0,
                     "agentInheritancePolicy": "none",
                     "agentLendingFactor": [0, 0],
                     "agentLoanDuration": [0, 0],
                     "agentLookaheadFactor": [0, 0],
                     "agentMaleInfertilityAge": [0, 0],
                     "agentMaleFertilityAge": [0, 0],
                     "agentMaleToFemaleRatio": 1.0,
                     "agentMaxAge": [-1, -1],
                     "agentMaxFriends": [0, 0],
                     "agentMovement": [1, 6],
                     "agentMovementMode": "cardinal",
                     "agentReplacements": 0,
                     "agentSelfishnessFactor": [-1, -1],
                     "agentSpiceMetabolism": [0, 0],
                     "agentStartingSpice": [0, 0],
                     "agentStartingSugar": [10, 40],
                     "agentStartingQuadrants": [1, 2, 3, 4],
                     "agentSugarMetabolism": [1, 4],
                     "agentTagStringLength": 0,
                     "agentTradeFactor": [0, 0],
                     "agentUniversalSpice": [0,0],
                     "agentUniversalSugar": [0,0],
                     "agentVision": [1, 6],
                     "agentVisionMode": "cardinal",
                     "debugMode": ["none"],
                     "diseaseAggressionPenalty": [0, 0],
                     "diseaseFertilityPenalty": [0, 0],
                     "diseaseMovementPenalty": [0, 0],
                     "diseaseSpiceMetabolismPenalty": [0, 0],
                     "diseaseSugarMetabolismPenalty": [0, 0],
                     "diseaseTagStringLength": [0, 0],
                     "diseaseVisionPenalty": [0, 0],
                     "environmentHeight": 50,
                     "environmentMaxCombatLoot": 0,
                     "environmentMaxSpice": 0,
                     "environmentMaxSugar": 4,
                     "environmentMaxTribes": 0,
                     "environmentPollutionDiffusionDelay": 0,
                     "environmentSeasonalGrowbackDelay": 0,
                     "environmentSeasonInterval": 0,
                     "environmentSpiceConsumptionPollutionFactor": 0,
                     "environmentSpiceProductionPollutionFactor": 0,
                     "environmentSpiceRegrowRate": 0,
                     "environmentSugarConsumptionPollutionFactor": 0,
                     "environmentSugarProductionPollutionFactor": 0,
                     "environmentSugarRegrowRate": 1,
                     "environmentUniversalSpiceIncomeInterval": 0,
                     "environmentUniversalSugarIncomeInterval": 0,
                     "environmentWidth": 50,
                     "headlessMode": False,
                     "interfaceHeight": 1000,
                     "interfaceWidth": 900,
                     "logfile": None,
                     "profileMode": False,
                     "screenshots": False,
                     "seed": -1,
                     "startingAgents": 250,
                     "startingDiseases": 0,
                     "timesteps": 200
                     }
    configuration = parseOptions(configuration)
    configuration = verifyConfiguration(configuration)
    if configuration["headlessMode"] == False:
        import gui
    random.seed(configuration["seed"])
    S = Sugarscape(configuration)
    if configuration["profileMode"] == True:
        import cProfile
        import tracemalloc
        tracemalloc.start()
        cProfile.run("S.runSimulation(configuration[\"timesteps\"])")
        snapshot = tracemalloc.take_snapshot()
        memoryStats = snapshot.statistics("lineno", True)
        for stat in memoryStats[:100]:
            print(stat)
    else:
        S.runSimulation(configuration["timesteps"])
    exit(0)
