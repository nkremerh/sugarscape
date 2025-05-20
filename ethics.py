import agent

import sys

class Bentham(agent.Agent):
    def __init__(self, agentID, birthday, cell, configuration):
        super().__init__(agentID, birthday, cell, configuration)

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
        futureNeighborhoodSize = len(self.findNeighborhood(cell))
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
            discount = neighbor.decisionModelLookaheadDiscount
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

            # If not the agent moving, consider these as opportunity costs
            if neighbor != self and cell != neighbor.cell and self.selfishnessFactor < 1:
                duration = -1 * duration
                intensity = -1 * intensity
                futureDuration = -1 * futureDuration
                futureIntensity = -1 * futureIntensity
                if self.decisionModelLookaheadFactor == 0:
                    neighborCellValue = neighbor.decisionModelFactor * ((extent * certainty * proximity) * ((intensity + duration) + (discount * (futureIntensity + futureDuration))))
                else:
                    neighborCellValue = neighbor.decisionModelFactor * ((certainty * proximity) * ((extent * (intensity + duration)) + (discount * (futureExtent * (futureIntensity + futureDuration)))))
            # If move will kill this neighbor, consider this a penalty
            elif neighbor != self and cell == neighbor.cell and self.selfishnessFactor < 1:
                if self.decisionModelLookaheadFactor == 0:
                    neighborCellValue = -1 * ((extent * certainty * proximity) * ((intensity + duration) + (discount * (futureIntensity + futureDuration))))
                else:
                    neighborCellValue = -1 * ((certainty * proximity) * ((extent * (intensity + duration)) + (discount * (futureExtent * (futureIntensity + futureDuration)))))
                # If penalty is too slight, make it more severe
                if neighborCellValue > -1:
                    neighborCellValue = -1
            else:
                if self.decisionModelLookaheadFactor == 0:
                    neighborCellValue = neighbor.decisionModelFactor * ((extent * certainty * proximity) * ((intensity + duration) + (discount * (futureIntensity + futureDuration))))
                else:
                    neighborCellValue = neighbor.decisionModelFactor * ((certainty * proximity) * ((extent * (intensity + duration)) + (discount * (futureExtent * (futureIntensity + futureDuration)))))

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

    def spawnChild(self, childID, birthday, cell, configuration):
        return Bentham(childID, birthday, cell, configuration)

class ReactiveBentham(Bentham):
    def __init__(self, agentID, birthday, cell, configuration):
        super().__init__(agentID, birthday, cell, configuration)
        self.lastTimeToLive = 0

    def updateValues(self):
        self.updateSelfishnessFactor()

    def updateSelfishnessFactor(self):
        if self.timeToLive < self.lastTimeToLive and self.selfishnessFactor < 1.0:
            self.selfishnessFactor += 0.01
        elif self.timeToLive > self.lastTimeToLive and self.selfishnessFactor > 0.0:
            self.selfishnessFactor -= 0.01
        self.lastTimeToLive = self.timeToLive

class Leader(agent.Agent):
    def __init__(self, agentID, birthday, cell, configuration):
        super().__init__(agentID, birthday, cell, configuration)
        # Special leader agent should be configured to be immortal and omniscient
        self.fertilityFactor = 0.0
        self.follower = False
        self.grid = [[None for j in range(self.cell.environment.height) ] for i in range(self.cell.environment.width)]
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

    def findBestCell(self):
        self.resetForTimestep()
        agents = self.cell.environment.sugarscape.agents
        agentsByNeed = []
        for agent in agents:
            agentsByNeed.append({"agent": agent, "ttl": agent.findTimeToLive(), "cells": agent.rankCellsInRange()})
        agentsByNeed = sorted(agentsByNeed, key=lambda agent: agent["ttl"])
        for agentRecord in agentsByNeed:
            agent = agentRecord["agent"]
            for cellRecord in agentRecord["cells"]:
                cell = cellRecord["cell"]
                if self.grid[cell.x][cell.y] == None:
                    self.grid[cell.x][cell.y] = agent
                    self.agentPlacements[agent.ID] = self.cell.environment.grid[cell.x][cell.y]
                    break
        # Default to remain at cell if agent cannot find a new cell
        if agent.ID not in self.agentPlacements:
            self.agentPlacements[agent.ID] = agent.cell
        return self.cell

    def findBestCellForAgent(self, agent):
        if agent.ID not in self.agentPlacements:
            return agent.cell
        return self.agentPlacements[agent.ID]

    def resetForTimestep(self):
        # Always ensure leader has maximum resources each timestep
        self.spice = sys.maxsize
        self.sugar = sys.maxsize
        self.grid = [[None for j in range(self.cell.environment.height) ] for i in range(self.cell.environment.width)]
        self.grid[self.cell.x][self.cell.y] = self
        self.agentPlacements = {self.ID: self.cell}

    def spawnChild(self, childID, birthday, cell, configuration):
        return Leader(childID, birthday, cell, configuration)
