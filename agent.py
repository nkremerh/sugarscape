import math
import random

class Agent:
    def __init__(self, agentID, birthday, cell, configuration):
        self.__id = agentID
        self.__born = birthday
        self.__cell = cell
        
        self.__sugarMetabolism = configuration["sugarMetabolism"]
        self.__spiceMetabolism = configuration["spiceMetabolism"]
        self.__movement = configuration["movement"]
        self.__vision = configuration["vision"]
        self.__sugar = configuration["sugar"]
        self.__spice = configuration["spice"]
        self.__startingSugar = configuration["sugar"]
        self.__startingSpice = configuration["spice"]
        self.__maxAge = configuration["maxAge"]
        self.__sex = configuration["sex"]
        self.__fertilityAge = configuration["fertilityAge"]
        self.__infertilityAge = configuration["infertilityAge"]
        self.__tags = configuration["tags"]
        self.__aggressionFactor = configuration["aggressionFactor"]
        self.__tradeFactor = configuration["tradeFactor"]
        self.__lookaheadFactor = configuration["lookaheadFactor"]
        self.__maxFriends = configuration["maxFriends"]
        self.__wealth = configuration["sugar"] + configuration["spice"]
        self.__seed = configuration["seed"]
        self.__inheritancePolicy = configuration["inheritancePolicy"]

        self.__alive = True
        self.__age = 0
        self.__cellsInVision = []
        self.__lastMoved = -1
        self.__vonNeumannNeighbors = {"north": None, "south": None, "east": None, "west": None}
        self.__mooreNeighbors = {"north": None, "northeast": None, "northwest": None, "south": None, "southeast": None, "southwest": None, "east": None, "west": None}
        self.__socialNetwork = {"father": None, "mother": None, "children": [], "friends": []}
        self.__parents = {"father": None, "mother": None}
        self.__children = []
        self.__friends = []
        self.__fertile = False
        self.__tribe = self.findTribe()
        self.__timestep = birthday
        self.__marginalRateOfSubstitution = 1
        self.__tagZeroes = 0

    def addChildToCell(self, mate, cell, childConfiguration):
        sugarscape = self.__cell.getEnvironment().getSugarscape()
        childID = sugarscape.generateAgentID()
        child = Agent(childID, self.__timestep, cell, childConfiguration)
        child.setCell(cell)
        sugarscape.addAgent(child)
        if self.__sex == "female":
            child.setMother(self)
            child.setFather(mate)
        else:
            child.setFather(self)
            child.setMother(mate)
        return child

    def addAgentToSocialNetwork(self, agentID):
        if agentID in self.__socialNetwork:
            return
        self.__socialNetwork[agentID] = {"lastSeen": self.__lastMoved, "timesVisited": 1, "timesReproduced": 0, "marginalRateOfSubstitution": 0}

    def calculateMarginalRateOfSubstitution(self, sugar, spice):
        spiceNeed = spice / self.__spiceMetabolism if self.__spiceMetabolism > 0 else 1
        sugarNeed = sugar / self.__sugarMetabolism if self.__sugarMetabolism > 0 else 1
        return spiceNeed / sugarNeed

    def collectResourcesAtCell(self):
        if self.__cell != None:
            sugarCollected = self.__cell.getCurrSugar()
            spiceCollected = self.__cell.getCurrSpice()
            self.__sugar += sugarCollected
            self.__spice += spiceCollected
            self.__wealth += sugarCollected + spiceCollected
            self.__cell.doProductionPollution(sugarCollected)
            self.__cell.doProductionPollution(spiceCollected)
            self.__cell.resetSugar()
            self.__cell.resetSpice()

    def doAging(self):
        if self.__alive == False:
            return
        self.__age += 1
        # Die if reached max age and if not infinitely-lived
        if self.__age >= self.__maxAge and self.__maxAge != -1:
            self.doDeath()

    def doCombat(self, cell):
        prey = cell.getAgent()
        if prey != None and prey != self:
            maxCombatLoot = self.__cell.getEnvironment().getMaxCombatLoot()
            preySugar = prey.getSugar()
            preySpice = prey.getSpice()
            sugarLoot = min(maxCombatLoot, preySugar)
            spiceLoot = min(maxCombatLoot, preySpice)
            self.__sugar += sugarLoot
            self.__spice += spiceLoot
            self.__wealth = self.__sugar + self.__spice
            prey.setSugar(preySugar - sugarLoot)
            prey.setSpice(preySpice - spiceLoot)
            prey.doDeath()
            # Debugging string
            #print("Agent {0} ({1} tribe) killed agent {2} ({3} tribe) and gained {4} wealth".format(str(self), self.__tribe, str(prey), prey.getTribe(), sugarLoot + spiceLoot))
        self.setCell(cell)

    def doDeath(self):
        if self.__sugar < 1 or self.__spice < 1:
            print("Agent {0} dying from starvation".format(str(self)))
        elif self.__age >= self.__maxAge and self.__maxAge != -1:
            print("Agent {0} dying from old age".format(str(self)))
        else:
            print("Agent {0} killed in combat".format(str(self)))

        self.setAlive(False)
        self.unsetCell()
        self.doInheritance()

    def doInheritance(self):
        # Provide inheritance for living children/sons/daughters/friends
        livingChildren = []
        livingSons = []
        livingDaughters = []
        livingFriends = []
        for child in self.__socialNetwork["children"]:
            if child.isAlive() == True:
                livingChildren.append(child)
                childSex = child.getSex()
                if childSex == "male":
                    livingSons.append(child)
                elif childSex == "female":
                    livingDaughters.append(child)
        for friend in self.__socialNetwork["friends"]:
            if friend["friend"].isAlive() == True:
                livingFriends.append(friend["friend"])

        if self.__inheritancePolicy == "children" and len(livingChildren) > 0:
            sugarInheritance = math.floor(self.__sugar / len(livingChildren))
            spiceInheritance = math.floor(self.__spice / len(livingChildren))
            for child in livingChildren:
                child.setSugar(child.getSugar() + sugarInheritance)
                child.setSpice(child.getSpice() + spiceInheritance)
        elif self.__inheritancePolicy == "sons" and len(livingSons) > 0:
            sugarInheritance = math.floor(self.__sugar / len(livingSons))
            spiceInheritance = math.floor(self.__spice / len(livingSons))
            for son in livingSons:
                son.setSugar(son.getSugar() + sugarInheritance)
                son.setSpice(son.getSpice() + spiceInheritance)
        elif self.__inheritancePolicy == "daughters" and len(livingDaughters) > 0:
            sugarInheritance = math.floor(self.__sugar / len(livingDaughters))
            spiceInheritance = math.floor(self.__spice / len(livingDaughters))
            for daughter in livingDaughters:
                daughter.setSugar(daughter.getSugar() + sugarInheritance)
                daughter.setSpice(daughter.getSpice() + spiceInheritance)
        elif self.__inheritancePolicy == "friends" and len(livingFriends) > 0:
            sugarInheritance = math.floor(self.__sugar / len(livingFriends))
            spiceInheritance = math.floor(self.__spice / len(livingFriends))
            for friend in livingFriends:
                friend.setSugar(friend.getSugar() + sugarInheritance)
                friend.setSpice(friend.getSpice() + spiceInheritance)
        self.__sugar = 0
        self.__spice = 0

    def doMetabolism(self):
        if self.__alive == False:
            return
        self.__sugar -= self.__sugarMetabolism
        self.__spice -= self.__spiceMetabolism
        self.__cell.doConsumptionPollution(self.__sugarMetabolism)
        self.__cell.doConsumptionPollution(self.__spiceMetabolism)
        if (self.__sugar < 1 and self.__sugarMetabolism > 0) or (self.__spice < 1 and self.__spiceMetabolism > 0):
            self.doDeath()

    def doReproduction(self):
        # Agent marked for removal should not reproduce
        if self.__alive == False:
            return
        neighborCells = self.__cell.getNeighbors()
        random.shuffle(neighborCells)
        emptyCells = self.findEmptyNeighborCells()
        for neighborCell in neighborCells:
            neighbor = neighborCell.getAgent()
            if neighbor != None:
                neighborCompatibility = self.isNeighborReproductionCompatible(neighbor)
                emptyCellsWithNeighbor = emptyCells + neighbor.findEmptyNeighborCells()
                random.shuffle(emptyCellsWithNeighbor)
                if self.isFertile() == True and neighborCompatibility == True and len(emptyCellsWithNeighbor) != 0:
                    emptyCell = emptyCellsWithNeighbor.pop()
                    while emptyCell.getAgent() != None and len(emptyCellsWithNeighbor) != 0:
                        # Debugging string
                        #print("Agent {0} could not produce child at ({1},{2}) since cell is not actually empty".format(str(self), emptyCell.getX(), emptyCell.getY()))
                        emptyCell = emptyCellsWithNeighbor.pop()
                    # If no adjacent empty cell is found, skip reproduction with this neighbor
                    if emptyCell.getAgent() != None:
                        continue
                    childEndowment = self.findChildEndowment(neighbor)
                    child = self.addChildToCell(neighbor, emptyCell, childEndowment)
                    self.__socialNetwork["children"].append(child)
                    childID = child.getID()
                    neighborID = neighbor.getID()
                    self.addAgentToSocialNetwork(childID)
                    neighbor.addAgentToSocialNetwork(childID)
                    neighbor.updateTimesVisitedFromAgent(self.__id, self.__lastMoved)
                    neighbor.updateTimesReproducedWithAgent(self.__id, self.__lastMoved)
                    self.updateTimesReproducedWithAgent(neighborID, self.__lastMoved)
                    # Debugging string
                    #print("Agents {0},{1} produced child at ({2},{3})".format(str(self), str(neighbor), emptyCell.getX(), emptyCell.getY()))

                    sugarCost = math.ceil(self.__startingSugar / 2)
                    spiceCost = math.ceil(self.__startingSpice / 2)
                    mateSugarCost = math.ceil(neighbor.getStartingSugar() / 2)
                    mateSpiceCost = math.ceil(neighbor.getStartingSpice() / 2)
                    self.__sugar -= sugarCost
                    self.__spice -= spiceCost
                    neighbor.setSugar(neighbor.getSugar() - mateSugarCost)
                    neighbor.setSpice(neighbor.getSpice() - mateSpiceCost)

    def doTagging(self):
        if self.__tags == None or self.__alive == False:
            return
        neighborCells = self.__cell.getNeighbors()
        random.shuffle(neighborCells)
        for neighborCell in neighborCells:
            neighbor = neighborCell.getAgent()
            if neighbor != None:
                position = random.randrange(len(self.__tags))
                neighbor.setTag(position, self.__tags[position])
                # Debugging string
                '''
                neighborTribe = neighbor.getTribe()
                neighborNewTribe = neighbor.findTribe()
                if neighborTribe != neighborNewTribe:
                    print("Agent {0} switched from {1} tribe to {2} tribe from agent {3}".format(str(neighbor), neighborTribe, neighborNewTribe, str(self)))
                '''
                neighbor.setTribe(neighbor.findTribe())

    def doTimestep(self, timestep):
        self.__timestep = timestep
        # Prevent dead or already moved agent from moving
        if self.__alive == True and self.__cell != None and self.__lastMoved != self.__timestep:
            self.__lastMoved = self.__timestep
            self.moveToBestCell()
            self.updateNeighbors()
            # TODO: Determine order of operations for post-move actions
            self.collectResourcesAtCell()
            self.doTrading()
            self.doMetabolism()
            self.doTagging()
            self.doReproduction()
            self.doAging()

    def doTrading(self):
        # If not a trader, skip trading
        if self.__tradeFactor == 0:
            return
        self.findMarginalRateOfSubstitution()
        neighborCells = self.__cell.getNeighbors()
        traders = []
        for neighborCell in neighborCells:
            neighbor = neighborCell.getAgent()
            if neighbor != None and neighbor.isAlive() == True:
                neighborMRS = neighbor.getMarginalRateOfSubstitution()
                if neighborMRS != self.__marginalRateOfSubstitution:
                    traders.append(neighbor)
        random.shuffle(traders)
        for trader in traders:
            traderMRS = trader.getMarginalRateOfSubstitution()
            spiceSeller = None
            sugarSeller = None
            tradeFlag = True

            while tradeFlag == True:
                if traderMRS > self.__marginalRateOfSubstitution:
                    spiceSeller = trader
                    sugarSeller = self
                else:
                    spiceSeller = self
                    sugarSeller = trader
                spiceSellerMRS = spiceSeller.getMarginalRateOfSubstitution()
                sugarSellerMRS = sugarSeller.getMarginalRateOfSubstitution()

                # Find geometric mean of spice and sugar seller MRS for trade price
                tradePrice = int(math.ceil(math.sqrt(spiceSellerMRS * sugarSellerMRS)))
                spiceSellerSpice = spiceSeller.getSpice()
                spiceSellerSugar = spiceSeller.getSugar()
                sugarSellerSpice = sugarSeller.getSpice()
                sugarSellerSugar = sugarSeller.getSugar()
                # If trade would be lethal, skip it
                if spiceSellerSpice - tradePrice < 1 or sugarSellerSugar - 1 < 1:
                    # Debugging string
                    #print("Agent {0} skipping lethal trade with agent {1}".format(str(self), str(trader)))
                    tradeFlag = False
                    continue
                spiceSellerNewMRS = spiceSeller.calculateMarginalRateOfSubstitution(spiceSellerSugar + 1, spiceSellerSpice - tradePrice)
                sugarSellerNewMRS = sugarSeller.calculateMarginalRateOfSubstitution(sugarSellerSugar - 1, sugarSellerSpice + tradePrice)

                # Calculate absolute difference from perfect spice/sugar parity in MRS
                betterForSpiceSeller = abs(1 - spiceSellerMRS) > abs(1 - spiceSellerNewMRS)
                betterForSugarSeller = abs(1 - sugarSellerMRS) > abs(1 - sugarSellerNewMRS)

                # Check that spice seller's new MRS does not cross over sugar seller's new MRS
                # Evaluates to False for successful trades
                checkForMRSCrossing = spiceSellerNewMRS < sugarSellerNewMRS
                if betterForSpiceSeller and betterForSugarSeller and checkForMRSCrossing == False:
                    # Debugging string
                    #print("Agent {0} [{1},{2}] ({3}-->{4}) selling {5} spice to agent {6} [{7},{8}] ({9}-->{10}) for 1 sugar".format(str(spiceSeller), spiceSeller.getSugar(), spiceSeller.getSpice(), spiceSellerMRS, spiceSellerNewMRS, tradePrice, str(sugarSeller), sugarSeller.getSugar(), sugarSeller.getSpice(), sugarSellerMRS, sugarSellerNewMRS))
                    spiceSeller.setSpice(spiceSellerSpice - tradePrice)
                    spiceSeller.setSugar(spiceSellerSugar + 1)
                    sugarSeller.setSpice(sugarSellerSpice + tradePrice)
                    sugarSeller.setSugar(sugarSellerSugar - 1)
                    spiceSeller.findMarginalRateOfSubstitution()
                    sugarSeller.findMarginalRateOfSubstitution()
                else:
                    tradeFlag = False
                    continue

    def findAgentWealthAtCell(self, cell):
        agent = cell.getAgent()
        if agent == None:
            return 0
        else:
            return agent.getWealth()

    def findBestCell(self):
        self.findCellsInVision()
        retaliators = self.findRetaliatorsInVision()
        retaliationPossible = {}
        for tribe in retaliators:
            retaliationPossible[tribe] = True if self.__tribe == tribe or retaliators[tribe] > self.__wealth else False
        totalMetabolism = self.__sugarMetabolism + self.__spiceMetabolism
        sugarMetabolismProportion = self.__sugarMetabolism / totalMetabolism
        spiceMetabolismProportion = self.__spiceMetabolism / totalMetabolism
        random.shuffle(self.__cellsInVision)

        bestCell = None
        bestRange = max(self.__cell.getEnvironment().getHeight(), self.__cell.getEnvironment().getWidth())
        bestWealth = 0
        agentX = self.__cell.getX()
        agentY = self.__cell.getY()
        combatMaxLoot = self.__cell.getEnvironment().getMaxCombatLoot()
        wraparound = self.__vision + 1
        #cellFinds = "Agent {0} at ({1},{2}) has [{3}/{4},{5}/{6}] and found cells in vision {7}:\n".format(str(self), self.__cell.getX(), self.__cell.getY(), self.__sugar, self.__sugarMetabolism, self.__spice, self.__spiceMetabolism, self.__vision)
        for currCell in self.__cellsInVision:
            cell = currCell["cell"]
            travelDistance = currCell["distance"]
            
            if cell.isOccupied() == True and self.__aggressionFactor == 0:
                continue
            cellSugar = cell.getCurrSugar()
            cellSpice = cell.getCurrSpice()
            prey = cell.getAgent()
            # Avoid attacking agents from the same tribe
            if prey != None and prey.getTribe() == self.__tribe:
                continue
            preyTribe = prey.getTribe() if prey != None else "empty"
            preyWealth = prey.getWealth() if prey != None else 0
            preySugar = prey.getSugar() if prey != None else 0
            preySpice = prey.getSpice() if prey != None else 0
            welfarePreySugar = self.__aggressionFactor * min(combatMaxLoot, preySugar)
            welfarePreySpice = self.__aggressionFactor * min(combatMaxLoot, preySpice)
            
            # Modify value of cell relative to the metabolism needs of the agent
            sugarLookahead = self.__sugarMetabolism * self.__lookaheadFactor
            spiceLookahead = self.__spiceMetabolism * self.__lookaheadFactor
            cellSugarTotal = (self.__sugar + cellSugar + welfarePreySugar) - sugarLookahead
            cellSpiceTotal = (self.__spice + cellSpice + welfarePreySpice) - spiceLookahead
            if cellSugarTotal < 0:
                cellSugarTotal = 0
            if cellSpiceTotal < 0:
                cellSpiceTotal = 0
            welfareFunction = (cellSugarTotal ** sugarMetabolismProportion) * (cellSpiceTotal ** spiceMetabolismProportion)
            if len(self.__tags) > 0:
                self.findTribe()
                fractionZeroesInTags = self.__tagZeroes / len(self.__tags)
                fractionOnesInTags = 1 - fractionZeroesInTags
                tagPreferences = (self.__sugarMetabolism * fractionZeroesInTags) + (self.__spiceMetabolism * fractionOnesInTags)
                tagPreferencesSugar = (self.__sugarMetabolism / tagPreferences) * fractionZeroesInTags
                tagPreferencesSpice = (self.__spiceMetabolism / tagPreferences) * fractionOnesInTags
                welfareFunction = (cellSugarTotal ** tagPreferencesSugar) * (cellSpiceTotal ** tagPreferencesSpice)
            cellWealth = welfareFunction / (1 + cell.getCurrPollution())

            #if prey == None:
            #    cellFinds += "({0},{1}) --> [{2},{3}] with no prey for {4} wealth at distance {5}\n".format(cell.getX(), cell.getY(), cell.getCurrSugar(), cell.getCurrSpice(), cellWealth, travelDistance)
            #else:
            #    cellFinds += "({0},{1}) --> [{2},{3}] with [{4},{5}] prey for {6} wealth at distance {7}\n".format(cell.getX(), cell.getY(), cell.getCurrSugar(), cell.getCurrSpice(), prey.getSugar(), prey.getSpice(), cellWealth, travelDistance)

            # Avoid attacking stronger agents or those protected from retaliation after killing prey
            if prey != None and (preyWealth > self.__wealth or (retaliators[preyTribe] > self.__wealth + cellWealth)):
                # Debugging string
                #print("Agent {0} ({1} tribe, {2} wealth) not attacking agent {3} ({4} tribe, {5} wealth) due to prey being stronger/protected".format(str(self), self.__tribe, self.__wealth, str(prey), preyTribe, preyWealth))
                continue
            
            if bestCell == None:
                bestCell = cell
                bestRange = travelDistance
                bestWealth = cellWealth
                # Debugging string
                #print("Agent {0} calculated best cell welfare of ({1},{2}) at distance {3} as {4}".format(str(self), cell.getX(), cell.getY(), bestRange, welfareFunction))
            
            # Select closest cell with the most resources
            if cellWealth > bestWealth or (cellWealth == bestWealth and travelDistance < bestRange):
                if prey != None and prey.getWealth() > self.__wealth:
                    continue
                bestRange = travelDistance
                bestCell = cell
                bestWealth = cellWealth
            #print("Current best cell ({0},{1}), current cell ({2},{3})".format(bestCell.getX(), bestCell.getY(), cell.getX(), cell.getY()))
        if bestCell == None:
            bestCell = self.__cell
        #if (bestCell.getCurrSugar() == 0 or bestCell.getCurrSpice() == 0) and (self.__sugar <= self.__sugarMetabolism or self.__spice <= self.__spiceMetabolism):
        #    print("Agent {0} moving to ({1},{2}) with [{3},{4}] while close to starvation with holds [{5},{6}]".format(str(self), bestCell.getX(), bestCell.getY(), bestCell.getCurrSugar(), bestCell.getCurrSpice(), self.__sugar, self.__spice))
        #cellFinds += "Selected ({0},{1}) --> [{2},{3}] for {4} wealth at distance {5}\n".format(bestCell.getX(), bestCell.getY(), bestCell.getCurrSugar(), bestCell.getCurrSpice(), bestWealth, bestRange)
        #print(cellFinds)
        return bestCell

    def findBestFriend(self):
        if self.__tags == None:
            return None
        minHammingDistance = len(self.__tags)
        bestFriend = None
        for friend in self.__socialNetwork["friends"]:
            # If already a friend, update Hamming Distance
            if friend["hammingDistance"] < minHammingDistance:
                bestFriend = friend
                minHammingDistance = friend["hammingDistance"]
        return bestFriend

    def findCellsInVision(self):
        if self.__vision > 0 and self.__cell != None:
            northCells = [{"cell": self.__cell.getNorthNeighbor(), "distance": 1}]
            southCells = [{"cell": self.__cell.getSouthNeighbor(), "distance": 1}]
            eastCells = [{"cell": self.__cell.getEastNeighbor(), "distance": 1}]
            westCells = [{"cell": self.__cell.getWestNeighbor(), "distance": 1}]
            # Vision 1 accounted for in list setup
            for i in range(1, self.__vision):
                northCells.append({"cell": northCells[-1]["cell"].getNorthNeighbor(), "distance": i + 1})
                southCells.append({"cell": southCells[-1]["cell"].getSouthNeighbor(), "distance": i + 1})
                eastCells.append({"cell": eastCells[-1]["cell"].getEastNeighbor(), "distance": i + 1})
                westCells.append({"cell": westCells[-1]["cell"].getWestNeighbor(), "distance": i + 1})
            self.setCellsInVision(northCells + southCells + eastCells + westCells)

    def findChildEndowment(self, mate):
        parentSugarMetabolisms = [self.__sugarMetabolism, mate.getSugarMetabolism()]
        parentSpiceMetabolisms = [self.__spiceMetabolism, mate.getSpiceMetabolism()]
        parentMovements = [self.__movement, mate.getMovement()]
        parentVisions = [self.__vision, mate.getVision()]
        parentMaxAges = [self.__maxAge, mate.getMaxAge()]
        parentInfertilityAges = [self.__infertilityAge, mate.getInfertilityAge()]
        parentFertilityAges = [self.__fertilityAge, mate.getFertilityAge()]
        parentSexes = [self.__sex, mate.getSex()]
        parentAggressionFactors = [self.__aggressionFactor, mate.getAggressionFactor()]
        parentTradeFactors = [self.__tradeFactor, mate.getTradeFactor()]
        parentLookaheadFactors = [self.__lookaheadFactor, mate.getLookaheadFactor()]
        parentMaxFriends = [self.__maxFriends, mate.getMaxFriends()]
        # Each parent gives 1/2 their starting endowment for child endowment
        childStartingSugar = math.ceil(self.__startingSugar / 2) + math.ceil(mate.getStartingSugar() / 2)
        childStartingSpice = math.ceil(self.__startingSpice / 2) + math.ceil(mate.getStartingSpice() / 2)

        childSugarMetabolism = parentSugarMetabolisms[random.randrange(2)]
        childSpiceMetabolism = parentSpiceMetabolisms[random.randrange(2)]
        childMovement = parentMovements[random.randrange(2)]
        childVision = parentVisions[random.randrange(2)]
        childMaxAge = parentMaxAges[random.randrange(2)]
        childInfertilityAge = parentInfertilityAges[random.randrange(2)]
        childFertilityAge = parentFertilityAges[random.randrange(2)]
        childSex = parentSexes[random.randrange(2)]
        childMaxFriends = parentMaxFriends[random.randrange(2)]
        childTags = []
        mateTags = mate.getTags()
        mismatchTags = [0, 1]
        if self.__tags == None:
            childTags = None
        else:
            for i in range(len(self.__tags)):
                if self.__tags[i] == mateTags[i]:
                    childTags.append(self.__tags[i])
                else:
                    childTags.append(mismatchTags[random.randrange(2)])
        childAggressionFactor = parentAggressionFactors[random.randrange(2)]
        childTradeFactor = parentTradeFactors[random.randrange(2)]
        childLookaheadFactor = parentLookaheadFactors[random.randrange(2)]
        endowment = {"movement": childMovement, "vision": childVision, "maxAge": childMaxAge, "sugar": childStartingSugar,
                     "spice": childStartingSpice, "sex": childSex, "fertilityAge": childFertilityAge, "infertilityAge": childInfertilityAge, "tags": childTags,
                     "aggressionFactor": childAggressionFactor, "maxFriends": childMaxFriends, "seed": self.__seed, "sugarMetabolism": childSugarMetabolism,
                     "spiceMetabolism": childSpiceMetabolism, "inheritancePolicy": self.__inheritancePolicy, "tradeFactor": childTradeFactor,
                     "lookaheadFactor": childLookaheadFactor}
        return endowment

    def findEmptyNeighborCells(self):
        emptyCells = []
        neighborCells = self.__cell.getNeighbors()
        for neighborCell in neighborCells:
            if neighborCell.getAgent() == None:
                emptyCells.append(neighborCell)
        return emptyCells

    def findHammingDistanceInTags(self, neighbor):
        if self.__tags == None:
            return 0
        neighborTags = neighbor.getTags()
        hammingDistance = 0
        for i in range(len(self.__tags)):
            if self.__tags[i] != neighborTags[i]:
                hammingDistance += 1
        return hammingDistance

    def findMarginalRateOfSubstitution(self):
        spiceNeed = self.__spice / self.__spiceMetabolism if self.__spiceMetabolism > 0 else 1
        sugarNeed = self.__sugar / self.__sugarMetabolism if self.__sugarMetabolism > 0 else 1
        # Debugging string
        #print("Agent {0} sugar need {1}, spice need {2}".format(str(self), sugarNeed, spiceNeed))
        # Trade factor may increase amount of spice traded for sugar in a transaction
        self.__marginalRateOfSubstitution = self.__tradeFactor * (spiceNeed / sugarNeed)

    def findRetaliatorsInVision(self):
        retaliators = {}
        for cell in self.__cellsInVision:
            agent = cell["cell"].getAgent()
            if agent != None:
                agentTribe = agent.getTribe()
                agentStrength = agent.getWealth()
                if agentTribe not in retaliators:
                    retaliators[agentTribe] = agentStrength
                elif retaliators[agentTribe] < agentStrength:
                    retaliators[agentTribe] = agentStrength
        return retaliators

    # TODO: Create list of max tribe colors or create tribe color generator
    def findTribe(self):
        if self.__tags == None:
            return None
        sugarscape = self.__cell.getEnvironment().getSugarscape()
        numTribes = sugarscape.getConfiguration()["environmentMaxTribes"]
        zeroes = 0
        tribeCutoff = math.floor(len(self.__tags) / numTribes)
        # Up to 11 tribes possible without significant color conflicts
        colors = ["green", "blue", "red", "orange", "purple", "teal", "pink", "mint", "blue2", "yellow", "salmon"]
        for tag in self.__tags:
            if tag == 0:
                zeroes += 1
        self.__tagZeroes = zeroes
        for i in range(1, numTribes + 1):
            if zeroes < (i * tribeCutoff) + 1 or i == numTribes:
                return colors[i - 1]
        # Default agent coloring
        return "red"

    def getAge(self):
        return self.__age

    def getAggressionFactor(self):
        return self.__aggressionFactor

    def getAlive(self):
        return self.__alive

    def getCell(self):
        return self.__cell

    def getCellsInVision(self):
        return self.__cellsInVision

    def getEnvironment(self):
        return self.__cell.getEnvironment()

    def getInfertilityAge(self):
        return self.__infertilityAge

    def getFather(self):
        return self.__socialNetwork["father"]

    def getFertile(self):
        return self.__fertile

    def getFertilityAge(self):
        return self.__fertilityAge

    def getID(self):
        return self.__id

    def getInheritancePolicy(self):
        return self.__inheritancePolicy

    def getLookaheadFactor(self):
        return self.__lookaheadFactor

    def getMarginalRateOfSubstitution(self):
        return self.__marginalRateOfSubstitution

    def getMaxAge(self):
        return self.__maxAge

    def getMaxFriends(self):
        return self.__maxFriends

    def getMovement(self):
        return self.__movement

    def getMooreNeighbors(self):
        return self.__mooreNeighbors

    def getMother(self):
        return self.__socialNetwork["mother"]

    def getSex(self):
        return self.__sex

    def getSocialNetwork(self):
        return self.__socialNetwork

    def getStartingSpice(self):
        return self.__startingSpice

    def getStartingSugar(self):
        return self.__startingSugar

    def getSpice(self):
        return self.__spice

    def getSpiceMetabolism(self):
        return self.__spiceMetabolism

    def getSugar(self):
        return self.__sugar

    def getSugarMetabolism(self):
        return self.__sugarMetabolism

    def getTag(self, position):
        return self.__tags[position]

    def getTags(self):
        return self.__tags

    def getTagZeroes(self):
        return self.__tagZeroes

    def getTradeFactor(self):
        return self.__tradeFactor

    def getTribe(self):
        return self.__tribe

    def getVision(self):
        return self.__vision

    def getVonNeumannNeighbors(self):
        return self.__vonNeumannNeigbbors

    def getWealth(self):
        return self.__sugar

    def isAlive(self):
        return self.getAlive()

    def isFertile(self):
        if self.__sugar >= self.__startingSugar and self.__spice >= self.__startingSpice and self.__age >= self.__fertilityAge and self.__age < self.__infertilityAge:
            return True
        return False

    def isNeighborReproductionCompatible(self, neighbor):
        if neighbor == None:
            return False
        neighborSex = neighbor.getSex()
        neighborFertility = neighbor.isFertile()
        if self.__sex == "female" and (neighborSex == "male" and neighborFertility == True):
            return True
        elif self.__sex == "male" and (neighborSex == "female" and neighborFertility == True):
            return True
        else:
            return False

    def moveToBestCell(self):
        bestCell = self.findBestCell()
        if self.__aggressionFactor > 0:
            self.doCombat(bestCell)
        else:
            self.setCell(bestCell)
        # Debugging string
        #print("Agent {0} moved to ({1},{2})".format(str(self), bestCell.getX(), bestCell.getY()))

    def setAge(self, age):
        self.__age = age

    def setAggressionFactor(self, aggressionFactor):
        self.__aggressionFactor = aggressionFactor

    def setAlive(self, alive):
        self.__alive = alive
    
    def setCell(self, cell):
        if(self.__cell != None):
            self.unsetCell()
        self.__cell = cell
        self.__cell.setAgent(self)

    def setCellsInVision(self, cells):
        self.__cellsInVision = cells

    def setInfertilityAge(self, infertilityAge):
        self.__infertilityAge = infertilityAge

    def setFather(self, father):
        fatherID = father.getID()
        if fatherID not in self.__socialNetwork:
            self.addAgentToSocialNetwork(father)
        self.__socialNetwork["father"] = father

    def setFertile(self, fertile):
        self.__fertile = fertile

    def setFertilityAge(self, fertilityAge):
        self.__fertilityAge = fertilityAge

    def setID(self, agentID):
        self.__id = agentID

    def setInheritancePolicy(self, inheritancePolicy):
        self.__inheritancePolicy = inheritancePolicy

    def setLookaheadFactor(self, lookaheadFactor):
        self.__lookaheadFactor = lookaheadFactor

    def setMarginalRateOfSubstitution(self, mrs):
        self.__marginalRateOfSubstitution = mrs

    def setMaxAge(self, maxAge):
        self.__maxAge = maxAge

    def setMaxFriends(self, maxFriends):
        self.__maxFriends = maxFriends

    def setMovement(self, movement):
        self.__movement = movement

    def setMooreNeighbors(self, mooreNeighbors):
        self.__mooreNeighbors = mooreNeighbors

    def setMother(self, mother):
        motherID = mother.getID()
        if motherID not in self.__socialNetwork:
            self.addAgentToSocialNetwork(mother)
        self.__socialNetwork["mother"] = mother

    def setSex(self, sex):
        self.__sex = sex

    def setSocialNetwork(self, socialNetwork):
        self.__socialNetwork = socialNetwork

    def setSpice(self, spice):
        self.__spice = spice

    def setSpiceMetabolism(self, spiceMetabolism):
        self.__spiceMetabolism = spiceMetabolism

    def setSugar(self, sugar):
        self.__sugar = sugar

    def setSugarMetabolism(self, sugarMetabolism):
        self.__sugarMetabolism = sugarMetabolism

    def setTag(self, position, value):
        self.__tags[position] = value

    def setTags(self, tags):
        self.__tags = tags

    def setTagZeroes(self, tagZeroes):
        self.__tagZeroes = tagZeroes

    def setTradeFactor(self, tradeFactor):
        self.__tradeFactor = tradeFactor

    def setTribe(self, tribe):
        self.__tribe = tribe

    def setVision(self, vision):
        self.__vision = vision
 
    def setVonNeumannNeighbors(self, vonNeumannNeigbors):
        self.__vonNeumannNeighbors = vonNeumannNeighbors

    def setWealth(self, wealth):
        self.__wealth = wealth

    def updateFriends(self, neighbor):
        neighborID = neighbor.getID()
        neighborHammingDistance = self.findHammingDistanceInTags(neighbor)
        neighborEntry = {"friend": neighbor, "hammingDistance": neighborHammingDistance}
        if len(self.__socialNetwork["friends"]) < self.__maxFriends:
            self.__socialNetwork["friends"].append(neighborEntry)
        else:
            maxHammingDistance = 0
            maxDifferenceFriend = None
            for friend in self.__socialNetwork["friends"]:
                # If already a friend, update Hamming Distance
                if friend["friend"].getID() == neighborID:
                    self.__socialNetwork["friends"].remove(friend)
                    self.__socialNetwork["friends"].append(neighborEntry)
                    return
                if friend["hammingDistance"] > maxHammingDistance:
                    maxDistanceFriend = friend
                    maxHammingDistance = friend["hammingDistance"]
            if maxHammingDistance > neighborHammingDistance:
                self.__socialNetwork["friends"].remove(maxDistanceFriend)
                self.__socialNetwork["friends"].append(neighborEntry)
        self.__socialNetwork["bestFriend"] = self.findBestFriend()

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
                self.updateTimesVisitedFromAgent(neighborID, self.__lastMoved)
                self.updateMarginalRateOfSubstitutionForAgent(neighbor)
            else:
                self.addAgentToSocialNetwork(neighborID)
            self.updateFriends(neighbor)

    def updateMarginalRateOfSubstitutionForAgent(self, agent):
        agentID = agent.getID()
        if agentID not in self.__socialNetwork:
            self.addToSocialNetwork(agentID)
        self.__socialNetwork[agentID]["marginalRateOfSubstitution"] = agent.getMarginalRateOfSubstitution()

    def updateTimesReproducedWithAgent(self, agentID, timestep):
        if agentID not in self.__socialNetwork:
            self.addToSocialNetwork(agentID)
        self.__socialNetwork[agentID]["timesReproduced"] += 1
        self.__socialNetwork[agentID]["lastSeen"] = timestep

    def updateTimesVisitedFromAgent(self, agentID, timestep):
        if agentID not in self.__socialNetwork:
            self.addAgentToSocialNetwork(agentID)
        else:
            self.__socialNetwork[agentID]["timesVisited"] += 1
            self.__socialNetwork[agentID]["lastSeen"] = timestep

    def updateVonNeumannNeighbors(self):
        self.__vonNeumannNeighbors["north"] = self.__cell.getNorthNeighbor().getAgent()
        self.__vonNeumannNeighbors["south"] = self.__cell.getSouthNeighbor().getAgent()
        self.__vonNeumannNeighbors["east"] = self.__cell.getEastNeighbor().getAgent()
        self.__vonNeumannNeighbors["west"] = self.__cell.getWestNeighbor().getAgent()

    def unsetCell(self):
        self.__cell.unsetAgent()
        self.__cell = None

    def __str__(self):
        return "{0}".format(self.__id)
