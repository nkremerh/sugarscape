import math
import random

class Environment:
    # Assumption: grid is always indexed by [height][width]
    def __init__(self, height, width, sugarscape, configuration):
        self.__width = width
        self.__height = height
        self.__globalMaxSugar = configuration["globalMaxSugar"]
        self.__sugarRegrowRate = configuration["sugarRegrowRate"]
        self.__globalMaxSpice = configuration["globalMaxSpice"]
        self.__spiceRegrowRate = configuration["spiceRegrowRate"]
        self.__sugarscape = sugarscape
        self.__timestep = 0
        self.__seed = configuration["sugarscapeSeed"]
        self.__seasonInterval = configuration["seasonInterval"]
        self.__seasonalGrowbackDelay = configuration["seasonalGrowbackDelay"]
        self.__seasonNorth = "summer" if configuration["seasonInterval"] > 0 else None
        self.__seasonSouth = "winter" if configuration["seasonInterval"] > 0 else None
        self.__seasonalGrowbackCountdown = configuration["seasonalGrowbackDelay"]
        self.__pollutionDiffusionDelay = configuration["pollutionDiffusionDelay"]
        self.__pollutionDiffusionCountdown = configuration["pollutionDiffusionDelay"]
        self.__sugarConsumptionPollutionRate = configuration["sugarConsumptionPollutionRate"]
        self.__spiceConsumptionPollutionRate = configuration["spiceConsumptionPollutionRate"]
        self.__sugarProductionPollutionRate = configuration["sugarProductionPollutionRate"]
        self.__spiceProductionPollutionRate = configuration["spiceProductionPollutionRate"]
        self.__maxCombatLoot = configuration["maxCombatLoot"]
        self.__equator = math.ceil(self.__height / 2)
        # Populate grid with NoneType objects
        self.__grid = [[None for j in range(width)]for i in range(height)]

    def doCellUpdate(self):
        for i in range(self.__height):
            for j in range(self.__width):
                cellCurrSugar = self.__grid[i][j].getCurrSugar()
                cellCurrSpice = self.__grid[i][j].getCurrSpice()
                cellMaxSugar = self.__grid[i][j].getMaxSugar()
                cellMaxSpice = self.__grid[i][j].getMaxSpice()
                cellSeason = self.__grid[i][j].getSeason()
                if self.__seasonInterval > 0:
                    if self.__timestep % self.__seasonInterval == 0:
                        self.__grid[i][j].updateSeason()
                    if (cellSeason == "summer") or (cellSeason == "winter" and self.__seasonalGrowbackCountdown == self.__seasonalGrowbackDelay):
                        self.__grid[i][j].setCurrSugar(min(cellCurrSugar + self.__sugarRegrowRate, cellMaxSugar))
                        self.__grid[i][j].setCurrSpice(min(cellCurrSpice + self.__spiceRegrowRate, cellMaxSpice))
                else:
                    self.__grid[i][j].setCurrSugar(min(cellCurrSugar + self.__sugarRegrowRate, cellMaxSugar))
                    self.__grid[i][j].setCurrSpice(min(cellCurrSpice + self.__spiceRegrowRate, cellMaxSpice))
                if self.__pollutionDiffusionDelay > 0 and self.__pollutionDiffusionCountdown == self.__pollutionDiffusionDelay:
                    self.__grid[i][j].doPollutionDiffusion()

    def doTimestep(self, timestep):
        self.__timestep = timestep
        self.updateSeasons()
        self.updatePollution()
        self.doCellUpdate()

    def getCell(self, x, y):
        return self.__grid[x][y]

    def getEquator(self):
        return self.__equator

    def getGlobalMaxSpice(self):
        return self.__globalMaxSpice

    def getGlobalMaxSugar(self):
        return self.__globalMaxSugar

    def getGrid(self):
        return self.__grid

    def getHeight(self):
        return self.__height

    def getMaxCombatLoot(self):
        return self.__maxCombatLoot

    def getPollutionDiffusionCountdown(self):
        return self.__pollutionDiffusionCountdown

    def getPollutionDiffusionDelay(self):
        return self.__pollutionDiffusionDelay

    def getSpiceProductionPollutionRate(self):
        return self.__spiceProductionPollutionRate

    def getSugarProductionPollutionRate(self):
        return self.__sugarProductionPollutionRate

    def getSeasonalGrowbackCountdown(self):
        return self.__seasonalGrowbackCountdown

    def getSeasonInterval(self):
        return self.__seasonInterval

    def getSeasonNorth(self):
        return self.__seasonNorth

    def getSeasonSouth(self):
        return self.__seasonSouth

    def getSpiceConsumptionPollutionRate(self):
        return self.__spiceConsumptionPollutionRate

    def getSugarConsumptionPollutionRate(self):
        return self.__sugarConsumptionPollutionRate

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

    def setEquator(self, equator):
        self.__equator = equator

    def setGlobalMaxSpice(self, globalMaxSpice):
        self.__globalMaxSpice = globalMaxSpice

    def setGlobalMaxSugar(self, globalMaxSugar):
        self.__globalMaxSugar = globalMaxSugar

    def setGrid(self, grid):
        self.__grid = grid

    def setHeight(self, height):
        self.__height = height

    def setMaxCombatLoot(self, maxCombatLoot):
        self.__maxCombatLoot = maxCombatLoot

    def setPollutionDiffusionCountdown(self, pollutionDiffusionCountdown):
        self.__pollutionDiffusionCountdown = pollutionDiffusionCountdown

    def setPollutionDiffusionDelay(self, pollutionDiffusionDelay):
        self.__pollutionDiffusionDelay = pollutionDiffisionDelay

    def setSeasonalGrowbackCountdown(self, seasonalGrowbackCountdown):
        self.__seasonalGrowbackCountdown = seasonalGrowbackCountdown

    def setSeasonInterval(self, seasonInterval):
        self.__seasonInterval = seasonInterval

    def setSeasonNorth(self, seasonNorth):
        self.__seasonNorth = seasonNorth

    def setSeasonSouth(self, seasonSouth):
        self.__seasonSouth = seasonSouth

    def setSpiceConsumptionPollutionRate(self, spiceConsumptionPollutionRate):
        self.__spiceConsumptionPollutionRate = spiceConsumptionPollutionRate

    def setSugarConsumptionPollutionRate(self, sugarConsumptionPollutionRate):
        self.__sugarConsumptionPollutionRate = sugarConsumptionPollutionRate

    def setSpiceProductionPollutionRate(self, spiceProductionPollutionRate):
        self.__spiceProductionPollutionRate = spiceProductionPollutionRate
 
    def setSugarProductionPollutionRate(self, sugarProductionPollutionRate):
        self.__sugarProductionPollutionRate = sugarProductionPollutionRate

    def setSugarscape(self, sugarscape):
        self.__sugarscape = sugarscape

    def setWidth(self, width):
        self.__width = width

    def updatePollution(self):
        if self.__pollutionDiffusionDelay > 0:
            self.__pollutionDiffusionCountdown -= 1
            # Pollution diffusion delay over
            if self.__pollutionDiffusionCountdown == 0:
                self.__pollutionDiffusionCountdown = self.__pollutionDiffusionDelay

    def updateSeasons(self):
        if self.__seasonInterval > 0:
            self.__seasonalGrowbackCountdown -= 1
            # Seasonal growback delay over
            if self.__seasonalGrowbackCountdown == 0:
                self.__seasonalGrowbackCountdown = self.__seasonalGrowbackDelay
            if self.__timestep % self.__seasonInterval == 0:
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
