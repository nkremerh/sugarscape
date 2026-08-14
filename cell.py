import math

class Cell:
    def __init__(self, x, y, environment, maxSugar=0, maxSpice=0, growbackRate=0, waterCapacity = 0.0):
        self.x = x
        self.y = y
        self.environment = environment
        self.maxSugar = maxSugar
        self.maxSpice = maxSpice

        # Water capacity as a float value in each cell (1.0/0.5/0.0)
        self.waterCapacity = float(waterCapacity)

        self.agent = None
        self.creature = None
        self.hemisphere = "north" if self.y < self.environment.equator else "south"
        self.neighbors = {}
        self.pollution = 0
        self.pollutionFlux = 0
        self.ranges = {}
        self.season = None
        self.spice = maxSpice
        self.spiceLastProduced = 0
        self.sugar = maxSugar
        self.sugarLastProduced = 0
        self.timestep = 0

    def doPollutionDiffusion(self):
        self.pollution = self.pollutionFlux

    def doSpiceConsumptionPollution(self, spiceConsumed):
        if self.isPollutionEnabled() == True:
            consumptionPollutionFactor = self.environment.spiceConsumptionPollutionFactor
            self.pollution += consumptionPollutionFactor * spiceConsumed

    def doSpiceProductionPollution(self, spiceProduced):
        if self.isPollutionEnabled() == True:
            productionPollutionFactor = self.environment.spiceProductionPollutionFactor
            self.pollution += productionPollutionFactor * spiceProduced

    def doSugarConsumptionPollution(self, sugarConsumed):
        if self.isPollutionEnabled() == True:
            consumptionPollutionFactor = self.environment.sugarConsumptionPollutionFactor
            self.pollution += consumptionPollutionFactor * sugarConsumed

    def doSugarProductionPollution(self, sugarProduced):
        if self.isPollutionEnabled() == True:
            productionPollutionFactor = self.environment.sugarProductionPollutionFactor
            self.pollution += productionPollutionFactor * sugarProduced

    # Help river configuration, by adjusting river capacity based on dist to the river center
    def findDistToRiver(self):
        config = self.environment.sugarscape.configuration
        riverOrient = config.get("environmentRiverOrientation", "vertical")
        orientation= riverOrient.lower()
        location = config.get("environmentRiverLocation", 30)
        slope = config.get("environmentRiverSlope", 0.0)

        riverCenter = location - 0.5

        # River orientation based on configuration
        if orientation == "horizontal":
            return abs(self.y - riverCenter)
        elif orientation == "vertical":
            return abs(self.x - riverCenter)

        # Diagonal river is based on the configured slope
        else:
            m = slope
            b = riverCenter
            numerator = abs(m * self.x - self.y + b)
            return numerator / math.sqrt(m ** 2 + 1)
        

    def findEastNeighbor(self):
        if self.environment.wraparound == False and self.x + 1 > self.environment.width - 1:
            return None
        eastNeighbor = self.environment.findCell((self.x + 1 + self.environment.width) % self.environment.width, self.y)
        return eastNeighbor

    def findNeighborAgents(self):
        agents = []
        for neighbor in self.neighbors.values():
            agent = neighbor.agent
            if agent != None:
                agents.append(agent)
        return agents

    def findNeighbors(self, mode):
        self.neighbors = {}

        north = self.findNorthNeighbor()
        south = self.findSouthNeighbor()
        east = self.findEastNeighbor()
        west = self.findWestNeighbor()
        if north is not None:
            self.neighbors["north"] = north
        if south is not None:
            self.neighbors["south"] = south
        if east is not None:
            self.neighbors["east"] = east
        if west is not None:
            self.neighbors["west"] = west

        if mode == "moore":
            northeast = north.findEastNeighbor() if north is not None else None
            northwest = north.findWestNeighbor() if north is not None else None
            southeast = south.findEastNeighbor() if south is not None else None
            southwest = south.findWestNeighbor() if south is not None else None
            if northeast is not None:
                self.neighbors["northeast"] = northeast
            if northwest is not None:
                self.neighbors["northwest"] = northwest
            if southeast is not None:
                self.neighbors["southeast"] = southeast
            if southwest is not None:
                self.neighbors["southwest"] = southwest

    def findNeighborWealth(self):
        neighborWealth = 0
        for neighbor in self.neighbors.values():
            if neighbor != None:
                neighborWealth += neighbor.sugar + neighbor.spice
        return neighborWealth

    def findNorthNeighbor(self):
        if self.environment.wraparound == False and self.y - 1 < 0:
            return None
        northNeighbor = self.environment.findCell(self.x, (self.y - 1 + self.environment.height) % self.environment.height)
        return northNeighbor

    def findPollutionFlux(self):

        config = self.environment.sugarscape.configuration
        waterPolFlow = config.get("environmentWaterPollutionFlow", True)
        orientation = config.get("environmentRiverOrientation", "horizontal")
        slope = config.get("environmentRiverSlope", 0.5)

        # Unidirectional pollution for river cells based on waterflow and direction
        if waterPolFlow and getattr(self, 'waterCapacity', 0.0) == 1.0:
            flowRate = config.get("environmentWaterPollutionFlowRate", 0.5)

            direction = self.environment.getWaterFlowDirection()

            # Look at cell right of or left of based on direction
            if orientation == "horizontal":
                targetX = self.x - direction
                targetY = self.y

            # Look at cell to the top or bottom based on direction
            if orientation == "vertical":
                targetX = self.x
                targetY = self.y - direction

            if orientation == "diagonal":
                # If slope = 0, it is horizontal
                if slope == 0.0:
                    targetX = self.x - direction
                    targetY = self.y   

                # If positive slope looks at NW and SE neighbors
                elif slope > 0.0:
                    targetX = self.x - direction
                    targetY = self.y - direction

                # If negative slope looks at NE and SW neighbors
                else:
                    targetX = self.x - direction
                    targetY = self.y + direction

                        
            if self.environment.wraparound:
                upstreamX = targetX % self.environment.width
                upstreamY = targetY % self.environment.height
                upstreamCell = self.environment.findCell(upstreamX, upstreamY)

            else:
                if 0 <= targetX < self.environment.width and 0 <= targetY < self.environment.height:
                    upstreamCell = self.environment.findCell(targetX, targetY)
                else:
                    upstreamCell = None

            if upstreamCell is not None and getattr(upstreamCell, 'waterCapacity', 0.0) == 1.0:
                self.pollutionFlux = (flowRate * upstreamCell.pollution) + ((1.0 - flowRate) * self.pollution)
                return

        # Standard pollution diffusion for non-river cells and floodplain cells
        meanPollution = 0
        for neighbor in self.neighbors.values():
            meanPollution += neighbor.pollution
        if len(self.neighbors) > 0:
            meanPollution = meanPollution / (len(self.neighbors))
        self.pollutionFlux = meanPollution

    # The river is thicker farther away from the equator for wet seasons so in order to make a smoooth trnasition
    def findRiverTaper(self):
        config = self.environment.sugarscape.configuration
        orientation = config.get("environmentRiverOrientation", "horizontal").lower()
        location = config.get("environmentRiverLocation", 30)
        equator = self.environment.equator
        slope = config.get("environmentRiverSlope", 0.0)


        riverCenter = location - 0.5

        if orientation == "vertical":
            localRiverY = self.y

        if orientation == "diagonal":
            localRiverY = slope * self.x + riverCenter

        # Using the local y coordinate in relation to the river
        distanceFromEquator = abs(localRiverY - equator)

        normalizedDistance = distanceFromEquator / (self.environment.height / 2)

        # Capped at 1 so that the tapering is limited between 0 and 1 (sine curve)
        if normalizedDistance > 1:
            normalizedDistance = 1

        taper = math.sin((math.pi/2)* normalizedDistance)

        return taper


    def findRiverWidth(self):
        config = self.environment.sugarscape.configuration
        orientation = config.get("environmentRiverOrientation", "horizontal").lower()
        dryWidth = config.get("environmentRiverWidthDry", 2)
        wetWidth = config.get("environmentRiverWidthWet", 4)
        equator = self.environment.equator

        location = config.get("environmentRiverLocation", 30)
        riverCenter = location - 0.5

        self.hemisphere = "north" if self.y < equator else "south"

        timeWeight = self.findSeasonTimeWeight()

        dryHalf = dryWidth / 2
        wetHalf = wetWidth / 2
        
        expandedHalf = dryHalf + (wetHalf - dryHalf) * timeWeight
        
        # Returns the halfwidth of the river which is used to determine if the cell in the river or flooplain
        if orientation == "horizontal":
            
            if self.hemisphere == "north":
                cellSeason = self.environment.seasonNorth
            else:
                cellSeason = self.environment.seasonSouth

            cellIsWet = True if cellSeason == "wet" else False

            # Crossing the equator means tapering
            if self.riverCrossesEquator():
                if cellIsWet:
                    return expandedHalf
                else:
                    return dryHalf

            else:
                if riverCenter < equator:
                    hemSeason = self.environment.seasonNorth
                else:
                    hemSeason = self.environment.seasonSouth

                if hemSeason == "wet":
                    return expandedHalf
                else:
                    return dryHalf        


        elif orientation == "vertical":

            # The tapered width is to determine weather teh cell contains water or not based on the seaasonal adjustment
            latTaper = self.findRiverTaper()
            taperedHalf = dryHalf + (expandedHalf - dryHalf) * latTaper
                        
            if self.y < equator:
                localSeason = self.environment.seasonNorth
            else:
                localSeason = self.environment.seasonSouth

            if localSeason == "wet":
                return taperedHalf
            else:
                return dryHalf

        elif orientation == "diagonal":
                         
            m = config.get("environmentRiverSlope", 0)
            b = riverCenter
            centerY = m*self.x + b

            if self.riverCrossesEquator():
                # Only for if the river crosses the equator
                latTaper = self.findRiverTaper()
                taperedHalf = dryHalf + (expandedHalf - dryHalf) * latTaper
                half = taperedHalf

                if centerY < equator:
                    localSeason = self.environment.seasonNorth
                else:
                    localSeason = self.environment.seasonSouth

            else:
                half = expandedHalf
                width = self.environment.width
                startY = b
                endY = m * (width - 1) + b

                if max(startY, endY) <= equator:
                    localSeason = self.environment.seasonNorth
                elif min(startY, endY) > equator:
                    localSeason = self.environment.seasonSouth

            # Returns the width of the river based on season to determine if the cell holds water and how much
            if localSeason == "wet":
                return half
            else:
                return dryHalf
       

    def findSouthNeighbor(self):
        if self.environment.wraparound == False and self.y + 1 > self.environment.height - 1:
            return None
        southNeighbor = self.environment.findCell(self.x, (self.y + 1 + self.environment.height) % self.environment.height)
        return southNeighbor

    def findWestNeighbor(self):
        if self.environment.wraparound == False and self.x - 1 < 0:
            return None
        westNeighbor = self.environment.findCell((self.x - 1 + self.environment.width) % self.environment.width, self.y)
        return westNeighbor

    def findSeasonTimeWeight(self):
        config = self.environment.sugarscape.configuration
        seasonInterval = config.get("environmentSeasonInterval", 50)
        currentTimestep = getattr(self.environment, 'timestep', 0)
              
        # Compute smooth temporal factor (0.0 to 1.0) over the season interval
        if seasonInterval > 0:
            seasonProgress = (currentTimestep % seasonInterval) / float(seasonInterval)
            # Smooth expansion envelope peaking at mid-season
            timeWeight = math.sin(math.pi * seasonProgress)
        else:
            timeWeight = 1.0

        return timeWeight

    def isOccupied(self):
        return self.agent != None

    def isPollutionEnabled(self):
        return self.environment.pollutionStart <= self.timestep <= self.environment.pollutionEnd

    def resetAgent(self):
        self.agent = None

    def resetSpice(self):
        self.spice = 0

    def resetSugar(self):
        self.sugar = 0

    def riverCrossesEquator(self):
        config = self.environment.sugarscape.configuration
        riverOrient = config.get("environmentRiverOrientation", "vertical")
        orientation= riverOrient.lower()
        location = config.get("environmentRiverLocation", 30)
        equator = self.environment.equator
        width = self.environment.width
        slope = config.get("environmentRiverSlope", 0.0)

        riverCenter = location - 0.5

        dryWidth = config.get("environmentRiverWidthDry", 2)
        wetWidth = config.get("environmentRiverWidthWet", 4)

        maxWidth = max(dryWidth, wetWidth)
        halfWidth = maxWidth / 2

        # River orientation based on configuration

        # checks the river edges to see where they fall in relation to the equator

        if orientation == "horizontal":
            topEdge = riverCenter - halfWidth
            bottomEdge = riverCenter + halfWidth
            if topEdge <= equator <= bottomEdge:
                return True
            
        elif orientation == "vertical":
            return True

        # Diagonal river is based on the configured slope -- y =mx + b
        else:
            m = slope
            b = riverCenter
            verticalHalfWidth = halfWidth * math.sqrt(m**2 + 1)
            startY = b
            endY = m *(width-1) + b
            lowestRiverY = min(startY, endY) - verticalHalfWidth
            highestRiverY = max(startY, endY) + verticalHalfWidth

            if lowestRiverY <= equator <= highestRiverY:
                return True
             
        return False
        

    def updateSeason(self):
        if self.season == "wet":
            self.season = "dry"
        else:
            self.season = "wet"

        # Cell water capacity dependent on seasons
        self.updateWaterCap()

    def updateWaterCap(self):

        # Get river half width, and the edges or distance of river to determine river and floodplain width
        halfWidth = self.findRiverWidth()
        distance = self.findDistToRiver()

        floodplainWidth = halfWidth

        # Determine cell water capactiy based on the cell's distance to the river based on width
        if distance < halfWidth:
            self.waterCapacity = 1.0

        elif distance < halfWidth + floodplainWidth:
            self.waterCapacity = 0.5

        else:
            self.waterCapacity = 0.0

        # Preserve base max capacities so when river shrinks it restores original values
        if not hasattr(self, 'baseMaxSugar') or self.maxSugar > self.baseMaxSugar:
            self.baseMaxSugar = self.maxSugar
        if not hasattr(self, 'baseMaxSpice') or self.maxSpice > self.baseMaxSpice:
            self.baseMaxSpice = self.maxSpice

        if self.waterCapacity == 1.0:
            self.maxSugar = 0
            self.maxSpice = 0
            self.sugar = 0
            self.spice = 0
        elif self.waterCapacity == 0.5:
            self.maxSugar = min(max(math.ceil(self.baseMaxSugar * 1.25), 2), math.ceil(self.baseMaxSugar * 1.25))
            self.maxSpice = min(max(math.ceil(self.baseMaxSpice * 1.25), 2), math.ceil(self.baseMaxSpice * 1.25))
            self.sugar = min(self.sugar, self.maxSugar)
            self.spice = min(self.spice, self.maxSpice)
        else:
            self.maxSugar = self.baseMaxSugar
            self.maxSpice = self.baseMaxSpice
            self.sugar = min(self.sugar, self.maxSugar)
            self.spice = min(self.spice, self.maxSpice)

    def __str__(self):
        string = ""
        if self.agent != None:
            string = "-A-"
        else:
            string = f"{str(self.sugar)}/{str(self.spice)}"
        return string
