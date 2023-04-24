class Cell:
    def __init__(self, x, y, environment, maxSugar=0, maxSpice=0, growbackRate=0):
        self.__x = x
        self.__y = y
        self.__environment = environment
        self.__maxSugar = maxSugar
        self.__currSugar = maxSugar
        self.__maxSpice = maxSpice
        self.__currSpice = maxSpice
        self.__currPollution = 0
        self.__agent = None
        self.__hemisphere = "north" if self.__x >= self.__environment.getEquator() else "south"
        self.__season = None
        self.__neighbors = []
    
    def doTimestep(self):
        if self.__agent != None:
            self.__agent.doTimestep()

    def getAgent(self):
        return self.__agent

    def getEnvironment(self):
        return self.__environment

    def getCurrPollution(self):
        return self.__currPollution

    def getCurrSpice(self):
        return self.__currSpice
    
    def getCurrSugar(self):
        return self.__currSugar

    def getEastNeighbor(self):
        eastWrapAround = self.__environment.getWidth()
        eastIndex = self.__x + 1
        if eastIndex >= eastWrapAround:
            eastIndex = 0
        eastNeighbor = self.__environment.getCell(eastIndex, self.__y)
        return eastNeighbor

    def getSeason(self):
        return self.__season

    def getMaxSpice(self):
        return self.__maxSpice

    def getMaxSugar(self):
        return self.__maxSugar 

    def getNeighbors(self):
        return self.__neighbors

    def getNorthNeighbor(self):
        northWrapAround = self.__environment.getHeight()
        northIndex = self.__y + 1
        if northIndex >= northWrapAround:
            northIndex = 0
        northNeighbor = self.__environment.getCell(self.__x, northIndex)
        return northNeighbor

    def getSouthNeighbor(self):
        southWrapAround = 0
        southIndex = self.__y - 1
        if southIndex < southWrapAround:
            southIndex = self.__environment.getHeight() - 1
        southNeighbor = self.__environment.getCell(self.__x, southIndex)
        return southNeighbor

    def getWestNeighbor(self):
        westWrapAround = 0
        westIndex = self.__x - 1
        if westIndex < westWrapAround:
            westIndex = self.__environment.getWidth() - 1
        westNeighbor = self.__environment.getCell(westIndex, self.__y)
        return westNeighbor

    def getX(self):
        return self.__x

    def getY(self):
        return self.__y

    def isOccupied(self):
        return self.__agent != None

    def resetSugar(self):
        currSugar = self.__currSugar
        self.setCurrSugar(0)
        return currSugar

    def setAgent(self, agent):
        self.__agent = agent

    def setCurrSpice(self, currSpice):
        self.__currSpice = currSpice

    def setCurrSugar(self, currSugar):
        self.__currSugar = currSugar

    def setEnvironment(self, environment):
        self.__environment = environment

    def setMaxSpice(self, maxSpice):
        self.__maxSpice = maxSpice

    def setMaxSugar(self, maxSugar):
        self.__maxSugar = maxSugar

    def setNeighbors(self):
        if(len(self.__neighbors) < 4):
            self.__neighbors = []
            self.__neighbors.append(self.getNorthNeighbor())
            self.__neighbors.append(self.getSouthNeighbor())
            self.__neighbors.append(self.getEastNeighbor())
            self.__neighbors.append(self.getWestNeighbor())

    def setSeason(self, season):
        self.__season = season

    def setX(self, x):
        self.__x = x

    def setY(self, y):
        self.__y = y

    def updateSeason(self):
        if self.__season == "summer":
            self.__season = "winter"
        else:
            self.__season = "summer"

    def unsetAgent(self):
        self.setAgent(None)
 
    def __str__(self):
        string = ""
        if self.getAgent() != None:
            string = 'A'
        else:
            string = str(self.__currSugar)
        return string
