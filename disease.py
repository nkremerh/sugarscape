import math
import random

class Disease:
    def __init__(self, agent, configuration):
        self.__agent = agent
        self.__sugarMetabolismPenalty = configuration["sugarMetabolismPenalty"]
        self.__spiceMetabolismPenalty = configuration["spiceMetabolismPenalty"]
        self.__visionPenalty = configuration["visionPenalty"]
        self.__movementPenalty = configuration["movementPenalty"]
        self.__fertilityPenalty = configuration["fertilityPenalty"]
        self.__aggressionPenalty = configuration["aggressionPenalty"]
        self.__tags = configuration["tags"]

    def getAgent(self):
        return self.__agent

    def getAggressionPenalty(self):
        return self.__aggressionPenalty

    def getFertilityPenalty(self):
        return self.__fertilityPenalty

    def getMovementPenalty(self):
        return self.__movementPenalty

    def getSpiceMetabolismPenalty(self):
        return self.__spiceMetabolismPenalty

    def getSugarMetabolismPenalty(self):
        return self.__sugarMetabolismPenalty

    def getTags(self):
        return self.__tags

    def getVisionPenalty(self):
        return self.__visionPenalty

    def setAgent(self, agent):
        self.__agent = agent

    def setAggressionPenalty(self, aggressionPenalty):
        self.__aggressionPenalty = aggressionPenalty

    def setFertilityPenalty(self, fertilityPenalty):
        self.__fertilityPenalty = fertilityPenalty

    def setMovementPenalty(self, movementPenalty):
        self.__movementPenalty = movementPenalty

    def setSpiceMetabolismPenalty(self, spiceMetabolismPenalty):
        self.__spiceMetabolismPenalty = spiceMetabolismPenalty

    def setSugarMetabolismPenalty(self, sugarMetabolismPenalty):
        self.__sugarMetabolismPenalty = sugarMetabolismPenalty

    def setTags(self, tags):
        self.__tags = tags

    def setVisionPenalty(self, visionPenalty):
        self.__visionPenalty = visionPenalty
