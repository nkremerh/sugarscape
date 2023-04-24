import random

class Agent:
    def __init__(self, agentID, cell, metabolism=0, vision=0, maxAge=0, sugar=0):
        self.__cell = cell
        self.__metabolism = metabolism
        self.__vision = vision
        self.__sugar = sugar
        self.__alive = True
        self.__age = 0
        self.__maxAge = maxAge
        self.__cellsInVision = []
        self.__lastMoved = 0
        self.__vonNeumannNeighbors = {"north": None, "south": None, "east": None, "west": None}
        self.__mooreNeighbors = {"north": None, "northeast": None, "northwest": None, "south": None, "southeast": None, "southwest": None, "east": None, "west": None}
        self.__socialNetwork = {}
        self.__id = agentID
        # Debugging print statement
        #print("Agent stats: {0} vision, {1} metabolism, {2} max age, {3} initial wealth".format(self.__vision, self.__metabolism, self.__maxAge, self.__sugar))

    def collectResourcesAtCell(self):
        if self.__cell != None:
            self.__sugar = self.__sugar + self.__cell.resetSugar()

    def doAging(self):
        self.__age += 1
        # Die if reached max age and if not infinitely-lived
        if self.__age >= self.__maxAge and self.__maxAge != -1:
            self.setAlive(False)
            self.unsetCell()

    def doMetabolism(self):
        self.__sugar = self.__sugar - self.__metabolism
        if self.__sugar < 1:
            self.setAlive(False)
            self.unsetCell()

    def doTimestep(self):
        timestep = self.__cell.getEnvironment().getSugarscape().getTimestep()
        # Prevent dead or already moved agent from moving
        if self.__alive == True and self.__lastMoved != timestep: 
            self.__lastMoved = timestep
            self.moveToBestCellInVision()
            self.updateNeighbors()
            self.collectResourcesAtCell()
            self.doMetabolism()
            self.doAging()

    def findBestCellInVision(self):
        self.findCellsInVision()
        random.seed(self.__cell.getEnvironment().getSugarscape().getSeed())
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
            # Move to closest cell with the most resources
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

    def getAge(self):
        return self.__age

    def getAlive(self):
        return self.__alive

    def getCell(self):
        return self.__cell

    def getCellsInVision(self):
        return self.__cellsInVision

    def getEnvironment(self):
        return self.__cell.getEnvironment()

    def getID(self):
        return self.__id

    def getMaxAge(self):
        return self.__maxAge

    def getMetabolism(self):
        return self.__metabolism

    def getMooreNeighbors(self):
        return self.__mooreNeighbors

    def getSocialNetwork(self):
        return self.__socialNetwork

    def getSugar(self):
        return self.__sugar

    def getVision(self):
        return self.__vision

    def getVonNeumannNeighbors(self):
        return self.__vonNeumannNeigbbors

    def isAlive(self):
        return self.getAlive()

    def moveToBestCellInVision(self):
        bestCell = self.findBestCellInVision()
        self.setCell(bestCell)

    def setAge(self, age):
        self.__age = age

    def setAlive(self, alive):
        self.__alive = alive
    
    def setCell(self, cell):
        if(self.__cell != None):
            self.unsetCell()
        self.__cell = cell
        self.__cell.setAgent(self)

    def setCellsInVision(self, cells):
        self.__cellsInVision = cells

    def setID(self, agentID):
        self.__id = agentID

    def setMaxAge(self, maxAge):
        self.__maxAge = maxAge

    def setMetabolism(self, metabolism):
        self.__metabolism = metabolism

    def setMooreNeighbors(self, mooreNeighbors):
        self.__mooreNeighbors = mooreNeighbors

    def setSocialNetwork(self, socialNetwork):
        self.__socialNetwork = socialNetwork

    def setVision(self, vision):
        self.__vision = vision
 
    def setVonNeumannNeighbors(self, vonNeumannNeigbors):
        self.__vonNeumannNeighbors = vonNeumannNeighbors

    def updateMooreNeighbors(self):
        for direction, neighbor in self.__vonNeumannNeighbors.items():
            self.__mooreNeighbors[direction] = neighbor
        north = self.__mooreNeighbors["north"]
        south = self.__mooreNeighbors["south"]
        east = self.__mooreNeighbors["east"]
        west = self.__mooreNeighbors["west"]
        self.__mooreNeighbors["northeast"] = north.getCell().getEastNeighbor() if north != None else None
        self.__mooreNeighbors["northeast"] = east.getCell().getNorthNeighbor() if east != None and self.__mooreNeighbors["northeast"] == None else None
        self.__mooreNeighbors["northwest"] = north.getCell().getWestNeighbor() if north != None else None
        self.__mooreNeighbors["northwest"] = west.getCell().getNorthNeighbor() if west != None and self.__mooreNeighbors["northwest"] == None else None
        self.__mooreNeighbors["southeast"] = south.getCell().getEastNeighbor() if south != None else None
        self.__mooreNeighbors["southeast"] = east.getCell().getSouthNeighbor() if east != None and self.__mooreNeighbors["southeast"] == None else None
        self.__mooreNeighbors["southwest"] = south.getCell().getWestNeighbor() if south != None else None
        self.__mooreNeighbors["southwest"] = west.getCell().getSouthNeighbor() if west != None and self.__mooreNeighbors["southwest"] == None else None

    def updateNeighbors(self):
        self.updateVonNeumannNeighbors()
        self.updateMooreNeighbors()
        self.updateSocialNetwork()

    def updateSocialNetwork(self):
        for direction, neighbor in self.__vonNeumannNeighbors.items():
            if neighbor == None:
                continue
            neighborID = neighbor.getID()
            if neighborID in self.__socialNetwork:
                self.__socialNetwork[neighborID]["lastSeen"] = self.__lastMoved
                self.__socialNetwork[neighborID]["timesVisited"] += 1
            else:
                self.__socialNetwork[neighborID] = {"lastSeen": self.__lastMoved, "timesVisited": 1}

    def updateVonNeumannNeighbors(self):
        self.__vonNeumannNeighbors["north"] = self.__cell.getNorthNeighbor().getAgent()
        self.__vonNeumannNeighbors["south"] = self.__cell.getSouthNeighbor().getAgent()
        self.__vonNeumannNeighbors["east"] = self.__cell.getEastNeighbor().getAgent()
        self.__vonNeumannNeighbors["west"] = self.__cell.getWestNeighbor().getAgent()

    def unsetCell(self):
        self.__cell.unsetAgent()
        self.__cell = None

    def __str__(self):
        return "{0}".format(self.getSugar())
