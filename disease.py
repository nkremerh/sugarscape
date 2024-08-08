import math
import random

class Disease:
    def __init__(self, diseaseID, configuration):
        self.ID = diseaseID
        self.sugarMetabolismPenalty = configuration["sugarMetabolismPenalty"]
        self.spiceMetabolismPenalty = configuration["spiceMetabolismPenalty"]
        self.visionPenalty = configuration["visionPenalty"]
        self.movementPenalty = configuration["movementPenalty"]
        self.fertilityPenalty = configuration["fertilityPenalty"]
        self.aggressionPenalty = configuration["aggressionPenalty"]
        self.startTimestep = configuration["startTimestep"]
        self.tags = configuration["tags"]
        self.configuration = configuration
        self.startingInfectedAgents = 0
        self.infectors = []
        self.infected = 0
        self.immuneAgents = []

    def resetRStats(self):
        self.infectors = []
        self.infected = 0

    def __str__(self):
        return f"{self.ID}"
