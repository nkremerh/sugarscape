import random

class Agent:
    def __init__(self, cell, metabolism=0, vision=0, sugar=0):
        self.__cell = cell
        self.__metabolism = metabolism
        self.__vision = vision
        self.__sugar = sugar
        self.__alive = True
        self.__cellsInVision = []
        print("Agent stats: {0} vision, {1} metabolism, {2} endowment".format(self.__vision, self.__metabolism, self.__sugar))

    def collectResourcesAtCell(self):
        if self.__cell != None:
            self.__sugar = self.__sugar + self.__cell.resetSugar()

    def doMetabolism(self):
        self.__sugar = self.__sugar - self.__metabolism
        if self.__sugar < 1:
            self.setAlive(False)
            self.unsetCell()

    def doTimestep(self):
        if self.__alive == True:
            # TODO: Determine if sugar/spice eaten before moving (requires initial endowment of sugar/spice)
            self.moveToBestCellInVision()
            self.collectResourcesAtCell()
            self.doMetabolism()

    def findBestCellInVision(self):
        self.findCellsInVision()
        random.shuffle(self.__cellsInVision)
        bestCell = None
        bestRange = max(self.__cell.getEnvironment().getHeight(), self.__cell.getEnvironment().getWidth())
        agentX = self.__cell.getX()
        agentY = self.__cell.getY()
        wraparound = self.__vision + 1
        for i in range(len(self.__cellsInVision)):
            currCell = self.__cellsInVision[i]
            # Either X or Y distance will be 0 due to cardinal direction movement only
            distanceX = (abs(agentX - currCell.getX()) % wraparound)
            distanceY = (abs(agentY - currCell.getY()) % wraparound)
            travelDistance = distanceX + distanceY
            if(currCell.isOccupied() == True):
                continue
            if bestCell == None:
                bestCell = currCell
                bestRange = travelDistance
            currSugar = currCell.getCurrSugar()
            bestSugar = bestCell.getCurrSugar()
            if currSugar > bestSugar or (currSugar == bestSugar and travelDistance < bestRange):
                bestCell = currCell
                bestRange = travelDistance
        if bestCell == None:
            bestCell = self.__cell
        return bestCell

    def findCellsInVision(self):
        if self.__vision > 0 and self.__cell != None:
            northCells = [self.__cell.getNorthNeighbor()]
            southCells = [self.__cell.getSouthNeighbor()]
            eastCells = [self.__cell.getEastNeighbor()]
            westCells = [self.__cell.getWestNeighbor()]
            # Vision 1 accounted for in list setup
            for i in range(self.__vision - 1):
                northCells.append(northCells[-1].getNorthNeighbor())
                southCells.append(southCells[-1].getSouthNeighbor())
                eastCells.append(eastCells[-1].getEastNeighbor())
                westCells.append(westCells[-1].getWestNeighbor())
            # Keep only unique neighbors
            self.setCellsInVision(list(set(northCells + southCells + eastCells + westCells)))

    def getAlive(self):
        return self.__alive

    def getCell(self):
        return self.__cell

    def getCellsInVision(self):
        return self.__cellsInVision

    def getEnvironment(self):
        return self.__cell.getEnvironment()

    def getMetabolism(self):
        return self.__metabolism

    def getSugar(self):
        return self.__sugar

    def getVision(self):
        return self.__vision

    def isAlive(self):
        return self.getAlive()

    def moveToBestCellInVision(self):
        bestCell = self.findBestCellInVision()
        self.setCell(bestCell)

    def setAlive(self, alive):
        self.__alive = alive
    
    def setCell(self, cell):
        if(self.__cell != None):
            self.unsetCell()
        self.__cell = cell
        self.__cell.setAgent(self)

    def setCellsInVision(self, cells):
        self.__cellsInVision = cells

    def setMetabolism(self, metabolism):
        self.__metabolism = metabolism

    def setVision(self, vision):
        self.__vision = vision
 
    def unsetCell(self):
        self.__cell.unsetAgent()
        self.__cell = None

    def __str__(self):
        return "{0}".format(self.getSugar())
