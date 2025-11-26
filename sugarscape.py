#! /usr/bin/python

import agent
import cell
import condition
import environment
import ethics

import getopt
import hashlib
import json
import math
import random
import re
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
        self.configureEnvironment(configuration["environmentMaxSugar"], configuration["environmentMaxSpice"], configuration["environmentSugarPeaks"], configuration["environmentSpicePeaks"], configuration["environmentFile"])
        self.debug = configuration["debugMode"]
        self.keepAlive = configuration["keepAlivePostExtinction"]
        self.agentEndowmentIndex = 0
        self.agentEndowments = []
        self.agentLeader = None
        self.agents = []
        self.bornAgents = []
        self.deadAgents = []
        self.depression = True if configuration["agentDepressionPercentage"] > 0 else False
        self.diseaseEndowmentIndex = 0
        self.diseaseEndowments = []
        self.diseases = []
        self.remainingDiseases = []
        self.replacedAgents = []

        self.activeQuadrants = self.findActiveQuadrants()
        self.agentRuntimeStats = []
        self.configureDepression()
        self.configureAgents(configuration["startingAgents"])
        self.configureDiseases(configuration["startingDiseases"], configuration["diseaseList"])
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
                             "remainingTribes": self.configuration["environmentMaxTribes"], "sickAgents": 0, "carryingCapacity": 0, "meanDeathsPercentage": 0,
                             "sickAgentsPercentage": 0, "meanSelfishness": 0, "diseaseEffectiveReproductionRate": 0, "diseaseIncidence": 0, "diseasePrevalence": 0,
                             "agentLastMoveOptimalityPercentage": 0, "meanNeighbors": 0, "meanMoveRank": 0, "meanMoveDifferenceFromOptimal": 0,
                             "meanValidMoves": 0
                             }
        self.graphStats = {"ageBins": [], "sugarBins": [], "spiceBins": [], "lorenzCurvePoints": [], "meanTribeTags": [],
                           "maxSugar": 0, "maxSpice": 0, "maxWealth": 0}
        self.log = open(configuration["logfile"], 'a') if configuration["logfile"] != None else None
        self.agentLog = open(configuration["agentLogfile"], 'a') if configuration["agentLogfile"] != None else None
        self.logFormat = configuration["logfileFormat"]
        self.experimentalGroup = configuration["experimentalGroup"]
        if self.experimentalGroup != None:
            self.groupMovementStats = {"meanControlNeighbors": 0, "meanExperimentalNeighbors": 0}
            self.runtimeStats.update(self.groupMovementStats)
            # Convert keys to Pythonic case scheme and initialize values
            groupRuntimeStats = {}
            for key in self.runtimeStats.keys():
                controlGroupKey = "control" + key[0].upper() + key[1:]
                experimentalGroupKey = self.experimentalGroup + key[0].upper() + key[1:]
                groupRuntimeStats[controlGroupKey] = 0
                groupRuntimeStats[experimentalGroupKey] = 0
            self.runtimeStats.update(groupRuntimeStats)
            self.groupInteractionRuntimeStats = {"combatControlGroupToControlGroup": 0, "combatControlGroupToExperimentalGroup": 0,
                                                 "combatExperimentalGroupToControlGroup": 0, "combatExperimentalGroupToExperimentalGroup": 0,
                                                 "diseaseControlGroupToControlGroup": 0, "diseaseControlGroupToExperimentalGroup": 0,
                                                 "diseaseExperimentalGroupToControlGroup": 0, "diseaseExperimentalGroupToExperimentalGroup": 0,
                                                 "lendingControlGroupToControlGroup": 0, "lendingControlGroupToExperimentalGroup": 0,
                                                 "lendingExperimentalGroupToControlGroup": 0, "lendingExperimentalGroupToExperimentalGroup": 0,
                                                 "reproductionControlGroupToControlGroup": 0, "reproductionControlGroupToExperimentalGroup": 0,
                                                 "reproductionExperimentalGroupToControlGroup": 0, "reproductionExperimentalGroupToExperimentalGroup": 0,
                                                 "tradeControlGroupToControlGroup": 0, "tradeControlGroupToExperimentalGroup": 0,
                                                 "tradeExperimentalGroupToControlGroup": 0, "tradeExperimentalGroupToExperimentalGroup": 0
                                                 }
            self.runtimeStats.update(self.groupInteractionRuntimeStats)

    def addAgent(self, agent):
        self.bornAgents.append(agent)
        self.agents.append(agent)

    def addRemainingDiseases(self):
        infectedDiseases = []
        for disease in self.remainingDiseases:
            if disease.startTimestep <= self.timestep:
                for agent in self.agents:
                    hammingDistance = agent.findNearestHammingDistanceInDisease(disease)["distance"]
                    if hammingDistance == 0:
                        continue
                    agent.catchDisease(disease, initial=True)
                    self.diseases.append(disease)
                    infectedDiseases.append(disease)
                    break
        for disease in infectedDiseases:
            self.remainingDiseases.remove(disease)

    def addResourcePeak(self, startX, startY, radius, maxValue, resource):
        height = self.environment.height
        width = self.environment.width
        radialDispersion = math.sqrt(max(startX, width - startX)**2 + max(startY, height - startY)**2) * (radius / width)
        for i in range(width):
            for j in range(height):
                euclideanDistanceToStart = math.sqrt((startX - i)**2 + (startY - j)**2)
                currDispersion = 1 + maxValue * (1 - euclideanDistanceToStart / radialDispersion)
                cellMaxCapacity = min(currDispersion, maxValue)
                cellMaxCapacity = math.ceil(cellMaxCapacity)
                if resource == "spice" and cellMaxCapacity > self.environment.findCell(i, j).maxSpice:
                    self.environment.findCell(i, j).maxSpice = cellMaxCapacity
                    self.environment.findCell(i, j).spice = cellMaxCapacity
                elif resource == "sugar" and cellMaxCapacity > self.environment.findCell(i, j).maxSugar:
                    self.environment.findCell(i, j).maxSugar = cellMaxCapacity
                    self.environment.findCell(i, j).sugar = cellMaxCapacity

    def configureAgents(self, numAgents, editCell=None):
        if self.environment == None:
            return
        if editCell != None and editCell.isOccupied():
            return
        if editCell != None and numAgents != 1:
            numAgents = 1

        if self.configuration["agentLeader"] == True and self.agentLeader == None:
            numAgents += 1

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
        if len(self.agentEndowments) == 0:
            self.agentEndowments = self.randomizeAgentEndowments(numAgents)
        quadrantIndices = []
        if editCell == None:
            for quadrant in emptyCells:
                random.shuffle(quadrant)
            quadrantIndices = [i for i in range(quadrants)]
            random.shuffle(quadrantIndices)

        for i in range(numAgents):
            placementCell = editCell
            if editCell == None:
                quadrantIndex = quadrantIndices[i % quadrants]
                placementCell = emptyCells[quadrantIndex].pop()
            agentConfiguration = self.agentEndowments[self.agentEndowmentIndex % len(self.agentEndowments)]
            self.agentEndowmentIndex += 1
            agentID = self.generateAgentID()
            a = agent.Agent(agentID, self.timestep, placementCell, agentConfiguration)
            if self.configuration["agentLeader"] == True and self.agentLeader == None:
                a = ethics.Leader(agentID, self.timestep, placementCell, agentConfiguration)
                cornerCell = self.environment.grid[0][0]
                a.gotoCell(cornerCell)
                self.agentLeader = a

            # If using a different decision model, replace new agent with instance of child class
            if "altruist" in agentConfiguration["decisionModel"]:
                a = ethics.Bentham(agentID, self.timestep, placementCell, agentConfiguration)
                a.selfishnessFactor = 0
            elif "bentham" in agentConfiguration["decisionModel"]:
                a = ethics.Bentham(agentID, self.timestep, placementCell, agentConfiguration)
                if agentConfiguration["selfishnessFactor"] < 0:
                    a.selfishnessFactor = 0.5
            elif "egoist" in agentConfiguration["decisionModel"]:
                a = ethics.Bentham(agentID, self.timestep, placementCell, agentConfiguration)
                a.selfishnessFactor = 1
            elif "negativeBentham" in agentConfiguration["decisionModel"]:
                a = ethics.Bentham(agentID, self.timestep, placementCell, agentConfiguration)
                a.selfishnessFactor = -1
            elif "temperance" in agentConfiguration["decisionModel"]:
                a = ethics.Temperance(agentID, self.timestep, placementCell, agentConfiguration)

            # If dynamic selfishness is desired but not defined, give a small degree of dynamic selfishness
            if "Dynamic" in agentConfiguration["decisionModel"] and self.configuration["agentDynamicSelfishnessFactor"] == [0.0, 0.0]:
                a.dynamicSelfishnessFactor = 0.01
            if "NoLookahead" in agentConfiguration["decisionModel"]:
                a.decisionModelLookaheadFactor = 0
            elif "HalfLookahead" in agentConfiguration["decisionModel"]:
                a.decisionModelLookaheadFactor = 0.5

            # If using a deontological decision model, replace new agent with instance of child class
            if "asimov" in agentConfiguration["decisionModel"]:
                a = ethics.Asimov(agentID, self.timestep, placementCell, agentConfiguration)

            if self.configuration["environmentTribePerQuadrant"] == True:
                tribe = quadrantIndex
                tags = self.generateTribeTags(tribe)
                a.tags = tags
                a.tribe = a.findTribe()
            placementCell.agent = a
            self.agents.append(a)
            if self.timestep > 0:
                self.replacedAgents.append(a)

        for a in self.agents:
            a.findCellsInRange()
            a.findNeighborhood()

    def configureCell(self, cell, mode, delta):
        if cell == None or delta == 0:
            return
        if mode == "currentSpice":
            cell.spice = min(max(0, (cell.spice + delta)), self.environment.globalMaxSpice)
        elif mode == "currentSugar":
            cell.sugar = min(max(0, (cell.sugar + delta)), self.environment.globalMaxSugar)
        elif mode == "maximumSpice":
            cell.maxSpice = min(max(0, (cell.maxSpice + delta)), self.environment.globalMaxSpice)
        elif mode == "maximumSugar":
            cell.maxSugar = min(max(0, (cell.maxSugar + delta)), self.environment.globalMaxSugar)

    def configureDepression(self):
        if self.depression == True:
            self.depression = condition.Depression()
            self.diseases.append(self.depression)

    def configureDiseases(self, numDiseases, namedDiseases, editCell=None):
        numAgents = len(self.agents)
        if numAgents == 0:
            return
        elif numAgents < numDiseases:
            numDiseases = numAgents

        if len(self.diseaseEndowments) == 0:
            premadeDiseases  = []
            for disease in namedDiseases:
                validDisease = 0
                if "zombieVirus" in disease:
                    zombie = condition.ZombieVirus("zombieVirus", {})
                    premadeDiseases.append(zombie)
                    validDisease = 1
                if validDisease == 1:
                    numDiseases -= 1

            self.diseaseEndowments = self.randomizeDiseaseEndowments(numDiseases)
            random.shuffle(self.agents)
            initialDiseases = []
            for i in range(numDiseases):
                diseaseID = self.generateDiseaseID()
                diseaseConfiguration = self.diseaseEndowments[i]
                newDisease = condition.Disease(diseaseID, diseaseConfiguration)
                if diseaseConfiguration["startTimestep"] == 0:
                    initialDiseases.append(newDisease)
                else:
                    self.remainingDiseases.append(newDisease)
            initialDiseases.extend(premadeDiseases)

            startingDiseases = self.configuration["startingDiseasesPerAgent"]
            minStartingDiseases = startingDiseases[0]
            maxStartingDiseases = startingDiseases[1]
            currStartingDiseases = minStartingDiseases
            for agent in self.agents:
                random.shuffle(initialDiseases)
                for newDisease in initialDiseases:
                    if len(agent.diseases) >= currStartingDiseases and startingDiseases != [0, 0]:
                        currStartingDiseases += 1
                        break
                    if newDisease.tags != None:
                        hammingDistance = agent.findNearestHammingDistanceInDisease(newDisease)["distance"]
                        if hammingDistance == 0:
                            continue
                    agent.catchDisease(newDisease, initial=True)
                    self.diseases.append(newDisease)
                    if startingDiseases == [0, 0]:
                        initialDiseases.remove(newDisease)
                        break
                if currStartingDiseases > maxStartingDiseases:
                    currStartingDiseases = minStartingDiseases

            if startingDiseases == [0, 0] and len(initialDiseases) > 0 and ("all" in self.debug or "sugarscape" in self.debug):
                print(f"Could not place {len(diseases)} diseases.")
        elif editCell != None and editCell.isOccupied() == True:
            selectedAgent = editCell.agent
            diseaseID = self.generateDiseaseID()
            newDisease = condition.Disease(diseaseID, self.diseaseEndowments[self.diseaseEndowmentIndex % len(self.diseaseEndowments)])
            self.diseaseEndowmentIndex += 1
            selectedAgent.catchDisease(newDisease)

    def configureEnvironment(self, maxSugar, maxSpice, sugarPeaks, spicePeaks, environmentFile=None):
        height = self.environment.height
        width = self.environment.width
        if environmentFile == None:
            for i in range(width):
                for j in range(height):
                    newCell = cell.Cell(i, j, self.environment)
                    self.environment.setCell(newCell, i, j)

            sugarRadiusScale = 2
            radius = math.ceil(math.sqrt(sugarRadiusScale * (height + width)))
            for peak in sugarPeaks:
                self.addResourcePeak(peak[0], peak[1], radius, peak[2], "sugar")

            spiceRadiusScale = 2
            radius = math.ceil(math.sqrt(spiceRadiusScale * (height + width)))
            for peak in spicePeaks:
                self.addResourcePeak(peak[0], peak[1], radius, peak[2], "spice")
        else:
            environmentFile = open(environmentFile)
            loadEnvironment = json.loads(environmentFile.read())
            environmentFile.close()
            height = len(loadEnvironment)
            width = len(loadEnvironment[0])
            self.environment.height = height
            self.environment.width = width
            self.environmentHeight = height
            self.environmentWidth = width
            for i in range(width):
                for j in range(height):
                    loadSpice = loadEnvironment[i][j]["spice"]
                    loadSugar = loadEnvironment[i][j]["sugar"]
                    newCell = cell.Cell(i, j, self.environment, loadSpice, loadSugar)
                    self.environment.setCell(newCell, i, j)
        self.environment.findCellNeighbors()
        self.environment.findCellRanges()

    def doTimestep(self):
        if self.timestep >= self.maxTimestep:
            self.toggleEnd()
            return
        if "all" in self.debug or "sugarscape" in self.debug:
            print(f"Timestep: {self.timestep}\nLiving Agents: {len(self.agents)}")
        self.timestep += 1
        if self.end == True or (len(self.agents) == 0 and self.keepAlive == False):
            self.toggleEnd()
        else:
            self.environment.doTimestep(self.timestep)
            random.shuffle(self.agents)
            self.addRemainingDiseases()
            if self.agentLeader != None:
                self.agentLeader.doTimestep(self.timestep)
            for agent in self.agents:
                if self.agentLeader != None and agent == self.agentLeader:
                    continue
                agent.doTimestep(self.timestep)
            self.removeDeadAgents()
            self.replaceDeadAgents()
            self.updateRuntimeStats()
            if self.gui != None:
                self.updateGraphStats()
                self.gui.doTimestep()
            # If final timestep, do not write to log to cleanly close JSON array log structure
            if self.timestep != self.maxTimestep and len(self.agents) > 0:
                self.writeToLog(self.log)
                # Start recording agent actions only after agents have started acting
                if self.timestep == 1:
                    self.startLog(self.agentLog)
                self.writeToLog(self.agentLog)
                self.agentRuntimeStats = []

    def endLog(self, log):
        if log == None:
            return
        # Update total wealth accumulation to include still living agents at simulation end
        stats = self.runtimeStats
        logString = ""
        if log == self.agentLog:
            stats = self.agentRuntimeStats
            for agentStats in stats:
                if agentStats == stats[-1]:
                    logString += f"\t{json.dumps(agentStats)}\n]"
                else:
                    logString += f"\t{json.dumps(agentStats)},\n"
        else:
            environmentWealthCreated = 0
            environmentWealthTotal = 0
            for i in range(self.environment.width):
                for j in range(self.environment.height):
                    environmentWealthCreated += self.environment.grid[i][j].sugarLastProduced + self.environment.grid[i][j].spiceLastProduced
                    environmentWealthTotal += self.environment.grid[i][j].sugar + self.environment.grid[i][j].spice
            self.runtimeStats["environmentWealthCreated"] = environmentWealthCreated
            self.runtimeStats["environmentWealthTotal"] = environmentWealthTotal
            logString = f"\t{json.dumps(stats)}\n]"
        if self.logFormat == "csv":
            logString = ""
            # Ensure consistent ordering for CSV format
            if log == self.agentLog:
                for agentStats in stats:
                    for stat in agentStats:
                        if logString == "":
                            logString += f"{agentStats[stat]}"
                        else:
                            logString += f",{agentStats[stat]}"
                    logString += "\n"
            else:
                for stat in sorted(stats):
                    if logString == "":
                        logString += f"{stats[stat]}"
                    else:
                        logString += f",{stats[stat]}"
                logString += "\n"
        log.write(logString)
        log.flush()
        log.close()

    def endSimulation(self):
        self.removeDeadAgents()
        self.endLog(self.log)
        self.endLog(self.agentLog)
        if "all" in self.debug or "sugarscape" in self.debug:
            print(str(self))
        exit(0)

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

    def isDiseaseExperimentalGroup(self, diseaseID):
        if self.experimentalGroup == None:
            return False
        if "disease" in self.experimentalGroup:
            experimentalDiseaseID = re.search(r"disease(?P<ID>\d+)", self.experimentalGroup).group("ID")
            if int(diseaseID) == int(experimentalDiseaseID):
                return True
        return False

    def pauseSimulation(self):
        while self.run == False:
            if self.gui != None and self.end == False:
                self.gui.window.update()
            if self.end == True:
                self.endSimulation()

    def randomizeAgentEndowments(self, numAgents):
        configs = self.configuration
        aggressionFactor = configs["agentAggressionFactor"]
        baseInterestRate = configs["agentBaseInterestRate"]
        decisionModelFactor = configs["agentDecisionModelFactor"]
        decisionModelLookaheadDiscount = configs["agentDecisionModelLookaheadDiscount"]
        decisionModelLookaheadFactor = configs["agentDecisionModelLookaheadFactor"]
        decisionModelTribalFactor = configs["agentDecisionModelTribalFactor"]
        diseaseProtectionChance = configs["agentDiseaseProtectionChance"]
        dynamicSelfishnessFactor = configs["agentDynamicSelfishnessFactor"]
        dynamicTemperanceFactor = configs["agentDynamicTemperanceFactor"]
        femaleFertilityAge = configs["agentFemaleFertilityAge"]
        femaleInfertilityAge = configs["agentFemaleInfertilityAge"]
        fertilityFactor = configs["agentFertilityFactor"]
        follower = configs["agentLeader"]
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
        temperanceFactor = configs["agentTemperanceFactor"]
        tradeFactor = configs["agentTradeFactor"]
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
                          "dynamicSelfishnessFactor": {"endowments": [], "curr": dynamicSelfishnessFactor[0], "min": dynamicSelfishnessFactor[0], "max": dynamicSelfishnessFactor[1]},
                          "dynamicTemperanceFactor": {"endowments": [], "curr": dynamicTemperanceFactor[0], "min": dynamicTemperanceFactor[0], "max": dynamicTemperanceFactor[1]},
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
                          "temperanceFactor": {"endowments": [], "curr": temperanceFactor[0], "min": temperanceFactor[0], "max": temperanceFactor[1]},
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
                              "depressionFactor": depressionFactors[i], "follower": follower}
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

    def randomizeDiseaseEndowments(self, numDiseases):
        configs = self.configuration
        aggressionPenalty = configs["diseaseAggressionPenalty"]
        fertilityPenalty = configs["diseaseFertilityPenalty"]
        friendlinessPenalty = configs["diseaseFriendlinessPenalty"]
        happinessPenalty = configs["diseaseHappinessPenalty"]
        incubationPeriod = configs["diseaseIncubationPeriod"]
        movementPenalty = configs["diseaseMovementPenalty"]
        spiceMetabolismPenalty = configs["diseaseSpiceMetabolismPenalty"]
        startTimestep = configs["diseaseTimeframe"]
        sugarMetabolismPenalty = configs["diseaseSugarMetabolismPenalty"]
        tagLength = configs["diseaseTagStringLength"]
        transmissionChance = configs["diseaseTransmissionChance"]
        visionPenalty = configs["diseaseVisionPenalty"]

        configurations = {"aggressionPenalty": {"endowments": [], "curr": aggressionPenalty[0], "min": aggressionPenalty[0], "max": aggressionPenalty[1]},
                          "fertilityPenalty": {"endowments": [], "curr": fertilityPenalty[0], "min": fertilityPenalty[0], "max": fertilityPenalty[1]},
                          "friendlinessPenalty": {"endowments": [], "curr": friendlinessPenalty[0], "min": friendlinessPenalty[0], "max": friendlinessPenalty[1]},
                          "happinessPenalty": {"endowments": [], "curr": happinessPenalty[0], "min": happinessPenalty[0], "max": happinessPenalty[1]},
                          "incubationPeriod": {"endowments": [], "curr": incubationPeriod[0], "min": incubationPeriod[0], "max": incubationPeriod[1]},
                          "movementPenalty": {"endowments": [], "curr": movementPenalty[0], "min": movementPenalty[0], "max": movementPenalty[1]},
                          "spiceMetabolismPenalty": {"endowments": [], "curr": spiceMetabolismPenalty[0], "min": spiceMetabolismPenalty[0], "max": spiceMetabolismPenalty[1]},
                          "startTimestep": {"endowments": [], "curr": startTimestep[0], "min": startTimestep[0], "max": startTimestep[1]},
                          "sugarMetabolismPenalty": {"endowments": [], "curr": sugarMetabolismPenalty[0], "min": sugarMetabolismPenalty[0], "max": sugarMetabolismPenalty[1]},
                          "tagLength": {"endowments": [], "curr": tagLength[0], "min": tagLength[0], "max": tagLength[1]},
                          "transmissionChance": {"endowments": [], "curr": transmissionChance[0], "min": transmissionChance[0], "max": transmissionChance[1]},
                          "visionPenalty": {"endowments": [], "curr": visionPenalty[0], "min": visionPenalty[0], "max": visionPenalty[1]}
                          }

        # Map configuration to a random number via hash to make random number generation independent of iteration order
        if (self.diseaseConfigHashes == None):
            self.diseaseConfigHashes = {}
            for penalty in configurations.keys():
                hashed = hashlib.md5(penalty.encode())
                self.diseaseConfigHashes[penalty] = int(hashed.hexdigest(), 16)

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
        tags = []
        for i in range(numDiseases):
            for config in configurations.keys():
                if config == "tagLength":
                    tagLength = configurations[config]["curr"]
                    tags.append([random.randrange(2) for i in range(tagLength)])
                config = configurations[config]
                config["endowments"].append(config["curr"])
                config["curr"] += config["inc"]
                config["curr"] = round(config["curr"], config["decimals"])
                if config["curr"] > config["max"]:
                    config["curr"] = config["min"]

        # Keep state of random numbers to allow extending agent endowments without altering original random object state
        randomNumberReset = random.getstate()
        for config in configurations:
            random.seed(self.diseaseConfigHashes[config] + self.timestep)
            random.shuffle(configurations[config]["endowments"])
        random.setstate(randomNumberReset)
        random.shuffle(tags)

        for i in range(numDiseases):
            diseaseEndowment = {"tags": tags.pop()}
            for config in configurations:
                    diseaseEndowment[config] = configurations[config]["endowments"].pop()
            endowments.append(diseaseEndowment)
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
            agent.doDeath()
            self.agents.remove(agent)

    def replaceDeadAgents(self):
        numAgents = len(self.agents)
        if numAgents < self.configuration["agentReplacements"]:
            numReplacements = self.configuration["agentReplacements"] - numAgents
            self.configureAgents(numReplacements)

    def runSimulation(self, timesteps=5):
        self.startLog(self.log)
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
        if self.configuration["keepAliveAtEnd"] == True and self.gui != None:
            self.run = False
            self.pauseSimulation()
        else:
            self.endSimulation()

    def startLog(self, log):
        if log == None:
            return
        stats = sorted(self.runtimeStats)
        if log == self.agentLog:
            stats = self.agentRuntimeStats[0]
        if self.logFormat == "csv":
            header = ""
            # Ensure consistent ordering for CSV format
            for stat in stats:
                if header == "":
                    header += f"{stat}"
                else:
                    header += f",{stat}"
            header += "\n"
            log.write(header)
        else:
            log.write("[\n")
        self.writeToLog(log)

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
                if agent == self.agentLeader:
                    continue
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
            if agent == self.agentLeader:
                continue
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
            self.updateRuntimeStatsPerGroup(self.experimentalGroup, notInGroup=True)
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
        meanSelfishness = 0
        meanSocialHappiness = 0
        meanSpiceMetabolism = 0
        meanSugarMetabolism = 0
        combinedMetabolism = 0
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
        carryingCapacityWeight = 0.05
        carryingCapacity = math.ceil((carryingCapacityWeight * len(self.agents)) + ((1 - carryingCapacityWeight) * self.runtimeStats["carryingCapacity"]))
        if self.timestep == 0:
            carryingCapacity = len(self.agents)

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
        agentLastMoveOptimalityPercentage = 0
        agentMoves = 0
        agentMeanTimeToLive = 0
        agentStarvationDeaths = 0
        agentTotalMetabolism = 0
        agentWealthBurnRate = 0
        agentWealthCollected = 0
        agentWealthTotal = 0

        meanDeathsPercentage = 0
        sickAgentsPercentage = 0

        diseaseEffectiveReproductionRate = 0
        diseaseIncidence = 0
        diseasePrevalence = 0
        infectors = set()

        combatControlToControl = 0
        combatControlToExperimental = 0
        combatExperimentalToControl = 0
        combatExperimentalToExperimental = 0
        diseaseControlToControl = 0
        diseaseControlToExperimental = 0
        diseaseExperimentalToControl = 0
        diseaseExperimentalToExperimental = 0
        lendingControlToControl = 0
        lendingControlToExperimental = 0
        lendingExperimentalToControl = 0
        lendingExperimentalToExperimental = 0
        reproductionControlToControl = 0
        reproductionControlToExperimental = 0
        reproductionExperimentalToControl = 0
        reproductionExperimentalToExperimental = 0
        tradeControlToControl = 0
        tradeControlToExperimental = 0
        tradeExperimentalToControl = 0
        tradeExperimentalToExperimental = 0

        agentsBorn = 0
        agentsReplaced = 0
        remainingTribes = 0
        tribes = {}
        
        meanNeighbors = 0
        meanControlNeighbors = 0
        meanExperimentalNeighbors = 0
        meanValidMoves = 0
        meanMoveRank = 0
        meanMoveDifferenceFromOptimal = 0

        for agent in self.agents:
            if group != None and agent.isInGroup(group, notInGroup) == False:
                continue
            agentTimeToLive = agent.findTimeToLive()
            agentTimeToLiveAgeLimited = agent.findTimeToLive(True)
            agentWealth = agent.sugar + agent.spice
            meanSelfishness += agent.selfishnessFactor
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
            if agent.lastMoveOptimal == True:
                agentLastMoveOptimalityPercentage += 1
            agentMoves += 1

            meanNeighbors += len(agent.movementNeighborhood)
            if self.experimentalGroup != None:
                for neighbor in agent.movementNeighborhood:
                    if neighbor.isInGroup(self.experimentalGroup, notInGroup=True):
                        meanControlNeighbors += 1
                    else:
                        meanExperimentalNeighbors += 1
            meanValidMoves += len(agent.validMoves)
            for i in range(len(agent.validMoves)):
                cell = agent.validMoves[i]["cell"]
                if cell == agent.cell:
                    meanMoveDifferenceFromOptimal += agent.validMoves[0]["wealth"] - agent.validMoves[i]["wealth"]
                    meanMoveRank += i
                    break

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
            if group != None and agent.isInGroup(group):
                combatExperimentalToControl += agent.combatWithControlGroup
                combatExperimentalToExperimental += agent.combatWithExperimentalGroup
                diseaseExperimentalToControl += agent.diseaseWithControlGroup
                diseaseExperimentalToExperimental += agent.diseaseWithExperimentalGroup
                lendingExperimentalToControl += agent.lendingWithControlGroup
                lendingExperimentalToExperimental += agent.lendingWithExperimentalGroup
                reproductionExperimentalToControl += agent.reproductionWithControlGroup
                reproductionExperimentalToExperimental += agent.reproductionWithExperimentalGroup
                tradeExperimentalToControl += agent.tradeWithControlGroup
                tradeExperimentalToExperimental += agent.tradeWithExperimentalGroup
                agent.resetTimestepMetrics()
            elif group != None and agent.isInGroup(group, notInGroup=True):
                combatControlToControl += agent.combatWithControlGroup
                combatControlToExperimental += agent.combatWithExperimentalGroup
                diseaseControlToControl += agent.diseaseWithControlGroup
                diseaseControlToExperimental += agent.diseaseWithExperimentalGroup
                lendingControlToControl += agent.lendingWithControlGroup
                lendingControlToExperimental += agent.lendingWithExperimentalGroup
                reproductionControlToControl += agent.reproductionWithControlGroup
                reproductionControlToExperimental += agent.reproductionWithExperimentalGroup
                tradeControlToControl += agent.tradeWithControlGroup
                tradeControlToExperimental += agent.tradeWithExperimentalGroup
                agent.resetTimestepMetrics()
            numAgents += 1

            for disease in agent.diseases:
                # If in the experimental group for a specific disease, skip other diseases
                if group != None and self.isDiseaseExperimentalGroup(disease["disease"].ID) == False and notInGroup == False:
                    continue
                # If in the control group for a specific disease, skip the experimental disease
                elif group != None and self.isDiseaseExperimentalGroup(disease["disease"].ID) == True and notInGroup == True:
                    continue
                if disease["caught"] == self.timestep:
                    diseaseIncidence += 1
                    if self.timestep != 0:
                        infectors.add(disease["infector"])

        numDeadAgents = 0
        meanAgeAtDeath = 0
        for agent in self.deadAgents:
            if group != None and agent.isInGroup(group, notInGroup) == False:
                continue
            # If agent moved this timestep but died, count its movement optimality
            if agent.timestep == self.timestep:
                if agent.lastMoveOptimal == True:
                    agentLastMoveOptimalityPercentage += 1
                agentMoves += 1
            agentWealth = agent.sugar + agent.spice
            meanAgeAtDeath += agent.age
            agentWealthCollected += agentWealth - (agent.lastSugar + agent.lastSpice)
            agentAgingDeaths += 1 if agent.causeOfDeath == "aging" else 0
            agentCombatDeaths += 1 if agent.causeOfDeath == "combat" else 0
            agentDiseaseDeaths += 1 if agent.diseaseDeath == True else 0
            agentStarvationDeaths += 1 if agent.causeOfDeath == "starvation" else 0
            if group != None and agent.isInGroup(group):
                combatExperimentalToControl += agent.combatWithControlGroup
                combatExperimentalToExperimental += agent.combatWithExperimentalGroup
                diseaseExperimentalToControl += agent.diseaseWithControlGroup
                diseaseExperimentalToExperimental += agent.diseaseWithExperimentalGroup
                lendingExperimentalToControl += agent.lendingWithControlGroup
                lendingExperimentalToExperimental += agent.lendingWithExperimentalGroup
                reproductionExperimentalToControl += agent.reproductionWithControlGroup
                reproductionExperimentalToExperimental += agent.reproductionWithExperimentalGroup
                tradeExperimentalToControl += agent.tradeWithControlGroup
                tradeExperimentalToExperimental += agent.tradeWithExperimentalGroup
            elif group != None and agent.isInGroup(group, notInGroup=True):
                combatControlToControl += agent.combatWithControlGroup
                combatControlToExperimental += agent.combatWithExperimentalGroup
                diseaseControlToControl += agent.diseaseWithControlGroup
                diseaseControlToExperimental += agent.diseaseWithExperimentalGroup
                lendingControlToControl += agent.lendingWithControlGroup
                lendingControlToExperimental += agent.lendingWithExperimentalGroup
                reproductionControlToControl += agent.reproductionWithControlGroup
                reproductionControlToExperimental += agent.reproductionWithExperimentalGroup
                tradeControlToControl += agent.tradeWithControlGroup
                tradeControlToExperimental += agent.tradeWithExperimentalGroup
            numDeadAgents += 1

            for disease in agent.diseases:
                # If in the experimental group for a specific disease, skip other diseases
                if group != None and self.isDiseaseExperimentalGroup(disease["disease"].ID) == False and notInGroup == False:
                    continue
                # If in the control group for a specific disease, skip the experimental disease
                elif group != None and self.isDiseaseExperimentalGroup(disease["disease"].ID) == True and notInGroup == True:
                    continue
                if disease["caught"] == self.timestep:
                    diseaseIncidence += 1
                    if self.timestep != 0:
                        infectors.add(disease["infector"])
        meanAgeAtDeath = round(meanAgeAtDeath / numDeadAgents, 2) if numDeadAgents > 0 else 0

        for disease in self.diseases:
            # If in the experimental group for a specific disease, skip other diseases
            if group != None and self.isDiseaseExperimentalGroup(disease.ID) == False and notInGroup == False:
                continue
            # If in the control group for a specific disease, skip the experimental disease
            elif group != None and self.isDiseaseExperimentalGroup(disease.ID) == True and notInGroup == True:
                continue
            # Depression does not have an infection mechanism for transmission
            if disease.ID == "depression":
                continue
            diseasePrevalence += len(disease.infected)

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
            meanSelfishness = round(meanSelfishness / numAgents, 2)
            meanSocialHappiness = round(meanSocialHappiness / numAgents, 2)
            meanTradePrice = round(meanTradePrice / numTraders, 2) if numTraders > 0 else 0
            meanVision = round(meanVision / numAgents, 2)
            meanWealth = round(meanWealth / numAgents, 2)
            meanWealthHappiness = round(meanWealthHappiness / numAgents, 2)
            minWealth = round(minWealth, 2)
            remainingTribes = len(tribes)
            tradeVolume = round(tradeVolume, 2)
            meanDeathsPercentage = round((numDeadAgents / numAgents) * 100, 2)
            sickAgentsPercentage = round((sickAgents / numAgents) * 100, 2)
            diseaseEffectiveReproductionRate = round(diseaseIncidence / len(infectors), 2) if len(infectors) > 0 else 0
            agentLastMoveOptimalityPercentage = round((agentLastMoveOptimalityPercentage / agentMoves) * 100, 2)
            
            meanNeighbors = round(meanNeighbors / numAgents, 2)
            meanControlNeighbors = round(meanControlNeighbors / numAgents, 2)
            meanExperimentalNeighbors = round(meanExperimentalNeighbors / numAgents, 2)
            meanValidMoves = round(meanValidMoves / numAgents, 2)
            meanMoveRank = round(meanMoveRank / numAgents, 2)
            meanMoveDifferenceFromOptimal = round(meanMoveDifferenceFromOptimal / meanNeighbors, 2) if meanNeighbors > 0 else 0
            
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
            meanSelfishness = 0
            meanSocialHappiness = 0
            meanVision = 0
            meanWealth = 0
            meanWealthHappiness = 0
            minWealth = 0
            remainingTribes = 0
            tradeVolume = 0
            diseaseEffectiveReproductionRate = 0

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
                        "carryingCapacity": carryingCapacity, "largestTribe": maxTribe, "largestTribeSize": maxTribeSize, "maxWealth": maxWealth,
                        "meanAge": meanAge, "meanAgeAtDeath": meanAgeAtDeath, "meanConflictHappiness": meanConflictHappiness,
                        "meanFamilyHappiness": meanFamilyHappiness, "meanHappiness": meanHappiness, "meanHealthHappiness": meanHealthHappiness,
                        "meanMetabolism": meanMetabolism, "meanMovement": meanMovement, "meanMoveDifferenceFromOptimal": meanMoveDifferenceFromOptimal,
                        "meanMoveRank": meanMoveRank, "meanNeighbors": meanNeighbors, "meanSelfishness": meanSelfishness,
                        "meanSocialHappiness": meanSocialHappiness, "meanTradePrice": meanTradePrice, "meanWealth": meanWealth,
                        "meanWealthHappiness": meanWealthHappiness, "meanValidMoves": meanValidMoves, "meanVision": meanVision, "minWealth": minWealth,
                        "population": numAgents, "sickAgents": sickAgents, "remainingTribes": remainingTribes, "tradeVolume": tradeVolume,
                        "meanDeathsPercentage": meanDeathsPercentage, "sickAgentsPercentage": sickAgentsPercentage,
                        "diseaseEffectiveReproductionRate": diseaseEffectiveReproductionRate, "diseaseIncidence": diseaseIncidence,
                        "diseasePrevalence": diseasePrevalence, "agentLastMoveOptimalityPercentage": agentLastMoveOptimalityPercentage
                        }

        controlInteractionStats = {"combatControlGroupToControlGroup": combatControlToControl, "combatControlGroupToExperimentalGroup": combatControlToExperimental,
                                   "diseaseControlGroupToControlGroup": diseaseControlToControl, "diseaseControlGroupToExperimentalGroup": diseaseControlToExperimental,
                                   "lendingControlGroupToControlGroup": lendingControlToControl, "lendingControlGroupToExperimentalGroup": lendingControlToExperimental,
                                   "reproductionControlGroupToControlGroup": reproductionControlToControl, "reproductionControlGroupToExperimentalGroup": reproductionControlToExperimental,
                                   "tradeControlGroupToControlGroup": tradeControlToControl, "tradeControlGroupToExperimentalGroup": tradeControlToExperimental,
                                   }

        experimentalInteractionStats = {"combatExperimentalGroupToControlGroup": combatExperimentalToControl, "combatExperimentalGroupToExperimentalGroup": combatExperimentalToExperimental,
                                        "diseaseExperimentalGroupToControlGroup": diseaseExperimentalToControl, "diseaseExperimentalGroupToExperimentalGroup": diseaseExperimentalToExperimental,
                                        "lendingExperimentalGroupToControlGroup": lendingExperimentalToControl, "lendingExperimentalGroupToExperimentalGroup": lendingExperimentalToExperimental,
                                        "reproductionExperimentalGroupToControlGroup": reproductionExperimentalToControl, "reproductionExperimentalGroupToExperimentalGroup": reproductionExperimentalToExperimental,
                                        "tradeExperimentalGroupToControlGroup": tradeExperimentalToControl, "tradeExperimentalGroupToExperimentalGroup": tradeExperimentalToExperimental
                                        }

        groupMovementStats = {"meanControlNeighbors": meanControlNeighbors, "meanExperimentalNeighbors": meanExperimentalNeighbors}
        if self.experimentalGroup != None:
            runtimeStats.update(groupMovementStats)

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
            if notInGroup == True:
                runtimeStats.update(controlInteractionStats)
            else:
                runtimeStats.update(experimentalInteractionStats)

        for key in runtimeStats.keys():
            self.runtimeStats[key] = runtimeStats[key]

    def writeToLog(self, log):
        if log == None:
            return
        stats = self.runtimeStats
        if log == self.agentLog:
            stats = self.agentRuntimeStats
            logString = ""
            for agentStats in stats:
                logString += f"\t{json.dumps(agentStats)},\n"
        else:
            logString = f"\t{json.dumps(stats)},\n"
        if self.logFormat == "csv":
            logString = ""
            # Ensure consistent ordering for CSV format
            if log == self.agentLog:
                for agentStats in stats:
                    for stat in agentStats:
                        if logString == "":
                            logString += f"{agentStats[stat]}"
                        else:
                            logString += f",{agentStats[stat]}"
                    logString += "\n"
            else:
                for stat in sorted(stats):
                    if logString == "":
                        logString += f"{stats[stat]}"
                    else:
                        logString += f",{stats[stat]}"
                logString += "\n"
        log.write(logString)

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

def sortConfigurationTimeframes(configuration, timeframe):
    config = configuration[timeframe]
    if configuration != [0, 0]:
        start = config[0]
        end = config[1]
        # Ensure start and end are in correct order
        if start > end and end >= 0:
            swap = start
            start = end
            end = swap
            if "all" in configuration["debugMode"] or "sugarscape" in configuration["debugMode"] or "environment" in configuration["debugMode"]:
                print(f"Start and end values provided for {timeframe} in incorrect order. Switching values around.")
        # If provided a negative value, assume the start timestep is the very first of the simulation
        if start < 0:
            if "all" in configuration["debugMode"] or "sugarscape" in configuration["debugMode"] or "environment" in configuration["debugMode"]:
                print(f"Start timestep {start} for {timeframe} is invalid. Setting {timeframe} start timestep to 0.")
            start = 0
        # If provided a negative value, assume the end timestep is the very end of the simulation
        if end < 0:
            if "all" in configuration["debugMode"] or "sugarscape" in configuration["debugMode"] or "environment" in configuration["debugMode"]:
                print(f"End timestep {end} for {timeframe} is invalid. Setting {timeframe} end timestep to {configuration['timesteps']}.")
            end = configuration["timesteps"]
        config = [start, end]
    return config

def verifyConfiguration(configuration):
    negativesAllowed = ["agentDecisionModelTribalFactor", "agentMaxAge", "agentSelfishnessFactor"]
    negativesAllowed += ["diseaseAggressionPenalty", "diseaseFertilityPenalty", "diseaseFriendlinessPenalty", "diseaseHappinessPenalty", "diseaseMovementPenalty"]
    negativesAllowed += ["diseaseSpiceMetabolismPenalty", "diseaseSugarMetabolismPenalty", "diseaseTimeframe", "diseaseVisionPenalty"]
    negativesAllowed += ["environmentEquator", "environmentPollutionDiffusionTimeframe", "environmentPollutionTimeframe", "environmentMaxSpice", "environmentMaxSugar"]
    negativesAllowed += ["interfaceHeight", "interfaceWidth", "seed", "timesteps"]
    timeframes = ["diseaseTimeframe", "environmentPollutionDiffusionTimeframe", "environmentPollutionTimeframe"]
    negativeFlag = 0
    for configName, configValue in configuration.items():
        if isinstance(configValue, list):
            if len(configValue) == 0:
                continue
            configType = type(configValue[0])
            if configName in timeframes:
                configuration[configName] = sortConfigurationTimeframes(configuration, configName)
            else:
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

    # If no specific disease is tracked, revert to generic sick experimental group
    if configuration["experimentalGroup"] != None and "disease" in configuration["experimentalGroup"]:
            experimentalDiseaseID = re.search(r"disease(?P<ID>\d+)", configuration["experimentalGroup"])
            if experimentalDiseaseID == None:
                configuration["experimentalGroup"] = "sick"

    if configuration["environmentMaxSpice"] < 0:
        configuration["environmentMaxSpice"] = random.randint(1, 10)
    if configuration["environmentMaxSugar"] < 0:
        configuration["environmentMaxSugar"] = random.randint(1, 10)
    for peak in configuration["environmentSpicePeaks"]:
        if len(peak) < 3:
            peak.append(configuration["environmentMaxSpice"])
        if peak[0] < 0 or peak[0] > configuration["environmentWidth"]:
            peak[0] = random.randint(0, configuration["environmentWidth"] - 1)
        if peak[1] < 0 or peak[1] > configuration["environmentHeight"]:
            peak[1] = random.randint(0, configuration["environmentHeight"] - 1)
        if len(peak) < 3 or peak[2] < 0:
            peak[2] = random.randint(1, configuration["environmentMaxSpice"])
        elif peak[2] > configuration["environmentMaxSpice"]:
            peak[2] = configuration["environmentMaxSpice"]
    for peak in configuration["environmentSugarPeaks"]:
        if len(peak) < 3:
            peak.append(configuration["environmentMaxSugar"])
        if peak[0] < 0 or peak[0] > configuration["environmentWidth"]:
            peak[0] = random.randint(0, configuration["environmentWidth"] - 1)
        if peak[1] < 0 or peak[1] > configuration["environmentHeight"]:
            peak[1] = random.randint(0, configuration["environmentHeight"] - 1)
        if peak[2] < 0:
            peak[2] = random.randint(1, configuration["environmentMaxSugar"])
        elif peak[2] > configuration["environmentMaxSugar"]:
            peak[2] = configuration["environmentMaxSugar"]

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
    
    # Ensure agent temperance is properly set
    if configuration["agentTemperanceFactor"][0] < 0:
        if configuration["agentTemperanceFactor"][1] != -1:
            if "all" in configuration["debugMode"] or "agent" in configuration["debugMode"]:
                print(f"Cannot have agent temperance factor range of  {configuration['agentTemperanceFactor']}. Disabling agent temperance.")
        configuration["agentTemperanceFactor"] = [-1,-1]
    elif configuration["agentTemperanceFactor"][1] > 1:
        if "all" in configuration["debugMode"] or "agent" in configuration["debugMode"]:
            print(f"Cannot have agent maximum temperance factor of {configuration['agentTemperanceFactor'][1]}. Setting agent maximum temperance factor to 1.0.")
        configuration["agentTemperanceFactor"][1] = 1.0
    
    if configuration["agentDynamicTemperanceFactor"][0] < 0:
        if configuration["agentTemperanceFactor"][1] != -1:
            if "all" in configuration["debugMode"] or "agent" in configuration["debugMode"]:
                print(f"Cannot have agent dynamic temperance factor of {configuration['agentDynamicTemperanceFactor']}. Disabling agent temperance.")
        configuration["agentDynamicTemperanceFactor"] = [-1,-1]
    elif configuration["agentDynamicTemperanceFactor"][1] > 1:
        if "all" in configuration["debugMode"] or "agent" in configuration["debugMode"]:
            print(f"Cannot have agent maximum dynamic temperance factor of {configuration['agentDynamicTemperanceFactor'][1]}. Setting agent maximum dynamic temperance change to 1.0.")
        configuration["agentDynamicTemperanceFactor"][1] = 1.0

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

    # Ensure the most number of starting diseases per agent is equal to total starting diseases in the environment
    if configuration["startingDiseasesPerAgent"] != [0, 0]:
        startingDiseasesPerAgent = sorted(configuration["startingDiseasesPerAgent"])
        startingDiseasesPerAgent = [max(0, numDiseases) for numDiseases in startingDiseasesPerAgent]
        startingDiseases = configuration["startingDiseases"]
        startingDiseasesPerAgent = [min(startingDiseases, numDiseases) for numDiseases in startingDiseasesPerAgent]
        if "all" in configuration["debugMode"] or "disease" in configuration["debugMode"] and startingDiseasesPerAgent != configuration["startingDiseasesPerAgent"]:
            print(f"Range of starting diseases per agent exceeds {startingDiseases} starting diseases. Setting range to {startingDiseasesPerAgent}.")
        configuration["startingDiseasesPerAgent"] = startingDiseasesPerAgent

    if configuration["logfile"] == "":
        configuration["logfile"] = None

    if configuration["agentLogfile"] == "":
        configuration["agentLogfile"] = None

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

    # Ensure experimental group is properly defined or otherwise ignored
    if configuration["experimentalGroup"] == "":
        configuration["experimentalGroup"] = None
    groupList = ["depressed", "female", "male", "sick"]
    if type(configuration["agentDecisionModels"]) == str:
        groupList.append(configuration["agentDecisionModels"])
    else:
        groupList += configuration["agentDecisionModels"]
    if configuration["experimentalGroup"] != None and configuration["experimentalGroup"] not in groupList and "disease" not in configuration["experimentalGroup"]:
        if "all" in configuration["debugMode"] or "agent" in configuration["debugMode"]:
            print(f"Cannot provide separate log stats for experimental group {configuration['experimentalGroup']}. Disabling separate log stats.")
        configuration["experimentalGroup"] = None
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
                     "agentDiseaseProtectionChance": [0.0, 0.0],
                     "agentDynamicSelfishnessFactor": [0.0, 0.0],
                     "agentDynamicTemperanceFactor": [0,0],
                     "agentFemaleInfertilityAge": [0, 0],
                     "agentFemaleFertilityAge": [0, 0],
                     "agentFertilityFactor": [0, 0],
                     "agentImmuneSystemLength": 0,
                     "agentInheritancePolicy": "none",
                     "agentLeader": False,
                     "agentLendingFactor": [0, 0],
                     "agentLoanDuration": [0, 0],
                     "agentLogfile": None,
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
                     "agentTemperanceFactor": [0,0],
                     "agentTradeFactor": [0, 0],
                     "agentUniversalSpice": [0,0],
                     "agentUniversalSugar": [0,0],
                     "agentVision": [1, 6],
                     "agentVisionMode": "cardinal",
                     "debugMode": ["none"],
                     "diseaseAggressionPenalty": [0, 0],
                     "diseaseFertilityPenalty": [0, 0],
                     "diseaseFriendlinessPenalty": [0, 0],
                     "diseaseHappinessPenalty": [0,0],
                     "diseaseIncubationPeriod": [0, 0],
                     "diseaseList": [],
                     "diseaseMovementPenalty": [0, 0],
                     "diseaseSpiceMetabolismPenalty": [0, 0],
                     "diseaseSugarMetabolismPenalty": [0, 0],
                     "diseaseTagStringLength": [0, 0],
                     "diseaseTimeframe": [0, 0],
                     "diseaseTransmissionChance": [1.0, 1.0],
                     "diseaseVisionPenalty": [0, 0],
                     "environmentEquator": -1,
                     "environmentFile": None,
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
                     "environmentSpicePeaks": [[35, 35, 4], [15, 15, 4]],
                     "environmentSpiceProductionPollutionFactor": 0,
                     "environmentSpiceRegrowRate": 0,
                     "environmentStartingQuadrants": [1, 2, 3, 4],
                     "environmentSugarConsumptionPollutionFactor": 0,
                     "environmentSugarPeaks": [[35, 15, 4], [15, 35, 4]],
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
                     "keepAliveAtEnd": False,
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
