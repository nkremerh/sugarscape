import hashlib
import math
import random
import sys

class Agent:
    def __init__(self, agentID, birthday, cell, configuration):
        self.ID = agentID
        self.born = birthday
        self.cell = cell
        self.debug = cell.environment.sugarscape.debug

        self.sugarMetabolism = configuration["sugarMetabolism"]
        self.spiceMetabolism = configuration["spiceMetabolism"]
        self.movement = configuration["movement"]
        self.movementMode = configuration["movementMode"]
        self.vision = configuration["vision"]
        self.visionMode = configuration["visionMode"]
        self.sugar = configuration["sugar"]
        self.spice = configuration["spice"]
        self.startingSugar = configuration["sugar"]
        self.startingSpice = configuration["spice"]
        self.universalSugar = configuration["universalSugar"]
        self.universalSpice = configuration["universalSpice"]
        self.maxAge = configuration["maxAge"]
        self.sex = configuration["sex"]
        self.fertilityAge = configuration["fertilityAge"]
        self.infertilityAge = configuration["infertilityAge"]
        self.tags = configuration["tags"]
        self.aggressionFactor = configuration["aggressionFactor"]
        self.tradeFactor = configuration["tradeFactor"]
        self.lookaheadFactor = configuration["lookaheadFactor"]
        self.lendingFactor = configuration["lendingFactor"]
        self.fertilityFactor = configuration["fertilityFactor"]
        self.baseInterestRate = configuration["baseInterestRate"]
        self.loanDuration = configuration["loanDuration"]
        self.maxFriends = configuration["maxFriends"]
        self.wealth = configuration["sugar"] + configuration["spice"]
        self.seed = configuration["seed"]
        self.inheritancePolicy = configuration["inheritancePolicy"]
        self.startingImmuneSystem = configuration["immuneSystem"]
        self.immuneSystem = configuration["immuneSystem"]
        self.decisionModelFactor = configuration["decisionModelFactor"]
        self.selfishnessFactor = configuration["selfishnessFactor"]
        self.decisionModel = configuration["decisionModel"]

        self.alive = True
        self.age = 0
        self.cellsInRange = []
        self.neighborhood = []
        self.lastMoved = -1
        self.vonNeumannNeighbors = {"north": None, "south": None, "east": None, "west": None}
        self.mooreNeighbors = {"north": None, "northeast": None, "northwest": None, "south": None, "southeast": None, "southwest": None, "east": None, "west": None}
        self.socialNetwork = {"father": None, "mother": None, "children": [], "friends": [], "creditors": [], "debtors": []}
        self.diseases = []
        self.fertile = False
        self.tribe = self.findTribe()
        self.timestep = birthday
        self.marginalRateOfSubstitution = 1
        self.tagZeroes = 0
        self.sugarMeanIncome = 1
        self.spiceMeanIncome = 1
        self.tradeVolume = 0
        self.spicePrice = 0
        self.sugarPrice = 0
        self.nice = 0
        self.childEndowmentHashes = None
        self.happiness = 0
        self.wealthHappiness = 0
        self.healthHappiness = 0
        self.familyHappiness = 0
        self.socialHappiness = 0
        self.conflictHappiness = 0
        self.lastDoneCombat = -1
        self.lastReproduced = -1
        self.lastSugar = 0
        self.lastSpice = 0
        self.causeOfDeath = None
        self.lastUniversalSpiceIncomeTimestep = 0
        self.lastUniversalSugarIncomeTimestep = 0
        self.sugarMetabolismModifier = 0
        self.spiceMetabolismModifier = 0
        self.movementModifier = 0
        self.visionModifier = 0
        self.aggressionFactorModifier = 0
        self.fertilityFactorModifier = 0

    def addChildToCell(self, mate, cell, childConfiguration):
        sugarscape = self.cell.environment.sugarscape
        childID = sugarscape.generateAgentID()
        child = self.spawnChild(childID, self.timestep, cell, childConfiguration)
        child.gotoCell(cell)
        sugarscape.addAgent(child)
        child.collectResourcesAtCell()
        if self.sex == "female":
            child.setMother(self)
            child.setFather(mate)
        else:
            child.setFather(self)
            child.setMother(mate)
        return child

    def addAgentToSocialNetwork(self, agent):
        agentID = agent.ID
        if agentID in self.socialNetwork:
            return
        self.socialNetwork[agentID] = {"agent": agent, "lastSeen": self.lastMoved, "timesVisited": 1, "timesReproduced": 0,
                                         "timesTraded": 0, "timesLoaned": 0, "marginalRateOfSubstitution": 0}

    def addLoanToAgent(self, agent, timestep, sugarPrincipal, sugarLoan, spicePrincipal, spiceLoan, duration):
        agentID = agent.ID
        if agentID not in self.socialNetwork:
            self.addAgentToSocialNetwork(agent)
        self.socialNetwork[agentID]["timesLoaned"] += 1
        agent.addLoanFromAgent(self, timestep, sugarLoan, spiceLoan, duration)
        loan = {"creditor": self.ID, "debtor": agentID, "sugarLoan": sugarLoan, "spiceLoan": spiceLoan, "loanDuration": duration,
                "loanOrigin": timestep}
        self.socialNetwork["debtors"].append(loan)
        self.sugar -= sugarPrincipal
        self.spice -= spicePrincipal
        agent.sugar = agent.sugar + sugarPrincipal
        agent.spice = agent.spice + spicePrincipal

    def addLoanFromAgent(self, agent, timestep, sugarLoan, spiceLoan, duration):
        agentID = agent.ID
        if agentID not in self.socialNetwork:
            self.addAgentToSocialNetwork(agent)
        self.socialNetwork[agentID]["timesLoaned"] += 1
        loan = {"creditor": agentID, "debtor": self.ID, "sugarLoan": sugarLoan, "spiceLoan": spiceLoan, "loanDuration": duration,
                "loanOrigin": timestep}
        self.socialNetwork["creditors"].append(loan)

    def canReachCell(self, cell):
        for seenCell in self.cellsInRange:
            if seenCell["cell"] == cell:
                return True
        return False

    def canTradeWithNeighbor(self, neighbor):
        # If both trying to sell the same commodity, stop trading
        if neighbor.marginalRateOfSubstitution >= 1 and self.marginalRateOfSubstitution >= 1:
            return False
        elif neighbor.marginalRateOfSubstitution < 1 and self.marginalRateOfSubstitution < 1:
            return False
        elif neighbor.marginalRateOfSubstitution == self.marginalRateOfSubstitution:
            return False

    def catchDisease(self, disease):
        diseaseID = disease.ID
        for currDisease in self.diseases:
            currDiseaseID = currDisease["disease"].ID
            # If currently sick with this disease, do not contract it again
            if diseaseID == currDiseaseID:
                return
        diseaseInImmuneSystem = self.findNearestHammingDistanceInDisease(disease)
        hammingDistance = diseaseInImmuneSystem["distance"]
        # If immune to disease, do not contract it
        if hammingDistance == 0:
            return
        startIndex = diseaseInImmuneSystem["start"]
        endIndex = diseaseInImmuneSystem["end"]
        caughtDisease = {"disease": disease, "startIndex": startIndex, "endIndex": endIndex}
        self.diseases.append(caughtDisease)
        self.updateDiseaseEffects(disease)
        disease.agent = self

    def collectResourcesAtCell(self):
        sugarCollected = self.cell.sugar
        spiceCollected = self.cell.spice
        self.sugar += sugarCollected
        self.spice += spiceCollected
        self.wealth += sugarCollected + spiceCollected
        self.updateMeanIncome(sugarCollected, spiceCollected)
        self.cell.doSugarProductionPollution(sugarCollected)
        self.cell.doSpiceProductionPollution(spiceCollected)
        self.cell.resetSugar()
        self.cell.resetSpice()

    def defaultOnLoan(self, loan):
        for creditor in self.socialNetwork["creditors"]:
            continue
        return

    def doAging(self):
        if self.alive == False:
            return
        self.age += 1
        # Die if reached max age and if not infinitely-lived
        if self.age >= self.maxAge and self.maxAge != -1:
            self.doDeath("aging")

    def doCombat(self, cell):
        prey = cell.agent
        if prey != None and prey != self:
            maxCombatLoot = self.cell.environment.maxCombatLoot
            preySugar = prey.sugar
            preySpice = prey.spice
            sugarLoot = min(maxCombatLoot, preySugar)
            spiceLoot = min(maxCombatLoot, preySpice)
            self.sugar += sugarLoot
            self.spice += spiceLoot
            self.wealth = self.sugar + self.spice
            prey.sugar -= sugarLoot
            prey.spice -= spiceLoot
            prey.doDeath("combat")
        self.gotoCell(cell)

    def doDeath(self, causeOfDeath):
        self.alive = False
        self.causeOfDeath = causeOfDeath
        self.resetCell()
        self.doInheritance()

        # Keep only debtors and children in social network to handle outstanding loans
        self.socialNetwork = {"debtors": self.socialNetwork["debtors"], "children": self.socialNetwork["children"]}
        self.neighborhood = []
        self.vonNeumannNeighbors = {}
        self.mooreNeighbors = {}

    def doDisease(self):
        diseases = self.diseases
        for diseaseRecord in diseases:
            diseaseTags = diseaseRecord["disease"].tags
            start = diseaseRecord["startIndex"]
            end = diseaseRecord["endIndex"] + 1
            immuneResponse = [self.immuneSystem[i] for i in range(diseaseRecord["startIndex"], diseaseRecord["endIndex"] + 1)]
            i = start
            j = 0
            for i in range(len(diseaseTags)):
                if immuneResponse[i] != diseaseTags[i]:
                    self.immuneSystem[start + i] = diseaseTags[i]
                    break
            immuneResponseCheck = [self.immuneSystem[i] for i in range(diseaseRecord["startIndex"], diseaseRecord["endIndex"] + 1)]
            if diseaseTags == immuneResponseCheck:
                self.diseases.remove(diseaseRecord)
                self.updateDiseaseEffects(diseaseRecord["disease"])

        diseaseCount = len(self.diseases)
        if diseaseCount == 0:
            return
        neighborCells = self.cell.neighbors
        neighbors = []
        for neighborCell in neighborCells:
            neighbor = neighborCell.agent
            if neighbor != None and neighbor.isAlive() == True:
                neighbors.append(neighbor)
        random.shuffle(neighbors)
        for neighbor in neighbors:
            self.spreadDisease(neighbor, self.diseases[random.randrange(diseaseCount)]["disease"])

    def doInheritance(self):
        if self.inheritancePolicy == "none":
            return
        # Provide inheritance for living children/sons/daughters/friends
        livingChildren = []
        livingSons = []
        livingDaughters = []
        livingFriends = []
        for child in self.socialNetwork["children"]:
            if child.isAlive() == True:
                livingChildren.append(child)
                childSex = child.sex
                if childSex == "male":
                    livingSons.append(child)
                elif childSex == "female":
                    livingDaughters.append(child)
        for friend in self.socialNetwork["friends"]:
            if friend["friend"].isAlive() == True:
                livingFriends.append(friend["friend"])

        if self.inheritancePolicy == "children" and len(livingChildren) > 0:
            sugarInheritance = self.sugar / len(livingChildren)
            spiceInheritance = self.spice / len(livingChildren)
            for child in livingChildren:
                child.sugar = child.sugar + sugarInheritance
                child.spice = child.spice + spiceInheritance
                self.sugar -= sugarInheritance
                self.spice -= spiceInheritance
        elif self.inheritancePolicy == "sons" and len(livingSons) > 0:
            sugarInheritance = self.sugar / len(livingSons)
            spiceInheritance = self.spice / len(livingSons)
            for son in livingSons:
                son.sugar = son.sugar + sugarInheritance
                son.spice = son.spice + spiceInheritance
                self.sugar -= sugarInheritance
                self.spice -= spiceInheritance
        elif self.inheritancePolicy == "daughters" and len(livingDaughters) > 0:
            sugarInheritance = self.sugar / len(livingDaughters)
            spiceInheritance = self.spice / len(livingDaughters)
            for daughter in livingDaughters:
                daughter.sugar = daughter.sugar + sugarInheritance
                daughter.spice = daughter.spice + spiceInheritance
                self.sugar -= sugarInheritance
                self.spice -= spiceInheritance
        elif self.inheritancePolicy == "friends" and len(livingFriends) > 0:
            sugarInheritance = self.sugar / len(livingFriends)
            spiceInheritance = self.spice / len(livingFriends)
            for friend in livingFriends:
                friend.sugar = friend.sugar + sugarInheritance
                friend.spice = friend.spice + spiceInheritance
                self.sugar -= sugarInheritance
                self.spice -= spiceInheritance

    def doLending(self):
        self.updateLoans()
        # If not a lender, skip lending
        if self.isLender() == False:
            return
        # Maximum interest rate of 100%
        interestRate = min(1, self.lendingFactor * self.baseInterestRate)
        neighbors = self.cell.findNeighborAgents()
        borrowers = []
        for neighbor in neighbors:
            if neighbor.isAlive() == False:
                continue
            elif neighbor.isBorrower() == True:
                borrowers.append(neighbor)
        random.shuffle(borrowers)
        spiceMetabolism = self.findSpiceMetabolism()
        sugarMetabolism = self.findSugarMetabolism()
        for borrower in borrowers:
            maxSugarLoan = self.sugar / 2
            maxSpiceLoan = self.spice / 2
            if self.isFertile() == True:
                maxSugarLoan = max(0, self.sugar - self.startingSugar)
                maxSpiceLoan = max(0, self.spice - self.startingSpice)
            # If not enough excess wealth to lend, stop lending
            if maxSugarLoan == 0 and maxSpiceLoan == 0:
                return
            sugarLoanNeed = max(0, borrower.startingSugar - borrower.sugar)
            spiceLoanNeed = max(0, borrower.startingSpice - borrower.spice)
            # Find sugar and spice loans
            sugarLoanPrincipal = min(maxSugarLoan, sugarLoanNeed)
            spiceLoanPrincipal = min(maxSpiceLoan, spiceLoanNeed)
            sugarLoanAmount = sugarLoanPrincipal + (sugarLoanPrincipal * interestRate)
            spiceLoanAmount = spiceLoanPrincipal + (spiceLoanPrincipal * interestRate)
            # If no loan needed within significant figures or lender excess resources exhausted
            if (sugarLoanNeed == 0 and spiceLoanNeed == 0) or (sugarLoanAmount == 0 and spiceLoanAmount == 0):
                continue
            # If lending would cause lender to starve, skip lending to potential borrower
            elif self.sugar - sugarLoanPrincipal <= sugarMetabolism or self.spice - spiceLoanPrincipal <= spiceMetabolism:
                continue
            elif borrower.isCreditWorthy(sugarLoanAmount, spiceLoanAmount, self.loanDuration) == True:
                if "all" in self.debug or "agent" in self.debug:
                    print("Agent {0} lending [{1},{2}]".format(self.ID, sugarLoanAmount, spiceLoanAmount))
                self.addLoanToAgent(borrower, self.lastMoved, sugarLoanPrincipal, sugarLoanAmount, spiceLoanPrincipal, spiceLoanAmount, self.loanDuration)

    def doMetabolism(self):
        if self.alive == False:
            return
        spiceMetabolism = self.findSpiceMetabolism()
        sugarMetabolism = self.findSugarMetabolism()
        self.sugar -= sugarMetabolism
        self.spice -= spiceMetabolism
        self.cell.doSugarConsumptionPollution(sugarMetabolism)
        self.cell.doSpiceConsumptionPollution(spiceMetabolism)
        if (self.sugar < 1 and sugarMetabolism > 0) or (self.spice < 1 and spiceMetabolism > 0):
            self.doDeath("starvation")

    def doReproduction(self):
        # Agent marked for removal or not interested in reproduction should not reproduce
        if self.alive == False or self.isFertile() == False:
            return
        neighborCells = self.cell.neighbors
        random.shuffle(neighborCells)
        emptyCells = self.findEmptyNeighborCells()
        for neighborCell in neighborCells:
            neighbor = neighborCell.agent
            if neighbor != None:
                neighborCompatibility = self.isNeighborReproductionCompatible(neighbor)
                emptyCellsWithNeighbor = emptyCells + neighbor.findEmptyNeighborCells()
                random.shuffle(emptyCellsWithNeighbor)
                if self.isFertile() == True and neighborCompatibility == True and len(emptyCellsWithNeighbor) != 0:
                    emptyCell = emptyCellsWithNeighbor.pop()
                    while emptyCell.agent != None and len(emptyCellsWithNeighbor) != 0:
                        emptyCell = emptyCellsWithNeighbor.pop()
                    # If no adjacent empty cell is found, skip reproduction with this neighbor
                    if emptyCell.agent != None:
                        continue
                    childEndowment = self.findChildEndowment(neighbor)
                    child = self.addChildToCell(neighbor, emptyCell, childEndowment)
                    self.socialNetwork["children"].append(child)
                    childID = child.ID
                    neighborID = neighbor.ID
                    self.addAgentToSocialNetwork(child)
                    neighbor.addAgentToSocialNetwork(child)
                    neighbor.updateTimesVisitedWithAgent(self, self.lastMoved)
                    neighbor.updateTimesReproducedWithAgent(self, self.lastMoved)
                    self.updateTimesReproducedWithAgent(neighbor, self.lastMoved)
                    self.lastReproduced += 1

                    sugarCost = self.startingSugar / (self.fertilityFactor * 2)
                    spiceCost = self.startingSpice / (self.fertilityFactor * 2)
                    mateSugarCost = neighbor.startingSugar / (neighbor.fertilityFactor * 2)
                    mateSpiceCost = neighbor.startingSpice / (neighbor.fertilityFactor * 2)
                    self.sugar -= sugarCost
                    self.spice -= spiceCost
                    neighbor.sugar = neighbor.sugar - mateSugarCost
                    neighbor.spice = neighbor.spice - mateSpiceCost
                    self.lastReproduced = self.cell.environment.sugarscape.timestep
                    if "all" in self.debug or "agent" in self.debug:
                        print("Agent {0} reproduced with agent {1} at cell ({2},{3})".format(self.ID, str(neighbor), emptyCell.x, emptyCell.y))

    def doTagging(self):
        if self.tags == None or self.alive == False:
            return
        neighborCells = self.cell.neighbors
        random.shuffle(neighborCells)
        for neighborCell in neighborCells:
            neighbor = neighborCell.agent
            if neighbor != None:
                position = random.randrange(len(self.tags))
                neighbor.flipTag(position, self.tags[position])
                neighbor.tribe = neighbor.findTribe()

    def doTimestep(self, timestep):
        self.timestep = timestep
        # Prevent dead or already moved agent from moving
        if self.alive == True and self.lastMoved != self.timestep:
            self.lastSugar = self.sugar
            self.lastSpice = self.spice
            self.lastMoved = self.timestep
            self.doUniversalIncome()
            self.moveToBestCell()
            self.updateNeighbors()
            self.collectResourcesAtCell()
            self.doMetabolism()
            # If dead from metabolism, skip remainder of timestep
            if self.alive == False:
                return
            self.doTagging()
            self.doTrading()
            self.doReproduction()
            self.doLending()
            self.doDisease()
            self.doAging()
            # If dead from aging, skip remainder of timestep
            if self.alive == False:
                return
            self.updateHappiness()

    def doUniversalIncome(self):
        if (self.timestep - self.lastUniversalSpiceIncomeTimestep) >= self.cell.environment.universalSpiceIncomeInterval:
            self.spice += self.universalSpice
            self.lastUniversalSpiceIncomeTimestep = self.timestep
        if (self.timestep - self.lastUniversalSugarIncomeTimestep) >= self.cell.environment.universalSugarIncomeInterval:
            self.sugar += self.universalSugar
            self.lastUniversalSugarIncomeTimestep = self.timestep

    def doTrading(self):
        # If not a trader, skip trading
        if self.tradeFactor == 0:
            return
        self.tradeVolume = 0
        self.sugarPrice = 0
        self.spicePrice = 0
        self.findMarginalRateOfSubstitution()
        neighborCells = self.cell.neighbors
        traders = []
        for neighborCell in neighborCells:
            neighbor = neighborCell.agent
            if neighbor != None and neighbor.isAlive() == True:
                neighborMRS = neighbor.marginalRateOfSubstitution
                if neighborMRS != self.marginalRateOfSubstitution:
                    traders.append(neighbor)
        random.shuffle(traders)
        for trader in traders:
            spiceSeller = None
            sugarSeller = None
            tradeFlag = True
            transactions = 0

            while tradeFlag == True:
                traderMRS = trader.marginalRateOfSubstitution
                # If both trying to sell the same commodity, stop trading
                if self.canTradeWithNeighbor(trader) == False:
                    tradeFlag = False
                    continue

                # MRS > 1 indicates the agent has less need of spice and should become the spice seller
                if traderMRS > self.marginalRateOfSubstitution:
                    spiceSeller = trader
                    sugarSeller = self
                else:
                    spiceSeller = self
                    sugarSeller = trader
                spiceSellerMRS = spiceSeller.marginalRateOfSubstitution
                sugarSellerMRS = sugarSeller.marginalRateOfSubstitution

                # Find geometric mean of spice and sugar seller MRS for trade price
                tradePrice = math.sqrt(spiceSellerMRS * sugarSellerMRS)
                sugarPrice = 0
                spicePrice = 0
                # Set proper highest value commodity based on trade price
                if tradePrice < 1:
                    spicePrice = 1
                    sugarPrice = tradePrice
                else:
                    spicePrice = tradePrice
                    sugarPrice = 1

                # If trade would be lethal, skip it
                if spiceSeller.spice - spicePrice < spiceSeller.spiceMetabolism or sugarSeller.sugar - sugarPrice < sugarSeller.sugarMetabolism:
                    tradeFlag = False
                    continue
                spiceSellerNewMRS = spiceSeller.findNewMarginalRateOfSubstitution(spiceSeller.sugar + sugarPrice, spiceSeller.spice - spicePrice)
                sugarSellerNewMRS = sugarSeller.findNewMarginalRateOfSubstitution(sugarSeller.sugar - sugarPrice, sugarSeller.spice + spicePrice)

                # Calculate absolute difference from perfect spice/sugar parity in MRS and change in agent welfare
                betterSpiceSellerMRS = abs(1 - spiceSellerMRS) > abs(1 - spiceSellerNewMRS)
                betterSugarSellerMRS = abs(1 - sugarSellerMRS) > abs(1 - sugarSellerNewMRS)
                betterSpiceSellerWelfare = spiceSeller.findWelfare(sugarPrice, (-1 * spicePrice)) >= spiceSeller.findWelfare(0, 0)
                betterSugarSellerWelfare = sugarSeller.findWelfare((-1 * sugarPrice), spicePrice) >= sugarSeller.findWelfare(0, 0)
                # If either MRS or welfare is improved, mark the trade as better for agent
                betterForSpiceSeller = betterSpiceSellerMRS or betterSpiceSellerWelfare
                betterForSugarSeller = betterSugarSellerMRS or betterSugarSellerWelfare

                # Check that spice seller's new MRS does not cross over sugar seller's new MRS
                # Evaluates to False for successful trades
                checkForMRSCrossing = spiceSellerNewMRS < sugarSellerNewMRS
                if betterForSpiceSeller == True and betterForSugarSeller == True and checkForMRSCrossing == False:
                    if "all" in self.debug or "agent" in self.debug:
                        print("Agent {0} trading [{1}, {2}]".format(self.ID, sugarPrice, spicePrice))
                    spiceSeller.sugar += sugarPrice
                    spiceSeller.spice -= spicePrice
                    sugarSeller.sugar -= sugarPrice
                    sugarSeller.spice += spicePrice
                    spiceSeller.findMarginalRateOfSubstitution()
                    sugarSeller.findMarginalRateOfSubstitution()
                    transactions += 1
                else:
                    tradeFlag = False
                    continue
            # If a trade occurred, log it
            if spiceSeller != None and sugarSeller != None:
                self.tradeVolume += 1
                self.sugarPrice += sugarPrice
                self.spicePrice += spicePrice
                trader.updateTimesTradedWithAgent(self, self.lastMoved, transactions)
                self.updateTimesTradedWithAgent(trader, self.lastMoved, transactions)

    def findAgentWealthAtCell(self, cell):
        agent = cell.agent
        if agent == None:
            return 0
        else:
            return agent.wealth

    def findAggression(self):
        return self.aggressionFactor + self.aggressionFactorModifier

    def findBestCell(self):
        self.findNeighborhood()
        retaliators = self.findRetaliatorsInVision()
        random.shuffle(self.cellsInRange)

        bestCell = None
        bestRange = max(self.cell.environment.height, self.cell.environment.width)
        bestWealth = 0
        agentX = self.cell.x
        agentY = self.cell.y
        combatMaxLoot = self.cell.environment.maxCombatLoot
        wraparound = self.findVision() + 1
        potentialCells = []
        aggression = self.findAggression()

        for currCell in self.cellsInRange:
            cell = currCell["cell"]
            travelDistance = currCell["distance"]

            if cell.isOccupied() == True and aggression == 0:
                continue
            prey = cell.agent
            # Avoid attacking agents ineligible to attack
            if prey != None and self.isNeighborValidPrey(prey) == False:
                continue
            preyTribe = prey.tribe if prey != None else "empty"
            preyWealth = prey.wealth if prey != None else 0
            preySugar = prey.sugar if prey != None else 0
            preySpice = prey.spice if prey != None else 0
            # Aggression factor may lead agent to see more reward than possible meaning combat itself is a reward
            welfarePreySugar = aggression * min(combatMaxLoot, preySugar)
            welfarePreySpice = aggression * min(combatMaxLoot, preySpice)

            cellWealth = 0
            # Modify value of cell relative to the metabolism needs of the agent
            welfare = self.findWelfare((cell.sugar + welfarePreySugar), (cell.spice + welfarePreySpice))
            cellWealth = welfare / (1 + cell.pollution)

            # Avoid attacking agents protected via retaliation
            if prey != None and retaliators[preyTribe] > self.wealth + cellWealth:
                continue

            if bestCell == None:
                bestCell = cell
                bestRange = travelDistance
                bestWealth = cellWealth

            # Select closest cell with the most resources
            if cellWealth > bestWealth or (cellWealth == bestWealth and travelDistance < bestRange):
                bestRange = travelDistance
                bestCell = cell
                bestWealth = cellWealth

            cellRecord = {"cell": cell, "wealth": cellWealth, "range": travelDistance}
            potentialCells.append(cellRecord)

        if self.decisionModelFactor > 0:
            bestCell = self.findBestEthicalCell(potentialCells, bestCell)
        if bestCell == None:
            bestCell = self.cell
        if "all" in self.debug or "agent" in self.debug:
            print("Agent {0} moving to ({1},{2})".format(self.ID, bestCell.x, bestCell.y))
        return bestCell

    def findBestEthicalCell(self, cells, greedyBestCell=None):
        if len(cells) == 0:
            return None
        bestCell = None
        cells = self.sortCellsByWealth(cells)
        if "all" in self.debug or "agent" in self.debug:
            self.printCellScores(cells)
        # If not an ethical agent, return top selfish choice
        if self.decisionModel == "none":
            return greedyBestCell

        for cell in cells:
            ethicalScore = self.findEthicalValueOfCell(cell["cell"])
            cell["wealth"] = ethicalScore
        for cell in cells:
            if cell["wealth"] > 0:
                bestCell = cell["cell"]
                break

        # If additional ordering consideration, select new best cell
        if "Top" in self.decisionModel:
            cells = self.sortCellsByWealth(cells)
            if "all" in self.debug or "agent" in self.debug:
                self.printEthicalCellScores(cells)
            bestCell = cells[0]["cell"]

        if bestCell == None:
            if greedyBestCell == None:
                bestCell = cells[0]["cell"]
            else:
                bestCell = greedyBestCell
            if "all" in self.debug or "agent" in self.debug:
                print("Agent {0} could not find an ethical cell".format(self.ID))
        return bestCell

    def findBestFriend(self):
        if self.tags == None:
            return None
        minHammingDistance = len(self.tags)
        bestFriend = None
        for friend in self.socialNetwork["friends"]:
            # If already a friend, update Hamming Distance
            if friend["hammingDistance"] < minHammingDistance:
                bestFriend = friend
                minHammingDistance = friend["hammingDistance"]
        return bestFriend

    def findCellsInRange(self, newCell=None):
        cell = self.cell if newCell == None else newCell
        vision = self.findVision()
        movement = self.findMovement()
        cellRange = min(vision, movement)
        if cellRange > 0:
            if (self.visionMode == "cardinal" and cellRange == vision) or (self.movementMode == "cardinal" and cellRange == movement):
                allCells = self.cell.environment.findCellsInCardinalRange(cell.x, cell.y, cellRange)
            else:
                allCells = self.cell.environment.findCellsInRadialRange(cell.x, cell.y, cellRange)
            if newCell == None:
                self.cellsInRange = allCells
            return allCells
        return []

    def findChildEndowment(self, mate):
        parentEndowments = {
        "aggressionFactor": [self.aggressionFactor, mate.aggressionFactor],
        "baseInterestRate": [self.baseInterestRate, mate.baseInterestRate],
        "decisionModelFactor": [self.decisionModelFactor, mate.decisionModelFactor],
        "decisionModel": [self.decisionModel, mate.decisionModel],
        "fertilityAge": [self.fertilityAge, mate.fertilityAge],
        "fertilityFactor": [self.fertilityFactor, mate.fertilityFactor],
        "infertilityAge": [self.infertilityAge, mate.infertilityAge],
        "inheritancePolicy": [self.inheritancePolicy, mate.inheritancePolicy],
        "lendingFactor": [self.lendingFactor, mate.lendingFactor],
        "loanDuration": [self.loanDuration, mate.loanDuration],
        "lookaheadFactor": [self.lookaheadFactor, mate.lookaheadFactor],
        "maxAge": [self.maxAge, mate.maxAge],
        "maxFriends": [self.maxFriends, mate.maxFriends],
        "movement": [self.movement, mate.movement],
        "movementMode": [self.movementMode, mate.movementMode],
        "selfishnessFactor" : [self.selfishnessFactor, mate.selfishnessFactor],
        "spiceMetabolism": [self.spiceMetabolism, mate.spiceMetabolism],
        "sugarMetabolism": [self.sugarMetabolism, mate.sugarMetabolism],
        "sex": [self.sex, mate.sex],
        "tradeFactor": [self.tradeFactor, mate.tradeFactor],
        "vision": [self.vision, mate.vision],
        "visionMode": [self.visionMode, mate.visionMode],
        "universalSpice": [self.universalSpice, mate.universalSpice],
        "universalSugar": [self.universalSugar, mate.universalSugar]
        }
        childEndowment = {"seed": self.seed}
        randomNumberReset = random.getstate()
        # Map configuration to a random number via hash to make random number generation independent of iteration order
        if self.childEndowmentHashes == None:
            self.childEndowmentHashes = {}
            for config in parentEndowments:
                hashed = hashlib.md5(config.encode())
                hashNum = int(hashed.hexdigest(), 16)
                self.childEndowmentHashes[config] = hashNum

        for endowment in parentEndowments:
            random.seed(self.childEndowmentHashes[endowment] + self.timestep)
            endowmentValue = parentEndowments[endowment][random.randrange(2)]
            childEndowment[endowment] = endowmentValue

        # Each parent gives a portion of their starting endowment for child endowment
        childStartingSugar = (self.startingSugar / (self.fertilityFactor * 2)) + (mate.startingSugar / (mate.fertilityFactor * 2))
        childStartingSpice = (self.startingSpice / (self.fertilityFactor * 2)) + (mate.startingSpice / (mate.fertilityFactor * 2))
        childEndowment["sugar"] = childStartingSugar
        childEndowment["spice"] = childStartingSpice

        hashed = hashlib.md5("tags".encode())
        hashNum = int(hashed.hexdigest(), 16)
        random.seed(hashNum + self.timestep)
        childTags = []
        childImmuneSystem = []
        mateTags = mate.tags
        mismatchBits = [0, 1]
        if self.tags == None:
            childTags = None
        else:
            for i in range(len(self.tags)):
                if self.tags[i] == mateTags[i]:
                    childTags.append(self.tags[i])
                else:
                    childTags.append(mismatchBits[random.randrange(2)])
        childEndowment["tags"] = childTags

        hashed = hashlib.md5("immuneSystem".encode())
        hashNum = int(hashed.hexdigest(), 16)
        random.seed(hashNum + self.timestep)
        if self.startingImmuneSystem == None:
            childImmuneSystem = None
        else:
            for i in range(len(self.immuneSystem)):
                if self.startingImmuneSystem[i] == mate.startingImmuneSystem[i]:
                    childImmuneSystem.append(self.startingImmuneSystem[i])
                else:
                    childImmuneSystem.append(mismatchBits[random.randrange(2)])
        childEndowment["immuneSystem"] = childImmuneSystem
        random.setstate(randomNumberReset)
        return childEndowment

    def findConflictHappiness(self):
        if self.lastDoneCombat == self.cell.environment.sugarscape.timestep:
            if(self.findAggression() > 1):
                return 1
            else:
                return -0.5
        return 0

    def findCurrentSpiceDebt(self):
        spiceDebt = 0
        for creditor in self.socialNetwork["creditors"]:
            spiceDebt += creditor["spiceLoan"] / creditor["loanDuration"]
        return spiceDebt

    def findCurrentSugarDebt(self):
        sugarDebt = 0
        for creditor in self.socialNetwork["creditors"]:
            sugarDebt += creditor["sugarLoan"] / creditor["loanDuration"]
        return sugarDebt

    def findTimeToLive(self, ageLimited=False):
        spiceMetabolism = self.findSpiceMetabolism()
        sugarMetabolism = self.findSugarMetabolism()
        # If no sugar or spice metabolism, set days to death for that resource to seemingly infinite
        sugarTimeToLive = self.sugar / sugarMetabolism if sugarMetabolism > 0 else sys.maxsize
        spiceTimeToLive = self.spice / spiceMetabolism if spiceMetabolism > 0 else sys.maxsize
        timeToLive = min(sugarTimeToLive, spiceTimeToLive)
        if ageLimited == True:
            timeToLive = min(timeToLive, self.maxAge - self.age)
        return timeToLive

    def findEmptyNeighborCells(self):
        emptyCells = []
        neighborCells = self.cell.neighbors
        for neighborCell in neighborCells:
            if neighborCell.agent == None:
                emptyCells.append(neighborCell)
        return emptyCells

    def findFamilyHappiness(self):
        familyHappiness = 0
        if self.lastReproduced == self.timestep:
            familyHappiness = 0.5
        for child in self.socialNetwork["children"]:
            if child.isAlive() == False and familyHappiness != -1:
                familyHappiness -= 0.125
            if child.isAlive() == True and familyHappiness < 1:
                if child.isSick():
                    familyHappiness -= 0.05
                else:
                    familyHappiness += 0.05
        return familyHappiness

    def findHammingDistanceInTags(self, neighbor):
        if self.tags == None:
            return 0
        neighborTags = neighbor.tags
        hammingDistance = 0
        for i in range(len(self.tags)):
            if self.tags[i] != neighborTags[i]:
                hammingDistance += 1
        return hammingDistance

    def findHappiness(self):
        return self.findWealthHappiness() + self.findConflictHappiness() + self.findFamilyHappiness() + self.findSocialHappiness() + self.findHealthHappiness()

    def findHealthHappiness(self):
        if self.isSick():
            return -1
        else:
            return 1

    def findMarginalRateOfSubstitution(self):
        spiceMetabolism = self.findSpiceMetabolism()
        sugarMetabolism = self.findSugarMetabolism()
        spiceNeed = self.spice / spiceMetabolism if spiceMetabolism > 0 else 1
        sugarNeed = self.sugar / sugarMetabolism if sugarMetabolism > 0 else 1
        # Trade factor may increase amount of spice traded for sugar in a transaction
        self.marginalRateOfSubstitution = self.tradeFactor * (spiceNeed / sugarNeed)

    def findMovement(self):
        return max(0, self.movement + self.movementModifier)

    def findNearestHammingDistanceInDisease(self, disease):
        if self.immuneSystem == None:
            return 0
        diseaseTags = disease.tags
        diseaseLength = len(diseaseTags)
        bestHammingDistance = diseaseLength
        bestRange = [0, diseaseLength - 1]
        for i in range(len(self.immuneSystem) - diseaseLength):
            hammingDistance = 0
            for j in range(diseaseLength):
                if self.immuneSystem[i + j] != diseaseTags[j]:
                    hammingDistance += 1
            if hammingDistance < bestHammingDistance:
                bestHammingDistance = hammingDistance
                bestRange = [i, i + (diseaseLength - 1)]
        diseaseStats = {"distance": bestHammingDistance, "start": bestRange[0], "end": bestRange[1]}
        return diseaseStats

    def findNeighborhood(self, newCell=None):
        newNeighborhood = self.findCellsInRange(newCell)
        neighborhood = []
        for neighborCell in newNeighborhood:
            neighbor = neighborCell["cell"].agent
            if neighbor != None and neighbor.isAlive() == True:
                neighborhood.append(neighbor)
        neighborhood.append(self)
        if newCell == None:
            self.neighborhood = neighborhood
        return neighborhood

    def findNewMarginalRateOfSubstitution(self, sugar, spice):
        spiceMetabolism = self.findSpiceMetabolism()
        sugarMetabolism = self.findSugarMetabolism()
        spiceNeed = spice / spiceMetabolism if spiceMetabolism > 0 else 1
        sugarNeed = sugar / sugarMetabolism if sugarMetabolism > 0 else 1
        # If zero metabolism, do not try to trade
        if spiceNeed == 1 and sugarNeed == 1:
            return 1
        # If no sugar or no spice, make missing resource the maximum need in MRS
        elif spiceNeed == 0:
            return spiceMetabolism
        elif sugarNeed == 0:
            return 1 / sugarMetabolism
        return spiceNeed / sugarNeed

    # TODO: Tally factors of hedons/dolors for given cell
    def findPotentialNiceOfCell(self, cell):
        potentialMates = []
        # TODO: Trading nice capped at max number of resources traded to achieve MRS of 1
        potentialTraders = []
        # TODO: Lending nice capped at max amount of wealth agent can lend
        potentialBorrowers = []
        # TODO: Combat nice capped at wealth agent can score for tribe/neighborhood/etc.
        potentialPrey = []
        cellNeighborAgents = cell.findNeighborAgents()
        aggression = self.findAggression()
        for agent in cellNeighborAgents:
            if agent.isAlive() == False:
                continue
            if self.isFertile() == True:
                neighborCompatibility = self.isNeighborReproductionCompatible(agent)
                emptyNeighborCells = agent.findEmptyNeighborCells()
                if neighborCompatibility == True and len(emptyNeighborCells) != 0:
                    potentialMates.append(agent)
            if self.isLender() == True and agent.isBorrower() == True:
                potentialBorrowers.append(agent)
            if self.tradeFactor > 0 and agent.tradeFactor > 0 and self.canTradeWithNeighbor(agent) == True:
                potentialTraders.append(agent)
            if aggression > 0 and self.tribe != agent.tribe and self.wealth >= agent.wealth:
                potentialPrey.append(agent)
        # TODO: Make nice calculation more fine-grained than just potentialities
        reproductionSugarCost = self.startingSugar / (self.fertilityFactor * 2) if self.fertilityFactor > 0 else 0
        reproductionSpiceCost = self.startingSpice / (self.fertilityFactor * 2) if self.fertilityFactor > 0 else 0
        maxReproductionAttemptsByResources = min(reproductionSugarCost, reproductionSpiceCost)
        potentialMates = min(len(potentialMates), maxReproductionAttemptsByResources)
        potentialNice = potentialMates + len(potentialTraders + potentialBorrowers + potentialPrey)
        return potentialNice

    def findRetaliatorsInVision(self):
        retaliators = {}
        for cell in self.cellsInRange:
            agent = cell["cell"].agent
            if agent != None:
                if agent.tribe not in retaliators:
                    retaliators[agent.tribe] = agent.wealth
                elif retaliators[agent.tribe] < agent.wealth:
                    retaliators[agent.tribe] = agent.wealth
        return retaliators

    def findSocialHappiness(self):
        if len(self.socialNetwork["friends"]) < 1:
            return -0.8
        elif len(self.socialNetwork["friends"]) < 2:
            return -0.7
        elif len(self.socialNetwork["friends"]) < 3:
            return -0.5
        elif len(self.socialNetwork["friends"]) <= len(self.socialNetwork["creditors"]):
            return -0.3
        elif len(self.socialNetwork["friends"]) <= len(self.socialNetwork["debtors"]):
            return -0.1
        else:
            if len(self.socialNetwork["friends"]) * 0.1 < 1:
                return len(self.socialNetwork["friends"]) * 0.1
            else:
                return 1

    def findSpiceMetabolism(self):
        return max(0, self.spiceMetabolism + self.spiceMetabolismModifier)

    def findSugarMetabolism(self):
        return max(0, self.sugarMetabolism + self.sugarMetabolismModifier)

    def findTribe(self):
        if self.tags == None:
            return None
        sugarscape = self.cell.environment.sugarscape
        numTribes = sugarscape.configuration["environmentMaxTribes"]
        zeroes = 0
        tribeCutoff = math.floor(len(self.tags) / numTribes)
        # Up to 11 tribes possible without significant color conflicts
        colors = ["red", "blue", "green", "orange", "purple", "teal", "pink", "mint", "blue2", "yellow", "salmon"]
        for tag in self.tags:
            if tag == 0:
                zeroes += 1
        self.tagZeroes = zeroes
        for i in range(1, numTribes + 1):
            if zeroes < (i * tribeCutoff) + 1 or i == numTribes:
                return colors[i - 1]
        # Default agent coloring
        return "red"

    def findVision(self):
        return max(0, self.vision + self.visionModifier)

    def findWealthHappiness(self):
        if self.cell.environment.sugarscape.runtimeStats["meanWealth"] < 1:
            return 0
        elif(self.wealth < 1):
            return -1
        else:
            if math.log(self.wealth * 0.01, self.cell.environment.sugarscape.runtimeStats["meanWealth"] )*5 > 1:
                return 1
            elif math.log(self.wealth * 0.01, self.cell.environment.sugarscape.runtimeStats["meanWealth"] )*5 < -1:
                return -1
            return (math.log(self.wealth * 0.01, self.cell.environment.sugarscape.runtimeStats["meanWealth"] )*5)

    def findWelfare(self, sugarReward, spiceReward):
        spiceMetabolism = self.findSpiceMetabolism()
        sugarMetabolism = self.findSugarMetabolism()
        totalMetabolism = sugarMetabolism + spiceMetabolism
        sugarMetabolismProportion = 0
        spiceMetabolismProportion = 0
        if totalMetabolism != 0:
            sugarMetabolismProportion = sugarMetabolism / totalMetabolism
            spiceMetabolismProportion = spiceMetabolism / totalMetabolism

        sugarLookahead = sugarMetabolism * self.lookaheadFactor
        spiceLookahead = spiceMetabolism * self.lookaheadFactor
        totalSugar = (self.sugar + sugarReward) - sugarLookahead
        totalSpice = (self.spice + spiceReward) - spiceLookahead
        if totalSugar < 0:
            totalSugar = 0
        if totalSpice < 0:
            totalSpice = 0

        welfare = (totalSugar ** sugarMetabolismProportion) * (totalSpice ** spiceMetabolismProportion)
        if self.tags != None and len(self.tags) > 0:
            # Tribe could have changed since last timestep, so recheck
            self.tribe = self.findTribe()
            fractionZeroesInTags = self.tagZeroes / len(self.tags)
            fractionOnesInTags = 1 - fractionZeroesInTags
            spiceMetabolism = spiceMetabolism if spiceMetabolism > 0 else 1
            sugarMetabolism = sugarMetabolism if sugarMetabolism > 0 else 1
            tagPreferences = (sugarMetabolism * fractionZeroesInTags) + (spiceMetabolism * fractionOnesInTags)
            if tagPreferences == 0:
                tagPreferences = 1
            tagPreferencesSugar = (sugarMetabolism / tagPreferences) * fractionZeroesInTags
            tagPreferencesSpice = (spiceMetabolism / tagPreferences) * fractionOnesInTags
            welfare = (totalSugar ** tagPreferencesSugar) * (totalSpice ** tagPreferencesSpice)
        return welfare

    def flipTag(self, position, value):
        self.tags[position] = value

    def gotoCell(self, cell):
        self.resetCell()
        self.cell = cell
        self.cell.agent = self

    def isAlive(self):
        return self.alive

    def isBorrower(self):
        if self.age >= self.fertilityAge and self.age < self.infertilityAge and self.isFertile() == False:
            return True
        return False

    def isCreditWorthy(self, sugarLoanAmount, spiceLoanAmount, loanDuration):
        if loanDuration == 0:
            return False
        spiceMetabolism = self.findSpiceMetabolism()
        sugarMetabolism = self.findSugarMetabolism()
        sugarLoanCostPerTimestep = sugarLoanAmount / loanDuration
        spiceLoanCostPerTimestep = spiceLoanAmount / loanDuration
        sugarIncomePerTimestep = ((self.sugarMeanIncome - sugarMetabolism) - self.findCurrentSugarDebt()) - sugarLoanCostPerTimestep
        spiceIncomePerTimestep = ((self.spiceMeanIncome - spiceMetabolism) - self.findCurrentSpiceDebt()) - spiceLoanCostPerTimestep
        if sugarIncomePerTimestep >= 0 and spiceIncomePerTimestep >= 0:
            return True
        return False

    def isFertile(self):
        if self.sugar >= self.startingSugar and self.spice >= self.startingSpice and self.age >= self.fertilityAge and self.age < self.infertilityAge and (self.fertilityFactor + self.fertilityFactorModifier) > 0:
            return True
        return False

    def isLender(self):
        # If not a lender, skip lending
        if self.lendingFactor == 0:
            return False
        # Fertile and not enough excess wealth to be a lender
        elif self.isFertile() == True and (self.sugar <= self.startingSugar or self.spice <= self.startingSpice):
            return False
        # Too young to reproduce, skip lending
        elif self.age < self.fertilityAge:
            return False
        return True

    def isNeighborReproductionCompatible(self, neighbor):
        if neighbor == None:
            return False
        neighborSex = neighbor.sex
        neighborFertility = neighbor.isFertile()
        if self.sex == "female" and (neighborSex == "male" and neighborFertility == True):
            return True
        elif self.sex == "male" and (neighborSex == "female" and neighborFertility == True):
            return True
        else:
            return False

    def isNeighborValidPrey(self, neighbor):
        if neighbor == None or self.findAggression() == 0:
            return False
        elif self.tribe != neighbor.tribe and self.wealth >= neighbor.wealth:
            return True
        return False

    def isSick(self):
        if len(self.diseases) > 0:
            return True
        return False

    def moveToBestCell(self):
        bestCell = self.findBestCell()
        if self.findAggression() > 0:
            self.doCombat(bestCell)
        else:
            self.gotoCell(bestCell)

    def payDebt(self, loan):
        creditorID = loan["creditor"]
        creditor = self.socialNetwork[creditorID]["agent"]
        if creditor.isAlive() == False:
            if creditor.inheritancePolicy != "children":
                self.socialNetwork["creditors"].remove(loan)
                creditor.removeDebt(loan)
            else:
                self.payDebtToCreditorChildren(loan)
        elif self.sugar - loan["sugarLoan"] > 0 and self.spice - loan["spiceLoan"] > 0:
            self.sugar -= loan["sugarLoan"]
            self.spice -= loan["spiceLoan"]
            creditor.sugar = creditor.sugar + loan["sugarLoan"]
            creditor.spice = creditor.spice + loan["spiceLoan"]
            self.socialNetwork["creditors"].remove(loan)
            creditor.removeDebt(loan)
        else:
            sugarPayout = self.sugar / 2
            spicePayout = self.spice / 2
            sugarRepaymentLeft = loan["sugarLoan"] - sugarPayout
            spiceRepaymentLeft = loan["spiceLoan"] - spicePayout
            self.sugar -= sugarPayout
            self.spice -= spicePayout
            creditor.sugar = creditor.sugar + sugarPayout
            creditor.spice = creditor.spice + spicePayout
            creditorInterestRate = creditor.lendingFactor * creditor.baseInterestRate
            newSugarLoan = sugarRepaymentLeft + (creditorInterestRate * sugarRepaymentLeft)
            newSpiceLoan = spiceRepaymentLeft + (creditorInterestRate * spiceRepaymentLeft)
            self.socialNetwork["creditors"].remove(loan)
            creditor.removeDebt(loan)
            # Initiate new loan with interest compounded on previous loan and not transferring any new principal
            creditor.addLoanToAgent(self, self.lastMoved, 0, newSugarLoan, 0, newSpiceLoan, creditor.loanDuration)

    def payDebtToCreditorChildren(self, loan):
        creditorID = loan["creditor"]
        creditor = self.socialNetwork[creditorID]["agent"]
        creditorChildren = creditor.socialNetwork["children"]
        livingCreditorChildren = []
        for child in creditorChildren:
            if child.isAlive() == True:
                livingCreditorChildren.append(child)
        numLivingChildren = len(livingCreditorChildren)
        if numLivingChildren > 0:
            sugarRepayment = loan["sugarLoan"] / numLivingChildren
            spiceRepayment = loan["spiceLoan"] / numLivingChildren
            for child in livingCreditorChildren:
                child.addLoanToAgent(self, self.lastMoved, 0, sugarRepayment, 0, spiceRepayment, 1)
        self.socialNetwork["creditors"].remove(loan)
        creditor.removeDebt(loan)

    def printCellScores(self, cells):
        i = 0
        while i < len(cells):
            cell = cells[i]
            cellString = "({0},{1}) [{2},{3}]".format(cell["cell"].x, cell["cell"].y, cell["wealth"], cell["range"])
            print("Cell {0}/{1}: ".format(i + 1, len(cells)) + cellString)
            i += 1

    def printEthicalCellScores(self, cells):
        i = 0
        while i < len(cells):
            cell = cells[i]
            cellString = "({0},{1}) [{2},{3}]".format(cell["cell"].x, cell["cell"].y, cell["wealth"], cell["range"])
            print("Ethical cell {0}/{1}: ".format(i + 1, len(cells)) + cellString)
            i += 1

    def removeDebt(self, loan):
        for debtor in self.socialNetwork["debtors"]:
            if debtor == loan:
                self.socialNetwork["debtors"].remove(debtor)
                return

    def resetCell(self):
        self.cell.resetAgent()
        self.cell = None

    def setFather(self, father):
        fatherID = father.ID
        if fatherID not in self.socialNetwork:
            self.addAgentToSocialNetwork(father)
        self.socialNetwork["father"] = father

    def setMother(self, mother):
        motherID = mother.ID
        if motherID not in self.socialNetwork:
            self.addAgentToSocialNetwork(mother)
        self.socialNetwork["mother"] = mother

    def spawnChild(self, childID, birthday, cell, configuration):
        return Agent(childID, birthday, cell, configuration)

    def spreadDisease(self, agent, disease):
        sugarscape = self.cell.environment.sugarscape
        sugarscape.addDisease(disease, agent)

    def sortCellsByWealth(self, cells):
        # Insertion sort of cells by wealth in descending order with range as a tiebreaker
        i = 0
        while i < len(cells):
            j = i
            while j > 0 and (cells[j - 1]["wealth"] < cells[j]["wealth"] or (cells[j - 1]["wealth"] == cells[j]["wealth"] and cells[j - 1]["range"] > cells[j]["range"])):
                currCell = cells[j]
                cells[j] = cells[j - 1]
                cells[j - 1] = currCell
                j -= 1
            i += 1
        return cells

    def updateDiseaseEffects(self, disease):
        # If disease not in list of diseases, agent has recovered and undo its effects
        recoveryCheck = -1
        for diseaseRecord in self.diseases:
            if disease == diseaseRecord["disease"]:
                recoveryCheck = 1
                break

        sugarMetabolismPenalty = disease.sugarMetabolismPenalty * recoveryCheck
        spiceMetabolismPenalty = disease.spiceMetabolismPenalty * recoveryCheck
        visionPenalty = disease.visionPenalty * recoveryCheck
        movementPenalty = disease.movementPenalty * recoveryCheck
        fertilityPenalty = disease.fertilityPenalty * recoveryCheck
        aggressionPenalty = disease.aggressionPenalty * recoveryCheck

        self.sugarMetabolismModifier += sugarMetabolismPenalty
        self.spiceMetabolismModifier += spiceMetabolismPenalty
        self.visionModifier += visionPenalty
        self.movementModifier += movementPenalty
        self.fertilityFactorModifier += fertilityPenalty
        self.aggressionFactorModifier += aggressionPenalty

    def updateFriends(self, neighbor):
        neighborID = neighbor.ID
        neighborHammingDistance = self.findHammingDistanceInTags(neighbor)
        neighborEntry = {"friend": neighbor, "hammingDistance": neighborHammingDistance}
        if len(self.socialNetwork["friends"]) < self.maxFriends:
            self.socialNetwork["friends"].append(neighborEntry)
        else:
            maxHammingDistance = 0
            maxDifferenceFriend = None
            for friend in self.socialNetwork["friends"]:
                # If already a friend, update Hamming Distance
                if friend["friend"].ID == neighborID:
                    self.socialNetwork["friends"].remove(friend)
                    self.socialNetwork["friends"].append(neighborEntry)
                    return
                if friend["hammingDistance"] > maxHammingDistance:
                    maxDistanceFriend = friend
                    maxHammingDistance = friend["hammingDistance"]
            if maxHammingDistance > neighborHammingDistance:
                self.socialNetwork["friends"].remove(maxDistanceFriend)
                self.socialNetwork["friends"].append(neighborEntry)
        self.socialNetwork["bestFriend"] = self.findBestFriend()

    def updateLoans(self):
        for debtor in self.socialNetwork["debtors"]:
            debtorID = debtor["debtor"]
            debtorAgent = self.socialNetwork[debtorID]["agent"]
            # Cannot collect on debt since debtor is dead
            if debtorAgent.isAlive() == False:
                self.socialNetwork["debtors"].remove(debtor)
        for creditor in self.socialNetwork["creditors"]:
            timeRemaining = (self.lastMoved - creditor["loanOrigin"]) - creditor["loanDuration"]
            if timeRemaining == 0:
                self.payDebt(creditor)

    def updateMooreNeighbors(self):
        for direction, neighbor in self.vonNeumannNeighbors.items():
            self.mooreNeighbors[direction] = neighbor
        north = self.mooreNeighbors["north"]
        south = self.mooreNeighbors["south"]
        east = self.mooreNeighbors["east"]
        west = self.mooreNeighbors["west"]
        self.mooreNeighbors["northeast"] = north.cell.findEastNeighbor() if north != None else None
        self.mooreNeighbors["northeast"] = east.cell.findNorthNeighbor() if east != None and self.mooreNeighbors["northeast"] == None else None
        self.mooreNeighbors["northwest"] = north.cell.findWestNeighbor() if north != None else None
        self.mooreNeighbors["northwest"] = west.cell.findNorthNeighbor() if west != None and self.mooreNeighbors["northwest"] == None else None
        self.mooreNeighbors["southeast"] = south.cell.findEastNeighbor() if south != None else None
        self.mooreNeighbors["southeast"] = east.cell.findSouthNeighbor() if east != None and self.mooreNeighbors["southeast"] == None else None
        self.mooreNeighbors["southwest"] = south.cell.findWestNeighbor() if south != None else None
        self.mooreNeighbors["southwest"] = west.cell.findSouthNeighbor() if west != None and self.mooreNeighbors["southwest"] == None else None

    def updateMarginalRateOfSubstitutionForAgent(self, agent):
        agentID = agent.ID
        if agentID not in self.socialNetwork:
            self.addAgentToSocialNetwork(agent)
        self.socialNetwork[agentID]["marginalRateOfSubstitution"] = agent.marginalRateOfSubstitution

    def updateMeanIncome(self, sugarIncome, spiceIncome):
        # Define weight for moving average
        alpha = 0.05
        self.sugarMeanIncome = (alpha * sugarIncome) + ((1 - alpha) * self.sugarMeanIncome)
        self.spiceMeanIncome = (alpha * spiceIncome) + ((1 - alpha) * self.spiceMeanIncome)

    def updateNeighbors(self):
        self.updateVonNeumannNeighbors()
        self.updateMooreNeighbors()
        self.updateSocialNetwork()

    def updateSocialNetwork(self):
        for direction, neighbor in self.vonNeumannNeighbors.items():
            if neighbor == None:
                continue
            neighborID = neighbor.ID
            if neighborID in self.socialNetwork:
                self.updateTimesVisitedWithAgent(neighbor, self.lastMoved)
                self.updateMarginalRateOfSubstitutionForAgent(neighbor)
            else:
                self.addAgentToSocialNetwork(neighbor)
            self.updateFriends(neighbor)

    def updateTimesReproducedWithAgent(self, agent, timestep):
        agentID = agent.ID
        if agentID not in self.socialNetwork:
            self.addAgentToSocialNetwork(agent)
        self.socialNetwork[agentID]["timesReproduced"] += 1
        self.socialNetwork[agentID]["lastSeen"] = timestep

    def updateTimesTradedWithAgent(self, agent, timestep, transactions=0):
        agentID = agent.ID
        if agentID not in self.socialNetwork:
            self.addAgentToSocialNetwork(agent)
        self.socialNetwork[agentID]["timesTraded"] += transactions
        self.socialNetwork[agentID]["lastSeen"] = timestep

    def updateTimesVisitedWithAgent(self, agent, timestep):
        agentID = agent.ID
        if agentID not in self.socialNetwork:
            self.addAgentToSocialNetwork(agent)
        else:
            self.socialNetwork[agentID]["timesVisited"] += 1
            self.socialNetwork[agentID]["lastSeen"] = timestep

    def updateVonNeumannNeighbors(self):
        self.vonNeumannNeighbors["north"] = self.cell.findNorthNeighbor().agent
        self.vonNeumannNeighbors["south"] = self.cell.findSouthNeighbor().agent
        self.vonNeumannNeighbors["east"] = self.cell.findEastNeighbor().agent
        self.vonNeumannNeighbors["west"] = self.cell.findWestNeighbor().agent

    def updateHappiness(self):
        if self.cell == None:
            print("Agent {0} has no cell and isAlive = {1}".format(self.ID, self.isAlive()))
        self.healthHappiness = self.findHealthHappiness()
        self.wealthHappiness = self.findWealthHappiness()
        self.socialHappiness = self.findSocialHappiness()
        self.familyHappiness = self.findFamilyHappiness()
        self.conflictHappiness = self.findConflictHappiness()
        self.happiness = self.findHappiness()

    def __str__(self):
        return "{0}".format(self.ID)
