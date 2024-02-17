import agent

class Altruist(agent.Agent):
    def __init__(self, agentID, birthday, cell, configuration, lookahead=None):
        super().__init__(agentID, birthday, cell, configuration)
        self.lookahead = lookahead
        if self.lookahead == None:
            self.findEthicalValueOfCell = self.findNoLookaheadValueOfCell
        else:
            self.findEthicalValueOfCell = self.findHalfLookaheadValueOfCell

    def findHalfLookaheadValueOfCell(self, cell):
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
        for neighbor in self.neighborhood:
            if neighbor == self:
                continue
            # Timesteps to reach cell, currently 1 since agent vision and movement are equal
            timestepDistance = 1
            neighborMetabolism = neighbor.sugarMetabolism + neighbor.spiceMetabolism
            # If agent does not have metabolism, set duration to seemingly infinite
            cellDuration = cellSiteWealth / neighborMetabolism if neighborMetabolism > 0 else 0
            certainty = 1 if neighbor.canReachCell(cell) == True else 0
            proximity = 1 / timestepDistance
            intensity = (1 / (1 + neighbor.findTimeToLive()) / (1 + cell.pollution))
            duration = cellDuration / cellMaxSiteWealth if cellMaxSiteWealth > 0 else 0
            # Agent discount, futureDuration, and futureIntensity implement Bentham's purity and fecundity
            discount = 0.5
            futureDuration = (cellSiteWealth - neighborMetabolism) / neighborMetabolism if neighborMetabolism > 0 else cellSiteWealth
            futureDuration = futureDuration / cellMaxSiteWealth if cellMaxSiteWealth > 0 else 0
            futureIntensity = cellNeighborWealth / (globalMaxWealth * 4)
            futureExtent = len(self.findNeighborhood(cell)) / (neighbor.vision * 4) if neighbor.vision > 0 else 1
            # Assuming agent can only see in four cardinal directions
            extent = len(self.neighborhood) / (neighbor.vision * 4) if neighbor.vision > 0 else 1
            neighborValueOfCell = 0
            # If not the agent moving, consider these as opportunity costs
            if neighbor != self and cell != neighbor.cell:
                duration = -1 * duration
                intensity = -1 * intensity
                futureDuration = -1 * futureDuration
                futureIntensity = -1 * futureIntensity
                neighborValueOfCell = neighbor.decisionModelFactor * ((certainty * proximity) * ((extent * (intensity + duration)) + (discount * (futureExtent * (futureIntensity + futureDuration)))))
            # If move will kill this neighbor, consider this a penalty
            elif neighbor != self and cell == neighbor.cell:
                neighborValueOfCell = -1 * ((certainty * proximity) * ((extent * (intensity + duration)) + (discount * (futureExtent * (futureIntensity + futureDuration)))))
                # If penalty is too slight, make it more severe
                if neighborValueOfCell > -1:
                    neighborValueOfCell = -1
            else:
                neighborValueOfCell = neighbor.decisionModelFactor * ((certainty * proximity) * ((extent * (intensity + duration)) + (discount * (futureExtent * (futureIntensity + futureDuration)))))
            cellValue += neighborValueOfCell
        return cellValue

    def findNoLookaheadValueOfCell(self, cell):
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
        for neighbor in self.neighborhood:
            if neighbor == self:
                continue
            # Timesteps to reach cell, currently 1 since agent vision and movement are equal
            timestepDistance = 1
            neighborMetabolism = neighbor.sugarMetabolism + neighbor.spiceMetabolism
            # If agent does not have metabolism, set duration to seemingly infinite
            cellDuration = cellSiteWealth / neighborMetabolism if neighborMetabolism > 0 else 0
            certainty = 1 if neighbor.canReachCell(cell) == True else 0
            proximity = 1 / timestepDistance
            intensity = (1 / (1 + neighbor.findTimeToLive()) / (1 + cell.pollution))
            duration = cellDuration / cellMaxSiteWealth if cellMaxSiteWealth > 0 else 0
            # Agent discount, futureDuration, and futureIntensity implement Bentham's purity and fecundity
            discount = 0.5
            futureDuration = (cellSiteWealth - neighborMetabolism) / neighborMetabolism if neighborMetabolism > 0 else cellSiteWealth
            futureDuration = futureDuration / cellMaxSiteWealth if cellMaxSiteWealth > 0 else 0
            futureIntensity = cellNeighborWealth / (globalMaxWealth * 4)
            # Assuming agent can only see in four cardinal directions
            extent = len(self.neighborhood) / (neighbor.vision * 4) if neighbor.vision > 0 else 1
            neighborValueOfCell = 0
            # If not the agent moving, consider these as opportunity costs
            if neighbor != self and cell != neighbor.cell:
                duration = -1 * duration
                intensity = -1 * intensity
                futureDuration = -1 * futureDuration
                futureIntensity = -1 * futureIntensity
                neighborValueOfCell = neighbor.decisionModelFactor * ((extent * certainty * proximity) * ((intensity + duration) + (discount * (futureIntensity + futureDuration))))
            # If move will kill this neighbor, consider this a penalty
            elif neighbor != self and cell == neighbor.cell:
                neighborValueOfCell = -1 * ((extent * certainty * proximity) * ((intensity + duration) + (discount * (futureIntensity + futureDuration))))
                # If penalty is too slight, make it more severe
                if neighborValueOfCell > -1:
                    neighborValueOfCell = -1
            else:
                neighborValueOfCell = neighbor.decisionModelFactor * ((extent * certainty * proximity) * ((intensity + duration) + (discount * (futureIntensity + futureDuration))))
            cellValue += neighborValueOfCell
        return cellValue

    def spawnChild(self, childID, birthday, cell, configuration):
        return Altruist(childID, birthday, cell, configuration, self.lookahead)

class Bentham(agent.Agent):
    def __init__(self, agentID, birthday, cell, configuration, lookahead=None):
        super().__init__(agentID, birthday, cell, configuration)
        self.lookahead = lookahead
        if self.lookahead == None:
            self.findEthicalValueOfCell = self.findNoLookaheadValueOfCell
        else:
            self.findEthicalValueOfCell = self.findHalfLookaheadValueOfCell

    def findHalfLookaheadValueOfCell(self, cell):
        cellSiteWealth = cell.sugar + cell.spice
        globalMaxCombatLoot = cell.environment.maxCombatLoot * 2
        cellMaxSiteWealth = cell.maxSugar + cell.maxSpice
        if cell.agent != None:
            cellSiteWealth += min(cell.agent.wealth, globalMaxCombatLoot)
            cellMaxSiteWealth += min(cell.agent.wealth, globalMaxCombatLoot)
        cellNeighborWealth = cell.findNeighborWealth()
        globalMaxWealth = cell.environment.globalMaxSugar + cell.environment.globalMaxSpice
        cellValue = 0
        selfishnessFactor = self.selfishnessFactor
        for neighbor in self.neighborhood:
            timestepDistance = 1
            neighborMetabolism = neighbor.sugarMetabolism + neighbor.spiceMetabolism
            cellDuration = cellSiteWealth / neighborMetabolism if neighborMetabolism > 0 else 0
            certainty = 1 if neighbor.canReachCell(cell) == True else 0
            proximity = 1 / timestepDistance
            intensity = (1 / (1 + neighbor.findTimeToLive()) / (1 + cell.pollution))
            duration = cellDuration / cellMaxSiteWealth if cellMaxSiteWealth > 0 else 0
            discount = 0.5
            futureDuration = (cellSiteWealth - neighborMetabolism) / neighborMetabolism if neighborMetabolism > 0 else cellSiteWealth
            futureDuration = futureDuration / cellMaxSiteWealth if cellMaxSiteWealth > 0 else 0
            futureIntensity = cellNeighborWealth / (globalMaxWealth * 4)
            extent = len(self.neighborhood) / (neighbor.vision * 4) if neighbor.vision > 0 else 1
            futureExtent = len(self.findNeighborhood(cell)) / (neighbor.vision * 4) if neighbor.vision > 0 else 1
            neighborValueOfCell = 0
            if neighbor != self and cell != neighbor.cell:
                duration = -1 * duration
                intensity = -1 * intensity
                futureDuration = -1 * futureDuration
                futureIntensity = -1 * futureIntensity
                neighborValueOfCell = neighbor.decisionModelFactor * ((certainty * proximity) * ((extent * (intensity + duration)) + (discount * (futureExtent * (futureIntensity + futureDuration)))))
            elif neighbor != self and cell == neighbor.cell:
                neighborValueOfCell = -1 * ((certainty * proximity) * ((extent * (intensity + duration)) + (discount * (futureExtent * (futureIntensity + futureDuration)))))
                if neighborValueOfCell > -1:
                    neighborValueOfCell = -1
            else:
                neighborValueOfCell = neighbor.decisionModelFactor * ((certainty * proximity) * ((extent * (intensity + duration)) + (discount * (futureExtent * (futureIntensity + futureDuration)))))
            if selfishnessFactor != -1:
                if neighbor == self:
                    neighborValueOfCell *= selfishnessFactor
                else:
                    neighborValueOfCell *= 1-selfishnessFactor
            cellValue += neighborValueOfCell
        return cellValue

    def findNoLookaheadValueOfCell(self, cell):
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
        selfishnessFactor = self.selfishnessFactor
        for neighbor in self.neighborhood:
            # Timesteps to reach cell, currently 1 since agent vision and movement are equal
            timestepDistance = 1
            neighborMetabolism = neighbor.sugarMetabolism + neighbor.spiceMetabolism
            # If agent does not have metabolism, set duration to seemingly infinite
            cellDuration = cellSiteWealth / neighborMetabolism if neighborMetabolism > 0 else 0
            certainty = 1 if neighbor.canReachCell(cell) == True else 0
            proximity = 1 / timestepDistance
            intensity = (1 / (1 + neighbor.findTimeToLive()) / (1 + cell.pollution))
            duration = cellDuration / cellMaxSiteWealth if cellMaxSiteWealth > 0 else 0
            # Agent discount, futureDuration, and futureIntensity implement Bentham's purity and fecundity
            discount = 0.5
            futureDuration = (cellSiteWealth - neighborMetabolism) / neighborMetabolism if neighborMetabolism > 0 else cellSiteWealth
            futureDuration = futureDuration / cellMaxSiteWealth if cellMaxSiteWealth > 0 else 0
            futureIntensity = cellNeighborWealth / (globalMaxWealth * 4)
            # Assuming agent can only see in four cardinal directions
            extent = len(self.neighborhood) / (neighbor.vision * 4) if neighbor.vision > 0 else 1
            neighborValueOfCell = 0
            # If not the agent moving, consider these as opportunity costs
            if neighbor != self and cell != neighbor.cell:
                duration = -1 * duration
                intensity = -1 * intensity
                futureDuration = -1 * futureDuration
                futureIntensity = -1 * futureIntensity
                neighborValueOfCell = neighbor.decisionModelFactor * ((extent * certainty * proximity) * ((intensity + duration) + (discount * (futureIntensity + futureDuration))))
            # If move will kill this neighbor, consider this a penalty
            elif neighbor != self and cell == neighbor.cell:
                neighborValueOfCell = -1 * ((extent * certainty * proximity) * ((intensity + duration) + (discount * (futureIntensity + futureDuration))))
                # If penalty is too slight, make it more severe
                if neighborValueOfCell > -1:
                    neighborValueOfCell = -1
            else:
                neighborValueOfCell = neighbor.decisionModelFactor * ((extent * certainty * proximity) * ((intensity + duration) + (discount * (futureIntensity + futureDuration))))
            if selfishnessFactor != -1:
                if neighbor == self:
                    neighborValueOfCell *= selfishnessFactor
                else:
                    neighborValueOfCell *= 1-selfishnessFactor
            cellValue += neighborValueOfCell
        return cellValue

    def spawnChild(self, childID, birthday, cell, configuration):
        return Bentham(childID, birthday, cell, configuration, self.lookahead)

class Egoist(agent.Agent):
    def __init__(self, agentID, birthday, cell, configuration, lookahead=None):
        super().__init__(agentID, birthday, cell, configuration)
        self.lookahead = lookahead
        if self.lookahead == None:
            self.findEthicalValueOfCell = self.findNoLookaheadValueOfCell
        else:
            self.findEthicalValueOfCell = self.findHalfLookaheadValueOfCell

    def findHalfLookaheadValueOfCell(self, cell):
        cellSiteWealth = cell.sugar + cell.spice
        globalMaxCombatLoot = cell.environment.maxCombatLoot * 2
        cellMaxSiteWealth = cell.maxSugar + cell.maxSpice
        if cell.agent != None:
            cellSiteWealth += min(cell.agent.wealth, globalMaxCombatLoot)
            cellMaxSiteWealth += min(cell.agent.wealth, globalMaxCombatLoot)
        cellNeighborWealth = cell.findNeighborWealth()
        globalMaxWealth = cell.environment.globalMaxSugar + cell.environment.globalMaxSpice
        cellValue = 0
        canSee = 0
        for neighbor in self.neighborhood:
            if neighbor.canReachCell(cell) == True:
                canSee += 1
        timestepDistance = 1
        neighborMetabolism = neighbor.sugarMetabolism + neighbor.spiceMetabolism
        cellDuration = cellSiteWealth / neighborMetabolism if neighborMetabolism > 0 else 0
        certainty = 1 if neighbor.canReachCell(cell) == True else 0
        proximity = 1 / timestepDistance
        intensity = (1 / (1 + neighbor.findTimeToLive()) / (1 + cell.pollution))
        duration = cellDuration / cellMaxSiteWealth if cellMaxSiteWealth > 0 else 0
        # Agent discount, futureDuration, and futureIntensity implement Bentham's purity and fecundity
        discount = 0.5
        futureDuration = (cellSiteWealth - neighborMetabolism) / neighborMetabolism if neighborMetabolism > 0 else cellSiteWealth
        futureDuration = futureDuration / cellMaxSiteWealth if cellMaxSiteWealth > 0 else 0
        futureIntensity = cellNeighborWealth / (globalMaxWealth * 4)
        futureExtent = len(self.findNeighborhood(cell)) / (neighbor.vision * 4) if neighbor.vision > 0 else 1
        # Assuming agent can only see in four cardinal directions
        extent = canSee / (neighbor.vision * 4) if neighbor.vision > 0 else 1
        neighborValueOfCell = neighbor.decisionModelFactor * ((certainty * proximity) * ((extent * (intensity + duration)) + (discount * (futureExtent * (futureIntensity + futureDuration)))))
        cellValue += neighborValueOfCell
        return cellValue

    def findNoLookaheadValueOfCell(self, cell):
        cellSiteWealth = cell.sugar + cell.spice
        globalMaxCombatLoot = cell.environment.maxCombatLoot * 2
        cellMaxSiteWealth = cell.maxSugar + cell.maxSpice
        if cell.agent != None:
            cellSiteWealth += min(cell.agent.wealth, globalMaxCombatLoot)
            cellMaxSiteWealth += min(cell.agent.wealth, globalMaxCombatLoot)
        cellNeighborWealth = cell.findNeighborWealth()
        globalMaxWealth = cell.environment.globalMaxSugar + cell.environment.globalMaxSpice
        cellValue = 0
        canSee = 0
        for neighbor in self.neighborhood:
            if neighbor.canReachCell(cell) == True:
                canSee += 1
        timestepDistance = 1
        neighborMetabolism = neighbor.sugarMetabolism + neighbor.spiceMetabolism
        cellDuration = cellSiteWealth / neighborMetabolism if neighborMetabolism > 0 else 0
        certainty = 1 if neighbor.canReachCell(cell) == True else 0
        proximity = 1 / timestepDistance
        intensity = (1 / (1 + neighbor.findTimeToLive()) / (1 + cell.pollution))
        duration = cellDuration / cellMaxSiteWealth if cellMaxSiteWealth > 0 else 0
        # Agent discount, futureDuration, and futureIntensity implement Bentham's purity and fecundity
        discount = 0.5
        futureDuration = (cellSiteWealth - neighborMetabolism) / neighborMetabolism if neighborMetabolism > 0 else cellSiteWealth
        futureDuration = futureDuration / cellMaxSiteWealth if cellMaxSiteWealth > 0 else 0
        futureIntensity = cellNeighborWealth / (globalMaxWealth * 4)
        # Assuming agent can only see in four cardinal directions
        extent = canSee / (neighbor.vision * 4) if neighbor.vision > 0 else 1
        neighborValueOfCell = neighbor.decisionModelFactor * ((extent * certainty * proximity) * ((intensity + duration) + (discount * (futureIntensity + futureDuration))))
        cellValue += neighborValueOfCell
        return cellValue

    def spawnChild(self, childID, birthday, cell, configuration):
        return Egoist(childID, birthday, cell, configuration, self.lookahead)
