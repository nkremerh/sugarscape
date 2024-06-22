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

    def createDistanceTable(self, maxCellRange):
        distanceTable = {}
        for deltaX in range(maxCellRange + 1):
            for deltaY in range(maxCellRange + 1):
                # Find distances accounting for wraparound
                deltaX, deltaY = self.findOrthogonalDistance(deltaX, deltaY)
                deltaXY = tuple(sorted((deltaX, deltaY)))
                distanceTable[deltaXY] = math.sqrt(deltaX ** 2 + deltaY ** 2)
        return distanceTable

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

    def findCardinalCellRanges(self, maxCellRange, cellCoords, numCells):
        for i in range(numCells):
            x1, y1 = cellCoords[i]
            eastRange = min(x1 + maxCellRange, self.width - 1)
            southRange = min(y1 + maxCellRange, self.height - 1)
            for j in range(x1 + 1, eastRange + 1):
                self.grid[x1][y1].ranges[j - x1].append({"cell": self.grid[j][y1], "distance": j - x1})
                self.grid[j][y1].ranges[j - x1].append({"cell": self.grid[x1][y1], "distance": j - x1})
            for j in range(y1 + 1, southRange + 1):
                self.grid[x1][y1].ranges[j - y1].append({"cell": self.grid[x1][j], "distance": j - y1})
                self.grid[x1][j].ranges[j - y1].append({"cell": self.grid[x1][y1], "distance": j - y1})

    def findCell(self, x, y):
        return self.grid[x][y]

    def findCellNeighbors(self):
        for i in range(self.width):
            for j in range(self.height):
                self.grid[i][j].findNeighbors(self.neighborhoodMode)

    def findCellRanges(self):
        config = self.sugarscape.configuration
        maxVision = config["startingDiseases"] * max(config["diseaseVisionPenalty"][1], 0) + config["agentVision"][1]
        maxMovement = config["startingDiseases"] * max(config["diseaseMovementPenalty"][1], 0) + config["agentMovement"][1]
        maxAgentRange = max(maxVision, maxMovement)
        maxCellRange = math.ceil(max(self.width - 1, self.height - 1))
        if maxAgentRange < maxCellRange:
            maxCellRange = maxAgentRange
        
        cellCoords = [(x, y) for x in range(self.width) for y in range(self.height)]
        numCells = self.width * self.height
        # Initialize cell.ranges with necessary range values
        for x, y in cellCoords:
            self.grid[x][y].ranges = {gridRange: [] for gridRange in range(maxCellRange + 1)}

        if config["agentVisionMode"] == "radial" and config["agentMovementMode"] == "radial":
            self.findRadialCellRanges(maxCellRange, cellCoords, numCells)
        else:
            self.findCardinalCellRanges(maxCellRange, cellCoords, numCells)

    def findOrthogonalDistance(self, deltaX, deltaY):
        if self.sugarscape.configuration["environmentWraparound"] == False:
            return deltaX, deltaY
        # Find shortest distance accounting for wraparound
        deltaX = abs(deltaX)
        if deltaX > self.width / 2:
            deltaX = self.width - deltaX
        deltaY = abs(deltaY)
        if deltaY > self.height / 2:
            deltaY = self.height - deltaY
        return deltaX, deltaY

    def findRadialCellRanges(self, maxCellRange, cellCoords, numCells):
        self.distanceTable = self.createDistanceTable(maxCellRange)
        for i in range(numCells):
            x1, y1 = cellCoords[i]
            for j in range(i + 1, numCells):
                x2, y2 = cellCoords[j]  
                deltaX, deltaY = self.findOrthogonalDistance(x1 - x2, y1 - y2)
                # Skip cells that are out of feasible range
                if deltaX > maxCellRange or deltaY > maxCellRange:
                    continue

                distance = self.distanceTable[tuple(sorted((deltaX, deltaY)))]
                gridRange = math.floor(distance)
                if gridRange <= maxCellRange:
                    self.grid[x1][y1].ranges[gridRange].append({"cell": self.grid[x2][y2], "distance": distance})
                    self.grid[x2][y2].ranges[gridRange].append({"cell": self.grid[x1][y1], "distance": distance})

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
