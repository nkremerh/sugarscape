#! /usr/bin/python

import agent
import cell
import environment

import math
import random

'''
Class: Sugarscape
Purpose: Container class for simulation storing environment, list of extant agents, sets options from command line/config file
'''
class Sugarscape:
    def __init__(self, gridHeight, gridWidth, startingAgents, globalMaxSugar, options):
        self.__environment = environment.Environment(gridHeight, gridWidth)
        self.configureEnvironment(globalMaxSugar)
        self.__agents = []
        self.configureAgents(startingAgents)

    def addSugarPeak(self, startX, startY, radius, maxCapacity):
        height = self.__environment.getHeight()
        width = self.__environment.getWidth()
        radialDispersion = math.sqrt(max(startX, width - startX)**2 + max(startY, height - startY)**2) * (radius / width)
        for i in range(height):
            for j in range(width):
                if self.__environment.getCell(i, j) == None:
                    self.__environment.setCell(cell.Cell(i, j, self.__environment), i, j)
                currDispersion = 1 + maxCapacity * (1 - math.sqrt((startX - i)**2 +  (startY - j)**2) / radialDispersion)
                cellMaxCapacity = min(currDispersion, maxCapacity)
                cellMaxCapacity = math.ceil(cellMaxCapacity)
                if cellMaxCapacity > self.__environment.getCell(i, j).getMaxSugar():
                    self.__environment.getCell(i, j).setMaxSugar(cellMaxCapacity)
                    self.__environment.getCell(i, j).setCurrSugar(cellMaxCapacity)

    def configureAgents(self, startingAgents):
        if self.__environment == None:
            return
        for i in range(startingAgents):
            randX = random.randrange(self.__environment.getHeight())
            randY = random.randrange(self.__environment.getWidth())
            while self.__environment.getCell(randX, randY).getAgent() != None:
                randX = random.randrange(self.__environment.getHeight())
                randY = random.randrange(self.__environment.getWidth())
            c = self.__environment.getCell(randX, randY)
            a = agent.Agent(c, 1, 2, 3)
            c.setAgent(a)
            self.__agents.append(a)

    def configureEnvironment(self, maxCapacity):
        height = self.__environment.getHeight()
        width = self.__environment.getWidth()
        startX1 = math.ceil(height * 0.7)
        startX2 = math.ceil(height * 0.3)
        startY1 = math.ceil(width * 0.3)
        startY2 = math.ceil(width * 0.7)
        radius = math.ceil(math.sqrt(1.25 * (height + width)))
        self.addSugarPeak(startX1, startY1, radius, maxCapacity)
        self.addSugarPeak(startX2, startY2, radius, maxCapacity)

    def doTimestep(self):
        self.__environment.doTimestep()
        for a in self.__agents:
            if a.isAlive() == False:
                self.__agents.remove(a)

    def __str__(self):
        string = "{0}Living Agents: {1}".format(str(self.__environment), len(self.__agents))
        return string

if __name__ == "__main__":
    S = Sugarscape(50, 50, 100, 4, None)
    print(str(S))
    for i in range(5):
        S.doTimestep()
        print(str(S))
    exit(0)
