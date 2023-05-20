import math

class Cell:
    def __init__(self, x, y, environment, maxSugar=0, maxSpice=0, growbackRate=0):
        self.x = x
        self.y = y
        self.environment = environment
        self.maxSugar = maxSugar
        self.currSugar = maxSugar
        self.maxSpice = maxSpice
        self.currSpice = maxSpice
        self.currPollution = 0
        self.agent = None
        self.hemisphere = "north" if self.x >= self.environment.equator else "south"
        self.season = None
        self.timestep = 0
        self.neighbors = []

    def doSpiceConsumptionPollution(self, spiceConsumed):
        consumptionPollutionFactor = self.environment.spiceConsumptionPollutionFactor
        self.currPollution += consumptionPollutionFactor * spiceConsumed

    def doSugarConsumptionPollution(self, sugarConsumed):
        consumptionPollutionFactor = self.environment.sugarConsumptionPollutionFactor
        self.currPollution += consumptionPollutionFactor * sugarConsumed

    def doPollutionDiffusion(self):
        meanPollution = self.currPollution
        for neighbor in self.neighbors:
            meanPollution += neighbor.currPollution
        meanPollution = meanPollution / (len(self.neighbors) + 1)
        for neighbor in self.neighbors:
            neighbor.currPollution = meanPollution
        self.currPollution = meanPollution

    def doSpiceProductionPollution(self, spiceProduced):
        productionPollutionFactor = self.environment.spiceProductionPollutionFactor
        self.currPollution += productionPollutionFactor * spiceProduced

    def doSugarProductionPollution(self, sugarProduced):
        productionPollutionFactor = self.environment.sugarProductionPollutionFactor
        self.currPollution += productionPollutionFactor * sugarProduced

    def doTimestep(self, timestep):
        return

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

    def findEastNeighbor(self):
        eastWrapAround = self.environment.width
        eastIndex = self.x + 1
        if eastIndex >= eastWrapAround:
            eastIndex = 0
        eastNeighbor = self.environment.findCell(eastIndex, self.y)
        return eastNeighbor

    def findNorthNeighbor(self):
        northWrapAround = self.environment.height
        northIndex = self.y + 1
        if northIndex >= northWrapAround:
            northIndex = 0
        northNeighbor = self.environment.findCell(self.x, northIndex)
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
        self.currSpice = 0

    def resetSugar(self):
        self.currSugar = 0

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
            string = "{0}/{1}".format(str(self.currSugar), str(self.currSpice))
        return string
