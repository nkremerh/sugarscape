import math

class Cell:
    def __init__(self, x, y, environment, maxSugar=0, maxSpice=0, growbackRate=0):
        self.x = x
        self.y = y
        self.environment = environment
        self.maxSugar = maxSugar
        self.sugar = maxSugar
        self.maxSpice = maxSpice
        self.spice = maxSpice
        self.pollution = 0
        self.pollutionFlux = 0
        self.agent = None
        self.hemisphere = "north" if self.x >= self.environment.equator else "south"
        self.season = None
        self.timestep = 0
        self.neighbors = {}
        self.ranges = {}
        self.sugarLastProduced = 0
        self.spiceLastProduced = 0

    def doSpiceConsumptionPollution(self, spiceConsumed):
        consumptionPollutionFactor = self.environment.spiceConsumptionPollutionFactor
        self.pollution += consumptionPollutionFactor * spiceConsumed

    def doSugarConsumptionPollution(self, sugarConsumed):
        consumptionPollutionFactor = self.environment.sugarConsumptionPollutionFactor
        self.pollution += consumptionPollutionFactor * sugarConsumed

    def doPollutionDiffusion(self):
        self.pollution = self.pollutionFlux

    def doSpiceProductionPollution(self, spiceProduced):
        productionPollutionFactor = self.environment.spiceProductionPollutionFactor
        self.pollution += productionPollutionFactor * spiceProduced

    def doSugarProductionPollution(self, sugarProduced):
        productionPollutionFactor = self.environment.sugarProductionPollutionFactor
        self.pollution += productionPollutionFactor * sugarProduced

    def findPollutionFlux(self):
        meanPollution = 0
        for neighbor in self.neighbors.values():
            meanPollution += neighbor.pollution
        meanPollution = meanPollution / (len(self.neighbors))
        self.pollutionFlux = meanPollution

    def findNeighborAgents(self):
        agents = []
        for neighbor in self.neighbors.values():
            agent = neighbor.agent
            if agent != None:
                agents.append(agent)
        return agents

    def findNeighbors(self, mode):
        self.neighbors = {}

        north = self.findNorthNeighbor()
        south = self.findSouthNeighbor()
        east = self.findEastNeighbor()
        west = self.findWestNeighbor()
        if north is not None:
            self.neighbors["north"] = north
        if south is not None:
            self.neighbors["south"] = south
        if east is not None:
            self.neighbors["east"] = east
        if west is not None:
            self.neighbors["west"] = west

        if mode == "moore":
            northeast = north.findEastNeighbor() if north is not None else None
            northwest = north.findWestNeighbor() if north is not None else None
            southeast = south.findEastNeighbor() if south is not None else None
            southwest = south.findWestNeighbor() if south is not None else None
            if northeast is not None:
                self.neighbors["northeast"] = northeast
            if northwest is not None:
                self.neighbors["northwest"] = northwest
            if southeast is not None:
                self.neighbors["southeast"] = southeast
            if southwest is not None:
                self.neighbors["southwest"] = southwest

    def findNeighborWealth(self):
        neighborWealth = 0
        for neighbor in self.neighbors.values():
            if neighbor != None:
                neighborWealth += neighbor.sugar + neighbor.spice
        return neighborWealth

    def findEastNeighbor(self):
        if self.environment.wraparound == False and self.x + 1 > self.environment.width - 1:
            return None
        eastNeighbor = self.environment.findCell((self.x + 1 + self.environment.width) % self.environment.width, self.y)
        return eastNeighbor

    def findNorthNeighbor(self):
        if self.environment.wraparound == False and self.y - 1 < 0:
            return None
        northNeighbor = self.environment.findCell(self.x, (self.y - 1 + self.environment.height) % self.environment.height)
        return northNeighbor

    def findSouthNeighbor(self):
        if self.environment.wraparound == False and self.y + 1 < self.environment.height - 1:
            return None
        southNeighbor = self.environment.findCell(self.x, (self.y + 1 + self.environment.height) % self.environment.height)
        return southNeighbor

    def findWestNeighbor(self):
        if self.environment.wraparound == False and self.x - 1 < 0:
            return None
        westNeighbor = self.environment.findCell((self.x - 1 + self.environment.width) % self.environment.width, self.y)
        return westNeighbor

    def isOccupied(self):
        return self.agent != None

    def resetAgent(self):
        self.agent = None

    def resetSpice(self):
        self.spice = 0

    def resetSugar(self):
        self.sugar = 0

    def updateSeason(self):
        if self.season == "wet":
            self.season = "dry"
        else:
            self.season = "wet"

    def __str__(self):
        string = ""
        if self.agent != None:
            string = "-A-"
        else:
            string = f"{str(self.sugar)}/{str(self.spice)}"
        return string
