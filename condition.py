import math

class Condition:
    def __init__(self, conditionID, configuration):
        self.ID = conditionID
        self.configuration = configuration
        self.recoverable = False
        self.tags = None

    def __str__(self):
        return f"{self.ID}"

class Depression(Condition):
    def __init__(self):
        super().__init__("depression", None)
        # Depressed agents have heightened aggression due to irritability
        self.aggressionPenalty = 1.145
        # Depressed agents have a smaller friend network due to social withdrawal
        self.friendlinessPenalty = 0.6333
        self.happinessPenalty = 0.5763
        # Depressed agents move slower due to fatigue
        self.movementPenalty = 0.429
        # Depressed agents undereat due to eating disorders
        # TODO: Current implementation increases metabolism, causing overeating instead
        self.spiceMetabolismPenalty = 1.544
        self.sugarMetabolismPenalty = 1.544

    def trigger(self, agent, infector=None, condition=None):
        agent.aggressionFactor *= self.aggressionPenalty
        agent.maxFriends = math.ceil(agent.maxFriends * self.friendlinessPenalty)
        agent.happinessUnit *= self.happinessPenalty
        agent.movement *= math.ceil(agent.movement * self.movementPenalty)
        agent.spiceMetabolism *= math.ceil(agent.spiceMetabolism * self.spiceMetabolismPenalty)
        agent.sugarMetabolism *= math.ceil(agent.sugarMetabolism * self.sugarMetabolismPenalty)

class Disease(Condition):
    def __init__(self, diseaseID, configuration):
        super().__init__(diseaseID, configuration)
        self.aggressionPenalty = configuration["aggressionPenalty"]
        self.fertilityPenalty = configuration["fertilityPenalty"]
        self.friendlinessPenalty = configuration["friendlinessPenalty"]
        self.happinessPenalty = configuration["happinessPenalty"]
        self.incubationPeriod = configuration["incubationPeriod"]
        self.movementPenalty = configuration["movementPenalty"]
        self.recoverable = True
        self.spiceMetabolismPenalty = configuration["spiceMetabolismPenalty"]
        self.startTimestep = configuration["startTimestep"]
        self.sugarMetabolismPenalty = configuration["sugarMetabolismPenalty"]
        self.tags = configuration["tags"]
        self.transmissionChance = configuration["transmissionChance"]
        self.visionPenalty = configuration["visionPenalty"]
        self.infected = []

    def infect(self, agent, infector=None, condition=None):
        self.infected.append(agent)

    def trigger(self, agent):
        agent.aggressionFactorModifier += self.aggressionPenalty
        agent.fertilityFactorModifier += self.fertilityPenalty
        agent.friendlinessModifier += self.friendlinessPenalty
        agent.happinessModifier += self.happinessPenalty
        agent.movementModifier += self.movementPenalty
        agent.spiceMetabolismModifier += self.spiceMetabolismPenalty
        agent.sugarMetabolismModifier += self.sugarMetabolismPenalty
        agent.visionModifier += self.visionPenalty

    def recover(self, agent):
        agent.aggressionFactorModifier -= self.aggressionPenalty
        agent.fertilityFactorModifier -= self.fertilityPenalty
        agent.friendlinessModifier -= self.friendlinessPenalty
        agent.happinessModifier -= self.happinessPenalty
        agent.movementModifier -= self.movementPenalty
        agent.spiceMetabolismModifier -= self.spiceMetabolismPenalty
        agent.sugarMetabolismModifier -= self.sugarMetabolismPenalty
        agent.visionModifier -= self.visionPenalty
        self.infected.remove(agent)

class ZombieVirus(Disease):
    def __init__(self, diseaseID, configuration):
        configuration["aggressionPenalty"] = 100000
        configuration["fertilityPenalty"] = -1
        configuration["friendlinessPenalty"] = 0
        configuration["happinessPenalty"] = 0
        configuration["incubationPeriod"] = 3
        configuration["movementPenalty"] = 0
        configuration["spiceMetabolismPenalty"] = -10
        configuration["startTimestep"] = 0
        configuration["sugarMetabolismPenalty"] = -10
        configuration["tags"] = None
        configuration["transmissionChance"] = 0.85
        configuration["visionPenalty"] = 1
        super().__init__(diseaseID, configuration)
        self.recoverable = False
