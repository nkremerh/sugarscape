#! /usr/bin/python

import agent
import cell
import environment
import gui

import math
import random
import time

class Sugarscape:
    def __init__(self, environmentOptions, agentOptions):
        self.__environment = environment.Environment(environmentOptions["height"], environmentOptions["width"], environmentOptions["maxSugar"], environmentOptions["sugarRegrowRate"])
        self.__environmentHeight = environmentOptions["height"]
        self.__environmentWidth = environmentOptions["width"]
        self.configureEnvironment(environmentOptions["maxSugar"])
        self.__agents = []
        self.configureAgents(agentOptions["initialAgents"], agentOptions["maxVision"], agentOptions["maxMetabolism"], agentOptions["maxInitialWealth"])
        self.__gui = gui.GUI(self)
        self.__run = False # Simulation start flag
        self.__end = False # Simulation end flag
        self.__timestep = 0

    # TODO: Make more consistent with book, dispersion more tightly concentrated than in book (ref: pg. 22)
    def addSugarPeak(self, startX, startY, radius, maxCapacity):
        height = self.__environment.getHeight()
        width = self.__environment.getWidth()
        radialDispersion = math.sqrt(max(startX, width - startX)**2 + max(startY, height - startY)**2) * (radius / width)
        for i in range(height):
            for j in range(width):
                if self.__environment.getCell(i, j) == None:
                    self.__environment.setCell(cell.Cell(i, j, self.__environment), i, j)
                euclideanDistanceToStart = math.sqrt((startX - i)**2 + (startY - j)**2)
                currDispersion = 1 + maxCapacity * (1 - euclideanDistanceToStart / radialDispersion)
                cellMaxCapacity = min(currDispersion, maxCapacity)
                cellMaxCapacity = math.ceil(cellMaxCapacity)
                if cellMaxCapacity > self.__environment.getCell(i, j).getMaxSugar():
                    self.__environment.getCell(i, j).setMaxSugar(cellMaxCapacity)
                    self.__environment.getCell(i, j).setCurrSugar(cellMaxCapacity)
 
    def configureAgents(self, initialAgents, maxMetabolism, maxVision, maxInitialWealth):
        if self.__environment == None:
            return
        totalCells = self.__environmentHeight * self.__environmentWidth
        if initialAgents > totalCells:
            print("Could not allocate {0} agents. Allocating maximum of {1}.".format(initialAgents, totalCells))
            initialAgents = totalCells
        agentEndowments = self.randomizeAgentEndowments(initialAgents, maxVision, maxMetabolism, maxInitialWealth)
        for i in range(initialAgents):
            randX = random.randrange(self.__environment.getHeight())
            randY = random.randrange(self.__environment.getWidth())
            while self.__environment.getCell(randX, randY).getAgent() != None:
                randX = random.randrange(self.__environment.getHeight())
                randY = random.randrange(self.__environment.getWidth())
            c = self.__environment.getCell(randX, randY)
            currMetabolism = agentEndowments[i][0]
            currVision = agentEndowments[i][1]
            currWealth = agentEndowments[i][2]
            a = agent.Agent(c, currMetabolism, currVision, currWealth)
            c.setAgent(a)
            self.__agents.append(a)

    def configureEnvironment(self, maxCapacity):
        height = self.__environment.getHeight()
        width = self.__environment.getWidth()
        startX1 = math.ceil(height * 0.7)
        startX2 = math.ceil(height * 0.3)
        startY1 = math.ceil(width * 0.3)
        startY2 = math.ceil(width * 0.7)
        radius = math.ceil(math.sqrt(2 * (height + width)))
        self.addSugarPeak(startX1, startY1, radius, maxCapacity)
        self.addSugarPeak(startX2, startY2, radius, maxCapacity)

    def doTimestep(self):
        if self.__end == True:
            self.endSimulation()
        self.__environment.doTimestep()
        for a in self.__agents:
            if a.isAlive() == False:
                self.__agents.remove(a)
        self.__gui.doTimestep()
        #print("Timestep: {0}".format(self.__timestep))
        self.__timestep += 1

    def endSimulation(self):
        print(str(self))
        exit(0)

    def getAgents(self):
        return self.__agents

    def getEnd(self):
        return self.__end

    def getEnvironment(self):
        return self.__environment
 
    def getEnvironmentHeight(self):
        return self.__environmentHeight

    def getEnvironmentWidth(self):
        return self.__environmentWidth

    def getGUI(self):
        return self.__gui

    def getRun(self):
        return self.__run
  
    def getTimestep(self):
        return self.__timestep

    def pauseSimulation(self):
        while self.__run == False:
            if self.__end == True:
                self.endSimulation()
            self.__gui.getWindow().update()

    def randomizeAgentEndowments(self, initialAgents, maxMetabolism, maxVision, maxInitialWealth):
        endowments = []
        metabolisms = []
        visions = []
        initialWealths = []
        minMetabolism = min(1, maxMetabolism) # Accept 0 case
        minVision = min(1, maxVision) # Accept 0 case
        minWealth = min(1, maxInitialWealth) # Accept 0 case
        currMetabolism = 1
        currVision = 1
        currWealth = 1
        for i in range(initialAgents):
            metabolisms.append(currMetabolism)
            visions.append(currVision)
            initialWealths.append(currWealth)
            currMetabolism += 1
            currVision += 1
            currWealth += 1
            if currMetabolism > maxMetabolism:
                currMetabolism = minMetabolism
            if currVision > maxVision:
                currVision = minVision
            if currWealth > maxInitialWealth:
                currWealth = minWealth
        random.shuffle(metabolisms)
        random.shuffle(visions)
        random.shuffle(initialWealths)
        for i in range(initialAgents):
            endowments.append([metabolisms[i], visions[i], initialWealths[i]])
        return endowments

    def runSimulation(self, timesteps=5):
        self.pauseSimulation() # Simulation begins paused until start button in GUI pressed
        t = 0
        timesteps = timesteps - self.__timestep
        while t < timesteps and self.__end == False and len(self.__agents) != 0:
            self.doTimestep()
            t += 1
            if self.__run == False:
                self.pauseSimulation()

    def setAgents(self, agents):
        self.__agents = agents

    def setEnd(self):
        self.__end = not self.__end

    def setEnvironment(self, environment):
        self.__environment = environment

    def setEnvironmentHeight(self, environmentHeight):
        self.__environmentHeight = environmentHeight

    def setEnvironmentWidth(self, environmentWidth):
        self.__environmentWidth = environmentWidth

    def setGUI(self, gui):
        self.__gui = gui

    def setTimestep(self, timestep):
        self.__timestep = timestep
  
    def setRun(self):
        self.__run = not self.__run
  
    def __str__(self):
        string = "{0}Timestep: {1}\nLiving Agents: {2}".format(str(self.__environment), self.__timestep, len(self.__agents))
        return string

if __name__ == "__main__":
    agentOptions = {"maxVision": 6, "maxMetabolism": 4, "maxInitialWealth": 5, "initialAgents": 250}
    environmentOptions = {"height": 50, "width": 50, "maxSugar": 4, "sugarRegrowRate": 1}
    S = Sugarscape(environmentOptions, agentOptions)
    print(str(S))
    S.runSimulation(10000)
    print(str(S))
    exit(0)
