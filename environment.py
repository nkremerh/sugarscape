import math
import random

class Environment:
    # Assumption: grid is always indexed by [height][width]
    def __init__(self, height, width, sugarscape, globalMaxSugar=0, sugarRegrowRate=0, seasonInterval=0, seasonalGrowbackDelay=0, consumptionPollutionRate=0, productionPollutionRate=0, pollutionDiffusionDelay=0):
        self.__width = width
        self.__height = height
        self.__globalMaxSugar = globalMaxSugar
        self.__sugarRegrowRate = sugarRegrowRate
        self.__sugarscape = sugarscape
        self.__seasonInterval = seasonInterval
        self.__seasonalGrowbackDelay = seasonalGrowbackDelay
        self.__seasonNorth = "summer" if seasonInterval > 0 else None
        self.__seasonSouth = "winter" if seasonInterval > 0 else None
        self.__equator = math.ceil(self.__height / 2)
        self.__seasonalGrowbackCountdown = seasonalGrowbackDelay
        self.__pollutionDiffusionDelay = pollutionDiffusionDelay
        self.__pollutionDiffusionCountdown = pollutionDiffusionDelay
        self.__consumptionPollutionRate = consumptionPollutionRate
        self.__productionPollutionRate = productionPollutionRate
        # Populate grid with NoneType objects
        self.__grid = [[None for j in range(width)]for i in range(height)]

    def doCellUpdate(self):
        timestep = self.__sugarscape.getTimestep()
        for i in range(self.__height):
            for j in range(self.__width):
                cellCurrSugar = self.__grid[i][j].getCurrSugar()
                cellMaxSugar = self.__grid[i][j].getMaxSugar()
                cellSeason = self.__grid[i][j].getSeason()
                if self.__seasonInterval > 0:
                    if timestep % self.__seasonInterval == 0:
                        self.__grid[i][j].updateSeason()
                    if (cellSeason == "summer") or (cellSeason == "winter" and self.__seasonalGrowbackCountdown == self.__seasonalGrowbackDelay):
                        self.__grid[i][j].setCurrSugar(min(cellCurrSugar + self.__sugarRegrowRate, cellMaxSugar))
                else:
                    self.__grid[i][j].setCurrSugar(min(cellCurrSugar + self.__sugarRegrowRate, cellMaxSugar))
                if self.__pollutionDiffusionDelay > 0 and self.__pollutionDiffusionCountdown == self.__pollutionDiffusionDelay:
                    self.__grid[i][j].doPollutionDiffusion()

    def doTimestep(self):
        self.updateSeasons()
        self.updatePollution()
        self.doCellUpdate()
        rows = list(range(self.__height))
        columns = list(range(self.__width))
        cells = [(x, y) for x in rows for y in columns]
        random.seed(self.__sugarscape.getSeed())
        random.shuffle(cells)
        for coords in cells:
            if self.__grid[coords[0]][coords[1]] != None:
                self.__grid[coords[0]][coords[1]].doTimestep()

    def getCell(self, x, y):
        return self.__grid[x][y]

    def getConsumptionPollutionRate(self):
        return self.__consumptionPollutionRate

    def getEquator(self):
        return self.__equator

    def getGlobalMaxSugar(self):
        return self.__globalMaxSugar

    def getGrid(self):
        return self.__grid

    def getHeight(self):
        return self.__height

    def getPollutionDiffusionCountdown(self):
        return self.__pollutionDiffusionCountdown

    def getPollutionDiffusionDelay(self):
        return self.__pollutionDiffusionDelay

    def getProductionPollutionRate(self):
        return self.__productionPollutionRate

    def getSeasonalGrowbackCountdown(self):
        return self.__seasonalGrowbackCountdown

    def getSeasonInterval(self):
        return self.__seasonInterval

    def getSeasonNorth(self):
        return self.__seasonNorth

    def getSeasonSouth(self):
        return self.__seasonSouth

    def getSugarscape(self):
        return self.__sugarscape

    def getWidth(self):
        return self.__width

    def setCell(self, cell, x, y):
        self.__grid[x][y] = cell

    def setCellNeighbors(self):
        for i in range(self.__height):
            for j in range(self.__width):
                self.__grid[i][j].setNeighbors()

    def setConsumptionPollutionRate(self, consumptionPollutionRate):
        self.__consumptionPollutionRate = consumptionPollutionRate

    def setEquator(self, equator):
        self.__equator = equator

    def setGlobalMaxSugar(self, globalMaxSugar):
        self.__globalMaxSugar = globalMaxSugar

    def setGrid(self, grid):
        self.__grid = grid

    def setHeight(self, height):
        self.__height = height

    def setPollutionDiffusionCountdown(self, pollutionDiffusionCountdown):
        self.__pollutionDiffusionCountdown = pollutionDiffusionCountdown

    def setPollutionDiffusionDelay(self, pollutionDiffusionDelay):
        self.__pollutionDiffusionDelay = pollutionDiffisionDelay

    def setProductionPollutionRate(self, productionPollutionRate):
        self.__productionPollutionRate = productionPollutionRate

    def setSeasonalGrowbackCountdown(self, seasonalGrowbackCountdown):
        self.__seasonalGrowbackCountdown = seasonalGrowbackCountdown

    def setSeasonInterval(self, seasonInterval):
        self.__seasonInterval = seasonInterval

    def setSeasonNorth(self, seasonNorth):
        self.__seasonNorth = seasonNorth

    def setSeasonSouth(self, seasonSouth):
        self.__seasonSouth = seasonSouth

    def setSugarscape(self, sugarscape):
        self.__sugarscape = sugarscape

    def setWidth(self, width):
        self.__width = width

    def updatePollution(self):
        timestep = self.__sugarscape.getTimestep()
        if self.__pollutionDiffusionDelay > 0:
            self.__pollutionDiffusionCountdown -= 1
            # Pollution diffusion delay over
            if self.__pollutionDiffusionCountdown == 0:
                self.__pollutionDiffusionCountdown = self.__pollutionDiffusionDelay

    def updateSeasons(self):
        timestep = self.__sugarscape.getTimestep()
        if self.__seasonInterval > 0:
            self.__seasonalGrowbackCountdown -= 1
            # Seasonal growback delay over
            if self.__seasonalGrowbackCountdown == 0:
                self.__seasonalGrowbackCountdown = self.__seasonalGrowbackDelay
            if timestep % self.__seasonInterval == 0:
                if self.__seasonNorth == "summer":
                    self.__seasonNorth = "winter"
                    self.__seasonSouth = "summer"
                else:
                    self.__seasonNorth = "summer"
                    self.__seasonSouth = "winter"

    def unsetCell(self, x, y):
        self.__grid[x][y] = None
  
    def __str__(self):
        string = ""
        for i in range(0, self.__height):
            for j in range(0, self.__width):
                cell = self.__grid[i][j]
                if cell == None:
                    cell = '_'
                else:
                    cell = str(cell)
                string = string + ' '+ cell
            string = string + '\n'
        return string
