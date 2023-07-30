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
        self.agent = None
        self.hemisphere = "north" if self.x >= self.environment.equator else "south"
        self.season = None
        self.timestep = 0
        self.neighbors = []
        self.sugarLastProduced = 0
        self.spiceLastProduced = 0

    def doSpiceConsumptionPollution(self, spiceConsumed):
        consumptionPollutionFactor = self.environment.spiceConsumptionPollutionFactor
        self.pollution += consumptionPollutionFactor * spiceConsumed

    def doSugarConsumptionPollution(self, sugarConsumed):
        consumptionPollutionFactor = self.environment.sugarConsumptionPollutionFactor
        self.pollution += consumptionPollutionFactor * sugarConsumed

    def doPollutionDiffusion(self):
        meanPollution = self.pollution
        for neighbor in self.neighbors:
            meanPollution += neighbor.pollution
        meanPollution = meanPollution / (len(self.neighbors) + 1)
        for neighbor in self.neighbors:
            neighbor.pollution = meanPollution
        self.pollution = meanPollution

    def doSpiceProductionPollution(self, spiceProduced):
        productionPollutionFactor = self.environment.spiceProductionPollutionFactor
        self.pollution += productionPollutionFactor * spiceProduced

    def doSugarProductionPollution(self, sugarProduced):
        productionPollutionFactor = self.environment.sugarProductionPollutionFactor
        self.pollution += productionPollutionFactor * sugarProduced

    def findNeighborAgents(self):
        agents = []
        for neighbor in self.neighbors:
            agent = neighbor.agent
            if agent != None:
                agents.append(agent)
        return agents

    def findNeighbors(self):
        self.neighbors = []
        self.neighbors.append(self.findNorthNeighbor())
        self.neighbors.append(self.findSouthNeighbor())
        self.neighbors.append(self.findEastNeighbor())
        self.neighbors.append(self.findWestNeighbor())

    def findNeighborWealth(self):
        neighborWealth = 0
        for neighbor in self.neighbors:
            neighborWealth += neighbor.sugar + neighbor.spice
        return neighborWealth

    def findEastNeighbor(self):
        eastWrapAround = self.environment.width
        eastIndex = self.x + 1
        if eastIndex >= eastWrapAround:
            eastIndex = 0
        eastNeighbor = self.environment.findCell(eastIndex, self.y)
        return eastNeighbor

    def findNorthNeighbor(self):
        northNeighbor = self.environment.findCell(self.x, (self.y + 1 + self.environment.height) % self.environment.height)
        return northNeighbor

    def findSouthNeighbor(self):
        southWrapAround = 0
        southIndex = self.y - 1
        if southIndex < southWrapAround:
            southIndex = self.environment.height - 1
        southNeighbor = self.environment.findCell(self.x, southIndex)
        return southNeighbor

    def findWestNeighbor(self):
        westWrapAround = 0
        westIndex = self.x - 1
        if westIndex < westWrapAround:
            westIndex = self.environment.width - 1
        westNeighbor = self.environment.findCell(westIndex, self.y)
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
        if self.season == "summer":
            self.season = "winter"
        else:
            self.season = "summer"

    def __str__(self):
        string = ""
        if self.agent != None:
            string = "-A-"
        else:
            string = "{0}/{1}".format(str(self.sugar), str(self.spice))
        return string
