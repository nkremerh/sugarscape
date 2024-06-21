import math
import random

class Environment:
    # Assumption: grid is always indexed by [width][height]
    def __init__(self, height, width, sugarscape, configuration):
        self.width = width
        self.height = height
        self.globalMaxSugar = configuration["globalMaxSugar"]
        self.sugarRegrowRate = configuration["sugarRegrowRate"]
        self.globalMaxSpice = configuration["globalMaxSpice"]
        self.spiceRegrowRate = configuration["spiceRegrowRate"]
        self.sugarscape = sugarscape
        self.timestep = 0
        self.seed = configuration["sugarscapeSeed"]
        self.seasonInterval = configuration["seasonInterval"]
        self.seasonalGrowbackDelay = configuration["seasonalGrowbackDelay"]
        self.seasonNorth = "wet" if configuration["seasonInterval"] > 0 else None
        self.seasonSouth = "dry" if configuration["seasonInterval"] > 0 else None
        self.seasonalGrowbackCountdown = configuration["seasonalGrowbackDelay"]
        self.pollutionDiffusionDelay = configuration["pollutionDiffusionDelay"]
        self.pollutionDiffusionCountdown = configuration["pollutionDiffusionDelay"]
        self.sugarConsumptionPollutionFactor = configuration["sugarConsumptionPollutionFactor"]
        self.spiceConsumptionPollutionFactor = configuration["spiceConsumptionPollutionFactor"]
        self.sugarProductionPollutionFactor = configuration["sugarProductionPollutionFactor"]
        self.spiceProductionPollutionFactor = configuration["spiceProductionPollutionFactor"]
        self.maxCombatLoot = configuration["maxCombatLoot"]
        self.universalSpiceIncomeInterval = configuration["universalSpiceIncomeInterval"]
        self.universalSugarIncomeInterval = configuration["universalSugarIncomeInterval"]
        self.equator = configuration["equator"] if configuration["equator"] >= 0 else math.ceil(self.height / 2)
        self.neighborhoodMode = configuration["neighborhoodMode"]
        self.wraparound = configuration["wraparound"]
        # Populate grid with NoneType objects
        self.grid = [[None for j in range(height)]for i in range(width)]

    def doCellUpdate(self):
        for i in range(self.width):
            for j in range(self.height):
                cellCurrSugar = self.grid[i][j].sugar
                cellCurrSpice = self.grid[i][j].spice
                cellMaxSugar = self.grid[i][j].maxSugar
                cellMaxSpice = self.grid[i][j].maxSpice
                cellSeason = self.grid[i][j].season
                sugarRegrowth = min(cellCurrSugar + self.sugarRegrowRate, cellMaxSugar)
                spiceRegrowth = min(cellCurrSpice + self.spiceRegrowRate, cellMaxSpice)
                if self.seasonInterval > 0:
                    if self.timestep % self.seasonInterval == 0:
                        self.grid[i][j].updateSeason()
                    if (cellSeason == "wet") or (cellSeason == "dry" and self.seasonalGrowbackCountdown == self.seasonalGrowbackDelay):
                        if self.grid[i][j].sugar + self.sugarRegrowRate != self.grid[i][j].sugar:
                            self.grid[i][j].sugarLastProduced = self.sugarRegrowRate
                        else:
                            self.grid[i][j].sugarLastProduced = 0
                        if self.grid[i][j].spice + self.spiceRegrowRate != self.grid[i][j].spice:
                            self.grid[i][j].spiceLastProduced = self.spiceRegrowRate
                        else:
                            self.grid[i][j].spiceLastProduced = 0
                        self.grid[i][j].sugar = sugarRegrowth
                        self.grid[i][j].spice = spiceRegrowth
                else:
                    if self.grid[i][j].sugar + self.sugarRegrowRate != self.grid[i][j].sugar:
                        self.grid[i][j].sugarLastProduced = self.sugarRegrowRate
                    else:
                        self.grid[i][j].sugarLastProduced = 0
                    if self.grid[i][j].spice + self.spiceRegrowRate != self.grid[i][j].spice:
                        self.grid[i][j].spiceLastProduced = self.spiceRegrowRate
                    else:
                        self.grid[i][j].spiceLastProduced = 0
                    self.grid[i][j].sugar = sugarRegrowth
                    self.grid[i][j].spice = spiceRegrowth
                if self.pollutionDiffusionDelay > 0 and self.pollutionDiffusionCountdown == self.pollutionDiffusionDelay:
                    self.grid[i][j].doPollutionDiffusion()

    def doTimestep(self, timestep):
        self.timestep = timestep
        self.updateSeasons()
        self.updatePollution()
        self.doCellUpdate()

    def findCell(self, x, y):
        return self.grid[x][y]

    def findCellNeighbors(self):
        for i in range(self.width):
            for j in range(self.height):
                self.grid[i][j].findNeighbors(self.neighborhoodMode)

    def findCellRanges(self):
        config = self.sugarscape.configuration
        minVisionPenalty = min(config["diseaseVisionPenalty"][0], 0)
        minVision = config["agentVision"][0] + minVisionPenalty
        minMovementPenalty = min(config["diseaseMovementPenalty"][0], 0)
        minMovement = config["agentMovement"][0] + minMovementPenalty
        minDistance = min(minVision, minMovement)

        maxVisionPenalty = max(config["diseaseVisionPenalty"][1], 0)
        maxVision = config["agentVision"][1] + maxVisionPenalty
        maxMovementPenalty = max(config["diseaseMovementPenalty"][1], 0)
        maxMovement = config["agentMovement"][1] + maxMovementPenalty
        maxDistance = max(maxVision, maxMovement)
        print(minDistance, maxDistance)
        if config["agentVisionMode"] == "radial" and config["agentMovementMode"] == "radial":
            findCellsInModeRange = self.findCellsInRadialRange
        else:
            findCellsInModeRange = self.findCellsInCardinalRange
        for i in range(self.width):
            for j in range(self.height):
                cell = self.grid[i][j]
                for distance in range(minDistance, maxDistance + 1):
                    cell.ranges[distance] = findCellsInModeRange(cell.x, cell.y, distance)

    def findCellsInCardinalRange(self, startX, startY, gridRange):
        cellsInRange = []
        if self.wraparound == True:
            for i in range(1, gridRange + 1):
                deltaNorth = startY - i
                deltaSouth = (startY + i + self.height) % self.height
                deltaEast = (startX + i + self.width) % self.width
                deltaWest = startX - i
                cellsInRange.append({"cell": self.grid[startX][deltaNorth], "distance": i})
                cellsInRange.append({"cell": self.grid[startX][deltaSouth], "distance": i})
                cellsInRange.append({"cell": self.grid[deltaEast][startY], "distance": i})
                cellsInRange.append({"cell": self.grid[deltaWest][startY], "distance": i})
        else:
            for i in range(1, gridRange + 1):
                deltaNorth = startY - i
                deltaSouth = startY + i
                deltaEast = startX + i
                deltaWest = startX - i
                if deltaNorth >= 0:
                    cellsInRange.append({"cell": self.grid[startX][deltaNorth], "distance": i})
                if deltaSouth <= self.height - 1:
                    cellsInRange.append({"cell": self.grid[startX][deltaSouth], "distance": i})
                if deltaEast <= self.width - 1:
                    cellsInRange.append({"cell": self.grid[deltaEast][startY], "distance": i})
                if deltaWest >= 0:
                    cellsInRange.append({"cell": self.grid[deltaWest][startY], "distance": i})
        return cellsInRange

    def findCellsInRadialRange(self, startX, startY, gridRange):
        if self.wraparound == True:
            cellsInRange = self.findCellsInCardinalRange(startX, startY, gridRange)
            # Iterate through the upper left quadrant of the circle's bounding box
            for deltaX in range(startX - gridRange, startX):
                for deltaY in range(startY - gridRange, startY):
                    euclideanDistance = math.sqrt(pow((deltaX - startX), 2) + pow((deltaY - startY), 2))
                    # If agent can see at least part of a cell, they should be allowed to consider it
                    if euclideanDistance < gridRange + 1:
                        reflectedX = (2 * startX - deltaX + self.width) % self.width
                        reflectedY = (2 * startY - deltaY + self.height) % self.height
                        cellsInRange.append({"cell": self.grid[deltaX][deltaY], "distance": euclideanDistance})
                        cellsInRange.append({"cell": self.grid[deltaX][reflectedY], "distance": euclideanDistance})
                        cellsInRange.append({"cell": self.grid[reflectedX][deltaY], "distance": euclideanDistance})
                        cellsInRange.append({"cell": self.grid[reflectedX][reflectedY], "distance": euclideanDistance})        
        else:
            cellsInRange = []
            # Iterate through the bounding box of the circle
            for deltaX in range(max(0, startX - gridRange), min(self.width, startX + gridRange + 1)):
                for deltaY in range(max(0, startY - gridRange), min(self.height, startY + gridRange + 1)):
                    # If agent can see at least part of a cell, they should be allowed to consider it
                    euclideanDistance = math.sqrt((deltaX - startX)**2 + (deltaY - startY)**2)
                    if euclideanDistance < gridRange + 1 and self.grid[deltaX][deltaY] != self.grid[startX][startY]:
                        cellsInRange.append({"cell": self.grid[deltaX][deltaY], "distance": euclideanDistance})
        return cellsInRange

    def resetCell(self, x, y):
        self.grid[x][y] = None

    def setCell(self, cell, x, y):
        if self.grid[x][y] == None:
            if y < self.equator:
                cell.season = self.seasonNorth
            else:
                cell.season = self.seasonSouth
            self.grid[x][y] = cell

    def updatePollution(self):
        if self.pollutionDiffusionDelay > 0:
            self.pollutionDiffusionCountdown -= 1
            # Pollution diffusion delay over
            if self.pollutionDiffusionCountdown == 0:
                self.pollutionDiffusionCountdown = self.pollutionDiffusionDelay

    def updateSeasons(self):
        if self.seasonInterval > 0:
            self.seasonalGrowbackCountdown -= 1
            # Seasonal growback delay over
            if self.seasonalGrowbackCountdown == 0:
                self.seasonalGrowbackCountdown = self.seasonalGrowbackDelay
            if self.timestep % self.seasonInterval == 0:
                if self.seasonNorth == "wet":
                    self.seasonNorth = "dry"
                    self.seasonSouth = "wet"
                else:
                    self.seasonNorth = "wet"
                    self.seasonSouth = "dry"

    def __str__(self):
        string = ""
        for i in range(self.width):
            for j in range(self.height):
                cell = self.grid[i][j]
                if cell == None:
                    cell = '_'
                else:
                    cell = str(cell)
                string = string + ' '+ cell
            string = string + '\n'
        return string
