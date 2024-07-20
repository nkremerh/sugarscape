import json
import random
import matplotlib.pyplot as plt
from sugarscape import Sugarscape, verifyConfiguration

def runSimulationAndLog(configuration):
    sim = Sugarscape(configuration)
    
    populationOverTime = []

    while not sim.end:
        sim.doTimestep()
        populationOverTime.append(sim.runtimeStats["population"])
        
        # Check for a stable population indicating carrying capacity
        if len(populationOverTime) > 10 and all(populationOverTime[-10:]) == populationOverTime[-1]:
            break
    
    with open(f"population_log_{configuration['seed']}.json", 'w') as f:
        json.dump(populationOverTime, f, indent=4)
    
    finalPopulation = sim.runtimeStats["population"]
    return finalPopulation

def runMultipleSimulations(configFile, numRuns):
    with open(configFile, 'r') as f:
        baseConfig = json.load(f)
    baseConfig = baseConfig.get("sugarscapeOptions", baseConfig)

    carryingCapacityReached = 0
    extinctionOccurred = 0

    for _ in range(numRuns):
        config = baseConfig.copy()
        config["seed"] = random.randint(0, 10000)
        config = verifyConfiguration(config)
        finalPopulation = runSimulationAndLog(config)

        if finalPopulation > 0:
            carryingCapacityReached += 1
        else:
            extinctionOccurred += 1

    results = {
        "carryingCapacityReached": carryingCapacityReached / numRuns,
        "extinctionOccurred": extinctionOccurred / numRuns
    }

    with open("carryingCapacityResults.json", 'w') as f:
        json.dump(results, f, indent=4)

def main():
    runMultipleSimulations('test.json', 10)

if __name__ == "__main__":
    main()
