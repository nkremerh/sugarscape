import math
import random
import sys

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
        self.__lendingFactor = configuration["lendingFactor"]
        self.__fertilityFactor = configuration["fertilityFactor"]
        self.__baseInterestRate = configuration["baseInterestRate"]
        self.__loanDuration = configuration["loanDuration"]
        self.__maxFriends = configuration["maxFriends"]
        self.__wealth = configuration["sugar"] + configuration["spice"]
        self.__seed = configuration["seed"]
        self.__inheritancePolicy = configuration["inheritancePolicy"]
        self.__startingImmuneSystem = configuration["immuneSystem"]
        self.__immuneSystem = configuration["immuneSystem"]
        self.__ethicalFactor = configuration["ethicalFactor"]

        self.__alive = True
        self.__age = 0
        self.__cellsInVision = []
        self.__neighborhood = []
        self.__lastMoved = -1
        self.__vonNeumannNeighbors = {"north": None, "south": None, "east": None, "west": None}
        self.__mooreNeighbors = {"north": None, "northeast": None, "northwest": None, "south": None, "southeast": None, "southwest": None, "east": None, "west": None}
        self.__socialNetwork = {"father": None, "mother": None, "children": [], "friends": [], "creditors": [], "debtors": []}
        self.__diseases = []
        self.__fertile = False
        self.__tribe = self.findTribe()
        self.__timestep = birthday
        self.__marginalRateOfSubstitution = 1
        self.__tagZeroes = 0
        self.__sugarMeanIncome = 1
        self.__spiceMeanIncome = 1
        self.__nice = 0

    def addChildToCell(self, mate, cell, childConfiguration):
        sugarscape = self.__cell.getEnvironment().getSugarscape()
        childID = sugarscape.generateAgentID()
        child = Agent(childID, self.__timestep, cell, childConfiguration)
        child.setCell(cell)
        sugarscape.addAgent(child)
        child.collectResourcesAtCell()
        if self.__sex == "female":
            child.setMother(self)
            child.setFather(mate)
        else:
            child.setFather(self)
            child.setMother(mate)
        return child

    def addAgentToSocialNetwork(self, agent):
        agentID = agent.getID()
        if agentID in self.__socialNetwork:
            return
        self.__socialNetwork[agentID] = {"agent": agent, "lastSeen": self.__lastMoved, "timesVisited": 1, "timesReproduced": 0,
                                         "timesTraded": 0, "timesLoaned": 0, "marginalRateOfSubstitution": 0}

    def addLoanToAgent(self, agent, timestep, sugarPrincipal, sugarLoan, spicePrincipal, spiceLoan, duration):
        agentID = agent.getID()
        if agentID not in self.__socialNetwork:
            self.addAgentToSocialNetwork(agent)
        self.__socialNetwork[agentID]["timesLoaned"] += 1
        agent.addLoanFromAgent(self, timestep, sugarLoan, spiceLoan, duration)
        loan = {"creditor": self.__id, "debtor": agentID, "sugarLoan": sugarLoan, "spiceLoan": spiceLoan, "loanDuration": duration,
                "loanOrigin": timestep}
        self.__socialNetwork["debtors"].append(loan)
        self.__sugar -= sugarPrincipal
        self.__spice -= spicePrincipal
        agent.setSugar(agent.getSugar() + sugarPrincipal)
        agent.setSpice(agent.getSpice() + spicePrincipal)

    def addLoanFromAgent(self, agent, timestep, sugarLoan, spiceLoan, duration):
        agentID = agent.getID()
        if agentID not in self.__socialNetwork:
            self.addAgentToSocialNetwork(agent)
        self.__socialNetwork[agentID]["timesLoaned"] += 1
        loan = {"creditor": agentID, "debtor": self.__id, "sugarLoan": sugarLoan, "spiceLoan": spiceLoan, "loanDuration": duration,
                "loanOrigin": timestep}
        self.__socialNetwork["creditors"].append(loan)

    def calculateMarginalRateOfSubstitution(self, sugar, spice):
        spiceNeed = spice / self.__spiceMetabolism if self.__spiceMetabolism > 0 else 1
        sugarNeed = sugar / self.__sugarMetabolism if self.__sugarMetabolism > 0 else 1
        # If no sugar or no spice, make missing resource the maximum need in MRS
        if spiceNeed == 0:
            return self.__spiceMetabolism
        elif sugarNeed == 0:
            return 1 / self.__sugarMetabolism
        return spiceNeed / sugarNeed

    def calculateWelfare(self, sugarReward, spiceReward):
        totalMetabolism = self.__sugarMetabolism + self.__spiceMetabolism
        sugarMetabolismProportion = 0
        spiceMetabolismProportion = 0
        if totalMetabolism != 0:
            sugarMetabolismProportion = self.__sugarMetabolism / totalMetabolism
            spiceMetabolismProportion = self.__spiceMetabolism / totalMetabolism

        sugarLookahead = self.__sugarMetabolism * self.__lookaheadFactor
        spiceLookahead = self.__spiceMetabolism * self.__lookaheadFactor
        totalSugar = (self.__sugar + sugarReward) - sugarLookahead
        totalSpice = (self.__spice + spiceReward) - spiceLookahead
        if totalSugar < 0:
            totalSugar = 0
        if totalSpice < 0:
            totalSpice = 0

        welfare = (totalSugar ** sugarMetabolismProportion) * (totalSpice ** spiceMetabolismProportion)
        if self.__tags != None and len(self.__tags) > 0:
            self.findTribe()
            fractionZeroesInTags = self.__tagZeroes / len(self.__tags)
            fractionOnesInTags = 1 - fractionZeroesInTags
            spiceMetabolism = self.__spiceMetabolism if self.__spiceMetabolism != 0 else 1
            sugarMetabolism = self.__sugarMetabolism if self.__sugarMetabolism != 0 else 1
            tagPreferences = (self.__sugarMetabolism * fractionZeroesInTags) + (self.__spiceMetabolism * fractionOnesInTags)
            if tagPreferences == 0:
                tagPreferences = 1
            tagPreferencesSugar = (self.__sugarMetabolism / tagPreferences) * fractionZeroesInTags
            tagPreferencesSpice = (self.__spiceMetabolism / tagPreferences) * fractionOnesInTags
            welfare = (totalSugar ** tagPreferencesSugar) * (totalSpice ** tagPreferencesSpice)
        return welfare

    def canReachCell(self, cell):
        if len(self.__cellsInVision) == 0:
            self.getCellsInVision()
        for seenCell in self.__cellsInVision:
            if seenCell["cell"] == cell:
                return True
        return False

    def catchDisease(self, disease):
        diseaseID = disease.getID()
        for currDisease in self.__diseases:
            currDiseaseID = currDisease["disease"].getID()
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
        self.__diseases.append(caughtDisease)
        self.updateDiseaseEffects(disease)
        disease.setAgent(self)

    def collectResourcesAtCell(self):
        if self.__cell != None:
            sugarCollected = self.__cell.getCurrSugar()
            spiceCollected = self.__cell.getCurrSpice()
            self.__sugar += sugarCollected
            self.__spice += spiceCollected
            self.__wealth += sugarCollected + spiceCollected
            self.updateMeanIncome(sugarCollected, spiceCollected)
            self.__cell.doSugarProductionPollution(sugarCollected)
            self.__cell.doSpiceProductionPollution(spiceCollected)
            self.__cell.resetSugar()
            self.__cell.resetSpice()

    def defaultOnLoan(self, loan):
        for creditor in self.__socialNetwork["creditors"]:
            continue
        return

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
        self.setCell(cell)

    def doDeath(self):
        self.setAlive(False)
        self.unsetCell()
        self.doInheritance()

    def doDisease(self):
        diseases = self.__diseases
        for diseaseRecord in diseases:
            diseaseTags = diseaseRecord["disease"].getTags()
            start = diseaseRecord["startIndex"]
            end = diseaseRecord["endIndex"] + 1
            immuneResponse = [self.__immuneSystem[i] for i in range(diseaseRecord["startIndex"], diseaseRecord["endIndex"] + 1)]
            i = start
            j = 0
            for i in range(len(diseaseTags)):
                if immuneResponse[i] != diseaseTags[i]:
                    self.__immuneSystem[start + i] = diseaseTags[i]
                    break
            immuneResponseCheck = [self.__immuneSystem[i] for i in range(diseaseRecord["startIndex"], diseaseRecord["endIndex"] + 1)]
            if diseaseTags == immuneResponseCheck:
                self.__diseases.remove(diseaseRecord)
                self.updateDiseaseEffects(diseaseRecord["disease"])

        diseaseCount = len(self.__diseases)
        if diseaseCount == 0:
            return
        neighborCells = self.__cell.getNeighbors()
        neighbors = []
        for neighborCell in neighborCells:
            neighbor = neighborCell.getAgent()
            if neighbor != None and neighbor.isAlive() == True:
                neighbors.append(neighbor)
        random.shuffle(neighbors)
        for neighbor in neighbors:
            self.spreadDisease(neighbor, self.__diseases[random.randrange(diseaseCount)]["disease"])

    def doInheritance(self):
        if self.__inheritancePolicy == "none":
            return
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
            sugarInheritance = self.__sugar / len(livingChildren)
            spiceInheritance = self.__spice / len(livingChildren)
            for child in livingChildren:
                child.setSugar(child.getSugar() + sugarInheritance)
                child.setSpice(child.getSpice() + spiceInheritance)
        elif self.__inheritancePolicy == "sons" and len(livingSons) > 0:
            sugarInheritance = self.__sugar / len(livingSons)
            spiceInheritance = self.__spice / len(livingSons)
            for son in livingSons:
                son.setSugar(son.getSugar() + sugarInheritance)
                son.setSpice(son.getSpice() + spiceInheritance)
        elif self.__inheritancePolicy == "daughters" and len(livingDaughters) > 0:
            sugarInheritance = self.__sugar / len(livingDaughters)
            spiceInheritance = self.__spice / len(livingDaughters)
            for daughter in livingDaughters:
                daughter.setSugar(daughter.getSugar() + sugarInheritance)
                daughter.setSpice(daughter.getSpice() + spiceInheritance)
        elif self.__inheritancePolicy == "friends" and len(livingFriends) > 0:
            sugarInheritance = self.__sugar / len(livingFriends)
            spiceInheritance = self.__spice / len(livingFriends)
            for friend in livingFriends:
                friend.setSugar(friend.getSugar() + sugarInheritance)
                friend.setSpice(friend.getSpice() + spiceInheritance)
        self.__sugar = 0
        self.__spice = 0

    def doLending(self):
        self.updateLoans()
        # If not a lender, skip lending
        if self.__lendingFactor == 0:
            return
        # Fertile and not enough excess wealth to be a lender
        elif self.isFertile() == True and (self.__sugar <= self.__startingSugar or self.__spice <= self.__startingSpice):
            return
        # Too young to reproduce, skip lending
        elif self.__age < self.__fertilityAge:
            return
        # Maximum interest rate of 100%
        interestRate = max(1, self.__lendingFactor * self.__baseInterestRate)
        neighborCells = self.__cell.getNeighbors()
        borrowers = []
        for neighborCell in neighborCells:
            neighbor = neighborCell.getAgent()
            if neighbor != None and neighbor.isAlive() == True:
                neighborAge = neighbor.getAge()
                if neighborAge > neighbor.getFertilityAge() and neighborAge < neighbor.getInfertilityAge() and neighbor.isFertile() == False:
                    borrowers.append(neighbor)
        random.shuffle(borrowers)
        for borrower in borrowers:
            maxSugarLoan = self.__sugar / 2
            maxSpiceLoan = self.__spice / 2
            if self.isFertile() == True:
                maxSugarLoan = max(0, self.__sugar - self.__startingSugar)
                maxSpiceLoan = max(0, self.__spice - self.__startingSpice)
            sugarLoanNeed = max(0, borrower.getStartingSugar() - borrower.getSugar())
            spiceLoanNeed = max(0, borrower.getStartingSpice() - borrower.getSpice())
            sugarLoanPrincipal = min(maxSugarLoan, sugarLoanNeed)
            spiceLoanPrincipal = min(maxSpiceLoan, spiceLoanNeed)
            sugarLoanAmount = sugarLoanPrincipal + (sugarLoanPrincipal * interestRate)
            spiceLoanAmount = spiceLoanPrincipal + (spiceLoanPrincipal * interestRate)
            # If lending would cause lender to starve, skip lending to potential borrower
            if self.__sugar - sugarLoanPrincipal < self.__sugarMetabolism or self.__spice - spiceLoanPrincipal < self.__spiceMetabolism:
                continue
            elif borrower.isCreditWorthy(sugarLoanAmount, spiceLoanAmount, self.__loanDuration) == True:
                self.addLoanToAgent(borrower, self.__lastMoved, sugarLoanPrincipal, sugarLoanAmount, spiceLoanPrincipal, spiceLoanAmount, self.__loanDuration)

    def doMetabolism(self):
        if self.__alive == False:
            return
        self.__sugar -= self.__sugarMetabolism
        self.__spice -= self.__spiceMetabolism
        self.__cell.doSugarConsumptionPollution(self.__sugarMetabolism)
        self.__cell.doSpiceConsumptionPollution(self.__spiceMetabolism)
        if (self.__sugar < 1 and self.__sugarMetabolism > 0) or (self.__spice < 1 and self.__spiceMetabolism > 0):
            self.doDeath()

    def doReproduction(self):
        # Agent marked for removal or not interested in reproduction should not reproduce
        if self.__alive == False or self.isFertile() == False:
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
                        emptyCell = emptyCellsWithNeighbor.pop()
                    # If no adjacent empty cell is found, skip reproduction with this neighbor
                    if emptyCell.getAgent() != None:
                        continue
                    childEndowment = self.findChildEndowment(neighbor)
                    child = self.addChildToCell(neighbor, emptyCell, childEndowment)
                    self.__socialNetwork["children"].append(child)
                    childID = child.getID()
                    neighborID = neighbor.getID()
                    self.addAgentToSocialNetwork(child)
                    neighbor.addAgentToSocialNetwork(child)
                    neighbor.updateTimesVisitedWithAgent(self, self.__lastMoved)
                    neighbor.updateTimesReproducedWithAgent(self, self.__lastMoved)
                    self.updateTimesReproducedWithAgent(neighbor, self.__lastMoved)

                    sugarCost = self.__startingSugar / (self.__fertilityFactor * 2)
                    spiceCost = self.__startingSpice / (self.__fertilityFactor * 2)
                    mateSugarCost = neighbor.getStartingSugar() / (neighbor.getFertilityFactor() * 2)
                    mateSpiceCost = neighbor.getStartingSpice() / (neighbor.getFertilityFactor() * 2)
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
                neighbor.setTribe(neighbor.findTribe())

    def doTimestep(self, timestep):
        self.__timestep = timestep
        # Prevent dead or already moved agent from moving
        if self.__alive == True and self.__cell != None and self.__lastMoved != self.__timestep:
            self.__lastMoved = self.__timestep
            self.moveToBestCell()
            self.updateNeighbors()
            self.collectResourcesAtCell()
            self.doMetabolism()
            # If dead from metabolism, skip remainder of timestep
            if self.__alive == False:
                return
            self.doTagging()
            self.doTrading()
            self.doReproduction()
            self.doLending()
            self.doDisease()
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
            transactions = 0

            # If both trying to sell the same commodity, stop trading
            if traderMRS >= 1 and self.__marginalRateOfSubstitution >= 1:
                print("Agent {0} and agent {1} both trying to sell spice".format(str(self), str(trader)))
                continue
            elif traderMRS < 1 and self.__marginalRateOfSubstitution < 1:
                print("Agent {0} and agent {1} both trying to sell sugar".format(str(self), str(trader)))
                continue

            while tradeFlag == True:
                if traderMRS == self.__marginalRateOfSubstitution:
                    print("Agent {0} and agent {1} MRS is equivalent".format(str(self), str(trader)))
                    tradeFlag = False
                    continue

                # MRS > 1 indicates the agent has less need of spice and should become the spice seller
                if traderMRS > self.__marginalRateOfSubstitution:
                    spiceSeller = trader
                    sugarSeller = self
                else:
                    spiceSeller = self
                    sugarSeller = trader
                spiceSellerMRS = spiceSeller.getMarginalRateOfSubstitution()
                sugarSellerMRS = sugarSeller.getMarginalRateOfSubstitution()

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

                spiceSellerSpice = spiceSeller.getSpice()
                spiceSellerSugar = spiceSeller.getSugar()
                spiceSellerSugarMetabolism = spiceSeller.getSugarMetabolism()
                spiceSellerSpiceMetabolism = spiceSeller.getSpiceMetabolism()
                sugarSellerSpice = sugarSeller.getSpice()
                sugarSellerSugar = sugarSeller.getSugar()
                sugarSellerSugarMetabolism = sugarSeller.getSugarMetabolism()
                sugarSellerSpiceMetabolism = sugarSeller.getSpiceMetabolism()
                # If trade would be lethal, skip it
                if spiceSellerSpice - spicePrice < spiceSellerSpiceMetabolism or sugarSellerSugar - sugarPrice < sugarSellerSugarMetabolism:
                    print("Agent {0} and agent {1} aborting fatal trade".format(str(self), str(trader)))
                    tradeFlag = False
                    continue
                spiceSellerNewMRS = spiceSeller.calculateMarginalRateOfSubstitution(spiceSellerSugar + sugarPrice, spiceSellerSpice - spicePrice)
                sugarSellerNewMRS = sugarSeller.calculateMarginalRateOfSubstitution(sugarSellerSugar - sugarPrice, sugarSellerSpice + spicePrice)

                # TODO: Determine why absolute difference from parity results in higher population across seeds than calculating welfare
                # Calculate absolute difference from perfect spice/sugar parity in MRS
                betterForSpiceSeller = abs(1 - spiceSellerMRS) > abs(1 - spiceSellerNewMRS)
                betterForSugarSeller = abs(1 - sugarSellerMRS) > abs(1 - sugarSellerNewMRS)

                #betterForSpiceSeller = spiceSeller.calculateWelfare(sugarPrice, (-1 * spicePrice)) > spiceSeller.calculateWelfare(0, 0)
                #betterForSugarSeller = sugarSeller.calculateWelfare((-1 * sugarPrice), spicePrice) > sugarSeller.calculateWelfare(0, 0)
                
                # Check that spice seller's new MRS does not cross over sugar seller's new MRS
                # Evaluates to False for successful trades
                checkForMRSCrossing = spiceSellerNewMRS < sugarSellerNewMRS
                if betterForSpiceSeller == True and betterForSugarSeller == True and checkForMRSCrossing == False:
                    print("Agent {0} and agent {1} confirming trade [{2}, {3}]\n\tSpice seller MRS: {4} --> {5}\n\tSugar seller MRS: {6} --> {7}".format(
                        str(self), str(trader), sugarPrice, spicePrice, spiceSellerMRS, spiceSellerNewMRS, sugarSellerMRS, sugarSellerNewMRS))
                    spiceSeller.setSugar(spiceSellerSugar + sugarPrice)
                    spiceSeller.setSpice(spiceSellerSpice - spicePrice)
                    sugarSeller.setSugar(sugarSellerSugar - sugarPrice)
                    sugarSeller.setSpice(sugarSellerSpice + spicePrice)
                    spiceSeller.findMarginalRateOfSubstitution()
                    sugarSeller.findMarginalRateOfSubstitution()
                    transactions += 1
                else:
                    print("Agent {0} and agent {1} aborting bad trade:\n\tBetter for spice seller --> {2}\n\tBetter for sugar seller --> {3}\n\tMRS crossing --> {4}".format(
                        str(self), str(trader), betterForSpiceSeller, betterForSugarSeller, checkForMRSCrossing))
                    tradeFlag = False
                    continue
            # If a trade occurred, log it
            if spiceSeller != None and sugarSeller != None:
                trader.updateTimesTradedWithAgent(self, self.__lastMoved, transactions)
                self.updateTimesTradedWithAgent(trader, self.__lastMoved, transactions)

    def findAgentWealthAtCell(self, cell):
        agent = cell.getAgent()
        if agent == None:
            return 0
        else:
            return agent.getWealth()

    '''
    We have concluded that intensity, duration, and certainty are correct. We need to normalize/scale them to either TTL or total resource value.
    Certainty will change once we implement a separation of movement and vision.
    Currently proximity is 1, because if you can see it, you can eat it. Again, this will change when we change movement from vision. (1/distance in time steps)
    Fecundity/purity are a single magical variable named futureBliss. The futureBliss variable represents the probability of future pleasure.
    Extent is # of agents in our vision.
    We will assume omniscience within our own neighborhood.
    utilicalcSugar:
    a.	Intensity: [0 : 1] (1/1+daysToDeath)
    b.	Duration: [0 : 1] [(cell site wealth / agent metabolism) / maxSiteWealth], which is rational
    c.  Certainty: [1 : 1] if agent can reach move cell, [0 : 0] otherwise
    d.  Proximity: [0 : 1] the (1/distance in time steps), which is currently 1
    e.  FutureBliss: [0 : 1] probability of immediate (or limited by computational horizon) future pleasure subsequent to this action
    f.  Extent: (0 : 1] number of agents in neighborhood  / #agents_visible_in_maxVision
    utility_of_cell = certainty * proximity * (intensity + duration + discount * futureBliss * futureReward??? + extent)
    We may wish to weight the variables inside the parenthesis based on some relative importance that we will make up, based on how we think Bentham thought.
    And of course, we will be right.
    '''
    def findBenthamActUtilitarianValueOfCell(self, cell):
        cellSiteWealth = cell.getCurrSugar() + cell.getCurrSpice()
        cellMaxSiteWealth = cell.getMaxSugar() + cell.getMaxSpice()
        cellValue = 0
        for agent in self.__neighborhood:
            # Timesteps to reach cell, currently 1 since agent vision and movement are equal
            timestepDistance = 1
            agentVision = agent.getVision()
            agentMetabolism = agent.getSugarMetabolism() + agent.getSpiceMetabolism()
            # If agent does not have metabolism, set duration to seemingly infinite
            cellDuration = cellSiteWealth / agentMetabolism if agentMetabolism > 0 else 0
            certainty = 1 if agent.canReachCell(cell) == True else 0
            proximity = 1 / timestepDistance
            intensity = 1 / (1 + agent.findDaysToDeath())
            # if metabolism == 0 case
            duration = cellDuration / cellMaxSiteWealth if cellMaxSiteWealth > 0 else 0
            # Agent discount, futureBliss, and futureReward deal with purity and fecundity, not currently included
            discount = 0
            futureBliss = 0
            futureReward = 0
            # Assuming agent can only see in four cardinal directions
            extent = len(self.__neighborhood) / (agentVision * 4) if agentVision > 0 else 1
            agentValueOfCell = agent.getEthicalFactor() * (certainty * proximity * (intensity + duration + (discount * futureBliss * futureReward) + extent))
            cellValue += agentValueOfCell
        return cellValue

    def findBestCell(self):
        self.findCellsInVision()
        neighborhood = []
        for neighborCell in self.__cellsInVision:
            neighbor = neighborCell["cell"].getAgent()
            if neighbor != None and neighbor.isAlive() == True:
                neighborhood.append(neighbor)
        neighborhood.append(self)
        self.__neighborhood = neighborhood
        retaliators = self.findRetaliatorsInVision()
        totalMetabolism = self.__sugarMetabolism + self.__spiceMetabolism
        sugarMetabolismProportion = 0
        spiceMetabolismProportion = 0
        if totalMetabolism != 0: 
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
            # Aggression factor may lead agent to see more reward than possible meaning combat itself is a reward
            welfarePreySugar = self.__aggressionFactor * min(combatMaxLoot, preySugar)
            welfarePreySpice = self.__aggressionFactor * min(combatMaxLoot, preySpice)

            # Avoid attacking stronger agents
            if prey != None and preyWealth > self.__wealth:
                continue

            cellWealth = 0
            if self.__ethicalFactor > 0:
                cellwealth = self.findBenthamActUtilitarianValueOfCell(cell)
            else:
                # Modify value of cell relative to the metabolism needs of the agent
                welfare = self.calculateWelfare((cellSugar + welfarePreySugar), (cellSpice + welfarePreySpice))
                cellWealth = welfare / (1 + cell.getCurrPollution())

            # Avoid attacking agents protected via retaliation
            if prey != None and retaliators[preyTribe] > self.__wealth + cellWealth:
                continue

            if bestCell == None:
                bestCell = cell
                bestRange = travelDistance
                bestWealth = cellWealth

            # Select closest cell with the most resources
            if cellWealth > bestWealth or (cellWealth == bestWealth and travelDistance < bestRange):
                if prey != None and prey.getWealth() > self.__wealth:
                    continue
                bestRange = travelDistance
                bestCell = cell
                bestWealth = cellWealth

        if bestCell == None:
            bestCell = self.__cell
        #TODO: Sort cells by wealth (using range as tiebreaker)
        #      From best to worst, select cell that produces positive nice
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
        parentLendingFactors = [self.__lendingFactor, mate.getLendingFactor()]
        parentFertilityFactors = [self.__fertilityFactor, mate.getFertilityFactor()]
        parentBaseInterestRates = [self.__baseInterestRate, mate.getBaseInterestRate()]
        parentLoanDuration = [self.__loanDuration, mate.getLoanDuration()]
        parentMaxFriends = [self.__maxFriends, mate.getMaxFriends()]
        parentEthicalFactors = [self.__ethicalFactor, mate.getEthicalFactor()]
        # Each parent gives 1/2 their starting endowment for child endowment
        childStartingSugar = (self.__startingSugar / 2) + (mate.getStartingSugar() / 2)
        childStartingSpice = (self.__startingSpice / 2) + (mate.getStartingSpice() / 2)

        childSugarMetabolism = parentSugarMetabolisms[random.randrange(2)]
        childSpiceMetabolism = parentSpiceMetabolisms[random.randrange(2)]
        childMovement = parentMovements[random.randrange(2)]
        childVision = parentVisions[random.randrange(2)]
        childMaxAge = parentMaxAges[random.randrange(2)]
        childInfertilityAge = parentInfertilityAges[random.randrange(2)]
        childFertilityAge = parentFertilityAges[random.randrange(2)]
        childFertilityFactor = parentFertilityFactors[random.randrange(2)]
        childSex = parentSexes[random.randrange(2)]
        childMaxFriends = parentMaxFriends[random.randrange(2)]
        childTags = []
        childImmuneSystem = []
        mateTags = mate.getTags()
        mismatchBits = [0, 1]
        if self.__tags == None:
            childTags = None
        else:
            for i in range(len(self.__tags)):
                if self.__tags[i] == mateTags[i]:
                    childTags.append(self.__tags[i])
                else:
                    childTags.append(mismatchBits[random.randrange(2)])
        mateStartingImmuneSystem = mate.getStartingImmuneSystem()
        if self.__startingImmuneSystem == None:
            childImmuneSystem = None
        else:
            for i in range(len(self.__immuneSystem)):
                if self.__startingImmuneSystem[i] == mateStartingImmuneSystem[i]:
                    childImmuneSystem.append(self.__startingImmuneSystem[i])
                else:
                    childImmuneSystem.append(mismatchBits[random.randrange(2)])
        childAggressionFactor = parentAggressionFactors[random.randrange(2)]
        childTradeFactor = parentTradeFactors[random.randrange(2)]
        childLookaheadFactor = parentLookaheadFactors[random.randrange(2)]
        childLendingFactor = parentLendingFactors[random.randrange(2)]
        childBaseInterestRate = parentBaseInterestRates[random.randrange(2)]
        childLoanDuration = parentLoanDuration[random.randrange(2)]
        childEthicalFactor = parentEthicalFactors[random.randrange(2)]
        endowment = {"movement": childMovement, "vision": childVision, "maxAge": childMaxAge, "sugar": childStartingSugar,
                     "spice": childStartingSpice, "sex": childSex, "fertilityAge": childFertilityAge, "infertilityAge": childInfertilityAge, "tags": childTags,
                     "aggressionFactor": childAggressionFactor, "maxFriends": childMaxFriends, "seed": self.__seed, "sugarMetabolism": childSugarMetabolism,
                     "spiceMetabolism": childSpiceMetabolism, "inheritancePolicy": self.__inheritancePolicy, "tradeFactor": childTradeFactor,
                     "lookaheadFactor": childLookaheadFactor, "lendingFactor": childLendingFactor, "baseInterestRate": childBaseInterestRate,
                     "loanDuration": childLoanDuration, "immuneSystem": childImmuneSystem, "fertilityFactor": childFertilityFactor,
                     "ethicalFactor": childEthicalFactor}
        return endowment

    def findCurrentSpiceDebt(self):
        spiceDebt = 0
        for creditor in self.__socialNetwork["creditors"]:
            spiceDebt += creditor["spiceLoan"] / creditor["loanDuration"]
        return spiceDebt

    def findCurrentSugarDebt(self):
        sugarDebt = 0
        for creditor in self.__socialNetwork["creditors"]:
            sugarDebt += creditor["sugarLoan"] / creditor["loanDuration"]
        return sugarDebt

    def findDaysToDeath(self):
        # If no sugar or spice metabolism, set days to death for that resource to seemingly infinite
        sugarDaysToDeath = self.__sugar / self.__sugarMetabolism if self.__sugarMetabolism > 0 else sys.maxsize
        spiceDaysToDeath = self.__spice / self.__spiceMetabolism if self.__spiceMetabolism > 0 else sys.maxsize
        daysToDeath = min(sugarDaysToDeath, spiceDaysToDeath)
        return daysToDeath

    def findEmptyNeighborCells(self):
        emptyCells = []
        neighborCells = self.__cell.getNeighbors()
        for neighborCell in neighborCells:
            if neighborCell.getAgent() == None:
                emptyCells.append(neighborCell)
        return emptyCells

    def findNearestHammingDistanceInDisease(self, disease):
        if self.__immuneSystem == None:
            return 0
        diseaseTags = disease.getTags()
        diseaseLength = len(diseaseTags)
        bestHammingDistance = diseaseLength
        bestRange = [0, diseaseLength - 1]
        for i in range(len(self.__immuneSystem) - diseaseLength):
            hammingDistance = 0
            for j in range(diseaseLength):
                if self.__immuneSystem[i + j] != diseaseTags[j]:
                    hammingDistance += 1
            if hammingDistance < bestHammingDistance:
                bestHammingDistance = hammingDistance
                bestRange = [i, i + (diseaseLength - 1)]
        diseaseStats = {"distance": bestHammingDistance, "start": bestRange[0], "end": bestRange[1]}
        return diseaseStats

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

    def getBaseInterestRate(self):
        return self.__baseInterestRate

    def getCell(self):
        return self.__cell

    def getCellsInVision(self):
        return self.__cellsInVision

    def getDiseases(self):
        return self.__diseases

    def getEnvironment(self):
        return self.__cell.getEnvironment()

    def getEthicalFactor(self):
        return self.__ethicalFactor

    def getFather(self):
        return self.__socialNetwork["father"]

    def getFertile(self):
        return self.__fertile

    def getFertilityAge(self):
        return self.__fertilityAge

    def getFertilityFactor(self):
        return self.__fertilityFactor

    def getID(self):
        return self.__id 

    def getImmuneSystem(self):
        return self.__immuneSystem

    def getInfertilityAge(self):
        return self.__infertilityAge

    def getInheritancePolicy(self):
        return self.__inheritancePolicy

    def getLendingFactor(self):
        return self.__lendingFactor

    def getLoanDuration(self):
        return self.__loanDuration

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

    def getNeighborhood(self):
        return self.__neighborhood

    def getNice(self):
        return self.__nice

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

    def getStartingImmuneSystem(self):
        return self.__startingImmuneSystem

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

    def isCreditWorthy(self, sugarLoanAmount, spiceLoanAmount, loanDuration):
        if loanDuration == 0:
            return False
        sugarLoanCostPerTimestep = sugarLoanAmount / loanDuration
        spiceLoanCostPerTimestep = spiceLoanAmount / loanDuration
        sugarIncomePerTimestep = ((self.__sugarMeanIncome - self.__sugarMetabolism) - self.findCurrentSugarDebt()) - sugarLoanCostPerTimestep
        spiceIncomePerTimestep = ((self.__spiceMeanIncome - self.__spiceMetabolism) - self.findCurrentSpiceDebt()) - spiceLoanCostPerTimestep
        if sugarIncomePerTimestep >= 0 and spiceIncomePerTimestep >= 0:
            return True
        return False

    def isFertile(self):
        if self.__sugar >= self.__startingSugar and self.__spice >= self.__startingSpice and self.__age >= self.__fertilityAge and self.__age < self.__infertilityAge and self.__fertilityFactor > 0:
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

    def payDebt(self, loan):
        creditorID = loan["creditor"]
        creditor = self.__socialNetwork[creditorID]["agent"]
        if creditor.isAlive() == False:
            if creditor.getInheritancePolicy() != "children":
                self.__socialNetwork["creditors"].remove(loan)
                creditor.removeDebt(loan)
            else:
                self.payDebtToCreditorChildren(loan)
        elif self.__sugar - loan["sugarLoan"] > 0 and self.__spice - loan["spiceLoan"] > 0:
            self.__sugar -= loan["sugarLoan"]
            self.__spice -= loan["spiceLoan"]
            creditor.setSugar(creditor.getSugar() + loan["sugarLoan"])
            creditor.setSpice(creditor.getSpice() + loan["spiceLoan"])
            self.__socialNetwork["creditors"].remove(loan)
            creditor.removeDebt(loan)
        else:
            sugarPayout = self.__sugar / 2
            spicePayout = self.__spice / 2
            sugarRepaymentLeft = loan["sugarLoan"] - sugarPayout
            spiceRepaymentLeft = loan["spiceLoan"] - spicePayout
            self.__sugar -= sugarPayout
            self.__spice -= spicePayout
            creditor.setSugar(creditor.getSugar() + sugarPayout)
            creditor.setSpice(creditor.getSpice() + spicePayout)
            creditorInterestRate = creditor.getLendingFactor() * creditor.getBaseInterestRate()
            newSugarLoan = sugarRepaymentLeft + (creditorInterestRate * sugarRepaymentLeft)
            newSpiceLoan = spiceRepaymentLeft + (creditorInterestRate * spiceRepaymentLeft)
            self.__socialNetwork["creditors"].remove(loan)
            creditor.removeDebt(loan)
            # Initiate new loan with interest compounded on previous loan and not transferring any new principal
            creditor.addLoanToAgent(self, self.__lastMoved, 0, newSugarLoan, 0, newSpiceLoan, creditor.getLoanDuration())

    def payDebtToCreditorChildren(self, loan):
        creditorID = loan["creditor"]
        creditor = self.__socialNetwork[creditorID]["agent"]
        creditorChildren = creditor.getSocialNetwork()["children"]
        livingCreditorChildren = []
        for child in creditorChildren:
            if child.isAlive() == True:
                livingCreditorChildren.append(child)
        numLivingChildren = len(livingCreditorChildren)
        if numLivingChildren > 0:
            sugarRepayment = loan["sugarLoan"] / numLivingChildren
            spiceRepayment = loan["spiceLoan"] / numLivingChildren
            for child in livingCreditorChildren:
                child.addLoanToAgent(self, self.__lastMoved, 0, sugarRepayment, 0, spiceRepayment, 1)
        self.__socialNetwork["creditors"].remove(loan)
        creditor.removeDebt(loan)

    def removeDebt(self, loan):
        debt = None
        for debtor in self.__socialNetwork["debtors"]:
            if debtor == loan:
                self.__socialNetwork["debtors"].remove(debtor)
                return

    def setAge(self, age):
        self.__age = age

    def setAggressionFactor(self, aggressionFactor):
        self.__aggressionFactor = aggressionFactor

    def setAlive(self, alive):
        self.__alive = alive

    def setBaseInterestRate(self, baseInterestRate):
        self.__baseInterestRate = baseInterestRate

    def setCell(self, cell):
        if(self.__cell != None):
            self.unsetCell()
        self.__cell = cell
        self.__cell.setAgent(self)

    def setCellsInVision(self, cells):
        self.__cellsInVision = cells

    def setDiseases(self, diseases):
        self.__diseases = diseases

    def setEthicalFactor(self, ethicalFactor):
        self.__ethicalFactor = ethicalFactor

    def setFather(self, father):
        fatherID = father.getID()
        if fatherID not in self.__socialNetwork:
            self.addAgentToSocialNetwork(father)
        self.__socialNetwork["father"] = father

    def setFertile(self, fertile):
        self.__fertile = fertile

    def setFertilityAge(self, fertilityAge):
        self.__fertilityAge = fertilityAge

    def setFertilityFactor(self, fertilityFactor):
        self.__fertilityFactor = fertilityFactor

    def setID(self, agentID):
        self.__id = agentID

    def setImmuneSystem(self, immuneSystem):
        self.__immuneSystem = immuneSystem

    def setInfertilityAge(self, infertilityAge):
        self.__infertilityAge = infertilityAge

    def setInheritancePolicy(self, inheritancePolicy):
        self.__inheritancePolicy = inheritancePolicy

    def setLendingFactor(self, lendingFactor):
        self.__lendingFactor = lendingFactor

    def setLoanDuration(self, loanDuration):
        self.__loanDuration = loanDuration

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

    def setNeighborhood(self, neighborhood):
        self.__neighborhood = neighborhood

    def setNice(self, nice):
        self.__nice = nice

    def setSex(self, sex):
        self.__sex = sex

    def setSocialNetwork(self, socialNetwork):
        self.__socialNetwork = socialNetwork

    def setSpice(self, spice):
        self.__spice = spice

    def setSpiceMetabolism(self, spiceMetabolism):
        self.__spiceMetabolism = spiceMetabolism

    def setStartingImmuneSystem(self, startingImmuneSystem):
        self.__startingImmuneSystem = startingImmuneSystem

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

    def spreadDisease(self, agent, disease):
        sugarscape = self.__cell.getEnvironment().getSugarscape()
        sugarscape.addDisease(disease, agent)

    def updateDiseaseEffects(self, disease): 
        # If disease not in list of diseases, agent has recovered and undo its effects
        recoveryCheck = -1
        for diseaseRecord in self.__diseases:
            if disease == diseaseRecord["disease"]:
                recoveryCheck = 1
                break

        sugarMetabolismPenalty = disease.getSugarMetabolismPenalty() * recoveryCheck
        spiceMetabolismPenalty = disease.getSpiceMetabolismPenalty() * recoveryCheck
        visionPenalty = disease.getVisionPenalty() * recoveryCheck
        movementPenalty = disease.getMovementPenalty() * recoveryCheck
        fertilityPenalty = disease.getFertilityPenalty() * recoveryCheck
        aggressionPenalty = disease.getAggressionPenalty() * recoveryCheck

        self.__sugarMetabolism = max(0, self.__sugarMetabolism + sugarMetabolismPenalty)
        self.__spiceMetabolism = max(0, self.__spiceMetabolism + spiceMetabolismPenalty)
        self.__vision = max(0, self.__vision + visionPenalty)
        self.__movement = max(0, self.__movement + movementPenalty)
        self.__fertilityFactor = max(0, self.__fertilityFactor + fertilityPenalty)
        self.__aggressionFactor = max(0, self.__aggressionFactor + aggressionPenalty)

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

    def updateLoans(self):
        for debtor in self.__socialNetwork["debtors"]:
            debtorID = debtor["debtor"]
            debtorAgent = self.__socialNetwork[debtorID]["agent"]
            # Cannot collect on debt since debtor is dead
            if debtorAgent.isAlive() == False:
                self.__socialNetwork["debtors"].remove(debtor)
        for creditor in self.__socialNetwork["creditors"]:
            timeRemaining = (self.__lastMoved - creditor["loanOrigin"]) - creditor["loanDuration"]
            if timeRemaining == 0:
                self.payDebt(creditor)

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

    def updateMarginalRateOfSubstitutionForAgent(self, agent):
        agentID = agent.getID()
        if agentID not in self.__socialNetwork:
            self.addAgentToSocialNetwork(agent)
        self.__socialNetwork[agentID]["marginalRateOfSubstitution"] = agent.getMarginalRateOfSubstitution()

    def updateMeanIncome(self, sugarIncome, spiceIncome):
        # Define weight for moving average
        alpha = 0.05
        self.__sugarMeanIncome = (alpha * sugarIncome) + ((1 - alpha) * self.__sugarMeanIncome)
        self.__spiceMeanIncome = (alpha * spiceIncome) + ((1 - alpha) * self.__spiceMeanIncome)

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
                self.updateTimesVisitedWithAgent(neighbor, self.__lastMoved)
                self.updateMarginalRateOfSubstitutionForAgent(neighbor)
            else:
                self.addAgentToSocialNetwork(neighbor)
            self.updateFriends(neighbor)

    def updateTimesReproducedWithAgent(self, agent, timestep):
        agentID = agent.getID()
        if agentID not in self.__socialNetwork:
            self.addAgentToSocialNetwork(agent)
        self.__socialNetwork[agentID]["timesReproduced"] += 1
        self.__socialNetwork[agentID]["lastSeen"] = timestep

    def updateTimesTradedWithAgent(self, agent, timestep, transactions=0):
        agentID = agent.getID()
        if agentID not in self.__socialNetwork:
            self.addAgentToSocialNetwork(agent)
        self.__socialNetwork[agentID]["timesTraded"] += transactions
        self.__socialNetwork[agentID]["lastSeen"] = timestep

    def updateTimesVisitedWithAgent(self, agent, timestep):
        agentID = agent.getID()
        if agentID not in self.__socialNetwork:
            self.addAgentToSocialNetwork(agent)
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
