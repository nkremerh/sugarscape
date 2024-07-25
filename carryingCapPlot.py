import json
import os
import matplotlib.pyplot as plt

def loadPopulationLogs(directory):
    populationLogs = []

    for filename in os.listdir(directory):
        if filename.startswith("population_log_") and filename.endswith(".json"):
            with open(os.path.join(directory, filename), 'r') as f:
                populationLogs.append(json.load(f))

    return populationLogs

def plotPopulationOverTime(populationLogs):
    carryingCapacities = []
    
    for log in populationLogs:
        plt.plot(log, label=f'Seed {populationLogs.index(log) + 1}')
        carryingCapacities.append(max(log))  # assuming the carrying capacity is the max population reached

    averageCarryingCapacity = sum(carryingCapacities) / len(carryingCapacities)
    
    plt.axhline(y=averageCarryingCapacity, color='r', linestyle='--', label='Avg Carrying Capacity')
    
    plt.xlabel('Timestep')
    plt.ylabel('Population')
    plt.title('Population Over Time')
    plt.legend()
    plt.show()

def main():
    directory = '.'  # Directory containing the population log files
    populationLogs = loadPopulationLogs(directory)
    plotPopulationOverTime(populationLogs)

if __name__ == "__main__":
    main()
