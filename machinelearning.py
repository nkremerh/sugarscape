import agent
import random
import sys
import neat

class NeuralAgent(agent.Agent):
    def __init__(self, agentID, birthday, cell, configuration, NEATConfiguration, genome=None):
        super().__init__(agentID, birthday, cell, configuration)
        if genome == None:
            self.genome = neat.DefaultGenome(agentID)
            self.genome.configure_new(NEATConfiguration.genome_config)
        else:
            self.genome = genome
        self.network = neat.nn.FeedForwardNetwork.create(self.genome, NEATConfiguration)

    def findBestCell(self):
        self.findNeighborhood()
        if len(self.cellsInRange) == 0:
            return self.cell
        cellsInRange = list(self.cellsInRange.items())
        random.shuffle(cellsInRange)

        sugarMetabolism = self.findSugarMetabolism()
        spiceMetabolism = self.findSpiceMetabolism()
        bestCell = None
        bestCellScore = -sys.maxsize
        for cell, _ in cellsInRange:
            preySugar = cell.agent.sugar if cell.agent != None else 0
            preySpice = cell.agent.spice if cell.agent != None else 0
            neighborAgents = len(cell.findNeighborAgents())
            cellData = [sugarMetabolism, spiceMetabolism, cell.sugar, cell.spice, preySugar, preySpice, neighborAgents]
            # cellData = [sugarMetabolism, spiceMetabolism, cell.sugar, cell.spice]
            cellScore = self.findCellScore(cellData)
            if cellScore > bestCellScore:
                bestCell = cell
                bestCellScore = cellScore
        
        return bestCell
    
    def findCellScore(self, inputs):
        return self.network.activate(inputs)[0]

    def spawnChild(self, childID, birthday, cell, configuration):
        return NeuralAgent(childID, birthday, cell, configuration, self)
