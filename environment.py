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
        if config["agentVisionMode"] == "radial" and config["agentMovementMode"] == "radial":
            findCellsAtModeRange = self.findCellsAtRadialRange
        else:
            findCellsAtModeRange = self.findCellsAtCardinalRange
        maxDistance = max(self.width, self.height)
        for i in range(self.width):
            for j in range(self.height):
                cell = self.grid[i][j]
                for distance in range(1, maxDistance):
                    cell.ranges[distance] = findCellsAtModeRange(cell.x, cell.y, distance)

    def findCellsAtCardinalRange(self, startX, startY, gridRange):
        cellsInRange = []
        deltaNorth = startY - gridRange
        deltaSouth = startY + gridRange
        deltaEast = startX + gridRange
        deltaWest = startX - gridRange
        if self.wraparound == True:
            cellsInRange.append({"cell": self.grid[startX][(deltaNorth + self.height) % self.height], "distance": gridRange})
            cellsInRange.append({"cell": self.grid[startX][(deltaSouth + self.height) % self.height], "distance": gridRange})
            cellsInRange.append({"cell": self.grid[(deltaEast + self.width) % self.width][startY], "distance": gridRange})
            cellsInRange.append({"cell": self.grid[(deltaWest + self.width) % self.width][startY], "distance": gridRange})
        else:
            if deltaNorth >= 0:
                cellsInRange.append({"cell": self.grid[startX][deltaNorth], "distance": gridRange})
            if deltaSouth <= self.height - 1:
                cellsInRange.append({"cell": self.grid[startX][deltaSouth], "distance": gridRange})
            if deltaEast <= self.width - 1:
                cellsInRange.append({"cell": self.grid[deltaEast][startY], "distance": gridRange})
            if deltaWest >= 0:
                cellsInRange.append({"cell": self.grid[deltaWest][startY], "distance": gridRange})
        return cellsInRange

    def findCellsAtRadialRange(self, startX, startY, gridRange):
        if self.wraparound == True:
            cellsInRange = self.findCellsAtCardinalRange(startX, startY, gridRange)
            # Iterate through the upper left quadrant of the circle's bounding box
            for deltaX in range(startX - gridRange, startX):
                for deltaY in range(startY - gridRange, startY):
                    euclideanDistance = math.sqrt((deltaX - startX) ** 2 + (deltaY - startY) ** 2)
                    # If agent can see at least part of a cell, they should be allowed to consider it
                    if euclideanDistance < gridRange + 1 and euclideanDistance >= gridRange and self.grid[deltaX][deltaY] != self.grid[startX][startY]:
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
                    euclideanDistance = math.sqrt((deltaX - startX) ** 2 + (deltaY - startY) ** 2)
                    if euclideanDistance < gridRange + 1 and euclideanDistance >= gridRange and self.grid[deltaX][deltaY] != self.grid[startX][startY]:
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
