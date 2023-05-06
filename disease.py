import math
import random

class Disease:
    def __init__(self, diseaseID, configuration):
        self.__id = diseaseID
        self.__sugarMetabolismPenalty = configuration["sugarMetabolismPenalty"]
        self.__spiceMetabolismPenalty = configuration["spiceMetabolismPenalty"]
        self.__visionPenalty = configuration["visionPenalty"]
        self.__movementPenalty = configuration["movementPenalty"]
        self.__fertilityPenalty = configuration["fertilityPenalty"]
        self.__aggressionPenalty = configuration["aggressionPenalty"]
        self.__tags = configuration["tags"]
        self.__configuration = configuration
        self.__agent = None

    def getAgent(self):
        return self.__agent

    def getAggressionPenalty(self):
        return self.__aggressionPenalty

    def getConfiguration(self):
        return self.__configuration

    def getFertilityPenalty(self):
        return self.__fertilityPenalty

    def getID(self):
        return self.__id

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

    def setConfiguration(self, configuration):
        self.__configuration = configuration

    def setFertilityPenalty(self, fertilityPenalty):
        self.__fertilityPenalty = fertilityPenalty

    def setID(self, diseaseID):
        self.__id = diseaseID

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

    def __str__(self):
        return "Disease stats: {0} - {1} ({2} {3} {4} {5} {6} {7})".format(len(self.__tags), self.__tags, self.__sugarMetabolismPenalty, self.__spiceMetabolismPenalty, self.__movementPenalty, self.__visionPenalty, self.__fertilityPenalty, self.__aggressionPenalty)
