import math
import random

class Disease:
    def __init__(self, diseaseID, configuration):
        self.ID = diseaseID
        self.configuration = configuration
        self.aggressionPenalty = configuration["aggressionPenalty"]
        self.fertilityPenalty = configuration["fertilityPenalty"]
        self.incubationPeriod = configuration["incubationPeriod"]
        self.movementPenalty = configuration["movementPenalty"]
        self.spiceMetabolismPenalty = configuration["spiceMetabolismPenalty"]
        self.sugarMetabolismPenalty = configuration["sugarMetabolismPenalty"]
        self.tags = configuration["tags"]
        self.transmissionChance = configuration["transmissionChance"]
        self.visionPenalty = configuration["visionPenalty"]

        self.infected = 0
        self.infectors = set()
        self.startingInfectedAgents = 0

    def resetRStats(self):
        self.infected = 0
        self.infectors = set()

    def __str__(self):
        return f"{self.ID}"
