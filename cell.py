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
        self.adjacentCells = set()
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

    def findNeighborWealth(self):
        neighborWealth = 0
        for neighbor in self.neighbors:
            neighborWealth += neighbor.sugar + neighbor.spice
        return neighborWealth

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
