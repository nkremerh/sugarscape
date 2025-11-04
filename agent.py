import hashlib
import math
import random
import re
import sys

class Agent:
    def __init__(self, agentID, birthday, cell, configuration):
        self.ID = agentID
        self.born = birthday
        self.cell = cell
        self.debug = cell.environment.sugarscape.debug

        self.aggressionFactor = configuration["aggressionFactor"]
        self.baseInterestRate = configuration["baseInterestRate"]
        self.decisionModel = configuration["decisionModel"]
        self.decisionModelFactor = configuration["decisionModelFactor"]
        self.decisionModelLookaheadDiscount = configuration["decisionModelLookaheadDiscount"]
        self.decisionModelLookaheadFactor = configuration["decisionModelLookaheadFactor"]
        self.decisionModelTribalFactor = configuration["decisionModelTribalFactor"]
        self.depressionFactor = configuration["depressionFactor"]
        self.diseaseProtectionChance = configuration["diseaseProtectionChance"]
        self.dynamicSelfishnessFactor = configuration["dynamicSelfishnessFactor"]
        self.dynamicTemperanceFactor = configuration["dynamicTemperanceFactor"]
        self.fertilityAge = configuration["fertilityAge"]
        self.fertilityFactor = configuration["fertilityFactor"]
        self.follower = configuration["follower"]
        self.leader = not self.follower
        self.immuneSystem = configuration["immuneSystem"]
        self.infertilityAge = configuration["infertilityAge"]
        self.inheritancePolicy = configuration["inheritancePolicy"]
        self.lendingFactor = configuration["lendingFactor"]
        self.loanDuration = configuration["loanDuration"]
        self.lookaheadFactor = configuration["lookaheadFactor"]
        self.maxAge = configuration["maxAge"]
        self.maxFriends = configuration["maxFriends"]
        self.movement = configuration["movement"]
        self.movementMode = configuration["movementMode"]
        self.neighborhoodMode = configuration["neighborhoodMode"]
        self.seed = configuration["seed"]
        self.selfishnessFactor = configuration["selfishnessFactor"]
        self.sex = configuration["sex"]
        self.spice = configuration["spice"]
        self.spiceMetabolism = configuration["spiceMetabolism"]
        self.startingImmuneSystem = configuration["immuneSystem"]
        self.startingSpice = configuration["spice"]
        self.startingSugar = configuration["sugar"]
        self.sugar = configuration["sugar"]
        self.sugarMetabolism = configuration["sugarMetabolism"]
        self.tagging = configuration["tagging"]
        self.tagPreferences = configuration["tagPreferences"]
        self.tags = configuration["tags"]
        self.temperanceFactor = configuration["temperanceFactor"]
        self.tradeFactor = configuration["tradeFactor"]
        self.universalSpice = configuration["universalSpice"]
        self.universalSugar = configuration["universalSugar"]
        self.vision = configuration["vision"]
        self.visionMode = configuration["visionMode"]

        self.age = 0
        self.aggressionFactorModifier = 0
        self.alive = True
        self.causeOfDeath = None
        self.cellsInRange = []
        self.childEndowmentHashes = None
        self.conflictHappiness = 0
        self.depressed = False
        self.diseaseDeath = False
        self.diseases = []
        self.familyHappiness = 0
        self.fertile = False
        self.fertilityFactorModifier = 0
        self.friendlinessModifier = 0
        self.happiness = 0
        self.happinessUnit = 1
        self.happinessModifier = 0
        self.healthHappiness = 0
        self.lastCombatTimestep = -1
        self.lastDiseasesSpread = 0
        self.lastLendedTimestep = -1
        self.lastLoans = 0
        self.lastMates = 0
        self.lastMovedTimestep = -1
        self.lastMoveOptimal = True
        self.lastMoveRank = 0
        self.lastPollution = 0
        self.lastPreyWealth = 0
        self.lastReproducedTimestep = -1
        self.lastSpice = 0
        self.lastSpreadDiseaseTimestep = -1
        self.lastSugar = 0
        self.lastTimeToLive = 0
        self.lastTradeTimestep = -1
        self.lastTradePartners = 0
        self.lastUniversalSpiceIncomeTimestep = 0
        self.lastUniversalSugarIncomeTimestep = 0
        self.lastValidMoves = 0
        self.marginalRateOfSubstitution = 1
        self.movementModifier = 0
        self.movementNeighborhood = []
        self.neighborhood = []
        self.neighbors = []
        self.nice = 0
        self.socialHappiness = 0
        self.socialNetwork = {"father": None, "mother": None, "children": [], "friends": [], "creditors": [], "debtors": [], "mates": []}
        self.spiceMeanIncome = 1
        self.spiceMetabolismModifier = 0
        self.spicePrice = 0
        self.sugarMeanIncome = 1
        self.sugarMetabolismModifier = 0
        self.sugarPrice = 0
        self.tagZeroes = 0
        self.timestep = birthday
        self.timeToLive = 0
        self.tradeVolume = 0
        self.tribe = self.findTribe()
        self.visionModifier = 0
        self.wealthHappiness = 0
        self.validMoves = []

        self.combatWithControlGroup = 0
        self.combatWithExperimentalGroup = 0
        self.diseaseWithControlGroup = 0
        self.diseaseWithExperimentalGroup = 0
        self.lendingWithControlGroup = 0
        self.lendingWithExperimentalGroup = 0
        self.reproductionWithControlGroup = 0
        self.reproductionWithExperimentalGroup = 0
        self.tradeWithControlGroup = 0
        self.tradeWithExperimentalGroup = 0

        # Change metrics for depressed agents
        if self.depressionFactor == 1:
            self.depressed = True
            depression = cell.environment.sugarscape.depression
            depression.trigger(self)

        self.runtimeStats = {"timestep": self.born, "ID": self.ID, "age": self.age, "wealth": round(self.sugar + self.spice, 2),
                             "sugar": round(self.sugar, 2), "spice": round(self.spice, 2), "sugarGained": 0,
                             "spiceGained": 0, "wealthGained": 0, "movement": self.findMovement(), "timeToLive": 0,
                             "depression": self.depressed, "compositeHappiness": 0, "preyKilled": False,
                             "preyWealth": 0, "tradePartners": 0, "diseasesSpread": 0, "mates": 0,
                             "neighbors": 0, "validMoves": 0, "moveRank": 0, "lendingPartners": 0,
                             "pollutionDifference": 0, "timeToLiveDifference": 0, "neighborsInTribe": 0,
                             "neighborsNotInTribe": 0, "experimentalGroupNeighbors": 0, "controlGroupNeighbors": 0}

    def addAgentToSocialNetwork(self, agent):
        agentID = agent.ID
        if agentID in self.socialNetwork:
            return
        self.socialNetwork[agentID] = {"agent": agent, "lastSeen": self.lastMovedTimestep, "timesVisited": 1, "timesReproduced": 0,
                                         "timesTraded": 0, "timesLoaned": 0, "marginalRateOfSubstitution": 0}

    def addChildToCell(self, mate, cell, childConfiguration):
        sugarscape = self.cell.environment.sugarscape
        childID = sugarscape.generateAgentID()
        childDecisionModel = childConfiguration["decisionModel"]
        child = None
        if childDecisionModel == self.decisionModel:
            child = self.spawnChild(childID, self.timestep, cell, childConfiguration)
        else:
            child = mate.spawnChild(childID, self.timestep, cell, childConfiguration)
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

    def addDisease(self, disease, infector=None):
        self.diseases.append(disease)
        disease["disease"].infect(self, infector)
        if disease["incubation"] == 0:
            disease["disease"].trigger(self)

    def addLoanFromAgent(self, agent, timestep, sugarLoan, spiceLoan, duration):
        agentID = agent.ID
        if agentID not in self.socialNetwork:
            self.addAgentToSocialNetwork(agent)
        self.socialNetwork[agentID]["timesLoaned"] += 1
        loan = {"creditor": agentID, "debtor": self.ID, "sugarLoan": sugarLoan, "spiceLoan": spiceLoan, "loanDuration": duration,
                "loanOrigin": timestep}
        self.socialNetwork["creditors"].append(loan)

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

    def canReachCell(self, cell):
        if cell == self.cell or cell in self.cellsInRange:
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

    def catchDisease(self, disease, infector=None, initial=False):
        diseaseID = disease.ID
        infectionTimestep = infector.timestep if infector != None else self.cell.environment.sugarscape.timestep
        # If currently sick with this disease, do not contract it again
        if self.isInfectedWithDisease(diseaseID) == True:
            return
        # Handle irrecoverable diseases without tags
        caughtDisease = {"disease": disease, "startIndex": None, "endIndex": None, "infector": infector, "caught": infectionTimestep, "incubation": disease.incubationPeriod}
        if disease.tags != None:
            diseaseInImmuneSystem = self.findNearestHammingDistanceInDisease(disease)
            hammingDistance = diseaseInImmuneSystem["distance"]
            # If immune to disease, do not contract it
            if hammingDistance == 0:
                return
            startIndex = diseaseInImmuneSystem["start"]
            endIndex = diseaseInImmuneSystem["end"]
            caughtDisease.update({"startIndex": startIndex, "endIndex": endIndex})

        if initial == True or self.doInfectionAttempt(disease) == True:
            self.addDisease(caughtDisease, infector)
        self.findCellsInRange()

    def collectResourcesAtCell(self):
        sugarCollected = self.cell.sugar
        spiceCollected = self.cell.spice
        self.sugar += sugarCollected
        self.spice += spiceCollected
        self.updateMeanIncome(sugarCollected, spiceCollected)
        if self.cell.environment.pollutionStart <= self.timestep <= self.cell.environment.pollutionEnd:
            self.cell.doSugarProductionPollution(sugarCollected)
            self.cell.doSpiceProductionPollution(spiceCollected)
        self.cell.resetSugar()
        self.cell.resetSpice()

    def defaultOnLoan(self, loan):
        for creditor in self.socialNetwork["creditors"]:
            continue
        return

    def doAging(self):
        if self.isAlive() == False:
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
            self.lastCombatTimestep = self.cell.environment.sugarscape.timestep
            self.lastPreyWealth = sugarLoot + spiceLoot
            prey.sugar -= sugarLoot
            prey.spice -= spiceLoot
            prey.doDeath("combat")
            sugarscape = self.cell.environment.sugarscape
            if sugarscape.experimentalGroup != None and prey.isInGroup(sugarscape.experimentalGroup):
                self.combatWithExperimentalGroup += 1
            elif sugarscape.experimentalGroup != None and prey.isInGroup(sugarscape.experimentalGroup, True):
                self.combatWithControlGroup += 1
        self.gotoCell(cell)

    def doDeath(self, causeOfDeath="unknown"):
        # TODO: Determine why some agents do not die cleanly (Sugarscape object needs to call their doDeath method)
        if causeOfDeath == "unknown" and self.causeOfDeath != None:
            return
        self.alive = False
        self.causeOfDeath = causeOfDeath
        # If sick at death, consider disease a contributing factor
        if self.isSick():
            self.diseaseDeath = True
        self.resetCell()
        self.doInheritance()

        self.neighbors = []
        self.neighborhood = []
        for disease in self.diseases:
            diseaseRecord = disease["disease"]
            diseaseRecord.recover(self)
        self.diseases = []

    def doDisease(self):
        random.shuffle(self.diseases)
        for diseaseRecord in self.diseases:
            disease = diseaseRecord["disease"]
            if diseaseRecord["caught"] != self.timestep and diseaseRecord["incubation"] > 0:
                diseaseRecord["incubation"] -= 1
            # Activate fully incubated disease
            if diseaseRecord["incubation"] == 0:
                disease.trigger(self)
            if disease.recoverable == False:
                continue
            diseaseTags = diseaseRecord["disease"].tags
            if diseaseTags != None:
                immuneResponseStart = diseaseRecord["startIndex"]
                immuneResponseEnd = min(diseaseRecord["endIndex"] + 1, len(self.immuneSystem))
                immuneResponse = self.immuneSystem[immuneResponseStart:immuneResponseEnd]
                for i in range(len(immuneResponse)):
                    if immuneResponse[i] != diseaseTags[i]:
                        self.immuneSystem[immuneResponseStart + i] = diseaseTags[i]
                        break
                if diseaseTags == immuneResponse:
                    self.diseases.remove(diseaseRecord)
                    disease.recover(self)

        diseaseCount = len(self.diseases)
        if diseaseCount == 0:
            return
        neighborCells = self.cell.neighbors.values()
        neighbors = []
        for neighborCell in neighborCells:
            neighbor = neighborCell.agent
            if neighbor != None and neighbor.isAlive() == True:
                neighbors.append(neighbor)
        diseasesSpread = 0
        random.shuffle(neighbors)
        for neighbor in neighbors:
            disease = self.diseases[random.randrange(diseaseCount)]["disease"]
            neighbor.catchDisease(disease, self)
            if neighbor.isInfectedWithDisease(disease.ID) == True:
                diseasesSpread += 1
            sugarscape = self.cell.environment.sugarscape
            if sugarscape.experimentalGroup != None and neighbor.isInGroup(sugarscape.experimentalGroup):
                self.diseaseWithExperimentalGroup += 1
            elif sugarscape.experimentalGroup != None and neighbor.isInGroup(sugarscape.experimentalGroup, True):
                self.diseaseWithControlGroup += 1
        if diseasesSpread > 0:
            self.lastSpreadDiseaseTimestep = self.timestep
            self.lastDiseasesSpread = diseasesSpread

    def doInfectionAttempt(self, disease):
        diseaseAttack = random.uniform(0.0, 1.0)
        immuneDefense = random.uniform(0.0, 1.0)
        attackSuccess = True if diseaseAttack <= disease.transmissionChance and disease.transmissionChance != 0.0 else False
        defenseSuccess = True if immuneDefense <= self.diseaseProtectionChance and self.diseaseProtectionChance != 0.0 else False
        if attackSuccess == True and defenseSuccess == False:
            return True
        return False

    def doInheritance(self):
        if self.inheritancePolicy == "none":
            return
        # Prevent negative inheritance
        if self.sugar < 0:
            self.sugar = 0
        if self.spice < 0:
            self.spice = 0
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
        loans = 0
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
                    print(f"Agent {self.ID} lending [{sugarLoanAmount},{spiceLoanAmount}]")
                self.addLoanToAgent(borrower, self.lastMovedTimestep, sugarLoanPrincipal, sugarLoanAmount, spiceLoanPrincipal, spiceLoanAmount, self.loanDuration)
                loans += 1
                sugarscape = self.cell.environment.sugarscape
                if sugarscape.experimentalGroup != None and borrower.isInGroup(sugarscape.experimentalGroup):
                    self.lendingWithExperimentalGroup += 1
                elif sugarscape.experimentalGroup != None and borrower.isInGroup(sugarscape.experimentalGroup, True):
                    self.lendingWithControlGroup += 1
        if loans > 0:
            self.lastLendedTimestep = self.timestep
            self.lastLoans = loans

    def doMetabolism(self):
        if self.isAlive() == False:
            return
        spiceMetabolism = self.findSpiceMetabolism()
        sugarMetabolism = self.findSugarMetabolism()
        self.sugar -= sugarMetabolism
        self.spice -= spiceMetabolism
        if self.cell.environment.pollutionStart <= self.timestep <= self.cell.environment.pollutionEnd:
            self.cell.doSugarConsumptionPollution(sugarMetabolism)
            self.cell.doSpiceConsumptionPollution(spiceMetabolism)
        if self.sugar < 0 or self.spice < 0:
            self.doDeath("starvation")
        elif (self.sugar <= 0 and sugarMetabolism > 0) or (self.spice <= 0 and spiceMetabolism > 0):
            self.doDeath("starvation")

    def doReproduction(self):
        # Agent marked for removal or not interested in reproduction should not reproduce
        if self.isAlive() == False or self.isFertile() == False:
            return
        neighborCells = list(self.cell.neighbors.values())
        random.shuffle(neighborCells)
        emptyCells = self.findEmptyNeighborCells()
        mates = []
        for neighborCell in neighborCells:
            neighbor = neighborCell.agent
            if neighbor != None and neighbor.isAlive() == True:
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
                    if neighbor not in self.socialNetwork["mates"]:
                        self.socialNetwork["mates"].append(neighbor)
                    childEndowment = self.findChildEndowment(neighbor)
                    child = self.addChildToCell(neighbor, emptyCell, childEndowment)
                    child.findCellsInRange()
                    child.findNeighborhood()
                    self.socialNetwork["children"].append(child)
                    childID = child.ID
                    neighborID = neighbor.ID
                    self.addAgentToSocialNetwork(child)
                    neighbor.addAgentToSocialNetwork(child)
                    neighbor.updateTimesVisitedWithAgent(self, self.lastMovedTimestep)
                    neighbor.updateTimesReproducedWithAgent(self, self.lastMovedTimestep)
                    self.updateTimesReproducedWithAgent(neighbor, self.lastMovedTimestep)

                    sugarCost = self.startingSugar / (self.fertilityFactor * 2)
                    spiceCost = self.startingSpice / (self.fertilityFactor * 2)
                    mateSugarCost = neighbor.startingSugar / (neighbor.fertilityFactor * 2)
                    mateSpiceCost = neighbor.startingSpice / (neighbor.fertilityFactor * 2)
                    self.sugar -= sugarCost
                    self.spice -= spiceCost
                    neighbor.sugar = neighbor.sugar - mateSugarCost
                    neighbor.spice = neighbor.spice - mateSpiceCost
                    self.lastReproducedTimestep = self.timestep
                    if neighbor not in mates:
                        mates.append(neighbor)
                    sugarscape = self.cell.environment.sugarscape
                    if sugarscape.experimentalGroup != None and neighbor.isInGroup(sugarscape.experimentalGroup):
                        self.reproductionWithExperimentalGroup += 1
                    elif sugarscape.experimentalGroup != None and neighbor.isInGroup(sugarscape.experimentalGroup, True):
                        self.reproductionWithControlGroup += 1
                    if "all" in self.debug or "agent" in self.debug:
                        print(f"Agent {self.ID} reproduced with agent {str(neighbor)} at cell ({emptyCell.x},{emptyCell.y})")
        self.lastMates = len(mates)

    def doTagging(self):
        if self.tags == None or self.isAlive() == False or self.tagging == False:
            return
        neighborCells = list(self.cell.neighbors.values())
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
        if self.isAlive() == True and self.lastMovedTimestep != self.timestep:
            # Bookkeeping before performing actions
            self.lastSugar = self.sugar
            self.lastSpice = self.spice
            # Beginning of timestep actions
            self.moveToBestCell()
            self.updateNeighbors()
            # Middle of timestep actions
            self.collectResourcesAtCell()
            self.doUniversalIncome()
            self.doMetabolism()
            # If dead from metabolism, skip remainder of timestep
            if self.alive == False:
                return
            self.doTagging()
            self.doTrading()
            self.doReproduction()
            self.doLending()
            # End of timestep actions
            self.doDisease()
            self.doAging()
            # If dead from aging, skip remainder of timestep
            if self.alive == False:
                return
            self.findCellsInRange()
            self.updateHappiness()
            self.updateRuntimeStats()
            self.updateValues()

    def doTrading(self):
        # If not a trader, skip trading
        if self.tradeFactor == 0:
            return
        self.tradeVolume = 0
        self.sugarPrice = 0
        self.spicePrice = 0
        self.findMarginalRateOfSubstitution()
        neighborCells = self.cell.neighbors.values()
        potentialTraders = []
        for neighborCell in neighborCells:
            neighbor = neighborCell.agent
            if neighbor != None and neighbor.isAlive() == True:
                neighborMRS = neighbor.marginalRateOfSubstitution
                if neighborMRS != self.marginalRateOfSubstitution:
                    potentialTraders.append(neighbor)
        random.shuffle(potentialTraders)
        tradePartners = []
        for trader in potentialTraders:
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

                if spiceSellerMRS < 0 or sugarSellerMRS < 0:
                    spiceSeller = None
                    sugarSeller = None
                    break

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
                        print(f"Agent {self.ID} trading [{sugarPrice}, {spicePrice}]")
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
                trader.updateTimesTradedWithAgent(self, self.lastMovedTimestep, transactions)
                self.updateTimesTradedWithAgent(trader, self.lastMovedTimestep, transactions)
                self.lastTradeTimestep = self.timestep
                sugarscape = self.cell.environment.sugarscape
                if trader not in tradePartners:
                        tradePartners.append(trader)
                if sugarscape.experimentalGroup != None and trader.isInGroup(sugarscape.experimentalGroup):
                    self.tradeWithExperimentalGroup += 1
                elif sugarscape.experimentalGroup != None and trader.isInGroup(sugarscape.experimentalGroup, True):
                    self.tradeWithControlGroup += 1
        if self.lastTradeTimestep == self.timestep:
            self.lastTradePartners = len(tradePartners)

    def doUniversalIncome(self):
        if (self.timestep - self.lastUniversalSpiceIncomeTimestep) >= self.cell.environment.universalSpiceIncomeInterval:
            self.spice += self.universalSpice
            self.lastUniversalSpiceIncomeTimestep = self.timestep
        if (self.timestep - self.lastUniversalSugarIncomeTimestep) >= self.cell.environment.universalSugarIncomeInterval:
            self.sugar += self.universalSugar
            self.lastUniversalSugarIncomeTimestep = self.timestep

    def findAggression(self):
        return max(0, self.aggressionFactor + self.aggressionFactorModifier)

    def findBestCell(self):
        leader = self.cell.environment.sugarscape.agentLeader
        if self.follower == True and leader != None:
            return leader.findBestCellForAgent(self)

        bestCell = None
        potentialCells = self.rankCellsInRange()
        greedyBestCell = potentialCells[0]["cell"]

        if self.decisionModelFactor > 0:
            bestCell = self.findBestEthicalCell(potentialCells[:], greedyBestCell)
        if bestCell == None:
            bestCell = greedyBestCell
        if bestCell == greedyBestCell:
            self.lastMoveOptimal = True
        else:
            self.lastMoveOptimal = False
        bestCellRank = 0
        for cell in potentialCells:
            if cell["cell"] != bestCell:
                bestCellRank += 1
            else:
                break
        self.lastMoveRank = bestCellRank
        self.lastValidMoves = len(potentialCells)
        return bestCell

    def findBestEthicalCell(self, cells, greedyBestCell=None):
        if len(cells) == 0:
            return None
        # If not an ethical agent, return top selfish choice
        return greedyBestCell

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
        cellRange = min(min(vision, movement), self.cell.environment.maxCellDistance)
        allCells = {}
        if cellRange <= 0:
            self.cellsInRange = allCells
            return allCells
        for i in range(1, cellRange + 1):
            allCells.update(cell.ranges[i])
        if newCell == None:
            self.cellsInRange = allCells
        return allCells

    def findChildEndowment(self, mate):
        parentEndowments = {
        "aggressionFactor": [self.aggressionFactor, mate.aggressionFactor],
        "baseInterestRate": [self.baseInterestRate, mate.baseInterestRate],
        "diseaseProtectionChance": [self.diseaseProtectionChance, mate.diseaseProtectionChance],
        "depressionFactor": [self.depressionFactor, mate.depressionFactor],
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
        "spiceMetabolism": [self.spiceMetabolism, mate.spiceMetabolism],
        "sugarMetabolism": [self.sugarMetabolism, mate.sugarMetabolism],
        "sex": [self.sex, mate.sex],
        "tradeFactor": [self.tradeFactor, mate.tradeFactor],
        "vision": [self.vision, mate.vision],
        "visionMode": [self.visionMode, mate.visionMode],
        "universalSpice": [self.universalSpice, mate.universalSpice],
        "universalSugar": [self.universalSugar, mate.universalSugar],
        "neighborhoodMode": [self.neighborhoodMode, mate.neighborhoodMode]
        }

        # These endowments should always come from the same parent for sensible outcomes
        pairedEndowments = {
        "decisionModel": [self.decisionModel, mate.decisionModel],
        "decisionModelFactor": [self.decisionModelFactor, mate.decisionModelFactor],
        "decisionModelLookaheadDiscount": [self.decisionModelLookaheadDiscount, mate.decisionModelLookaheadDiscount],
        "decisionModelLookaheadFactor": [self.decisionModelLookaheadFactor, mate.decisionModelLookaheadFactor],
        "decisionModelTribalFactor": [self.decisionModelTribalFactor, mate.decisionModelTribalFactor],
        "dynamicSelfishnessFactor": [self.dynamicSelfishnessFactor, mate.dynamicSelfishnessFactor],
        "dynamicTemperanceFactor" : [self.dynamicTemperanceFactor, mate.dynamicTemperanceFactor],
        "selfishnessFactor" : [self.selfishnessFactor, mate.selfishnessFactor],
        "temperanceFactor" : [self.temperanceFactor, mate.temperanceFactor]
        }
        childEndowment = {"seed": self.seed, "follower": self.follower}
        randomNumberReset = random.getstate()

        # Map configuration to a random number via hash to make random number generation independent of iteration order
        if self.childEndowmentHashes == None:
            self.childEndowmentHashes = {}
            for config in parentEndowments:
                hashed = hashlib.md5(config.encode())
                hashNum = int(hashed.hexdigest(), 16)
                self.childEndowmentHashes[config] = hashNum
            for config in pairedEndowments:
                hashed = hashlib.md5(config.encode())
                hashNum = int(hashed.hexdigest(), 16)
                self.childEndowmentHashes[config] = hashNum

        for endowment in parentEndowments:
            random.seed(self.childEndowmentHashes[endowment] + self.timestep)
            index = random.randrange(2)
            endowmentValue = parentEndowments[endowment][index]
            childEndowment[endowment] = endowmentValue

        pairedEndowmentIndex = -1
        for endowment in pairedEndowments:
            if pairedEndowmentIndex == -1:
                random.seed(self.childEndowmentHashes[endowment] + self.timestep)
                pairedEndowmentIndex = random.randrange(2)
            endowmentValue = pairedEndowments[endowment][pairedEndowmentIndex]
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
        childEndowment["tagPreferences"] = self.tagPreferences
        childEndowment["tagging"] = self.tagging

        # Current implementation randomly assigns depressed state at agent birth
        depressionPercentage = self.cell.environment.sugarscape.configuration["agentDepressionPercentage"]
        depression = random.random()
        if depression <= depressionPercentage:
            childEndowment["depressionFactor"] = 1
        else:
            childEndowment["depressionFactor"] = 0

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
        if self.lastCombatTimestep == self.cell.environment.sugarscape.timestep:
            if(self.findAggression() > 1):
                return self.happinessUnit
            else:
                return self.happinessUnit * -1
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

    def findEmptyNeighborCells(self):
        emptyCells = []
        neighborCells = self.cell.neighbors.values()
        for neighborCell in neighborCells:
            if neighborCell.agent == None:
                emptyCells.append(neighborCell)
        return emptyCells

    def findFamilyHappiness(self):
        familyHappiness = 0
        for child in self.socialNetwork["children"]:
            if child.isAlive() == True:
                familyHappiness += self.happinessUnit
                if child.isSick() == True:
                    familyHappiness -= self.happinessUnit * 0.5
                if child.born == self.timestep:
                    familyHappiness += self.happinessUnit
            else:
                familyHappiness -= self.happinessUnit
        for mate in self.socialNetwork["mates"]:
            if mate.isAlive() == True:
                familyHappiness += self.happinessUnit
                if mate.isSick() == True:
                    familyHappiness -= self.happinessUnit * 0.5
            else:
                familyHappiness -= self.happinessUnit
        return math.erf(familyHappiness)

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
        return self.conflictHappiness + self.familyHappiness + self.healthHappiness + self.socialHappiness + self.wealthHappiness

    def findHealthHappiness(self):
        if self.isSick():
            return self.happinessUnit * -1
        else:
            return self.happinessUnit

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
        if self.immuneSystem == None or disease.tags == None:
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
        if newCell == None:
            newNeighborhood = self.cellsInRange
        else:
            newNeighborhood = self.findCellsInRange(newCell)
        neighborhood = []
        for neighborCell in newNeighborhood.keys():
            neighbor = neighborCell.agent
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

    def findRetaliatorsInVision(self):
        retaliators = {}
        for cell in self.cellsInRange.keys():
            agent = cell.agent
            if agent != None:
                agentWealth = agent.sugar + agent.spice
                if agent.tribe not in retaliators:
                    retaliators[agent.tribe] = agentWealth
                elif retaliators[agent.tribe] < agentWealth:
                    retaliators[agent.tribe] = agentWealth
        return retaliators

    def findSocialHappiness(self):
        if self.maxFriends == 0:
            return 0
        step = 2 / self.maxFriends
        socialHappiness = (len(self.socialNetwork["friends"]) * step) - 1
        return socialHappiness * self.happinessUnit

    def findSpiceMetabolism(self):
        return max(0, self.spiceMetabolism + self.spiceMetabolismModifier)

    def findSugarMetabolism(self):
        return max(0, self.sugarMetabolism + self.sugarMetabolismModifier)

    def findTimeToLive(self, ageLimited=False):
        spiceMetabolism = self.findSpiceMetabolism()
        sugarMetabolism = self.findSugarMetabolism()
        # If no sugar or spice metabolism, set days to death for that resource to seemingly infinite
        sugarTimeToLive = self.sugar / sugarMetabolism if sugarMetabolism > 0 else sys.maxsize
        spiceTimeToLive = self.spice / spiceMetabolism if spiceMetabolism > 0 else sys.maxsize
        # If an agent has basic income, include the income for at least as many timesteps as they can already survive
        if self.universalSugar != 0:
            sugarIncome = (sugarTimeToLive * self.universalSugar) / self.cell.environment.universalSugarIncomeInterval
            sugarTimeToLive = (self.sugar + sugarIncome) / sugarMetabolism if sugarMetabolism > 0 else sys.maxsize
        if self.universalSpice != 0:
            spiceIncome = (spiceTimeToLive * self.universalSpice) / self.cell.environment.universalSpiceIncomeInterval
            spiceTimeToLive = (self.spice + spiceIncome) / spiceMetabolism if spiceMetabolism > 0 else sys.maxsize
        timeToLive = min(sugarTimeToLive, spiceTimeToLive)
        if ageLimited == True:
            timeToLive = min(timeToLive, self.maxAge - self.age)
        self.timeToLive = timeToLive
        return timeToLive

    def findTribe(self):
        if self.tags == None:
            return None
        config = self.cell.environment.sugarscape.configuration
        numTribes = config["environmentMaxTribes"]
        possibleZeroes = config["agentTagStringLength"] + 1
        self.tagZeroes = self.tags.count(0)
        tribeSize = possibleZeroes / numTribes
        tribe = min(math.ceil((self.tagZeroes + 1) / tribeSize) - 1, numTribes - 1)
        return tribe

    def findVision(self):
        return max(0, self.vision + self.visionModifier)

    def findWealthHappiness(self):
        wealth = self.sugar + self.spice
        diffWealth = wealth - self.cell.environment.sugarscape.runtimeStats["meanWealth"]
        diffWealth *= self.happinessUnit
        return math.erf(diffWealth)

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
        if self.tagPreferences == True and self.tags != None and len(self.tags) > 0:
            # Tribe could have changed since last timestep, so recheck
            self.tribe = self.findTribe()
            fractionZeroesInTags = self.tagZeroes / len(self.tags)
            fractionOnesInTags = 1 - fractionZeroesInTags
            tagPreferences = (sugarMetabolism * fractionZeroesInTags) + (spiceMetabolism * fractionOnesInTags)
            if tagPreferences <= 0:
                tagPreferences = 1
            tagPreferencesSugar = (sugarMetabolism / tagPreferences) * fractionZeroesInTags
            tagPreferencesSpice = (spiceMetabolism / tagPreferences) * fractionOnesInTags
            welfare = (totalSugar ** tagPreferencesSugar) * (totalSpice ** tagPreferencesSpice)
        return welfare

    def flipTag(self, position, value):
        self.tags[position] = value

    def getDiseaseRecord(self, diseaseID):
        for currDisease in self.diseases:
            currDiseaseID = currDisease["disease"].ID
            if int(diseaseID) == currDiseaseID:
                return currDisease
        return None

    def gotoCell(self, cell):
        if cell != None:
            self.lastMovedTimestep = self.timestep
            self.lastPollution = self.cell.pollution
        self.resetCell()
        self.cell = cell
        self.cell.agent = self

    def isAlive(self):
        if self.spice < 0 or self.sugar < 0:
            self.alive = False
        return self.alive and self.spice >= 0 and self.sugar >= 0

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

    def isInfectedWithDisease(self, diseaseID):
        for currDisease in self.diseases:
            currDiseaseID = currDisease["disease"].ID
            if diseaseID == currDiseaseID:
                return True
        return False

    def isInGroup(self, group, notInGroup=False):
        membership = False
        if group == self.decisionModel:
            membership = True
        elif group == "depressed":
            membership = self.depressed
        elif "disease" in group:
            diseaseID = re.search(r"disease(?P<ID>\d+)", group).group("ID")
            membership = self.isInfectedWithDisease(diseaseID)
        elif group == "female":
            membership = True if self.sex == "female" else False
        elif group == "male":
            membership = True if self.sex == "male" else False
        elif group == "sick":
            membership = self.isSick()

        if notInGroup == True:
            membership = not membership
        return membership

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
        if neighbor == None or self.findAggression() <= 0:
            return False
        elif self.tribe != neighbor.tribe and self.sugar + self.spice >= neighbor.sugar + neighbor.spice:
            return True
        return False

    def isSick(self):
        if len(self.diseases) > 0:
            return True
        return False

    def moveToBestCell(self):
        bestCell = self.findBestCell()
        if "all" in self.debug or "agent" in self.debug:
            print(f"Agent {self.ID} moving to ({bestCell.x},{bestCell.y})")
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
            creditor.addLoanToAgent(self, self.lastMovedTimestep, 0, newSugarLoan, 0, newSpiceLoan, creditor.loanDuration)

    def payDebtToCreditorChildren(self, loan):
        creditorID = loan["creditor"]
        creditor = self.socialNetwork[creditorID]["agent"]
        creditorChildren = creditor.socialNetwork["children"]
        livingCreditorChildren = []
        for child in creditorChildren:
            # Children who took loans out with their parents should not owe themselves
            if child != self and child.isAlive() == True:
                livingCreditorChildren.append(child)
        numLivingChildren = len(livingCreditorChildren)
        if numLivingChildren > 0:
            sugarRepayment = loan["sugarLoan"] / numLivingChildren
            spiceRepayment = loan["spiceLoan"] / numLivingChildren
            for child in livingCreditorChildren:
                child.addLoanToAgent(self, self.lastMovedTimestep, 0, sugarRepayment, 0, spiceRepayment, 1)
        self.socialNetwork["creditors"].remove(loan)
        creditor.removeDebt(loan)

    def printCellScores(self, cells):
        i = 0
        while i < len(cells):
            cell = cells[i]
            cellString = f"({cell['cell'].x},{cell['cell'].y}) [{cell['wealth']},{cell['range']}]"
            print(f"Cell {i + 1}/{len(cells)}: {cellString}")
            i += 1

    def printEthicalCellScores(self, cells):
        i = 0
        while i < len(cells):
            cell = cells[i]
            cellString = f"({cell['cell'].x},{cell['cell'].y}) [{cell['wealth']},{cell['range']}]"
            print(f"Ethical cell {i + 1}/{len(cells)}: {cellString}")
            i += 1

    def rankCellsInRange(self):
        self.findNeighborhood()

        if len(self.cellsInRange) == 0:
            return [{"cell": self.cell, "wealth": 0, "range": 0}]
        cellsInRange = list(self.cellsInRange.items())
        random.shuffle(cellsInRange)

        retaliators = self.findRetaliatorsInVision()
        combatMaxLoot = self.cell.environment.maxCombatLoot
        aggression = self.findAggression()

        bestCell = None
        bestWealth = 0
        bestRange = max(self.cell.environment.height, self.cell.environment.width)
        potentialCells = []

        for cell, travelDistance in cellsInRange:
            # Avoid attacking agents ineligible to attack
            prey = cell.agent
            if cell.isOccupied() and self.isNeighborValidPrey(prey) == False:
                continue
            preyTribe = prey.tribe if prey != None else "empty"
            preySugar = prey.sugar if prey != None else 0
            preySpice = prey.spice if prey != None else 0
            # Aggression factor may lead agent to see more reward than possible meaning combat itself is a reward
            welfarePreySugar = aggression * min(combatMaxLoot, preySugar)
            welfarePreySpice = aggression * min(combatMaxLoot, preySpice)

            # Modify value of cell relative to the metabolism needs of the agent
            welfare = self.findWelfare(((cell.sugar + welfarePreySugar) / (1 + cell.pollution)), ((cell.spice + welfarePreySpice) / (1 + cell.pollution)))

            # Avoid attacking agents protected via retaliation
            if prey != None and retaliators[preyTribe] > self.sugar + self.spice + welfare:
                continue

            # Select closest cell with the most resources
            if welfare > bestWealth or (welfare == bestWealth and travelDistance < bestRange):
                bestCell = cell
                bestWealth = welfare
                bestRange = travelDistance

            cellRecord = {"cell": cell, "wealth": welfare, "range": travelDistance}
            potentialCells.append(cellRecord)

        if len(potentialCells) == 0:
            potentialCells.append({"cell": self.cell, "wealth": 0, "range": 0})

        rankedCells = self.sortCellsByWealth(potentialCells)
        self.updateMovementStats(rankedCells)
        return rankedCells

    def removeDebt(self, loan):
        for debtor in self.socialNetwork["debtors"]:
            if debtor == loan:
                self.socialNetwork["debtors"].remove(debtor)
                return

    def resetCell(self):
        self.cell.resetAgent()
        self.cell = None

    def resetTimestepMetrics(self):
        self.combatWithControlGroup = 0
        self.combatWithExperimentalGroup = 0
        self.diseaseWithControlGroup = 0
        self.diseaseWithExperimentalGroup = 0
        self.lendingWithControlGroup = 0
        self.lendingWithExperimentalGroup = 0
        self.reproductionWithControlGroup = 0
        self.reproductionWithExperimentalGroup = 0
        self.tradeWithControlGroup = 0
        self.tradeWithExperimentalGroup = 0

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

    def spawnChild(self, childID, birthday, cell, configuration):
        return Agent(childID, birthday, cell, configuration)

    def triggerDisease(self, disease, infector=None):
        self.diseases.append(disease)
        disease["disease"].trigger(self, infector)

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

    def updateHappiness(self):
        if self.isAlive() == False:
            return
        self.conflictHappiness = self.findConflictHappiness()
        self.familyHappiness = self.findFamilyHappiness()
        self.healthHappiness = self.findHealthHappiness()
        self.socialHappiness = self.findSocialHappiness()
        self.wealthHappiness = self.findWealthHappiness()
        self.happiness = self.findHappiness()

    def updateLoans(self):
        for debtor in self.socialNetwork["debtors"]:
            debtorID = debtor["debtor"]
            debtorAgent = self.socialNetwork[debtorID]["agent"]
            # Cannot collect on debt since debtor is dead
            if debtorAgent.isAlive() == False:
                self.socialNetwork["debtors"].remove(debtor)
        for creditor in self.socialNetwork["creditors"]:
            timeRemaining = (self.lastMovedTimestep - creditor["loanOrigin"]) - creditor["loanDuration"]
            if timeRemaining == 0:
                self.payDebt(creditor)

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

    def updateMovementStats(self, cells):
        validCells = []
        for cell in cells:
            newRecord = {"cell": cell["cell"], "wealth": cell["wealth"]}
            validCells.append(newRecord)
        self.validMoves = validCells
        self.movementNeighborhood = self.neighborhood[:]

    def updateNeighbors(self):
        self.neighbors = [neighborCell.agent for neighborCell in self.cell.neighbors.values() if neighborCell.agent != None]
        self.updateSocialNetwork()

    def updateRuntimeStats(self):
        diseasesSpread = 0
        loans = 0
        mates = 0
        tradePartners = 0
        preyKilled = False
        preyWealth = 0
        if self.lastReproducedTimestep == self.timestep:
            mates = self.lastMates
        if self.lastCombatTimestep == self.timestep:
            preyKilled = True
            preyWealth = self.lastPreyWealth
        if self.lastTradeTimestep == self.timestep:
            tradePartners = self.lastTradePartners
        if self.lastSpreadDiseaseTimestep == self.timestep:
            diseasesSpread = self.lastDiseasesSpread
        if self.lastLendedTimestep == self.timestep:
            loans = self.lastLoans
        spiceGained = self.spice - self.lastSpice
        sugarGained = self.sugar - self.lastSugar
        wealthGained = spiceGained + sugarGained

        controlNeighbors = 0
        experimentalNeighbors = 0
        sugarscape = self.cell.environment.sugarscape
        neighborsInTribe = 0
        for neighbor in self.neighbors:
            if neighbor.tribe == self.tribe:
                neighborsInTribe += 1
            if sugarscape.experimentalGroup != None and prey.isInGroup(sugarscape.experimentalGroup):
                experimentalNeighbors += 1
            elif sugarscape.experimentalGroup != None and prey.isInGroup(sugarscape.experimentalGroup, True):
                controlNeighbors += 1

        self.lastTimeToLive = self.timeToLive
        self.findTimeToLive()
        timeToLiveDifference = self.timeToLive - self.lastTimeToLive
        pollutionDifference = self.cell.pollution - self.lastPollution

        self.runtimeStats = {"timestep": self.timestep, "ID": self.ID, "age": self.age, "wealth": round(self.sugar + self.spice, 2),
                             "sugar": round(self.sugar, 2), "spice": round(self.spice, 2), "sugarGained": round(sugarGained, 2),
                             "spiceGained": round(spiceGained, 2), "wealthGained": round(wealthGained, 2), "movement": self.findMovement(), "timeToLive": round(self.timeToLive, 1),
                             "depression": self.depressed, "compositeHappiness": round(self.happiness, 1), "preyKilled": preyKilled,
                             "preyWealth": preyWealth, "tradePartners": tradePartners, "diseasesSpread": diseasesSpread, "mates": mates,
                             "neighbors": len(self.neighbors), "validMoves": self.lastValidMoves, "moveRank": self.lastMoveRank, "lendingPartners": loans,
                             "pollutionDifference": pollutionDifference, "timeToLiveDifference": timeToLiveDifference, "neighborsInTribe": neighborsInTribe,
                             "neighborsNotInTribe": len(self.neighbors) - neighborsInTribe, "experimentalGroupNeighbors": experimentalNeighbors,
                             "controlGroupNeighbors": controlNeighbors}

        sugarscape.agentRuntimeStats.append(self.runtimeStats)

    def updateSocialNetwork(self):
        for neighbor in self.neighbors:
            if neighbor == None:
                continue
            neighborID = neighbor.ID
            if neighborID in self.socialNetwork:
                self.updateTimesVisitedWithAgent(neighbor, self.lastMovedTimestep)
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

    def updateValues(self):
        # Method to be used by child classes to do interesting things with agent behavior
        return

    def __str__(self):
        return f"{self.ID}"
