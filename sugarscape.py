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
        self.agentConfigHashes = None
        self.diseaseConfigHashes = None
        self.configuration = configuration
        self.maxTimestep = configuration["timesteps"]
        self.timestep = 0
        self.nextAgentID = 0
        self.nextDiseaseID = 0
        environmentConfiguration = {"equator": configuration["environmentEquator"],
                                    "globalMaxSpice": configuration["environmentMaxSpice"],
                                    "globalMaxSugar": configuration["environmentMaxSugar"],
                                    "maxCombatLoot": configuration["environmentMaxCombatLoot"],
                                    "neighborhoodMode": configuration["neighborhoodMode"],
                                    "pollutionDiffusionDelay": configuration["environmentPollutionDiffusionDelay"],
                                    "pollutionDiffusionTimeframe": configuration["environmentPollutionDiffusionTimeframe"],
                                    "pollutionTimeframe": configuration["environmentPollutionTimeframe"],
                                    "seasonalGrowbackDelay": configuration["environmentSeasonalGrowbackDelay"],
                                    "seasonInterval": configuration["environmentSeasonInterval"],
                                    "spiceConsumptionPollutionFactor": configuration["environmentSpiceConsumptionPollutionFactor"],
                                    "spiceProductionPollutionFactor": configuration["environmentSpiceProductionPollutionFactor"],
                                    "spiceRegrowRate": configuration["environmentSpiceRegrowRate"],
                                    "sugarConsumptionPollutionFactor": configuration["environmentSugarConsumptionPollutionFactor"],
                                    "sugarProductionPollutionFactor": configuration["environmentSugarProductionPollutionFactor"],
                                    "sugarRegrowRate": configuration["environmentSugarRegrowRate"],
                                    "sugarscapeSeed": configuration["seed"],
                                    "universalSpiceIncomeInterval": configuration["environmentUniversalSpiceIncomeInterval"],
                                    "universalSugarIncomeInterval": configuration["environmentUniversalSugarIncomeInterval"],
                                    "wraparound": configuration["environmentWraparound"]}
        self.seed = configuration["seed"]
        self.environment = environment.Environment(configuration["environmentHeight"], configuration["environmentWidth"], self, environmentConfiguration)
        self.environmentHeight = configuration["environmentHeight"]
        self.environmentWidth = configuration["environmentWidth"]
        self.configureEnvironment(configuration["environmentMaxSugar"], configuration["environmentMaxSpice"], configuration["environmentSugarPeaks"], configuration["environmentSpicePeaks"])
        self.debug = configuration["debugMode"]
        self.keepAlive = configuration["keepAlivePostExtinction"]
        self.agents = []
        self.replacedAgents = []
        self.bornAgents = []
        self.deadAgents = []
        self.diseases = []
        self.diseasesCount = [[] for i in range(configuration["diseaseStartTimeframe"][1] + 1)]
        self.activeQuadrants = self.findActiveQuadrants()
        self.configureAgents(configuration["startingAgents"])
        self.configureDiseases(configuration["startingDiseases"])
        self.gui = gui.GUI(self, self.configuration["interfaceHeight"], self.configuration["interfaceWidth"]) if configuration["headlessMode"] == False else None
        self.run = False # Simulation start flag
        self.end = False # Simulation end flag
        # TODO: Remove redundant metrics
        # TODO: Streamline naming
        self.runtimeStats = {"timestep": 0, "population": 0, "meanMetabolism": 0, "meanMovement": 0, "meanVision": 0, "meanWealth": 0, "meanAge": 0, "giniCoefficient": 0,
                             "meanTradePrice": 0, "tradeVolume": 0, "maxWealth": 0, "minWealth": 0, "meanHappiness": 0, "meanWealthHappiness": 0, "meanHealthHappiness": 0,
                             "meanSocialHappiness": 0, "meanFamilyHappiness": 0, "meanConflictHappiness": 0, "meanAgeAtDeath": 0, "seed": self.seed, "agentsReplaced": 0,
                             "agentsBorn": 0, "agentStarvationDeaths": 0, "agentDiseaseDeaths": 0, "environmentWealthCreated": 0, "agentWealthTotal": 0,
                             "environmentWealthTotal": 0, "agentWealthCollected": 0, "agentWealthBurnRate": 0, "agentMeanTimeToLive": 0, "agentTotalMetabolism": 0,
                             "agentCombatDeaths": 0, "agentAgingDeaths": 0, "agentDeaths": 0, "largestTribe": 0, "largestTribeSize": 0,
                             "remainingTribes": self.configuration["environmentMaxTribes"], "sickAgents": 0}        
        diseaseStats = {}
        for disease in self.diseases:
            diseaseStats[f"disease{disease.ID}Incidence"] = 0
            diseaseStats[f"disease{disease.ID}Prevalence"] = 0
            diseaseStats[f"disease{disease.ID}RValue"] = 0.0
        self.runtimeStats.update(diseaseStats)
        self.graphStats = {"ageBins": [], "sugarBins": [], "spiceBins": [], "lorenzCurvePoints": [], "meanTribeTags": [],
                           "maxSugar": 0, "maxSpice": 0, "maxWealth": 0}
        self.log = open(configuration["logfile"], 'a') if configuration["logfile"] != None else None
        self.logFormat = configuration["logfileFormat"]
        self.experimentalGroup = configuration["experimentalGroup"]
        if self.experimentalGroup != None:
            # Convert keys to Pythonic case scheme and initialize values
            groupRuntimeStats = {}
            for key in self.runtimeStats.keys():
                controlGroupKey = "control" + key[0].upper() + key[1:]
                experimentalGroupKey = self.experimentalGroup + key[0].upper() + key[1:]
                groupRuntimeStats[controlGroupKey] = 0
                groupRuntimeStats[experimentalGroupKey] = 0
            self.runtimeStats.update(groupRuntimeStats)

    def addAgent(self, agent):
        self.bornAgents.append(agent)
        self.agents.append(agent)

    def addSpicePeak(self, startX, startY, radius, maxSpice):
        height = self.environment.height
        width = self.environment.width
        radialDispersion = math.sqrt(max(startX, width - startX)**2 + max(startY, height - startY)**2) * (radius / width)
        for i in range(width):
            for j in range(height):
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
        for i in range(width):
            for j in range(height):
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

        emptyCells = [[cell for cell in quadrant if cell.agent == None] for quadrant in self.activeQuadrants]
        totalCells = sum(len(quadrant) for quadrant in emptyCells)
        quadrants = len(emptyCells)
        if totalCells == 0:
            return
        if numAgents > totalCells:
            if "all" in self.debug or "sugarscape" in self.debug:
                print(f"Could not allocate {numAgents} agents. Allocating maximum of {totalCells}.")
            numAgents = totalCells

        # Ensure agent endowments are randomized across initial agent count to make replacements follow same distributions
        agentEndowments = self.randomizeAgentEndowments(numAgents)
        for quadrant in emptyCells:
            random.shuffle(quadrant)
        quadrantIndices = [i for i in range(quadrants)]
        random.shuffle(quadrantIndices)

        for i in range(numAgents):
            quadrantIndex = quadrantIndices[i % quadrants]
            randomCell = emptyCells[quadrantIndex].pop()
            agentConfiguration = agentEndowments[i]
            agentID = self.generateAgentID()
            a = agent.Agent(agentID, self.timestep, randomCell, agentConfiguration)
            # If using a different decision model, replace new agent with instance of child class
            if "altruist" in agentConfiguration["decisionModel"]:
                a = ethics.Bentham(agentID, self.timestep, randomCell, agentConfiguration)
                a.selfishnessFactor = 0
            elif "bentham" in agentConfiguration["decisionModel"]:
                a = ethics.Bentham(agentID, self.timestep, randomCell, agentConfiguration)
                if agentConfiguration["selfishnessFactor"] < 0:
                    a.selfishnessFactor = 0.5
            elif "egoist" in agentConfiguration["decisionModel"]:
                a = ethics.Bentham(agentID, self.timestep, randomCell, agentConfiguration)
                a.selfishnessFactor = 1
            elif "negativeBentham" in agentConfiguration["decisionModel"]:
                a = ethics.Bentham(agentID, self.timestep, randomCell, agentConfiguration)
                a.selfishnessFactor = -1

            if "NoLookahead" in agentConfiguration["decisionModel"]:
                a.decisionModelLookaheadFactor = 0
            elif "HalfLookahead" in agentConfiguration["decisionModel"]:
                a.decisionModelLookaheadFactor = 0.5
            if self.configuration["environmentTribePerQuadrant"] == True:
                tribe = quadrantIndex
                tags = self.generateTribeTags(tribe)
                a.tags = tags
                a.tribe = a.findTribe()
            randomCell.agent = a
            self.agents.append(a)
            if self.timestep > 0:
                self.replacedAgents.append(a)

        for a in self.agents:
            a.findCellsInRange()
            a.findNeighborhood()

    def configureDiseases(self, numDiseases):
        numAgents = len(self.agents)
        if numAgents == 0:
            return
        elif numAgents < numDiseases:
            numDiseases = numAgents

        diseaseEndowments = self.randomizeDiseaseEndowments(numDiseases)
        for i in range(numDiseases):
            diseaseID = self.generateDiseaseID()
            diseaseConfiguration = diseaseEndowments[i]
            newDisease = disease.Disease(diseaseID, diseaseConfiguration)
            timestep = diseaseConfiguration["startTimestep"]
            self.diseases.append(newDisease)
            self.diseasesCount[timestep].append(newDisease)
        self.infectAgents()

    def infectAgents(self):
        timestep = self.timestep
        if timestep > self.configuration["diseaseStartTimeframe"][1]:
            return
        diseases = self.diseasesCount[timestep]
        if len(diseases) == 0:
            return
        startingDiseases = self.configuration["startingDiseasesPerAgent"]
        minStartingDiseases = startingDiseases[0]
        maxStartingDiseases = startingDiseases[1]
        currStartingDiseases = minStartingDiseases
        random.shuffle(self.agents)
        random.shuffle(diseases)
        for agent in self.agents:
            for newDisease in diseases:
                if newDisease.startingInfectedAgents == 1 and startingDiseases == [0, 0]:
                    continue
                if agent.startingDiseases >= currStartingDiseases and startingDiseases != [0, 0]:
                    currStartingDiseases += 1
                    break
                if agent.canCatchDisease(newDisease) == False:
                    continue
                agent.catchDisease(newDisease)
                if startingDiseases == [0, 0]:
                    diseases.remove(newDisease)
                    break
            if currStartingDiseases > maxStartingDiseases:
                currStartingDiseases = minStartingDiseases
        if startingDiseases == [0, 0] and self.timestep == self.configuration["diseaseStartTimeframe"][1] and len(diseases) > 0:
            if  "all" in self.debug or "sugarscape" in self.debug:
                print(f"Could not place {len(diseases)} diseases.")

    def configureEnvironment(self, maxSugar, maxSpice, sugarPeaks, spicePeaks):
        height = self.environment.height
        width = self.environment.width
        for i in range(width):
            for j in range(height):
                newCell = cell.Cell(i, j, self.environment)
                self.environment.setCell(newCell, i, j)

        sugarRadiusScale = 2
        radius = math.ceil(math.sqrt(sugarRadiusScale * (height + width)))
        for peak in sugarPeaks:
            self.addSugarPeak(peak[0], peak[1], radius, maxSugar)

        spiceRadiusScale = 2
        radius = math.ceil(math.sqrt(spiceRadiusScale * (height + width)))
        for peak in spicePeaks:
            self.addSpicePeak(peak[0], peak[1], radius, maxSpice)
        self.environment.findCellNeighbors()
        self.environment.findCellRanges()

    def countInfectedAgents(self, disease):
        totalInfected = 0
        for agent in self.agents:
            combinedDiseases = agent.incubatingDiseases + agent.symptomaticDiseases
            for agentDisease in combinedDiseases:
                if disease == agentDisease["disease"]:
                    totalInfected += 1
        return totalInfected

    def doTimestep(self):
        if self.timestep >= self.maxTimestep:
            self.toggleEnd()
            return
        for disease in self.diseases:
            disease.resetRStats()
        if "all" in self.debug or "sugarscape" in self.debug:
            print(f"Timestep: {self.timestep}\nLiving Agents: {len(self.agents)}")
        self.timestep += 1
        if self.end == True or (len(self.agents) == 0 and self.keepAlive == False):
            self.toggleEnd()
        else:
            self.environment.doTimestep(self.timestep)
            self.infectAgents()
            random.shuffle(self.agents)
            for agent in self.agents:
                agent.doTimestep(self.timestep)
            self.removeDeadAgents()
            self.replaceDeadAgents()
            self.updateRuntimeStats()
            if self.gui != None:
                self.updateGraphStats()
                self.gui.doTimestep()
            # If final timestep, do not write to log to cleanly close JSON array log structure
            if self.timestep != self.maxTimestep and len(self.agents) > 0:
                self.writeToLog()

    def endLog(self):
        if self.log == None:
            return
        # Update total wealth accumulation to include still living agents at simulation end
        environmentWealthCreated = 0
        environmentWealthTotal = 0
        for i in range(self.environment.width):
            for j in range(self.environment.height):
                environmentWealthCreated += self.environment.grid[i][j].sugarLastProduced + self.environment.grid[i][j].spiceLastProduced
                environmentWealthTotal += self.environment.grid[i][j].sugar + self.environment.grid[i][j].spice
        self.runtimeStats["environmentWealthCreated"] = environmentWealthCreated
        self.runtimeStats["environmentWealthTotal"] = environmentWealthTotal
        logString = '\t' + json.dumps(self.runtimeStats) + "\n]"
        if self.logFormat == "csv":
            logString = ""
            # Ensure consistent ordering for CSV format
            for stat in sorted(self.runtimeStats):
                if logString == "":
                    logString += f"{self.runtimeStats[stat]}"
                else:
                    logString += f",{self.runtimeStats[stat]}"
            logString += "\n"
        self.log.write(logString)
        self.log.flush()
        self.log.close()

    def findActiveQuadrants(self):
        quadrants = self.configuration["environmentStartingQuadrants"]
        cellRange = []
        quadrantWidth = math.floor(self.environmentWidth / 2 * self.configuration["environmentQuadrantSizeFactor"])
        quadrantHeight = math.floor(self.environmentHeight / 2 * self.configuration["environmentQuadrantSizeFactor"])
        quadrantIndex = 0
        # Quadrant I at origin in top left corner, other quadrants in clockwise order
        if 1 in quadrants:
            quadrantOne = [self.environment.grid[i][j] for j in range(quadrantHeight) for i in range(quadrantWidth)]
            cellRange.append(quadrantOne)
            quadrantIndex += 1
        if 2 in quadrants:
            quadrantTwo = [self.environment.grid[i][j] for j in range(quadrantHeight) for i in range(self.environmentWidth - quadrantWidth, self.environmentWidth)]
            cellRange.append(quadrantTwo)
            quadrantIndex += 1
        if 3 in quadrants:
            quadrantThree = [self.environment.grid[i][j] for j in range(self.environmentHeight - quadrantHeight, self.environmentHeight) for i in range(self.environmentWidth - quadrantWidth, self.environmentWidth)]
            cellRange.append(quadrantThree)
            quadrantIndex += 1
        if 4 in quadrants:
            quadrantFour = [self.environment.grid[i][j] for j in range(self.environmentHeight - quadrantHeight, self.environmentHeight) for i in range(quadrantWidth)]
            cellRange.append(quadrantFour)
        return cellRange

    def generateAgentID(self):
        agentID = self.nextAgentID
        self.nextAgentID += 1
        return agentID

    def generateAgentTags(self, numAgents):
        configs = self.configuration
        if configs["agentTagStringLength"] == 0 or configs["environmentMaxTribes"] == 0 or self.configuration["environmentTribePerQuadrant"] == True:
            return [None for i in range(numAgents)]
        numTribes = configs["environmentMaxTribes"]
        tagsEndowments = []
        for i in range(numAgents):
            currTribe = i % numTribes
            tags = self.generateTribeTags(currTribe)
            tagsEndowments.append(tags)
        random.shuffle(tagsEndowments)
        return tagsEndowments

    def generateDiseaseID(self):
        diseaseID = self.nextDiseaseID
        self.nextDiseaseID += 1
        return diseaseID

    def generateTribeTags(self, tribe):
        tagStringLength = self.configuration["agentTagStringLength"]
        numTribes = self.configuration["environmentMaxTribes"]
        tribeSize = (tagStringLength + 1) / numTribes
        minZeroes = math.floor(tribe * tribeSize)
        maxZeroes = math.floor((tribe + 1) * tribeSize) - 1
        maxZeroes = min(maxZeroes, tagStringLength)
        zeroes = random.randint(minZeroes, maxZeroes)
        ones = tagStringLength - zeroes
        tags = [0 for i in range(zeroes)] + [1 for i in range(ones)]
        random.shuffle(tags)
        return tags

    def endSimulation(self):
        self.removeDeadAgents()
        self.endLog()
        if "all" in self.debug or "sugarscape" in self.debug:
            print(str(self))
        exit(0)

    def pauseSimulation(self):
        while self.run == False:
            if self.gui != None and self.end == False:
                self.gui.window.update()
            if self.end == True:
                self.endSimulation()

    def randomizeDiseaseEndowments(self, numDiseases):
        configs = self.configuration
        aggressionPenalty = configs["diseaseAggressionPenalty"]
        fertilityPenalty = configs["diseaseFertilityPenalty"]
        incubationPeriod = configs["diseaseIncubationPeriod"]
        movementPenalty = configs["diseaseMovementPenalty"]
        spiceMetabolismPenalty = configs["diseaseSpiceMetabolismPenalty"]
        startTimeframe = configs["diseaseStartTimeframe"]
        sugarMetabolismPenalty = configs["diseaseSugarMetabolismPenalty"]
        tagLengths = configs["diseaseTagStringLength"]
        transmissionChance = configs["diseaseTransmissionChance"]
        visionPenalty = configs["diseaseVisionPenalty"]

        minAggressionPenalty = aggressionPenalty[0]
        minFertilityPenalty = fertilityPenalty[0]
        minIncubationPeriod = incubationPeriod[0]
        minMovementPenalty = movementPenalty[0]
        minSpiceMetabolismPenalty = spiceMetabolismPenalty[0]
        minStartTimeframe = startTimeframe[0]
        minSugarMetabolismPenalty = sugarMetabolismPenalty[0]
        minTagLength = tagLengths[0]
        minTransmissionChance = transmissionChance[0]
        minVisionPenalty = visionPenalty[0]

        maxAggressionPenalty = aggressionPenalty[1]
        maxFertilityPenalty = fertilityPenalty[1]
        maxIncubationPeriod = incubationPeriod[1]
        maxMovementPenalty = movementPenalty[1]
        maxSpiceMetabolismPenalty = spiceMetabolismPenalty[1]
        maxStartTimeframe = startTimeframe[1]
        maxSugarMetabolismPenalty = sugarMetabolismPenalty[1]
        maxTagLength = tagLengths[1]
        maxTransmissionChance = transmissionChance[1]
        maxVisionPenalty = visionPenalty[1]

        aggressionPenalties = []
        diseaseTags = []
        endowments = []
        fertilityPenalties = []
        incubationPeriods = []
        movementPenalties = []
        spiceMetabolismPenalties = []
        startTimesteps = []
        sugarMetabolismPenalties = []
        transmissionChances = []
        visionPenalties = []

        currAggressionPenalty = minAggressionPenalty
        currFertilityPenalty = minFertilityPenalty
        currIncubationPeriod = minIncubationPeriod
        currMovementPenalty = minMovementPenalty
        currSpiceMetabolismPenalty = minSpiceMetabolismPenalty
        currStartTimestep = minStartTimeframe
        currSugarMetabolismPenalty = minSugarMetabolismPenalty
        currTagLength = minTagLength
        currTransmissionChance = minTransmissionChance
        currVisionPenalty = minVisionPenalty

        for i in range(numDiseases):
            aggressionPenalties.append(currAggressionPenalty)
            diseaseTags.append([random.randrange(2) for i in range(currTagLength)])
            fertilityPenalties.append(currFertilityPenalty)
            incubationPeriods.append(currIncubationPeriod)
            movementPenalties.append(currMovementPenalty)
            spiceMetabolismPenalties.append(currSpiceMetabolismPenalty)
            startTimesteps.append(currStartTimestep)
            sugarMetabolismPenalties.append(currSugarMetabolismPenalty)
            transmissionChances.append(currTransmissionChance)
            visionPenalties.append(currVisionPenalty)

            currAggressionPenalty += 1
            currFertilityPenalty += 1
            currIncubationPeriod += 1
            currMovementPenalty += 1
            currSpiceMetabolismPenalty += 1
            currStartTimestep += 1
            currSugarMetabolismPenalty += 1
            currTagLength += 1
            # To make sure the disease's transmissionChance is a properly-formatted decimal
            currTransmissionChance = round(currTransmissionChance + (10 ** -1), 1)
            currVisionPenalty += 1

            if currAggressionPenalty > maxAggressionPenalty:
                currAggressionPenalty = minAggressionPenalty
            if currFertilityPenalty > maxFertilityPenalty:
                currFertilityPenalty = minFertilityPenalty
            if currIncubationPeriod > maxIncubationPeriod:
                currIncubationPeriod = minIncubationPeriod
            if currMovementPenalty > maxMovementPenalty:
                currMovementPenalty = minMovementPenalty
            if currSpiceMetabolismPenalty > maxSpiceMetabolismPenalty:
                currSpiceMetabolismPenalty = minSpiceMetabolismPenalty
            if currStartTimestep > maxStartTimeframe:
                currStartTimestep = minStartTimeframe
            if currSugarMetabolismPenalty > maxSugarMetabolismPenalty:
                currSugarMetabolismPenalty = minSugarMetabolismPenalty
            if currTagLength > maxTagLength:
                currTagLength = minTagLength
            if currTransmissionChance > maxTransmissionChance:
                currTransmissionChance = minTransmissionChance
            if currVisionPenalty > maxVisionPenalty:
                currVisionPenalty = minVisionPenalty

        randomDiseaseEndowment = {"aggressionPenalties": aggressionPenalties,
                     "diseaseTags": diseaseTags,
                     "fertilityPenalties": fertilityPenalties,
                     "incubationPeriods": incubationPeriods,
                     "movementPenalties": movementPenalties,
                     "spiceMetabolismPenalties": spiceMetabolismPenalties,
                     "startTimesteps": startTimesteps,
                     "sugarMetabolismPenalties": sugarMetabolismPenalties,
                     "transmissionChances": transmissionChances,
                     "visionPenalties": visionPenalties}

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
                                "incubationPeriod": incubationPeriods.pop(),
                                "movementPenalty": movementPenalties.pop(),
                                "spiceMetabolismPenalty": spiceMetabolismPenalties.pop(),
                                "startTimestep": startTimesteps.pop(),
                                "sugarMetabolismPenalty": sugarMetabolismPenalties.pop(),
                                "tags": diseaseTags.pop(),
                                "transmissionChance": transmissionChances.pop(),
                                "visionPenalty": visionPenalties.pop()}
            endowments.append(diseaseEndowment)
        return endowments

    def randomizeAgentEndowments(self, numAgents):
        configs = self.configuration
        aggressionFactor = configs["agentAggressionFactor"]
        baseInterestRate = configs["agentBaseInterestRate"]
        decisionModelFactor = configs["agentDecisionModelFactor"]
        decisionModelLookaheadDiscount = configs["agentDecisionModelLookaheadDiscount"]
        decisionModelLookaheadFactor = configs["agentDecisionModelLookaheadFactor"]
        decisionModelTribalFactor = configs["agentDecisionModelTribalFactor"]
        diseaseProtectionChance = configs["agentDiseaseProtectionChance"]
        femaleFertilityAge = configs["agentFemaleFertilityAge"]
        femaleInfertilityAge = configs["agentFemaleInfertilityAge"]
        fertilityFactor = configs["agentFertilityFactor"]
        immuneSystemLength = configs["agentImmuneSystemLength"]
        inheritancePolicy = configs["agentInheritancePolicy"]
        lendingFactor = configs["agentLendingFactor"]
        loanDuration = configs["agentLoanDuration"]
        lookaheadFactor = configs["agentLookaheadFactor"]
        maleFertilityAge = configs["agentMaleFertilityAge"]
        maleInfertilityAge = configs["agentMaleInfertilityAge"]
        maleToFemaleRatio = configs["agentMaleToFemaleRatio"]
        maxAge = configs["agentMaxAge"]
        maxFriends = configs["agentMaxFriends"]
        movement = configs["agentMovement"]
        movementMode = configs["agentMovementMode"]
        neighborhoodMode = configs["neighborhoodMode"]
        selfishnessFactor = configs["agentSelfishnessFactor"]
        spiceMetabolism = configs["agentSpiceMetabolism"]
        startingSpice = configs["agentStartingSpice"]
        startingSugar = configs["agentStartingSugar"]
        sugarMetabolism = configs["agentSugarMetabolism"]
        tagPreferences = configs["agentTagPreferences"]
        tagging = configs["agentTagging"]
        tradeFactor = configs["agentTradeFactor"]
        tagging = configs["agentTagging"]
        universalSpice = configs["agentUniversalSpice"]
        universalSugar = configs["agentUniversalSugar"]
        vision = configs["agentVision"]
        visionMode = configs["agentVisionMode"]

        numDepressedAgents = int(math.ceil(numAgents * configs["agentDepressionPercentage"]))
        depressionFactors = [1 for i in range(numDepressedAgents)] + [0 for i in range(numAgents - numDepressedAgents)]
        random.shuffle(depressionFactors)

        configurations = {"aggressionFactor": {"endowments": [], "curr": aggressionFactor[0], "min": aggressionFactor[0], "max": aggressionFactor[1]},
                          "baseInterestRate": {"endowments": [], "curr": baseInterestRate[0], "min": baseInterestRate[0], "max": baseInterestRate[1]},
                          "decisionModelFactor": {"endowments": [], "curr": decisionModelFactor[0], "min": decisionModelFactor[0], "max": decisionModelFactor[1]},
                          "decisionModelLookaheadDiscount": {"endowments": [], "curr": decisionModelLookaheadDiscount[0], "min": decisionModelLookaheadDiscount[0], "max": decisionModelLookaheadDiscount[1]},
                          "decisionModelTribalFactor": {"endowments": [], "curr": decisionModelTribalFactor[0], "min": decisionModelTribalFactor[0], "max": decisionModelTribalFactor[1]},
                          "diseaseProtectionChance": {"endowments": [], "curr": diseaseProtectionChance[0], "min": diseaseProtectionChance[0], "max": diseaseProtectionChance[1]},
                          "femaleFertilityAge": {"endowments": [], "curr": femaleFertilityAge[0], "min": femaleFertilityAge[0], "max": femaleFertilityAge[1]},
                          "femaleInfertilityAge": {"endowments": [], "curr": femaleInfertilityAge[0], "min": femaleInfertilityAge[0], "max": femaleInfertilityAge[1]},
                          "fertilityFactor": {"endowments": [], "curr": fertilityFactor[0], "min": fertilityFactor[0], "max": fertilityFactor[1]},
                          "lendingFactor": {"endowments": [], "curr": lendingFactor[0], "min": lendingFactor[0], "max": lendingFactor[1]},
                          "loanDuration": {"endowments": [], "curr": loanDuration[0], "min": loanDuration[0], "max": loanDuration[1]},
                          "lookaheadFactor": {"endowments": [], "curr": lookaheadFactor[0], "min": lookaheadFactor[0], "max": lookaheadFactor[1]},
                          "maleFertilityAge": {"endowments": [], "curr": maleFertilityAge[0], "min": maleFertilityAge[0], "max": maleFertilityAge[1]},
                          "maleInfertilityAge": {"endowments": [], "curr": maleInfertilityAge[0], "min": maleInfertilityAge[0], "max": maleInfertilityAge[1]},
                          "maxAge": {"endowments": [], "curr": maxAge[0], "min": maxAge[0], "max": maxAge[1]},
                          "maxFriends": {"endowments": [], "curr": maxFriends[0], "min": maxFriends[0], "max": maxFriends[1]},
                          "movement": {"endowments": [], "curr": movement[0], "min": movement[0], "max": movement[1]},
                          "selfishnessFactor": {"endowments": [], "curr": selfishnessFactor[0], "min": selfishnessFactor[0], "max": selfishnessFactor[1]},
                          "spice": {"endowments": [], "curr": startingSpice[0], "min": startingSpice[0], "max": startingSpice[1]},
                          "spiceMetabolism": {"endowments": [], "curr": spiceMetabolism[0], "min": spiceMetabolism[0], "max": spiceMetabolism[1]},
                          "sugar": {"endowments": [], "curr": startingSugar[0], "min": startingSugar[0], "max": startingSugar[1]},
                          "sugarMetabolism": {"endowments": [], "curr": sugarMetabolism[0], "min": sugarMetabolism[0], "max": sugarMetabolism[1]},
                          "tradeFactor": {"endowments": [], "curr": tradeFactor[0], "min": tradeFactor[0], "max": tradeFactor[1]},
                          "universalSpice": {"endowments": [], "curr": universalSpice[0], "min": universalSpice[0], "max": universalSugar[1]},
                          "universalSugar": {"endowments": [], "curr": universalSugar[0], "min": universalSugar[0], "max": universalSugar[1]},
                          "vision": {"endowments": [], "curr": vision[0], "min": vision[0], "max": vision[1]}
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

        decisionModels = []
        endowments = []
        immuneSystems = []
        sexes = []
        tags = self.generateAgentTags(numAgents)

        sexDistributionCountdown = numAgents
        # Determine count of male agents and set as switch for agent generation
        if maleToFemaleRatio != None and maleToFemaleRatio != 0:
            sexDistributionCountdown = math.floor(sexDistributionCountdown / (maleToFemaleRatio + 1)) * maleToFemaleRatio

        for i in range(numAgents):
            for config in configurations.values():
                config["endowments"].append(config["curr"])
                config["curr"] += config["inc"]
                config["curr"] = round(config["curr"], config["decimals"])
                if config["curr"] > config["max"]:
                    config["curr"] = config["min"]

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
            decisionModel = configs["agentDecisionModels"][i % len(configs["agentDecisionModels"])]
            # Convert clever name for default behavior
            if decisionModel == "rawSugarscape":
                decisionModel = "none"
            decisionModels.append(decisionModel)

        # Keep state of random numbers to allow extending agent endowments without altering original random object state
        randomNumberReset = random.getstate()
        for config in configurations:
            random.seed(self.agentConfigHashes[config] + self.timestep)
            random.shuffle(configurations[config]["endowments"])
        random.setstate(randomNumberReset)
        random.shuffle(sexes)
        random.shuffle(decisionModels)
        for i in range(numAgents):
            agentEndowment = {"seed": self.seed, "sex": sexes[i], "tags": tags.pop(), "tagPreferences": tagPreferences, "tagging": tagging,
                              "immuneSystem": immuneSystems.pop(), "inheritancePolicy": inheritancePolicy,
                              "decisionModel": decisionModels.pop(), "decisionModelLookaheadFactor": decisionModelLookaheadFactor,
                              "movementMode": movementMode, "neighborhoodMode": neighborhoodMode, "visionMode": visionMode,
                              "depressionFactor": depressionFactors[i]}
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

    def runSimulation(self, timesteps=5):
        self.startLog()
        if self.log == None:
            self.updateRuntimeStats()
        if self.gui != None:
            # Simulation begins paused until start button in GUI pressed
            self.gui.updateLabels()
            self.pauseSimulation()
        t = 1
        timesteps = timesteps - self.timestep
        screenshots = 0
        while t <= timesteps:
            if len(self.agents) == 0 and self.keepAlive == False:
                break
            if self.configuration["screenshots"] == True and self.configuration["headlessMode"] == False:
                self.gui.canvas.postscript(file=f"screenshot{screenshots}.ps", colormode="color")
                screenshots += 1
            self.doTimestep()
            t += 1
            if self.gui != None and self.run == False:
                self.pauseSimulation()
        self.endSimulation()

    def startLog(self):
        if self.log == None:
            return
        if self.logFormat == "csv":
            header = ""
            # Ensure consistent ordering for CSV format
            for stat in sorted(self.runtimeStats):
                if header == "":
                    header += f"{stat}"
                else:
                    header += f",{stat}"
            header += "\n"
            self.log.write(header)
        else:
            self.log.write("[\n")
        self.updateRuntimeStats()
        self.writeToLog()

    def toggleEnd(self):
        self.end = True

    def toggleRun(self):
        self.run = not self.run

    def updateGiniCoefficient(self):
        if len(self.agents) == 0:
            return 0
        agentWealths = sorted([agent.sugar + agent.spice for agent in self.agents])
        # Calculate normalized area of Lorenz curve of agent wealths
        numAgents = len(agentWealths)
        totalWealth = sum(agentWealths)
        if totalWealth == 0:
            return 1
        cumulativeWealth = 0
        lorenzCurveArea = 0
        for i in range(numAgents - 1):
            cumulativeWealth += agentWealths[i]
            lorenzCurveArea += cumulativeWealth / totalWealth
        # Use trapezoidal area to maintain accuracy with smaller populations
        cumulativeWealth += agentWealths[-1]
        lorenzCurveArea += (cumulativeWealth / 2) / totalWealth
        lorenzCurveArea /= numAgents
        # The total area under the equality line will be 0.5
        equalityLineArea = 0.5
        giniCoefficient = round((equalityLineArea - lorenzCurveArea) / equalityLineArea, 3)
        return giniCoefficient
    
    def updateGraphStats(self):
        histogramBins = self.gui.xTicks

        maxAge = self.configuration["agentMaxAge"][1]
        ageBins = [0] * histogramBins
        if maxAge != -1:
            for agent in self.agents:
                ageBins[math.floor(agent.age / (maxAge + 1) * histogramBins)] += 1

        maxSpice = 0
        maxSugar = 0
        maxWealth = 0
        for agent in self.agents:
            if agent.spice > maxSpice:
                maxSpice = agent.spice
            if agent.sugar > maxSugar:
                maxSugar = agent.sugar
            if agent.sugar + agent.spice > maxWealth:
                maxWealth = agent.sugar + agent.spice
        self.graphStats["maxSpice"] = maxSpice
        self.graphStats["maxSugar"] = maxSugar
        self.graphStats["maxWealth"] = maxWealth

        sugarBins = [0] * histogramBins
        spiceBins = [0] * histogramBins
        agentWealths = []
        for agent in self.agents:
            spiceBins[math.floor(agent.spice / (maxSpice + 1) * histogramBins)] += 1
            sugarBins[math.floor(agent.sugar / (maxSugar + 1) * histogramBins)] += 1
            agentWealths.append(agent.sugar + agent.spice)

        meanTribeTags = [0] * self.configuration["agentTagStringLength"]
        totalPopulation = len(self.agents)
        if self.configuration["agentTagStringLength"] > 0 and totalPopulation > 0:
            for agent in self.agents:
                meanTribeTags = [i + j for i, j in zip(meanTribeTags, agent.tags)]
            meanTribeTags = [round(tag / totalPopulation, 2) * 100 for tag in meanTribeTags]

        agentWealths.sort()
        totalWealth = sum(agentWealths)
        cumulativeWealth = 0
        if totalWealth > 0 and len(agentWealths) > 0:
            lorenzCurvePoints = [(0, 0)]
            for i, wealth in enumerate(agentWealths):
                cumulativePopulation = (i + 1)
                cumulativeWealth += wealth
                lorenzCurvePoints.append((cumulativePopulation / totalPopulation, cumulativeWealth / totalWealth))
            if lorenzCurvePoints[-1] != (1, 1):
                lorenzCurvePoints.append((1, 1))
        else:
            lorenzCurvePoints = [(0, 0), (1, 1)]

        self.graphStats["ageBins"] = ageBins
        self.graphStats["lorenzCurvePoints"] = lorenzCurvePoints
        self.graphStats["meanTribeTags"] = meanTribeTags
        self.graphStats["spiceBins"] = spiceBins
        self.graphStats["sugarBins"] = sugarBins

    def updateRuntimeStats(self):
        # Log separate stats for experimental and control groups
        if self.experimentalGroup != None:
            self.updateRuntimeStatsPerGroup(self.experimentalGroup)
            self.updateRuntimeStatsPerGroup(self.experimentalGroup, True)
        self.updateRuntimeStatsPerGroup()

    def updateRuntimeStatsPerGroup(self, group=None, notInGroup=False):
        maxTribe = 0
        maxTribeSize = 0
        maxWealth = 0
        meanAge = 0
        meanConflictHappiness = 0
        meanFamilyHappiness = 0
        meanHappiness = 0
        meanHealthHappiness = 0
        meanMetabolism = 0
        meanMovement = 0
        meanSocialHappiness = 0
        meanSpiceMetabolism = 0
        meanSugarMetabolism = 0
        meanTradePrice = 0
        meanVision = 0
        meanWealth = 0
        meanWealthHappiness = 0
        minWealth = sys.maxsize
        numAgents = 0
        numTraders = 0
        numTribes = 0
        sickAgents = 0
        tradeVolume = 0

        environmentWealthCreated = 0
        environmentWealthTotal = 0
        for i in range(self.environment.width):
            for j in range(self.environment.height):
                environmentWealthCreated += self.environment.grid[i][j].sugarLastProduced + self.environment.grid[i][j].spiceLastProduced
                environmentWealthTotal += self.environment.grid[i][j].sugar + self.environment.grid[i][j].spice
                if self.timestep == 1:
                    environmentWealthCreated += self.environment.grid[i][j].maxSugar + self.environment.grid[i][j].maxSpice

        agentAgingDeaths = 0
        agentCombatDeaths = 0
        agentDiseaseDeaths = 0
        agentMeanTimeToLive = 0
        agentStarvationDeaths = 0
        agentTotalMetabolism = 0
        agentWealthBurnRate = 0
        agentWealthCollected = 0
        agentWealthTotal = 0

        agentsBorn = 0
        agentsReplaced = 0
        tribes = {}

        for agent in self.agents:
            if group != None and agent.isInGroup(group, notInGroup) == False:
                continue
            agentTimeToLive = agent.findTimeToLive()
            agentTimeToLiveAgeLimited = agent.findTimeToLive(True)
            agentWealth = agent.sugar + agent.spice
            meanSugarMetabolism += agent.sugarMetabolism
            meanSpiceMetabolism += agent.spiceMetabolism
            meanMovement += agent.movement
            meanVision += agent.vision
            meanAge += agent.age
            meanWealth += agentWealth
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
            agentWealthTotal += agentWealth
            agentWealthCollected += agentWealth - (agent.lastSugar + agent.lastSpice)
            agentWealthBurnRate += agentTimeToLive
            agentMeanTimeToLive += agentTimeToLiveAgeLimited
            agentTotalMetabolism += agent.sugarMetabolism + agent.spiceMetabolism
            if agent.isSick():
                sickAgents += 1
            if agentWealth < minWealth:
                minWealth = agentWealth
            if agentWealth > maxWealth:
                maxWealth = agentWealth
            if agent.tribe not in tribes:
                tribes[agent.tribe] = 1
            else:
                tribes[agent.tribe] += 1
            numAgents += 1

        if numAgents > 0:
            agentMeanTimeToLive = round(agentMeanTimeToLive / numAgents, 2)
            agentWealthBurnRate = round(agentWealthBurnRate / numAgents, 2)
            agentWealthTotal = round(agentWealthTotal, 2)
            maxTribe = max(tribes, key=tribes.get)
            maxTribeSize = tribes[maxTribe]
            maxWealth = round(maxWealth, 2)
            meanAge = round(meanAge / numAgents, 2)
            meanConflictHappiness = round(meanConflictHappiness / numAgents, 2)
            meanFamilyHappiness = round(meanFamilyHappiness / numAgents, 2)
            meanHappiness = round(meanHappiness / numAgents, 2)
            meanHealthHappiness = round(meanHealthHappiness / numAgents, 2)
            combinedMetabolism = meanSugarMetabolism + meanSpiceMetabolism
            if meanSugarMetabolism > 0 and meanSpiceMetabolism > 0:
                combinedMetabolism = round(combinedMetabolism / 2, 2)
            meanMetabolism = round(combinedMetabolism / numAgents, 2)
            meanMovement = round(meanMovement / numAgents, 2)
            meanSocialHappiness = round(meanSocialHappiness / numAgents, 2)
            meanTradePrice = round(meanTradePrice / numTraders, 2) if numTraders > 0 else 0
            meanVision = round(meanVision / numAgents, 2)
            meanWealth = round(meanWealth / numAgents, 2)
            meanWealthHappiness = round(meanWealthHappiness / numAgents, 2)
            minWealth = round(minWealth, 2)
            remainingTribes = len(tribes)
            tradeVolume = round(tradeVolume, 2)
        else:
            agentMeanTimeToLive = 0
            agentWealthBurnRate = 0
            maxTribe = 0
            maxWealth = 0
            meanAge = 0
            meanConflictHappiness = 0
            meanFamilyHappiness = 0
            meanHappiness = 0
            meanHealthHappiness = 0
            meanMetabolism = 0
            meanMovement = 0
            meanSocialHappiness = 0
            meanVision = 0
            meanWealth = 0
            meanWealthHappiness = 0
            minWealth = 0
            remainingTribes = 0
            tradeVolume = 0

        numDeadAgents = 0
        meanAgeAtDeath = 0
        for agent in self.deadAgents:
            if group != None and agent.isInGroup(group, notInGroup) == False:
                continue
            agentWealth = agent.sugar + agent.spice
            meanAgeAtDeath += agent.age
            agentWealthCollected += agentWealth - (agent.lastSugar + agent.lastSpice)
            agentAgingDeaths += 1 if agent.causeOfDeath == "aging" else 0
            agentCombatDeaths += 1 if agent.causeOfDeath == "combat" else 0
            agentDiseaseDeaths += 1 if agent.diseaseDeath == True else 0
            agentStarvationDeaths += 1 if agent.causeOfDeath == "starvation" else 0
            numDeadAgents += 1
        meanAgeAtDeath = round(meanAgeAtDeath / numDeadAgents, 2) if numDeadAgents > 0 else 0

        for agent in self.replacedAgents:
            if group != None and agent.isInGroup(group, notInGroup) == False:
                continue
            agentsReplaced += 1

        for agent in self.bornAgents:
            if group != None and agent.isInGroup(group, notInGroup) == False:
                continue
            agentsBorn += 1

        # TODO: make clear whether agent or environment calculation
        runtimeStats = {"agentAgingDeaths": agentAgingDeaths, "agentCombatDeaths": agentCombatDeaths, "agentDeaths": numDeadAgents,
                        "agentDiseaseDeaths": agentDiseaseDeaths, "agentMeanTimeToLive": agentMeanTimeToLive, "agentsBorn": agentsBorn,
                        "agentsReplaced": agentsReplaced, "agentStarvationDeaths": agentStarvationDeaths, "agentTotalMetabolism": agentTotalMetabolism,
                        "agentWealthBurnRate": agentWealthBurnRate, "agentWealthCollected": agentWealthCollected, "agentWealthTotal": agentWealthTotal,
                        "largestTribe": maxTribe, "largestTribeSize": maxTribeSize, "maxWealth": maxWealth, "meanAge": meanAge,
                        "meanAgeAtDeath": meanAgeAtDeath, "meanConflictHappiness": meanConflictHappiness, "meanFamilyHappiness": meanFamilyHappiness,
                        "meanHappiness": meanHappiness, "meanHealthHappiness": meanHealthHappiness, "meanMetabolism": meanMetabolism,
                        "meanMovement": meanMovement, "meanSocialHappiness": meanSocialHappiness, "meanTradePrice": meanTradePrice,
                        "meanWealth": meanWealth, "meanWealthHappiness": meanWealthHappiness, "meanVision": meanVision, "minWealth": minWealth,
                        "population": numAgents, "sickAgents": sickAgents, "remainingTribes": remainingTribes, "tradeVolume": tradeVolume}

        if group == None:
            self.runtimeStats["environmentWealthCreated"] = environmentWealthCreated
            self.runtimeStats["environmentWealthTotal"] = environmentWealthTotal
            self.runtimeStats["giniCoefficient"] = self.updateGiniCoefficient()
            self.runtimeStats["timestep"] = self.timestep
            self.bornAgents = []
            self.replacedAgents = []
            self.deadAgents = []
        else:
            # Convert keys to Pythonic case scheme
            groupString = group if notInGroup == False else "control"
            groupStats = {}
            for key in runtimeStats.keys():
                groupKey = groupString + key[0].upper() + key[1:]
                groupStats[groupKey] = runtimeStats[key]
            runtimeStats = groupStats

        for key in runtimeStats.keys():
            self.runtimeStats[key] = runtimeStats[key]

        for disease in self.diseases:
            incidence = 0
            prevalence = 0
            r = 0.0
            if numAgents > 0:
                infectors = len(disease.infectors)
                incidence = disease.infected
                prevalence = self.countInfectedAgents(disease)
                r = 0.0
                if infectors > 0:
                    r = round(float(incidence / infectors), 2)
            self.runtimeStats[f"disease{disease.ID}Incidence"] = incidence
            self.runtimeStats[f"disease{disease.ID}Prevalence"] = prevalence
            self.runtimeStats[f"disease{disease.ID}RValue"] = r

    def writeToLog(self):
        if self.log == None:
            return
        logString = '\t' + json.dumps(self.runtimeStats) + ",\n"
        if self.logFormat == "csv":
            logString = ""
            # Ensure consistent ordering for CSV format
            for stat in sorted(self.runtimeStats):
                if logString == "":
                    logString += f"{self.runtimeStats[stat]}"
                else:
                    logString += f",{self.runtimeStats[stat]}"
            logString += "\n"
        self.log.write(logString)

    def __str__(self):
        string = f"{str(self.environment)}Seed: {self.seed}\nTimestep: {self.timestep}\nLiving Agents: {len(self.agents)}"
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
    negativesAllowed = ["agentDecisionModelTribalFactor", "agentMaxAge", "agentSelfishnessFactor"]
    negativesAllowed += ["diseaseAggressionPenalty", "diseaseFertilityPenalty", "diseaseMovementPenalty", "diseaseSpiceMetabolismPenalty", "diseaseSugarMetabolismPenalty", "diseaseVisionPenalty"]
    negativesAllowed += ["environmentEquator", "environmentPollutionDiffusionTimeframe", "environmentPollutionTimeframe"]
    negativesAllowed += ["seed", "timesteps"]
    negativeFlag = 0
    for configName, configValue in configuration.items():
        if isinstance(configValue, list):
            if len(configValue) == 0:
                continue
            configType = type(configValue[0])
            if configName != "environmentPollutionDiffusionTimeFrame" and configName != "environmentPollutionTimeFrame":
                configValue.sort()
            if configName not in negativesAllowed and (configType == int or configType == float):
                for i in range(len(configValue)):
                    if configValue[i] < 0:
                        configValue[i] = 0
                        negativeFlag += 1
        else:
            configType = type(configValue)
            if configName not in negativesAllowed and (configType == int or configType == float) and configValue < 0:
                configValue = 0
                negativeFlag += 1
    if negativeFlag > 0:
        print(f"Detected negative values provided for {negativeFlag} option(s). Setting these values to zero.")


    if configuration["environmentQuadrantSizeFactor"] > 1 or configuration["environmentQuadrantSizeFactor"] < 0:
        if "all" in configuration["debugMode"] or "environment" in configuration["debugMode"]:
            print(f"Cannot have a quadrant size factor of {configuration['environmentQuadrantSizeFactor']}. Setting quadrant size factor to 1.")
        configuration["environmentQuadrantSizeFactor"] = 1

    if len(configuration["environmentStartingQuadrants"]) == 0:
        configuration["environmentStartingQuadrants"] = [1, 2, 3, 4]

    if configuration["environmentTribePerQuadrant"] == True:
        configuration["environmentMaxTribes"] = len(configuration["environmentStartingQuadrants"])

    # Ensure starting agents are not larger than available cells
    totalCells = configuration["environmentHeight"] * configuration["environmentWidth"]
    totalCells = totalCells * (configuration["environmentQuadrantSizeFactor"] ** 2) * len(configuration["environmentStartingQuadrants"]) / 4
    if configuration["startingAgents"] > totalCells:
        if "all" in configuration["debugMode"] or "sugarscape" in configuration["debugMode"]:
            print(f"Could not allocate {configuration['startingAgents']} agents. Allocating maximum of {totalCells} agents.")
        configuration["startingAgents"] = totalCells

    # Set timesteps to (seemingly) unlimited runtime
    if configuration["timesteps"] < 0:
        if "all" in configuration["debugMode"] or "agent" in configuration["debugMode"]:
            print("Cannot have a negative amount of timesteps. Setting timesetup to unlimited runtime.")
        configuration["timesteps"] = sys.maxsize

    # Ensure infinitely-lived agents are properly initialized
    if configuration["agentDecisionModelTribalFactor"][0] < 0:
        if configuration["agentDecisionModelTribalFactor"][1] != -1:
            if "all" in configuration["debugMode"] or "agent" in configuration["debugMode"]:
                print(
                    f"Cannot have age tribal factor range of {configuration['agentDecisionModelTribalFactor']}. Disabling agent tribal factor.")
        configuration["agentDecisionModelTribalFactor"] = [-1, -1]
    elif configuration["agentDecisionModelTribalFactor"][1] > 1:
        if "all" in configuration["debugMode"] or "agent" in configuration["debugMode"]:
            print(
                f"Cannot have agent maximum tribal factor of {configuration['agentDecisionModelTribalFactor'][1]}. Setting agent maximum tribal factor to 1.0.")
        configuration["agentDecisionModelTribalFactor"][1] = 1

    if configuration["agentMaxAge"][0] < 0:
        if configuration["agentMaxAge"][1] != -1:
            if "all" in configuration["debugMode"] or "agent" in configuration["debugMode"]:
                print(f"Agent cannot have agent maximum age range of {configuration['agentMaxAge']}. Setting agents to live infinitely.")
        configuration["agentMaxAge"] = [-1, -1]

    if configuration["agentSelfishnessFactor"][0] < 0:
        if configuration["agentSelfishnessFactor"][1] != -1:
            if "all" in configuration["debugMode"] or "agent" in configuration["debugMode"]:
                print(f"Cannot have agent selfishness factor range of {configuration['agentSelfishnessFactor']}. Disabling agent selfishness.")
        configuration["agentSelfishnessFactor"] = [-1, -1]
    elif configuration["agentSelfishnessFactor"][1] > 1:
        if "all" in configuration["debugMode"] or "agent" in configuration["debugMode"]:
            print(f"Cannot have agent maximum selfishness factor of {configuration['agentSelfishnessFactor'][1]}. Setting agent maximum selfishness factor to 1.0.")
        configuration["agentSelfishnessFactor"][1] = 1

    if configuration["agentDiseaseProtectionChance"][0] < 0:
        if "all" in configuration["debugMode"] or "agent" in configuration["debugMode"]:
            print(f"Cannot have agent minimum disease protection chance of {configuration['agentDiseaseProtectionChance'][0]}. Setting agent minimum disease protection chance to 0.0.")
        configuration["agentDiseaseProtectionChance"][0] = 0.0
    if configuration["agentDiseaseProtectionChance"][1] > 1:
        if "all" in configuration["debugMode"] or "agent" in configuration["debugMode"]:
            print(f"Cannot have agent maximum disease protection chance of {configuration['agentDiseaseProtectionChance'][1]}. Setting agent maximum disease protection chance to 1.0.")
        configuration["agentDiseaseProtectionChance"][1] = 1.0

    if configuration["agentTagStringLength"] < 0:
        if "all" in configuration["debugMode"] or "agent" in configuration["debugMode"]:
            print(f"Cannot have a negative agent tag string length. Setting agent tag string length to 0.")
        configuration["agentTagStringLength"] = 0

    if configuration["environmentMaxTribes"] < 0:
        if "all" in configuration["debugMode"] or "environment" in configuration["debugMode"]:
            print(f"Cannot have a negative number of tribes. Setting number of tribes to 0.")
        configuration["environmentMaxTribes"] = 0
    
    # Ensure at most number of tribes is equal to agent tag string length
    if configuration["agentTagStringLength"] > 0 and configuration["environmentMaxTribes"] > configuration["agentTagStringLength"]:
        if "all" in configuration["debugMode"] or "environment" in configuration["debugMode"] or "agent" in configuration["debugMode"]:
            print(f"Cannot have a longer agent tag string length than maximum number of tribes. Setting the number of tribes to {configuration['agentTagStringLength']}.")
        configuration["environmentMaxTribes"] = configuration["agentTagStringLength"]

    if configuration["diseaseTransmissionChance"][0] < 0.0:
        if "all" in configuration["debugMode"] or "disease" in configuration["debugMode"]:
            print(f"Cannot have a minimum disease transmission chance of {configuration['diseaseTransmissionChance'][0]}. Setting disease transmission chance to 0.0.")
        configuration["diseaseTransmissionChance"][0] = 0.0
    if configuration["diseaseTransmissionChance"][1] > 1.0:
        if "all" in configuration["debugMode"] or "disease" in configuration["debugMode"]:
            print(f"Cannot have a maximum disease transmission chance of {configuration['diseaseTransmissionChance'][1]}. Setting disease transmission chance to 1.0.")
        configuration["diseaseTransmissionChance"][1] = 1.0

    # Ensure at most number of tribes and decision models are equal to the number of colors in the GUI
    maxColors = 25
    uniqueAgentDecisionModels = set(configuration["agentDecisionModels"])
    numUniqueAgentDecisionModels = len(uniqueAgentDecisionModels)
    if numUniqueAgentDecisionModels > maxColors:
        if "all" in configuration["debugMode"] or "agent" in configuration["debugMode"]:
            print(
                f"Cannot provide {len(configuration['agentDecisionModels'])} decision models. Allocating maximum of {maxColors}.")
        removeDecisionModels = uniqueAgentDecisionModels[maxColors:]
        configuration["agentDecisionModels"] = [i for i in configuration["agentDecisionModels"] if
                                                i not in removeDecisionModels]
    if configuration["environmentMaxTribes"] > maxColors:
        if "all" in configuration["debugMode"] or "sugarscape" in configuration["debugMode"] or "environment" in configuration["debugMode"]:
            print(f"Cannot provide {configuration['environmentMaxTribes']} tribes. Allocating maximum of {maxColors}.")
        configuration["environmentMaxTribes"] = maxColors

    # Ensure experimental group is properly defined or otherwise ignored
    if configuration["experimentalGroup"] == "":
        configuration["experimentalGroup"] = None
    elif configuration["experimentalGroup"] != None and configuration["experimentalGroup"] not in ["depressed", "female", "male", "sick"]:
        if "all" in configuration["debugMode"] or "agent" in configuration["debugMode"]:
            print(f"Cannot provide separate log stats for experimental group {configuration['experimentalGroup']}. Disabling separate log stats.")
        configuration["experimentalGroup"] = None

    # Ensure the most number of starting diseases per agent is equal to total starting diseases in the environment
    if configuration["startingDiseasesPerAgent"] != [0, 0]:
        startingDiseasesPerAgent = sorted(configuration["startingDiseasesPerAgent"])
        startingDiseasesPerAgent = [max(0, numDiseases) for numDiseases in startingDiseasesPerAgent]
        startingDiseases = configuration["startingDiseases"]
        startingDiseasesPerAgent = [min(startingDiseases, numDiseases) for numDiseases in startingDiseasesPerAgent]
        if "all" in configuration["debugMode"] or "disease" in configuration["debugMode"] and startingDiseasesPerAgent != configuration["startingDiseasesPerAgent"]:
            print(f"Range of starting diseases per agent exceeds {startingDiseases} starting diseases. Setting range to {startingDiseasesPerAgent}.")
        configuration["startingDiseasesPerAgent"] = startingDiseasesPerAgent

    # Ensure the pollution diffusion start and end timesteps are in the proper order
    if configuration["environmentPollutionDiffusionTimeframe"] != [0, 0]:
        pollutionDiffusionStart, pollutionDiffusionEnd = configuration["environmentPollutionDiffusionTimeframe"]
        if pollutionDiffusionStart > pollutionDiffusionEnd and pollutionDiffusionEnd >= 0:
            swap = pollutionDiffusionStart
            pollutionDiffusionStart = pollutionDiffusionEnd
            pollutionDiffusionEnd = swap
            if "all" in configuration["debugMode"] or "sugarscape" in configuration["debugMode"] or "environment" in configuration["debugMode"]:
                print(f"Pollution diffusion start and end values provided in incorrect order. Switching values around.")
        # If provided a negative value, assume the start timestep is the very first of the simulation
        if pollutionDiffusionStart < 0:
            if "all" in configuration["debugMode"] or "sugarscape" in configuration["debugMode"] or "environment" in configuration["debugMode"]:
                print(f"Pollution diffusion start timestep {pollutionDiffusionStart} is invalid. Setting pollution diffusion start timestep to 0.")
            pollutionDiffusionStart = 0
        # If provided a negative value, assume the end timestep is the very end of the simulation
        if pollutionDiffusionEnd < 0:
            if "all" in configuration["debugMode"] or "sugarscape" in configuration["debugMode"] or "environment" in configuration["debugMode"]:
                print(f"Pollution diffusion end timestep {pollutionDiffusionEnd} is invalid. Setting pollution diffusion end timestep to {configuration['timesteps']}.")
            pollutionDiffusionEnd = configuration["timesteps"]
        configuration["environmentPollutionDiffusionTimeframe"] = [pollutionDiffusionStart, pollutionDiffusionEnd]

    # Ensure the pollution start and end timesteps are in the proper order
    if configuration["environmentPollutionTimeframe"] != [0, 0]:
        pollutionStart, pollutionEnd = configuration["environmentPollutionTimeframe"]
        if pollutionStart > pollutionEnd and pollutionEnd >= 0:
            swap = pollutionStart
            pollutionStart = pollutionEnd
            pollutionEnd = swap
            if "all" in configuration["debugMode"] or "sugarscape" in configuration["debugMode"] or "environment" in configuration["debugMode"]:
                print(f"Pollution start and end values provided in incorrect order. Switching values around.")
        # If provided a negative value, assume the start timestep is the very first of the simulation
        if pollutionStart < 0:
            if "all" in configuration["debugMode"] or "sugarscape" in configuration["debugMode"] or "environment" in configuration["debugMode"]:
                print(f"Pollution start timestep {pollutionStart} is invalid. Setting pollution start timestep to 0.")
            pollutionStart = 0
        # If provided a negative value, assume the end timestep is the very end of the simulation
        if pollutionEnd < 0:
            if "all" in configuration["debugMode"] or "sugarscape" in configuration["debugMode"] or "environment" in configuration["debugMode"]:
                print(f"Pollution end timestep {pollutionEnd} is invalid. Setting pollution end timestep to {configuration['timesteps']}.")
            pollutionEnd = configuration["timesteps"]
        configuration["environmentPollutionTimeframe"] = [pollutionStart, pollutionEnd]

    if configuration["logfile"] == "":
        configuration["logfile"] = None

    if configuration["seed"] == -1:
        configuration["seed"] = random.randrange(sys.maxsize)

    recognizedDebugModes = ["agent", "all", "cell", "disease", "environment", "ethics", "none", "sugarscape"]
    validModes = True
    for mode in configuration["debugMode"]:
        if mode not in recognizedDebugModes:
            print(f"Debug mode {mode} not recognized")
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

    # Keep compatibility with outdated configuration files
    if configuration["agentDecisionModel"] != None and type(configuration["agentDecisionModel"]) == str:
            configuration["agentDecisionModels"] = [configuration["agentDecisionModel"]]
    elif configuration["agentDecisionModel"] != None and type(configuration["agentDecisionModel"]) == list:
            configuration["agentDecisionModels"] = configuration["agentDecisionModel"]
    if type(configuration["agentDecisionModels"]) == str:
            configuration["agentDecisionModels"] = [configuration["agentDecisionModels"]]
    return configuration

if __name__ == "__main__":
    # Set default values for simulation configuration
    configuration = {"agentAggressionFactor": [0, 0],
                     "agentBaseInterestRate": [0.0, 0.0],
                     "agentDecisionModels": ["none"],
                     "agentDecisionModel": None,
                     "agentDecisionModelFactor": [0, 0],
                     "agentDecisionModelLookaheadDiscount": [0, 0],
                     "agentDecisionModelLookaheadFactor": [0],
                     "agentDecisionModelTribalFactor": [-1, -1],
                     "agentDepressionPercentage": 0,
                     "agentDiseaseProtectionChance": [0.0, 1.0],
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
                     "agentSugarMetabolism": [1, 4],
                     "agentTagging": False,
                     "agentTagPreferences": False,
                     "agentTagStringLength": 0,
                     "agentTradeFactor": [0, 0],
                     "agentUniversalSpice": [0,0],
                     "agentUniversalSugar": [0,0],
                     "agentVision": [1, 6],
                     "agentVisionMode": "cardinal",
                     "debugMode": ["none"],
                     "diseaseAggressionPenalty": [0, 0],
                     "diseaseFertilityPenalty": [0, 0],
                     "diseaseIncubationPeriod": [0, 0],
                     "diseaseMovementPenalty": [0, 0],
                     "diseaseSpiceMetabolismPenalty": [0, 0],
                     "diseaseStartTimeframe": [0, 0],
                     "diseaseSugarMetabolismPenalty": [0, 0],
                     "diseaseTagStringLength": [0, 0],
                     "diseaseTransmissionChance": [0.0, 1.0],
                     "diseaseVisionPenalty": [0, 0],
                     "environmentEquator": -1,
                     "environmentHeight": 50,
                     "environmentMaxCombatLoot": 0,
                     "environmentMaxSpice": 0,
                     "environmentMaxSugar": 4,
                     "environmentMaxTribes": 0,
                     "environmentPollutionDiffusionDelay": 0,
                     "environmentPollutionDiffusionTimeframe": [0, 0],
                     "environmentPollutionTimeframe": [0, 0],
                     "environmentQuadrantSizeFactor": 1,
                     "environmentSeasonalGrowbackDelay": 0,
                     "environmentSeasonInterval": 0,
                     "environmentSpiceConsumptionPollutionFactor": 0,
                     "environmentSpicePeaks": [[35, 35], [15, 15]],
                     "environmentSpiceProductionPollutionFactor": 0,
                     "environmentSpiceRegrowRate": 0,
                     "environmentStartingQuadrants": [1, 2, 3, 4],
                     "environmentSugarConsumptionPollutionFactor": 0,
                     "environmentSugarPeaks": [[35, 15], [15, 35]],
                     "environmentSugarProductionPollutionFactor": 0,
                     "environmentSugarRegrowRate": 1,
                     "environmentTribePerQuadrant": False,
                     "environmentUniversalSpiceIncomeInterval": 0,
                     "environmentUniversalSugarIncomeInterval": 0,
                     "environmentWidth": 50,
                     "environmentWraparound": True,
                     "experimentalGroup": None,
                     "headlessMode": False,
                     "interfaceHeight": 1000,
                     "interfaceWidth": 900,
                     "keepAlivePostExtinction": False,
                     "logfile": None,
                     "logfileFormat": "json",
                     "neighborhoodMode": "vonNeumann",
                     "profileMode": False,
                     "screenshots": False,
                     "seed": -1,
                     "startingAgents": 250,
                     "startingDiseases": 0,
                     "startingDiseasesPerAgent": [0, 0],
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
