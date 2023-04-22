import math
import random

class Environment:
    # Assumption: grid is always indexed by [height][width]
    def __init__(self, height, width, globalMaxSugar=0, sugarRegrowRate=0):
        self.__width = width
        self.__height = height
        self.__globalMaxSugar = globalMaxSugar
        self.__sugarRegrowRate = sugarRegrowRate
        # Populate grid with NoneType objects
        self.__grid = [[None for j in range(width)]for i in range(height)]

    def doCellUpdate(self):
        for i in range(self.__height):
            for j in range(self.__width):
                cellCurrSugar = self.__grid[i][j].getCurrSugar()
                cellMaxSugar = self.__grid[i][j].getMaxSugar()
                self.__grid[i][j].setCurrSugar(min(cellCurrSugar + self.__sugarRegrowRate, cellMaxSugar))

    def doTimestep(self):
        self.doCellUpdate()
        randomRows = list(range(self.__height))
        randomColumns = list(range(self.__width))
        random.shuffle(randomRows)
        random.shuffle(randomColumns)
        for i in randomRows:
            for j in randomColumns:
                if self.__grid[i][j] != None:
                    self.__grid[i][j].doTimestep()

    def getCell(self, x, y):
        return self.__grid[x][y]

    def getGlobalMaxSugar(self):
        return self.__globalMaxSugar

    def getGrid(self):
        return self.__grid

    def getHeight(self):
        return self.__height

    def getWidth(self):
        return self.__width

    def setCell(self, cell, x, y):
        self.__grid[x][y] = cell

    def setGlobalMaxSugar(self, globalMaxSugar):
        self.__globalMaxSugar = globalMaxSugar

    def setGrid(self, grid):
        self.__grid = grid

    def setHeight(self, height):
        self.__height = height

    def setWidth(self, width):
        self.__width = width
 
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
