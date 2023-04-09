'''
Class: Agent
Purpose: Provides autonomous agent behavior for simulation, stores cell
Data Members: vision, metabolism, sugar, spice, maxAge, currAge, tags, children, parents, cell, alive
'''
class Agent:
    def __init__(self, cell, metabolism = 0, vision = 0, sugar = 0):
        self.__cell = cell
        self.__metabolism = metabolism
        self.__vision = vision
        self.__sugar = 0
        self.__alive = True

    def getAlive(self):
        return self.__alive

    def getCell(self):
        return self.__cell

    def getEnvironment(self):
        return self.__cell.getEnvironment()

    def getMetabolism(self):
        return self.__metabolism

    def getVision(self):
        return self.__vision

    def getSugar(self):
        return self.__sugar

    def setCell(self, cell):
        if(self.__cell != None):
            self.unsetCell()
        self.__cell = cell

    def unsetCell(self):
        self.__cell.unsetAgent()
        self.__cell = None

    def setMetabolism(self, metabolism):
        self.__metabolism = metabolism

    def setVision(self, vision):
        self.__vision = vision

    def setAlive(self, alive):
        self.__alive = alive

    def isAlive(self):
        return self.getAlive()

    def getResourcesAtCell(self):
        self.__sugar = self.__sugar + self.__cell.resetSugar()

    def doMetabolism(self):
        self.__sugar = self.__sugar - self.__metabolism
        if self.__sugar < 1:
            self.setAlive(False)
            self.unsetCell()

    def doTimestep(self):
        # TODO: Determine if sugar/spice eaten before moving (requires initial endowment of sugar/spice)
        self.getResourcesAtCell()
        self.doMetabolism()

    def __Str__(self):
        return "[Agent Object with {0} sugar]".format(self.getSugarHold())
