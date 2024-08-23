import math
import random

class Environment:
    # Assumption: grid is always indexed by [width][height]
    def __init__(self, height, width, sugarscape, configuration):
        self.width = width
        self.height = height
        self.sugarscape = sugarscape
        self.equator = configuration["equator"] if configuration["equator"] >= 0 else math.ceil(self.height / 2)
        self.globalMaxSpice = configuration["globalMaxSpice"]
        self.globalMaxSugar = configuration["globalMaxSugar"]
        self.maxCombatLoot = configuration["maxCombatLoot"]
        self.neighborhoodMode = configuration["neighborhoodMode"]
        self.pollutionDiffusionCountdown = configuration["pollutionDiffusionDelay"]
        self.pollutionDiffusionDelay = configuration["pollutionDiffusionDelay"]
        self.pollutionDiffusionEnd = configuration["pollutionDiffusionTimeframe"][1]
        self.pollutionDiffusionStart = configuration["pollutionDiffusionTimeframe"][0]
        self.pollutionEnd = configuration["pollutionTimeframe"][1]
        self.pollutionStart = configuration["pollutionTimeframe"][0]
        self.seasonalGrowbackCountdown = configuration["seasonalGrowbackDelay"]
        self.seasonalGrowbackDelay = configuration["seasonalGrowbackDelay"]
        self.seasonInterval = configuration["seasonInterval"]
        self.seasonNorth = "wet" if configuration["seasonInterval"] > 0 else None
        self.seasonSouth = "dry" if configuration["seasonInterval"] > 0 else None
        self.seed = configuration["sugarscapeSeed"]
        self.spiceConsumptionPollutionFactor = configuration["spiceConsumptionPollutionFactor"]
        self.spiceProductionPollutionFactor = configuration["spiceProductionPollutionFactor"]
        self.spiceRegrowRate = configuration["spiceRegrowRate"]
        self.sugarConsumptionPollutionFactor = configuration["sugarConsumptionPollutionFactor"]
        self.sugarProductionPollutionFactor = configuration["sugarProductionPollutionFactor"]
        self.sugarRegrowRate = configuration["sugarRegrowRate"]
        self.universalSpiceIncomeInterval = configuration["universalSpiceIncomeInterval"]
        self.universalSugarIncomeInterval = configuration["universalSugarIncomeInterval"]
        self.wraparound = configuration["wraparound"]
        self.maxCellDistance = 0
        self.timestep = 0

        # Populate grid with NoneType objects
        self.grid = [[None for j in range(height)]for i in range(width)]

    def createDistanceTable(self, maxDeltaX, maxDeltaY):
        distanceTable = {}
        lowerMax = min(maxDeltaX, maxDeltaY)
        upperMax = max(maxDeltaX, maxDeltaY)
        lowerBorder = self.width if lowerMax == maxDeltaX else self.height
        upperBorder = self.width if lowerMax == maxDeltaY else self.height
        for lowerDelta in range(lowerMax + 1):
            for upperDelta in range(max(1, lowerDelta), upperMax + 1):
                lowerDelta = self.findWraparoundDistance(lowerDelta, lowerBorder)
                upperDelta = self.findWraparoundDistance(upperDelta, upperBorder)
                # Delta pair is used as a key to look up hypotenuse
                deltaPair = (lowerDelta, upperDelta)
                distanceTable[deltaPair] = math.sqrt(lowerDelta ** 2 + upperDelta ** 2)
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
        if self.pollutionDiffusionStart <= self.timestep <= self.pollutionDiffusionEnd and self.pollutionDiffusionDelay > 0 and self.pollutionDiffusionCountdown == self.pollutionDiffusionDelay:
            for i in range(self.height):
                for j in range(self.width):
                    self.grid[i][j].findPollutionFlux()
            for i in range(self.height):
                for j in range(self.width):
                    self.grid[i][j].doPollutionDiffusion()

    def doTimestep(self, timestep):
        self.timestep = timestep
        self.updateSeasons()
        self.updatePollution()
        self.doCellUpdate()

    def findCardinalCellRanges(self, maxDeltaX, maxDeltaY, cellCoords):
        numCells = self.width * self.height
        for i in range(numCells):
            x1, y1 = cellCoords[i]
            for j in range(x1 + 1, x1 + maxDeltaX + 1):
                deltaX = self.findWraparoundDistance(j - x1, self.width)
                self.grid[x1][y1].ranges[deltaX][self.grid[j % self.width][y1]] = deltaX
                self.grid[j % self.width][y1].ranges[deltaX][self.grid[x1][y1]] = deltaX
            for j in range(y1 + 1, y1 + maxDeltaY + 1):
                deltaY = self.findWraparoundDistance(j - y1, self.height)
                self.grid[x1][y1].ranges[deltaY][self.grid[x1][j % self.height]] = deltaY
                self.grid[x1][j % self.height].ranges[deltaY][self.grid[x1][y1]] = deltaY

    def findCell(self, x, y):
        return self.grid[x][y]

    def findCellNeighbors(self):
        for i in range(self.width):
            for j in range(self.height):
                self.grid[i][j].findNeighbors(self.neighborhoodMode)

    def findCellRanges(self):
        config = self.sugarscape.configuration
        # Determine maximum range to memoize based on the maximum possible agent vision and movement from bonuses
        maxVision = config["startingDiseases"] * max(config["diseaseVisionPenalty"][1], 0) + config["agentVision"][1]
        maxMovement = config["startingDiseases"] * max(config["diseaseMovementPenalty"][1], 0) + config["agentMovement"][1]
        maxAgentRange = max(maxVision, maxMovement)
        maxDeltaX = min(maxAgentRange, self.width // 2)
        maxDeltaY = min(maxAgentRange, self.height // 2)
        maxRadialDelta = min(maxAgentRange, math.floor(math.sqrt((self.width // 2) ** 2 + (self.height // 2) ** 2)))
        if self.wraparound == False:
            maxDeltaX = min(maxAgentRange, self.width - 1)
            maxDeltaY = min(maxAgentRange, self.height - 1)
            maxRadialDelta = min(maxAgentRange, math.floor(math.sqrt((self.width - 1) ** 2 + (self.height - 1) ** 2)))
        maxCardinalDelta = max(maxDeltaX, maxDeltaY)
        self.maxCellDistance = maxRadialDelta if config["agentVisionMode"] == "radial" and config["agentMovementMode"] == "radial" else maxCardinalDelta
        cellCoords = [(x, y) for x in range(self.width) for y in range(self.height)]
        # Initialize ranges with all possible values
        for x, y in cellCoords:
            self.grid[x][y].ranges = {gridRange: {} for gridRange in range(1, self.maxCellDistance + 1)}

        if config["agentVisionMode"] == "radial" and config["agentMovementMode"] == "radial":
            self.findRadialCellRanges(maxDeltaX, maxDeltaY, maxRadialDelta, cellCoords)
        else:
            self.findCardinalCellRanges(maxDeltaX, maxDeltaY, cellCoords)

    def findRadialCellRanges(self, maxDeltaX, maxDeltaY, maxDeltaRadius, cellCoords):
        distanceTable = self.createDistanceTable(maxDeltaX, maxDeltaY)
        numCells = self.width * self.height
        for i in range(numCells):
            x1, y1 = cellCoords[i]
            for j in range(i + 1, numCells):
                x2, y2 = cellCoords[j]
                deltaX = self.findWraparoundDistance(x1 - x2, self.width)
                deltaY = self.findWraparoundDistance(y1 - y2, self.height)
                if deltaX > maxDeltaX or deltaY > maxDeltaY:
                    continue
                deltaPair = tuple(sorted((deltaX, deltaY)))
                distance = distanceTable[deltaPair]
                gridRange = math.floor(distance)
                if gridRange <= maxDeltaRadius:
                    self.grid[x1][y1].ranges[gridRange][self.grid[x2][y2]] = distance
                    self.grid[x2][y2].ranges[gridRange][self.grid[x1][y1]] = distance

    def findWraparoundDistance(self, delta, border):
        delta = abs(delta)
        if self.sugarscape.configuration["environmentWraparound"] == True and delta > border / 2:
            delta = border - delta
        return delta

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
        if self.pollutionDiffusionStart <= self.timestep <= self.pollutionDiffusionEnd and self.pollutionDiffusionDelay > 0:
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
