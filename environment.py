'''
Class: Environment
Purpose: Store toroid grid of Sugarscape cells
Data Members: grid width, grid height
Methods: constructor, getters and setters, add/remove Cell object to/from grid, get/set Cell object at grid location
Assumptions: grid is always indexed by [height][width]
'''
import random

class Environment:
    def __init__(self, height, width, globalMaxSugar=0):
        self.__width = width
        self.__height = height
        self.__globalMaxSugar = globalMaxSugar
        # Populate grid with NoneType objects
        self.__grid = [[None for j in range(width)]for i in range(height)]

    def getHeight(self):
        return self.__height

    def getWidth(self):
        return self.__width

    def getGrid(self):
        return self.__grid
    
    def getGlobalMaxSugar(self):
        return self.__globalMaxSugar

    def setGlobalMaxSugar(self, globalMaxSugar):
        self.__globalMaxSugar = globalMaxSugar

    def setHeight(self, height):
        self.__height = height

    def setWidth(self, width):
        self.__width = width

    def setGrid(self, grid):
        self.__grid = grid

    def setCell(self, cell, x, y):
        self.__grid[x][y] = cell

    def unsetCell(self, x, y):
        self.__grid[x][y] = None

    def getCell(self, x, y):
        return self.__grid[x][y]

    def doTimestep(self):
        randomRows = list(range(self.__height))
        randomColumns = list(range(self.__width))
        random.shuffle(randomRows)
        random.shuffle(randomColumns)
        for i in randomRows:
            for j in randomColumns:
                if self.__grid[i][j] != None:
                    self.__grid[i][j].doTimestep()

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
