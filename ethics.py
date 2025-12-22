import agent

import random
import sys
from math import erf

class Asimov(agent.Agent):
    def __init__(self, agentID, birthday, cell, configuration):
        super().__init__(agentID, birthday, cell, configuration)
        self.lastTimeToLive = 0

    def findBestEthicalCell(self, cells, greedyBestCell=None):
        if len(cells) == 0:
            return None
        bestCell = None
        if "all" in self.debug or "agent" in self.debug:
            self.printCellScores(cells)

        for cell in cells:
            cell["wealth"] = self.findEthicalValueOfCell(cell["cell"])
        cells = self.sortCellsByWealth(cells)
        for cell in cells:
            if cell["wealth"] > 0:
                bestCell = cell["cell"]
                break

        if bestCell == None:
            bestCell = self.cell
            if "all" in self.debug or "agent" in self.debug:
                print(f"Agent {self.ID} could not find an ethical cell")
        return bestCell

    def findEthicalValueOfCell(self, cell):
        cellValue = cell.sugar + cell.spice
        # Max combat loot for sugar and spice
        globalMaxCombatLoot = cell.environment.maxCombatLoot * 2
        if cell.agent != None:
            agentWealth = cell.agent.sugar + cell.agent.spice
            cellValue += min(agentWealth, globalMaxCombatLoot)
        lawThreeScore = self.scoreLawThree(cell)
        scoreModifier = lawThreeScore
        for neighbor in self.neighborhood:
            lawOneScore = self.scoreLawOne(neighbor, cell)
            # If the first law would be broken, immediately stop consideration
            if lawOneScore < 0:
                return lawOneScore
            lawScores = lawOneScore + self.scoreLawTwo(neighbor)
            scoreModifier += lawScores
        cellValue = scoreModifier * cellValue
        return cellValue

    def scoreLawOne(self, neighbor, cell):
        nonRobot = self.decisionModel != neighbor.decisionModel
        starvation = cell.spice + neighbor.spice - neighbor.findSpiceMetabolism() <= 0 or cell.sugar + neighbor.sugar - neighbor.findSugarMetabolism() <= 0
        # A robot may not injure a human being
        if cell.isOccupied() == True and neighbor == cell.agent and nonRobot == True:
            return -1 * sys.maxsize
        if neighbor.canReachCell(cell) == False:
            return 1
        # Through inaction, a robot may not allow a human being to come to harm
        elif nonRobot == True and starvation == True:
            return -1 * sys.maxsize
        return 0

    def scoreLawTwo(self, neighbor):
        # A robot must obey the orders given it by human beings except where such orders would conflict with the first law
        # Robots are fully autonomous, thus implicitly always conform to the second law
        return 0

    def scoreLawThree(self, cell):
        spiceIncrease = cell.spice + self.spice - self.findSpiceMetabolism() > 0
        sugarIncrease = cell.sugar + self.sugar - self.findSugarMetabolism() > 0
        # A robot must protect its own existence as such protection does not conflict with the first or second law
        if spiceIncrease == True and sugarIncrease == True:
            return 1
        elif spiceIncrease == False and sugarIncrease == False:
            return -1
        return 0

    def spawnChild(self, childID, birthday, cell, configuration):
        return Asimov(childID, birthday, cell, configuration)

class Bentham(agent.Agent):
    def __init__(self, agentID, birthday, cell, configuration):
        super().__init__(agentID, birthday, cell, configuration)
        self.lastTimeToLive = 0

    def findBestEthicalCell(self, cells, greedyBestCell=None):
        if len(cells) == 0:
            return None
        bestCell = None
        cells = self.sortCellsByWealth(cells)
        if "all" in self.debug or "agent" in self.debug:
            self.printCellScores(cells)

        for cell in cells:
            cell["wealth"] = self.findEthicalValueOfCell(cell["cell"])
        if self.selfishnessFactor >= 0:
            for cell in cells:
                if cell["wealth"] > 0:
                    bestCell = cell["cell"]
                    break
        else:
            # Negative utilitarian model uses positive and negative utility to find minimum harm
            cells.sort(key = lambda cell: (cell["wealth"]["unhappiness"], cell["wealth"]["happiness"]), reverse = True)
            bestCell = cells[0]["cell"]

        # If additional ordering consideration, select new best cell
        if "Top" in self.decisionModel:
            cells = self.sortCellsByWealth(cells)
            if "all" in self.debug or "agent" in self.debug:
                self.printEthicalCellScores(cells)
            bestCell = cells[0]["cell"]

        if bestCell == None:
            if greedyBestCell == None:
                bestCell = cells[0]["cell"]
            else:
                bestCell = greedyBestCell
            if "all" in self.debug or "agent" in self.debug:
                print(f"Agent {self.ID} could not find an ethical cell")
        return bestCell

    def findEthicalValueOfCell(self, cell):
        happiness = 0
        unhappiness = 0
        cellSiteWealth = cell.sugar + cell.spice
        # Max combat loot for sugar and spice
        globalMaxCombatLoot = cell.environment.maxCombatLoot * 2
        cellMaxSiteWealth = cell.maxSugar + cell.maxSpice
        if cell.agent != None:
            agentWealth = cell.agent.sugar + cell.agent.spice
            cellSiteWealth += min(agentWealth, globalMaxCombatLoot)
            cellMaxSiteWealth += min(agentWealth, globalMaxCombatLoot)
        cellNeighborWealth = cell.findNeighborWealth()
        globalMaxWealth = cell.environment.globalMaxSugar + cell.environment.globalMaxSpice
        cellValue = 0
        neighborhoodSize = len(self.neighborhood)
        futureNeighborhoodSize = len(self.findNeighborhood(cell)) if self.decisionModelLookaheadFactor != 0 else 1
        for neighbor in self.neighborhood:
            certainty = 1 if neighbor.canReachCell(cell) == True else 0
            # Skip if agent cannot reach cell
            if certainty == 0:
                continue
            # Timesteps to reach cell, currently 1 since agents only plan for the current timestep
            timestepDistance = 1
            neighborMetabolism = neighbor.sugarMetabolism + neighbor.spiceMetabolism
            # If agent does not have metabolism, set duration to seemingly infinite
            cellDuration = cellSiteWealth / neighborMetabolism if neighborMetabolism > 0 else 0
            proximity = 1 / timestepDistance
            intensity = (1 / (1 + neighbor.findTimeToLive()) / (1 + cell.pollution))
            duration = cellDuration / cellMaxSiteWealth if cellMaxSiteWealth > 0 else 0
            # Agent discount, futureDuration, and futureIntensity implement Bentham's purity and fecundity
            discount = neighbor.decisionModelLookaheadDiscount if neighbor.decisionModelLookaheadFactor != 0 else 0
            futureDuration = (cellSiteWealth - neighborMetabolism) / neighborMetabolism if neighborMetabolism > 0 else cellSiteWealth
            futureDuration = futureDuration / cellMaxSiteWealth if cellMaxSiteWealth > 0 else 0
            # Normalize future intensity by number of adjacent cells
            cellNeighbors = len(neighbor.cell.neighbors)
            futureIntensity = cellNeighborWealth / (globalMaxWealth * cellNeighbors)
            # Normalize extent by total cells in range
            cellsInRange = len(neighbor.cellsInRange)
            extent = neighborhoodSize / cellsInRange if cellsInRange > 0 else 1
            futureExtent = futureNeighborhoodSize / cellsInRange if cellsInRange > 0 and self.decisionModelLookaheadFactor != 0 else 1
            neighborCellValue = 0

            currentReward = extent * (intensity + duration)
            futureReward = futureExtent * (futureIntensity + futureDuration)
            neighborCellValue = (certainty * proximity) * (currentReward + (discount * futureReward))

            # If not the agent moving, consider these as opportunity costs
            if neighbor != self and self.selfishnessFactor < 1:
                neighborCellValue = -1 * neighborCellValue
                # If move will kill this neighbor and penalty is too slight, make it more severe
                if cell == neighbor.cell and neighborCellValue > -1:
                    neighborCellValue = -1

            if self.decisionModelTribalFactor >= 0:
                if neighbor.findTribe() == self.findTribe():
                    neighborCellValue *= self.decisionModelTribalFactor
                else:
                    neighborCellValue *= 1 - self.decisionModelTribalFactor
            if self.selfishnessFactor >= 0:
                if neighbor == self:
                    neighborCellValue *= self.selfishnessFactor
                else:
                    neighborCellValue *= 1 - self.selfishnessFactor
            else:
                if neighborCellValue > 0:
                    happiness += neighborCellValue
                else:
                    unhappiness += neighborCellValue
            cellValue += neighborCellValue

        if self.selfishnessFactor < 0:
            return {"happiness": happiness, "unhappiness": unhappiness}
        return cellValue

    def updateValues(self):
        if self.dynamicSelfishnessFactor != 0:
            self.updateSelfishnessFactor()

    def updateSelfishnessFactor(self):
        if self.timeToLive < self.lastTimeToLive and self.selfishnessFactor < 1.0:
            self.selfishnessFactor += self.dynamicSelfishnessFactor
        elif self.timeToLive > self.lastTimeToLive and self.selfishnessFactor > 0.0:
            self.selfishnessFactor -= self.dynamicSelfishnessFactor
        self.selfishnessFactor = round(self.selfishnessFactor, 2)
        self.lastTimeToLive = self.timeToLive

    def spawnChild(self, childID, birthday, cell, configuration):
        return Bentham(childID, birthday, cell, configuration)

class Leader(agent.Agent):
    def __init__(self, agentID, birthday, cell, configuration):
        super().__init__(agentID, birthday, cell, configuration)
        # Special leader agent should be configured to be immortal and omniscient
        self.fertilityFactor = 0.0
        self.follower = False
        self.grid = [[[] for j in range(self.cell.environment.height)] for i in range(self.cell.environment.width)]
        self.agentPlacements = {}
        self.leader = True
        self.maxAge = -1
        self.movement = 0
        self.spice = sys.maxsize
        self.spiceMetabolism = 0
        self.sugar = sys.maxsize
        self.sugarMetabolism = 0
        self.tradeFactor = 0.0
        self.vision = max(self.cell.environment.height, self.cell.environment.width)

    def doAging(self):
        agents = self.cell.environment.sugarscape.agents
        # Consider being the last one left alive as an aging death for the leader
        if len(agents) == 1 and agents[0] == self:
            self.doDeath("aging")

    def moveAgentsToCells(self):
        self.resetForTimestep()
        env = self.cell.environment
        agents = env.sugarscape.agents

    def findBestCell(self):
        self.resetForTimestep()
        agents = self.cell.environment.sugarscape.agents
        agentsByNeed = []
        for agent in agents:
            if agent.isAlive() == False or agent == self:
                continue
            urgency = self.findUrgencyForAgent(agent)
            viableCells = self.findViableCellsForAgent(agent)
            for cell in viableCells:
                self.grid[cell.x][cell.y].append({"agent": agent, "urgency": urgency})

        width = self.cell.environment.width
        height = self.cell.environment.height

        placedAgents = []
        for i in range(width):
            for j in range(height):
                if len(self.grid[i][j]) == 0:
                    continue
                sorted(self.grid[i][j], key=lambda agentRecord: agentRecord["urgency"])
                agent = self.grid[i][j].pop()["agent"]
                cell = self.cell.environment.grid[i][j]
                invalidCell = cell.isOccupied() and agent.isNeighborValidPrey(cell.agent) == False
                while len(self.grid[i][j]) > 0 and (agent in placedAgents or agent.isAlive() == False or invalidCell == True) and len(self.grid[i][j]):
                    agent = self.grid[i][j].pop()["agent"]
                    invalidCell = cell.isOccupied() and agent.isNeighborValidPrey(cell.agent) == False
                self.agentPlacements[agent.ID] = cell

        # Leader agent should not move
        return self.cell

    def findBestCellForAgent(self, agent):
        if agent.ID not in self.agentPlacements:
            return agent.cell
        return self.agentPlacements[agent.ID]

    def findUrgencyForAgent(self, agent):
        diseased = 0 if agent.isSick() else 1
        happiness = agent.findHappiness()
        timeToLive = agent.findTimeToLive()
        # Lower score yields higher urgency
        return diseased + happiness + timeToLive

    def findViableCellsForAgent(self, agent):
        agent.findCellsInRange()
        viableCells = []
        spiceMetabolism = agent.findSpiceMetabolism()
        sugarMetabolism = agent.findSugarMetabolism()
        for cell in agent.cellsInRange:
            viableSpice = agent.spice + cell.spice - spiceMetabolism
            viableSugar = agent.sugar + cell.sugar - sugarMetabolism
            if viableSpice > 0 and viableSugar > 0:
                viableCells.append(cell)
        return viableCells

    def resetForTimestep(self):
        # Always ensure leader has maximum resources each timestep
        self.spice = sys.maxsize
        self.sugar = sys.maxsize
        self.grid = [[[] for j in range(self.cell.environment.height) ] for i in range(self.cell.environment.width)]
        #self.grid[self.cell.x][self.cell.y] = self
        self.agentPlacements = {self.ID: self.cell}

    def spawnChild(self, childID, birthday, cell, configuration):
        return Leader(childID, birthday, cell, configuration)

class Temperance(agent.Agent):
    def __init__(self, agentID, birthday, cell, configuration):
        super().__init__(agentID, birthday, cell, configuration)
        self.totalMetabolism = self.findSugarMetabolism() + self.findSpiceMetabolism()
        self.rules = {
                "agentConsumedAdequateResources": 0,
                "agentConsumedAmpleResources": 0,
                "communityDisapprovalOfAmpleResourceConsumption":  0,
                "agentOverconsumedResources": 0,
                "communityDisdainOfExtremeOverconsumption": 0
            }
        self.timeSeenOverconsuming = 0
        self.timesSeenIndulging = 0
        self.lastSelectedCellWealthToNeedRatio = 0
        self.socialPressure = 0
        self.previousCellWealthToMetabolismRatio = 0
        
    def doTemperanceDecision(self, cells, greedyBestCell):
        randomValue = random.random()
        if (randomValue >= self.temperanceFactor):
            self.doIntemperanceAction()
            return greedyBestCell
        else:
            self.doTemperanceAction()
            # Temperance action, seek cell closest to metabolic needs
            cells.sort(key = lambda cell: abs(cell["wealth"] - self.totalMetabolism))

            return cells[0]["cell"]
      
    def doIntemperanceAction(self):
        newTemperanceFactor = round(self.temperanceFactor - self.dynamicTemperanceFactor, 2)
        self.temperanceFactor = newTemperanceFactor if newTemperanceFactor >= 0 else 0
        print(f"Agent {self.ID} decreased temperance factor to {self.temperanceFactor}")

    def doTemperanceAction(self):
        newTemperanceFactor = round(self.temperanceFactor + self.dynamicTemperanceFactor, 2)
        self.temperanceFactor = newTemperanceFactor if newTemperanceFactor <= 1 else 1
        print(f"Agent {self.ID} increased temperance factor to {self.temperanceFactor}")

    def findBestEthicalCell(self, cells, greedyBestCell=None):
        if len(cells) == 0:
            return None
        if "all" in self.debug or "agent" in self.debug:
            self.printCellScores(cells)
        
        self.findPECSValueOfCells(cells)
                
        return self.doTemperanceDecision(cells, greedyBestCell)
    
    def findPECSValueOfCells(self, weightedCells):

        if self.totalMetabolism == 0:
            print(f"Agent {self.ID} has zero metabolic need, cannot compute cell PECS values")
            return 
        
        for weightedCell in weightedCells:
            cellWealth = weightedCell["wealth"]    
            
            physicalScore = self.findCellPhysicalScore()
            emotionalScore = self.findCellEmotionalScore(cellWealth)  
            cognitiveScore = self.findCellCognitiveScore(cellWealth)   
            socialScore = self.findCellSocialScore(weightedCell, cellWealth)
            
            weightedCell["wealth"] = round((erf(physicalScore) + erf(emotionalScore) + erf(cognitiveScore) + erf(socialScore)), 2)
            print(f"Agent {self.ID} evaluated cell at ({weightedCell['cell'].x},{weightedCell['cell'].y}) with wealth {cellWealth} has PECS score {weightedCell['wealth']} (P:{physicalScore},E:{emotionalScore},C:{cognitiveScore},S:{socialScore})")
        
            weightedCell["wealthToMetabolismRatio"] = self.findCellWealth(weightedCell["cell"]) / self.totalMetabolism if self.totalMetabolism > 0 else 0
     
        weightedCells.sort(key = lambda cell: cell["wealth"])
        
    def findCellPhysicalScore(self):
        if self.timeToLive <= 1:
            return 4
        elif self.timeToLive > 1 and self.timeToLive <= 2:
            return 3
        elif self.timeToLive > 2 and self.timeToLive <=3:
            return 2
        else:
            return 1
        
    def findCellEmotionalScore(self,cellWealth):
        emotionalScore = 0            
        environmentMaxSugar = self.cell.environment.sugarscape.configuration["environmentMaxSugar"]
        environmentMaxSpice = self.cell.environment.sugarscape.configuration["environmentMaxSpice"]
        meanMaxCellWealth = (environmentMaxSugar + environmentMaxSpice) / 2

        if cellWealth == 0:
            emotionalScore = -1
        elif cellWealth > 0 and cellWealth < meanMaxCellWealth:
            emotionalScore = 1
        elif cellWealth >= meanMaxCellWealth and cellWealth < max(environmentMaxSugar, environmentMaxSpice):
            emotionalScore = 2
        else:
            emotionalScore = 3 - (self.rules["communityDisdainOfExtremeOverconsumption"] + self.rules["communityDisapprovalOfAmpleResourceConsumption"])
        return emotionalScore
    
    def findCellCognitiveScore(self,cellWealth):
        cognitiveScore = 0
        wealthToTotalMetabolismRatio = cellWealth / self.totalMetabolism
        
        print("Wealth to metabolism ratio:", wealthToTotalMetabolismRatio)
        print("CellWealth:", cellWealth, "TotalMetabolism:", self.totalMetabolism)
        if wealthToTotalMetabolismRatio < 1: 
            cognitiveScore = -1
        elif wealthToTotalMetabolismRatio >= 1 and wealthToTotalMetabolismRatio < 2 and self.rules['agentConsumedAdequateResources']:
            cognitiveScore = self.rules["agentConsumedAdequateResources"]   
        elif wealthToTotalMetabolismRatio >= 2 and wealthToTotalMetabolismRatio < 3:
            if self.rules["agentConsumedAmpleResources"]:
                cognitiveScore = self.rules["agentConsumedAmpleResources"]
            if self.rules["communityDisapprovalOfAmpleResourceConsumption"]:
                cognitiveScore -= self.rules["communityDisapprovalOfAmpleResourceConsumption"]
        elif wealthToTotalMetabolismRatio >= 3:
            if self.rules["agentOverconsumedResources"]:
                cognitiveScore -= self.rules["agentOverconsumedResources"]
            elif self.rules["communityDisdainOfExtremeOverconsumption"]:
                cognitiveScore -= self.rules["communityDisdainOfExtremeOverconsumption"]  
        print(self.rules["agentConsumedAdequateResources"], self.rules["agentConsumedAmpleResources"], self.rules["communityDisapprovalOfAmpleResourceConsumption"], self.rules["agentOverconsumedResources"], self.rules["communityDisdainOfExtremeOverconsumption"])
        return cognitiveScore
    
    def findCellSocialScore(self, cell, cellWealth):
        socialScore = 0
        wealthToTotalMetabolismRatio = cellWealth / self.totalMetabolism
        
        if wealthToTotalMetabolismRatio <= 1:
            socialScore = 1
        elif wealthToTotalMetabolismRatio > 1 and wealthToTotalMetabolismRatio <= 2:
            socialScore -= self.timeSeenOverconsuming
        elif wealthToTotalMetabolismRatio > 2:
            socialScore -= self.timesSeenIndulging
        
        print(f"Agent {self.ID} has social score {socialScore} with social pressure {self.socialPressure} for cell at ({cell['cell'].x},{cell['cell'].y})")
        
        return round((socialScore * self.socialPressure), 1)
    
    def findNumberOfAgentsInNeighborhood(self, cell):
        return len(self.findNeighborhood(cell))
    
    def updateAgentSocialPressureAfterConsumption(self):
        if self.cell is None:
            return
        numAgentsInNeighborhood = self.findNumberOfAgentsInNeighborhood(self.cell)
        
        # print(f"Agent {self.ID} found {numAgentsInNeighborhood} agents in neighborhood of cell at ({cell.x},{cell.y})")
        if numAgentsInNeighborhood == 0:
            return 0
        #TODO: modify this to be dynamic based on number of agents and distance from current agent
        # That is, farther agents have less social pressure, closer ones have more (up to configured maxSocialPressure)
        else:
            print("called socialPressure addition")
            self.socialPressure += self.dynamicSocialPressureFactor
            return self.socialPressure
    
    def updateAgentTemperanceRules(self):
        numAgentsInNeighborhood = self.findNumberOfAgentsInNeighborhood(self.cell)
        
        if self.previousCellWealthToMetabolismRatio <= 1: 
            # Consuming up to 1x metabolic need is good for the agent
            self.rules["agentConsumedAdequateResources"] += 1
            
        elif self.previousCellWealthToMetabolismRatio > 1 and self.previousCellWealthToMetabolismRatio <= 2:
            # Consuming 1-2x metabolic is is great for the agent
            self.rules["agentConsumedAmpleResources"] += 1
            
            # Consuming 1-2x metabolic need is overconsumption and is bad for the community
            if numAgentsInNeighborhood > 0:
                self.timeSeenOverconsuming += 1
                self.rules["communityDisapprovalOfAmpleResourceConsumption"] += 1
            
        elif self.previousCellWealthToMetabolismRatio > 2:
            # Consuming more than 2x metabolic need is bad for both the agent and the community
            self.rules["agentOverconsumedResources"] += 1
            
            if numAgentsInNeighborhood > 0:
                self.timesSeenIndulging += 1 
                self.rules["communityDisdainOfExtremeOverconsumption"] += 1
        print("Updated temperance rules:", self.rules)
        print("Number of agents in neighborhood:", numAgentsInNeighborhood)
        print("Wealth to metabolism ratio when updating:", self.previousCellWealthToMetabolismRatio)
    
    def collectResourcesAtCell(self):
        self.previousCellWealthToMetabolismRatio = self.findCellWealth(self.cell) / self.totalMetabolism if self.totalMetabolism > 0 else 0
        super().collectResourcesAtCell()
    
    def doMetabolism(self):        
        self.updateAgentSocialPressureAfterConsumption()
        super().doMetabolism()

    def updateValues(self):
        super().updateValues()
        self.updateAgentTemperanceRules()
    
    def rankCellsInRange(self):
        self.findCellsInRange()
        if len(self.cellsInRange) == 0:
            return [{"cell": self.cell, "wealth": 0, "range": 0}]
        cellsInRange = list(self.cellsInRange.items())
        
        potentialCells = []
        
        for cell, travelDistance in cellsInRange:
            cellWealth = self.findCellWealth(cell)
            cellRange = travelDistance
            
            if cell.isOccupied() and not self.isNeighborValidPrey(cell.agent):
                continue
            
            #TODO: for temperance, should we just base it off the available resources there?
            
           
            potentialCells.append({"cell": cell, "wealth": cellWealth, "range": cellRange})
        
        return self.sortCellsByWealth(potentialCells)
    
    def findCellWealth(self, cell = None):
        if cell is None:
            cell = self.cell
        totalResources = cell.sugar + cell.spice
        
        maxCombatLoot = self.findCombatLootAtCell(cell)
        
        print(f"Agent {self.ID} found cell at ({cell.x},{cell.y}) has total resources {totalResources} and combat loot {maxCombatLoot} for a total wealth of {totalResources + maxCombatLoot}")
        return totalResources + maxCombatLoot
    
    def findCombatLootAtCell(self, cell):
        combatLoot = 0
        if cell.isOccupied():
            preyAgent = cell.agent
            if self.isNeighborValidPrey(preyAgent):
                preyWealth = preyAgent.sugar + preyAgent.spice
                maxCombatLoot = cell.environment.maxCombatLoot
                combatLoot = min(preyWealth, maxCombatLoot)
        return combatLoot
        
    def spawnChild(self, childID, birthday, cell, configuration):
        return Temperance(childID, birthday, cell, configuration)
