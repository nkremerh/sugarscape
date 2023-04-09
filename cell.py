'''
Class: Cell
Purpose: Store resources (sugar, spice), pollution, an Agent object, an Environment, its neighboring cells
Data Members: X and Y coordinates, environment, agent, maxSugar, maxSpice, currSugar, currSpice, currPollution, growbackRate, neigbors array of Cell objects
Methods: constructor, getters and setters, setEnvironment, getEnvironment, setAgent, getAgent, unsetAgent, growResources, diffusePollution
'''

class Cell:
    def __init__(self, x, y, environment, maxSugar = 0, maxSpice = 0, growbackRate = 0):
        self.__x = x
        self.__y = y
        self.__environment = environment
        self.__maxSugar = maxSugar
        self.__currSugar = maxSugar
        self.__maxSpice = maxSpice
        self.__currSpice = maxSpice
        self.__currPollution = 0
        self.__agent = None
        self.__neighbors = []

    def getEnvironment(self):
        return self.__environment

    def getMaxSugar(self):
        return self.__maxSugar

    def getCurrSugar(self):
        return self.__currSugar

    def getMaxSpice(self):
        return self.__maxSpice

    def getCurrSpice(self):
        return self.__currSpice

    def getCurrPollution(self):
        return self.__currPollution

    def getAgent(self):
        return self.__agent

    def getX(self):
        return self.__x

    def getY(self):
        return self.__y

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
        southNeighbor = self.__environment.getCell(x, southIndex)
        return southNeighbor

    def getEastNeighbor(self):
        eastWrapAround = self.__environment.getWidth()
        eastIndex = self.__x + 1
        if eastIndex >= eastWrapAround:
            eastIndex = 0
        easthNeighbor = self.__environment.getCell(eastIndex, self.__y)
        return eastNeighbor

    def getWestNeighbor(self):
        westWrapAround = self.__environment.getHeight()
        westIndex = self.__y - 1
        if westIndex < westWrapAround:
            westIndex = self.__environment.getWidth() - 1
        westNeighbor = self.__environment.getCell(westIndex, y)
        return westNeighbor

    def setNeighbors(self):
        self.__neighbors.append(self.getNorthNeighbor())
        self.__neighbors.append(self.getSouthNeighbor())
        self.__neighbors.append(self.getEastNeighbor())
        self.__neighbors.append(self.getWestNeighbor())

    def setX(self, x):
        self.__x = x

    def setY(self, y):
        self.__y = y

    def setEnvironment(self, environment):
        self.__environment = environment

    def setMaxSugar(self, maxSugar):
        self.__maxSugar = maxSugar

    def setCurrSugar(self, currSugar):
        self.__currSugar = currSugar

    def setMaxSpice(self, maxSpice):
        self.__maxSpice = maxSpice

    def setCurrSpice(self, currSpice):
        self.__currSpice = currSpice

    def setAgent(self, agent):
        self.__agent = agent

    def unsetAgent(self):
        self.setAgent(None)

    def resetSugar(self):
        currSugar = self.__currSugar
        self.setCurrSugar(0)
        return currSugar

    def doTimestep(self):
        if self.__agent != None:
            self.__agent.doTimestep()

    def __str__(self):
        string = ""
        if self.getAgent() != None:
            string = 'A'
        #string = "{0}:{1}:{2}".format(string, self.__currSugar, self.__currSpice)
        else:
            string = str(self.__currSugar)
        #string = "{0},{1}".format(self.__x, self.__y)
        return string
