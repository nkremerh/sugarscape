import math
import random

class Disease:
    def __init__(self, diseaseID, configuration):
        self.ID = diseaseID
        self.configuration = configuration
        self.aggressionPenalty = configuration["aggressionPenalty"]
        self.fertilityPenalty = configuration["fertilityPenalty"]
        self.movementPenalty = configuration["movementPenalty"]
        self.spiceMetabolismPenalty = configuration["spiceMetabolismPenalty"]
        self.sugarMetabolismPenalty = configuration["sugarMetabolismPenalty"]
        self.tags = configuration["tags"]
        self.visionPenalty = configuration["visionPenalty"]

    def __str__(self):
        return f"{self.ID}"
