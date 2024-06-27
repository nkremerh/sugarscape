import agent

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
            cellSiteWealth += min(cell.agent.wealth, globalMaxCombatLoot)
            cellMaxSiteWealth += min(cell.agent.wealth, globalMaxCombatLoot)
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
