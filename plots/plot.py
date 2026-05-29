import csv
import getopt
import json
import math
import matplotlib.pyplot
import matplotlib.ticker
import os
import re
import statistics
import sys

def findMeans(dataset):
    print(f"Finding mean values across {totalTimesteps} timesteps")
    for model in dataset:
        for column in dataset[model]["metrics"]:
            for i in range(len(dataset[model]["metrics"][column])):
                if column not in dataset[model]["aggregates"]:
                    dataset[model]["aggregates"][column] = [0 for j in range(totalTimesteps + 1)]
                    dataset[model]["standardDeviations"][column] = [0 for j in range(totalTimesteps + 1)]
                dataset[model]["standardDeviations"][column][i] = statistics.stdev(dataset[model]["metrics"][column][i])
                dataset[model]["aggregates"][column][i] = sum(dataset[model]["metrics"][column][i]) / dataset[model]["runs"]
    return dataset

def findMeansByConfig(dataset):
    print(f"Finding mean values by config")
    for model in dataset:
        if "metrics" not in dataset[model]:
            continue
        # dataset[model]["aggregates"][column][configBasePrefix][configNumRange] = average across runs for this config and number range
        dataset[model]["aggregates"] = {}
        dataset[model]["standardDeviations"] = {}
        for column, configs in dataset[model]["metrics"].items():
            if column not in dataset[model]["aggregates"]:
                dataset[model]["aggregates"][column] = {}
                dataset[model]["standardDeviations"][column] = {}
            for configBasePrefix, ranges in configs.items():
                if configBasePrefix not in dataset[model]["aggregates"][column]:
                    dataset[model]["aggregates"][column][configBasePrefix] = {}
                    dataset[model]["standardDeviations"][column][configBasePrefix] = {}
                for configNumRange, metrics in ranges.items():
                    if not column.lower().endswith("extinctperconfig") and column != "runsPerConfig":
                        # Aggregate across runs within this config
                        dataset[model]["standardDeviations"][column][configBasePrefix][configNumRange] = statistics.stdev(metrics) if len(metrics) > 1 else 0
                        dataset[model]["aggregates"][column][configBasePrefix][configNumRange] = sum(metrics) / len(metrics) if metrics else None
                    elif column.lower().endswith("extinctperconfig") and dataset[model]["metrics"]["runsPerConfig"][configBasePrefix][configNumRange] > 0:
                        # For extinction counts, divide by total runs per config to get extinction rate
                        dataset[model]["aggregates"][column][configBasePrefix][configNumRange] = metrics / dataset[model]["metrics"]["runsPerConfig"][configBasePrefix][configNumRange]
                        dataset[model]["standardDeviations"][column][configBasePrefix][configNumRange] = 0
    return dataset

def findMedians(dataset):
    print(f"Finding median values across {totalTimesteps} timesteps")
    for model in dataset:
        for column in dataset[model]["metrics"]:
            for i in range(len(dataset[model]["metrics"][column])):
                sortedColumn = sorted(dataset[model]["metrics"][column][i])
                columnLength = len(sortedColumn)
                midpoint = math.floor(columnLength / 2)
                median = sortedColumn[midpoint]
                quartile = math.floor(columnLength / 4)
                firstQuartile = sortedColumn[quartile]
                thirdQuartile = sortedColumn[midpoint + quartile]
                if columnLength % 2 == 0:
                    median = round((sortedColumn[midpoint - 1] + median) / 2, 2)
                    firstQuartile = round((sortedColumn[quartile - 1] + firstQuartile) / 2, 2)
                    thirdQuartile = round((sortedColumn[(midpoint + quartile) - 1] + thirdQuartile) / 2, 2)
                if column not in dataset[model]["aggregates"]:
                    dataset[model]["aggregates"][column] = [0 for j in range(totalTimesteps + 1)]
                    dataset[model]["firstQuartiles"][column] = [0 for j in range(totalTimesteps + 1)]
                    dataset[model]["thirdQuartiles"][column] = [0 for j in range(totalTimesteps + 1)]
                dataset[model]["aggregates"][column][i] = median
    return dataset

def findSameGroupInteractionProportionsAcrossTimesteps(dataset, model, rawData, configBasePrefix, configNumRange, experimentalGroup=None):
    if experimentalGroup == None:
        print(f"No experimental group specified. Skipping same-group interaction data processing for {configBasePrefix}-{configNumRange}.")
        return
    same_group_sums = {"lending": 0, "reproduction": 0, "trade": 0}
    total_sums = {"lending": 0, "reproduction": 0, "trade": 0}
    for item in rawData:
        if int(item["timestep"]) > totalTimesteps:
            break
        
        same_group_lending = float(item.get("lendingControlGroupToControlGroup", 0)) + float(item.get("lendingExperimentalGroupToExperimentalGroup", 0))
        same_group_reproduction = float(item.get("reproductionControlGroupToControlGroup", 0)) + float(item.get("reproductionExperimentalGroupToExperimentalGroup", 0))
        same_group_trade = float(item.get("tradeControlGroupToControlGroup", 0)) + float(item.get("tradeExperimentalGroupToExperimentalGroup", 0))

        same_group_sums["lending"] += same_group_lending
        same_group_sums["reproduction"] += same_group_reproduction
        same_group_sums["trade"] += same_group_trade

        total_sums["lending"] += same_group_lending + float(item.get("lendingControlGroupToExperimentalGroup", 0)) + float(item.get("lendingExperimentalGroupToControlGroup", 0))
        total_sums["reproduction"] += same_group_reproduction + float(item.get("reproductionControlGroupToExperimentalGroup", 0)) + float(item.get("reproductionExperimentalGroupToControlGroup", 0))
        total_sums["trade"] += same_group_trade + float(item.get("tradeControlGroupToExperimentalGroup", 0)) + float(item.get("tradeExperimentalGroupToControlGroup", 0))

    lending_proportion = same_group_sums["lending"] / total_sums["lending"] if total_sums["lending"] > 0 else None
    reproduction_proportion = same_group_sums["reproduction"] / total_sums["reproduction"] if total_sums["reproduction"] > 0 else None
    trade_proportion = same_group_sums["trade"] / total_sums["trade"] if total_sums["trade"] > 0 else None

    if "lending_same_group_proportion" not in dataset[model]["metrics"]:
        dataset[model]["metrics"]["lending_same_group_proportion"] = {}
    if configBasePrefix not in dataset[model]["metrics"]["lending_same_group_proportion"]:
        dataset[model]["metrics"]["lending_same_group_proportion"][configBasePrefix] = {}
    if configNumRange not in dataset[model]["metrics"]["lending_same_group_proportion"][configBasePrefix]:
        dataset[model]["metrics"]["lending_same_group_proportion"][configBasePrefix][configNumRange] = []
    if lending_proportion is not None:
        dataset[model]["metrics"]["lending_same_group_proportion"][configBasePrefix][configNumRange].append(lending_proportion)

    if "reproduction_same_group_proportion" not in dataset[model]["metrics"]:
        dataset[model]["metrics"]["reproduction_same_group_proportion"] = {}
    if configBasePrefix not in dataset[model]["metrics"]["reproduction_same_group_proportion"]:
        dataset[model]["metrics"]["reproduction_same_group_proportion"][configBasePrefix] = {}
    if configNumRange not in dataset[model]["metrics"]["reproduction_same_group_proportion"][configBasePrefix]:
        dataset[model]["metrics"]["reproduction_same_group_proportion"][configBasePrefix][configNumRange] = []
    if reproduction_proportion is not None:
        dataset[model]["metrics"]["reproduction_same_group_proportion"][configBasePrefix][configNumRange].append(reproduction_proportion)

    if "trade_same_group_proportion" not in dataset[model]["metrics"]:
        dataset[model]["metrics"]["trade_same_group_proportion"] = {}
    if configBasePrefix not in dataset[model]["metrics"]["trade_same_group_proportion"]:
        dataset[model]["metrics"]["trade_same_group_proportion"][configBasePrefix] = {}
    if configNumRange not in dataset[model]["metrics"]["trade_same_group_proportion"][configBasePrefix]:
        dataset[model]["metrics"]["trade_same_group_proportion"][configBasePrefix][configNumRange] = []
    if trade_proportion is not None:
        dataset[model]["metrics"]["trade_same_group_proportion"][configBasePrefix][configNumRange].append(trade_proportion)

def findWeightedAverageAcrossTimesteps(dataset, model, rawData, entry, configBasePrefix, configNumRange, experimentalGroup=None):
    # If the column is in this list, we will do a weighted average by population (specific to control/experimental if doing these columns)
    # Otherwise, all timesteps are weighted the same regardless of population size
    weighted_average_columns = ["meanAgeAtDeath", "agentMeanTimeToLive", "meanWealth",
                                "controlMeanAgeAtDeath", "controlAgentMeanTimeToLive", "controlMeanWealth"]
    if experimentalGroup is not None:
        weighted_average_columns.extend([experimentalGroup + "MeanAgeAtDeath", experimentalGroup + "AgentMeanTimeToLive", experimentalGroup + "MeanWealth"])

    weighted_sum = 0.0
    weights_sum = 0.0
    unweighted_sum = 0
    count = 0
    for item in rawData:
        if int(item["timestep"]) > totalTimesteps:
            break
        if int(item["timestep"]) > dataset[model]["timesteps"]:
                    dataset[model]["timesteps"] += 1
        val = item.get(entry, None)
        if val is None or val == "" or val == "None":
            continue
        try:
            val = float(val)
        except ValueError:
            continue
        
        # Collect corresponding population weight for this timestep
        if entry in weighted_average_columns:
            weight = None
            # Choose appropriate population column for this metric
            if experimentalGroup is not None and "control" in entry.lower() and item.get("controlPopulation") not in (None, "", "None"):
                weight = float(item["controlPopulation"])
            elif experimentalGroup is not None and experimentalGroup in entry.lower() and item.get(experimentalGroup + "Population") not in (None, "", "None"):
                weight = float(item[experimentalGroup + "Population"])
            elif item.get("population") not in (None, "", "None"):
                weight = float(item["population"])
            if weight is not None:
                weighted_sum += val * weight
                weights_sum += weight
        unweighted_sum += val
        count += 1

    if entry in weighted_average_columns and weights_sum > 0:
        weighted_average = weighted_sum / weights_sum
    else:
        weighted_average = unweighted_sum / count if count > 0 else 0

    if entry not in dataset[model]["metrics"]:
        dataset[model]["metrics"][entry] = {}
    if configBasePrefix not in dataset[model]["metrics"][entry]:
        dataset[model]["metrics"][entry][configBasePrefix] = {}
    if configNumRange not in dataset[model]["metrics"][entry][configBasePrefix]:
        dataset[model]["metrics"][entry][configBasePrefix][configNumRange] = []
    if weighted_average is not None:
        dataset[model]["metrics"][entry][configBasePrefix][configNumRange].append(weighted_average)

def generatePlots(config, models, totalTimesteps, dataset, statistic, experimentalGroup=None, plotGroups=False, xlabel=None):
    titleStatistic = statistic.title()
    if "ageism" in config["plots"]:
        print(f"Generating {statistic} ageism plot")
        if statistic == "meansByConfig":
            generateSimpleBarChart(dataset, config.get("plotConfigPrefixesWithExperimentalGroups", {}), f"{statistic}_ageism.pdf", "meanAgeismFactor", "Mean Ageism Factor", "best", percentage=False, plotGroups=plotGroups, xlabel=xlabel)
        else:
            generateSimpleLinePlot(models, dataset, totalTimesteps, f"{statistic}_ageism.pdf", "meanAgeismFactor", f"{titleStatistic} Ageism Factor", "lower center", percentage=False, experimentalGroup=experimentalGroup, plotGroups=plotGroups, xlabel=xlabel)
    if "biasFactors" in config["plots"]:
        if statistic == "meansByConfig":
            print(f"{statistic} bias factors plot function does not exist, skipping. Use individual bias factor plots instead")
        else:
            print(f"Generating {statistic} bias factors plot")
            generatePlotForBiases(dataset, totalTimesteps, f"{statistic}_bias_factors.pdf", "Mean Bias Factors", "lower center", experimentalGroup=experimentalGroup, xlabel=xlabel)
    if "conflictHappiness" in config["plots"]:
        print(f"Generating {statistic} conflict happiness plot")
        if statistic == "meansByConfig":
            generateSimpleBarChart(dataset, config.get("plotConfigPrefixesWithExperimentalGroups", {}), f"{statistic}_conflict_happiness.pdf", "meanConflictHappiness", "Mean Conflict Happiness", "best", percentage=False, plotGroups=plotGroups, xlabel=xlabel)
        else:
            generateSimpleLinePlot(models, dataset, totalTimesteps, f"{statistic}_conflict_happiness.pdf", "meanConflictHappiness", f"{titleStatistic} Conflict Happiness", "center right", percentage=False, experimentalGroup=experimentalGroup, plotGroups=plotGroups, xlabel=xlabel)
    if "combatInteractions" in config["plots"]:
        if statistic == "meansByConfig":
            print(f"{statistic} combat interactions plot function does not exist, skipping")
        else:
            print(f"Generating {statistic} combat interactions plot")
            generateGroupInteractionLinePlot(models, dataset, totalTimesteps, f"{statistic}_combat_interactions.pdf", "combat", f"{titleStatistic} Combat Interactions", "center right", xlabel=xlabel)
    if "deaths" in config["plots"]:
        print(f"Generating {statistic} deaths plot")
        if statistic == "meansByConfig":
            generateSimpleBarChart(dataset, config.get("plotConfigPrefixesWithExperimentalGroups", {}), f"{statistic}_deaths.pdf", "meanDeathsPercentage", "Mean Deaths", "best", percentage=True, plotGroups=plotGroups, xlabel=xlabel)
        else:
            generateSimpleLinePlot(models, dataset, totalTimesteps, f"{statistic}_deaths.pdf", "meanDeathsPercentage", f"{titleStatistic} Deaths", "center right", percentage=True, experimentalGroup=experimentalGroup, plotGroups=plotGroups, xlabel=xlabel)
    if "familyHappiness" in config["plots"]:
        print(f"Generating {statistic} family happiness plot")
        if statistic == "meansByConfig":
            generateSimpleBarChart(dataset, config.get("plotConfigPrefixesWithExperimentalGroups", {}), f"{statistic}_family_happiness.pdf", "meanFamilyHappiness", "Mean Family Happiness", "best", percentage=False, plotGroups=plotGroups, xlabel=xlabel)
        else:
            generateSimpleLinePlot(models, dataset, totalTimesteps, f"{statistic}_family_happiness.pdf", "meanFamilyHappiness", f"{titleStatistic} Family Happiness", "center right", percentage=False, experimentalGroup=experimentalGroup, plotGroups=plotGroups, xlabel=xlabel)
    if "giniCoefficient" in config["plots"]:
        print(f"Generating {statistic} Gini coefficient plot")
        if statistic == "meansByConfig":
            generateSimpleBarChart(dataset, config.get("plotConfigPrefixesWithExperimentalGroups", {}), f"{statistic}_gini.pdf", "giniCoefficient", "Mean Gini Coefficient", "best", percentage=False, plotGroups=plotGroups, xlabel=xlabel)
        else:
            generateSimpleLinePlot(models, dataset, totalTimesteps, f"{statistic}_gini.pdf", "giniCoefficient", f"{titleStatistic} Gini Coefficient", "center right", percentage=False, experimentalGroup=experimentalGroup, plotGroups=plotGroups, xlabel=xlabel)
    if "extinctions" in config["plots"]:
        print(f"Generating {statistic} extinctions plot")
        if statistic == "meansByConfig":
            generateSimpleBarChart(dataset, config.get("plotConfigPrefixesWithExperimentalGroups", {}), f"{statistic}_extinctions.pdf", "extinctPerConfig", "Extinction Rate", "best", percentage=True, plotGroups=plotGroups, xlabel=xlabel)
        else:
            print(f"{statistic} extinctions plot function does not exist, skipping")
    if "happiness" in config["plots"]:
        print(f"Generating {statistic} happiness plot")
        if statistic == "meansByConfig":
            generateSimpleBarChart(dataset, config.get("plotConfigPrefixesWithExperimentalGroups", {}), f"{statistic}_happiness.pdf", "meanHappiness", "Mean Happiness", "best", percentage=False, plotGroups=plotGroups, xlabel=xlabel)
        else:
            generateSimpleLinePlot(models, dataset, totalTimesteps, f"{statistic}_happiness.pdf", "meanHappiness", f"{titleStatistic} Happiness", "center right", percentage=False, experimentalGroup=experimentalGroup, plotGroups=plotGroups, xlabel=xlabel)
    if "healthHappiness" in config["plots"]:
        print(f"Generating {statistic} health happiness plot")
        if statistic == "meansByConfig":
            generateSimpleBarChart(dataset, config.get("plotConfigPrefixesWithExperimentalGroups", {}), f"{statistic}_health_happiness.pdf", "meanHealthHappiness", "Mean Health Happiness", "best", percentage=False, plotGroups=plotGroups, xlabel=xlabel)
        else:
            generateSimpleLinePlot(models, dataset, totalTimesteps, f"{statistic}_health_happiness.pdf", "meanHealthHappiness", f"{titleStatistic} Health Happiness", "center right", percentage=False, experimentalGroup=experimentalGroup, plotGroups=plotGroups, xlabel=xlabel)
    if "lifeExpectancy" in config["plots"]:
        print(f"Generating {statistic} life expectancy plot")
        if statistic == "meansByConfig":
            generateSimpleBarChart(dataset, config.get("plotConfigPrefixesWithExperimentalGroups", {}), f"{statistic}_life_expectancy.pdf", "meanAgeAtDeath", "Mean Life Expectancy", "best", percentage=False, plotGroups=plotGroups, xlabel=xlabel)
        else:
            generateSimpleLinePlot(models, dataset, totalTimesteps, f"{statistic}_life_expectancy.pdf", "meanAgeAtDeath", f"{titleStatistic} Life Expectancy", "lower right", percentage=False, experimentalGroup=experimentalGroup, plotGroups=plotGroups, xlabel=xlabel)
    if "loanVolume" in config["plots"]:
        print(f"Generating {statistic} loan volume plot")
        if statistic == "meansByConfig":
            generateSimpleBarChart(dataset, config.get("plotConfigPrefixesWithExperimentalGroups", {}), f"{statistic}_loans.pdf", "loanVolume", "Mean Loan Volume", "best", percentage=False, plotGroups=plotGroups, xlabel=xlabel)
        else:
            generateSimpleLinePlot(models, dataset, totalTimesteps, f"{statistic}_loans.pdf", "loanVolume", f"{titleStatistic} Loan Volume", "center right", percentage=False, experimentalGroup=experimentalGroup, plotGroups=plotGroups, xlabel=xlabel)
    if "lendingInteractions" in config["plots"]:
        if statistic == "meansByConfig":
            print(f"{statistic} lending interactions plot function does not exist, skipping. Use same-group interactions plot instead")
        else:
            print(f"Generating {statistic} lending interactions plot")
            generateGroupInteractionLinePlot(models, dataset, totalTimesteps, f"{statistic}_lending_interactions.pdf", "lending", f"{titleStatistic} Lending Interactions", "center right", xlabel=xlabel)
    if "population" in config["plots"]:
        print(f"Generating {statistic} population plot")
        if statistic == "meansByConfig":
            generateSimpleBarChart(dataset, config.get("plotConfigPrefixesWithExperimentalGroups", {}), f"{statistic}_population.pdf", "population", "Mean Population", "best", percentage=False, plotGroups=plotGroups, xlabel=xlabel)
        else:
            generateSimpleLinePlot(models, dataset, totalTimesteps, f"{statistic}_population.pdf", "population", f"{titleStatistic} Population", "lower right", percentage=False, experimentalGroup=experimentalGroup, plotGroups=plotGroups, xlabel=xlabel)
    if "racism" in config["plots"]:
        print(f"Generating {statistic} racism plot")
        if statistic == "meansByConfig":
            generateSimpleBarChart(dataset, config.get("plotConfigPrefixesWithExperimentalGroups", {}), f"{statistic}_racism.pdf", "meanRacismFactor", "Mean Racism Factor", "best", percentage=False, plotGroups=plotGroups, xlabel=xlabel)
        else:
            generateSimpleLinePlot(models, dataset, totalTimesteps, f"{statistic}_racism.pdf", "meanRacismFactor", f"{titleStatistic} Racism Factor", "lower center", percentage=False, experimentalGroup=experimentalGroup, plotGroups=plotGroups, xlabel=xlabel)
    if "reproductionInteractions" in config["plots"]:
        print(f"Generating {statistic} reproduction interactions plot")
        if statistic == "meansByConfig":
            print(f"{statistic} reproduction interactions plot function does not exist, skipping. Use same-group interactions plot instead")
        else:
            generateGroupInteractionLinePlot(models, dataset, totalTimesteps, f"{statistic}_reproduction_interactions.pdf", "reproduction", f"{titleStatistic} Reproduction Interactions", "center right", xlabel=xlabel)
    if "sameGroupInteractions" in config["plots"]:
        print(f"Generating {statistic} same-group interactions plot")
        if statistic != "meansByConfig":
            print(f"{statistic} same-group interactions plot function does not exist, skipping. Use individual interaction plots instead")
        else:
            generateSameGroupInteractionPercentageBarChart(dataset, config.get("plotConfigPrefixesWithExperimentalGroups", {}), f"{statistic}_same_group_interactions.pdf", "Same-Group Interactions", "best", xlabel=xlabel)
    if "selfishness" in config["plots"]:
        print(f"Generating {statistic} selfishness plot")
        if statistic == "meansByConfig":
            generateSimpleBarChart(dataset, config.get("plotConfigPrefixesWithExperimentalGroups", {}), f"{statistic}_selfishness.pdf", "meanSelfishness", "Mean Selfishness Factor", "best", percentage=False, plotGroups=plotGroups, xlabel=xlabel)
        else:
            generateSimpleLinePlot(models, dataset, totalTimesteps, f"{statistic}_selfishness.pdf", "meanSelfishness", f"{titleStatistic} Selfishness Factor", "lower center", percentage=False, experimentalGroup=experimentalGroup, plotGroups=plotGroups, xlabel=xlabel)
    if "sexism" in config["plots"]:
        print(f"Generating {statistic} sexism plot")
        if statistic == "meansByConfig":
            generateSimpleBarChart(dataset, config.get("plotConfigPrefixesWithExperimentalGroups", {}), f"{statistic}_sexism.pdf", "meanSexismFactor", "Mean Sexism Factor", "best", percentage=False, plotGroups=plotGroups, xlabel=xlabel)
        else:
            generateSimpleLinePlot(models, dataset, totalTimesteps, f"{statistic}_sexism.pdf", "meanSexismFactor", f"{titleStatistic} Sexism Factor", "lower center", percentage=False, experimentalGroup=experimentalGroup, plotGroups=plotGroups, xlabel=xlabel)
    if "sickness" in config["plots"]:
        print(f"Generating {statistic} sick percentage plot")
        if statistic == "meansByConfig":
            generateSimpleBarChart(dataset, config.get("plotConfigPrefixesWithExperimentalGroups", {}), f"{statistic}_sickness.pdf", "sickAgentsPercentage", "Mean Sickness Percentage", "best", percentage=True, plotGroups=plotGroups, xlabel=xlabel)
        else:
            generateSimpleLinePlot(models, dataset, totalTimesteps, f"{statistic}_sickness.pdf", "sickAgentsPercentage", f"{titleStatistic} Diseased Agents", "center right", percentage=True, experimentalGroup=experimentalGroup, plotGroups=plotGroups, xlabel=xlabel)
    if "socialHappiness" in config["plots"]:
        print(f"Generating {statistic} social happiness plot")
        if statistic == "meansByConfig":
            generateSimpleBarChart(dataset, config.get("plotConfigPrefixesWithExperimentalGroups", {}), f"{statistic}_social_happiness.pdf", "meanSocialHappiness", "Mean Social Happiness", "best", percentage=False, plotGroups=plotGroups, xlabel=xlabel)
        else:
            generateSimpleLinePlot(models, dataset, totalTimesteps, f"{statistic}_social_happiness.pdf", "meanSocialHappiness", f"{titleStatistic} Social Happiness", "center right", percentage=False, experimentalGroup=experimentalGroup, plotGroups=plotGroups, xlabel=xlabel)
    if "totalWealth" in config["plots"]:
        print(f"Generating {statistic} total wealth plot")
        if statistic == "meansByConfig":
            generateSimpleBarChart(dataset, config.get("plotConfigPrefixesWithExperimentalGroups", {}), f"{statistic}_wealth.pdf", "agentWealthTotal", "Mean Total Wealth", "best", percentage=False, plotGroups=plotGroups, xlabel=xlabel)
        else:
            generateSimpleLinePlot(models, dataset, totalTimesteps, f"{statistic}_wealth.pdf", "agentWealthTotal", f"{titleStatistic} Total Wealth", "center right", percentage=False, experimentalGroup=experimentalGroup, plotGroups=plotGroups, xlabel=xlabel)
    if "tradeVolume" in config["plots"]:
        print(f"Generating {statistic} trade volume plot")
        if statistic == "meansByConfig":
            generateSimpleBarChart(dataset, config.get("plotConfigPrefixesWithExperimentalGroups", {}), f"{statistic}_trades.pdf", "tradeVolume", "Mean Trade Volume", "best", percentage=False, plotGroups=plotGroups, xlabel=xlabel)
        else:
            generateSimpleLinePlot(models, dataset, totalTimesteps, f"{statistic}_trades.pdf", "tradeVolume", f"{titleStatistic} Trade Volume", "center right", percentage=False, experimentalGroup=experimentalGroup, plotGroups=plotGroups, xlabel=xlabel)
    if "tradeInteractions" in config["plots"]:
        if statistic == "meansByConfig":
            print(f"{statistic} trade interactions plot function does not exist, skipping. Use same-group interactions plot instead")
        else:
            print(f"Generating {statistic} trade interactions plot")
            generateGroupInteractionLinePlot(models, dataset, totalTimesteps, f"{statistic}_trade_interactions.pdf", "trade", f"{titleStatistic} Trade Interactions", "center right", xlabel=xlabel)
    if "ttl" in config["plots"]:
        print(f"Generating {statistic} time to live plot")
        if statistic == "meansByConfig":
            generateSimpleBarChart(dataset, config.get("plotConfigPrefixesWithExperimentalGroups", {}), f"{statistic}_ttl.pdf", "agentMeanTimeToLive", "Mean Time to Live", "best", percentage=False, plotGroups=plotGroups, xlabel=xlabel)
        else:
            generateSimpleLinePlot(models, dataset, totalTimesteps, f"{statistic}_ttl.pdf", "agentMeanTimeToLive", f"{titleStatistic} Time to Live", "upper right", percentage=False, experimentalGroup=experimentalGroup, plotGroups=plotGroups, xlabel=xlabel)
    if "wealth" in config["plots"]:
        print(f"Generating {statistic} wealth plot")
        if statistic == "meansByConfig":
            generateSimpleBarChart(dataset, config.get("plotConfigPrefixesWithExperimentalGroups", {}), f"{statistic}_wealth.pdf", "meanWealth", "Mean Wealth", "best", percentage=False, plotGroups=plotGroups, xlabel=xlabel)
        else:
            generateSimpleLinePlot(models, dataset, totalTimesteps, f"{statistic}_wealth.pdf", "meanWealth", f"{titleStatistic} Wealth", "center right", percentage=False, experimentalGroup=experimentalGroup, plotGroups=plotGroups, xlabel=xlabel)
    if "wealthHappiness" in config["plots"]:
        print(f"Generating {statistic} wealth happiness plot")
        if statistic == "meansByConfig":
            generateSimpleBarChart(dataset, config.get("plotConfigPrefixesWithExperimentalGroups", {}), f"{statistic}_total_wealth_happiness.pdf", "meanWealthHappiness", "Mean Wealth Happiness", "best", percentage=False, plotGroups=plotGroups, xlabel=xlabel)
        else:
            generateSimpleLinePlot(models, dataset, totalTimesteps, f"{statistic}_total_wealth_happiness.pdf", "meanWealthHappiness", f"{titleStatistic} Wealth Happiness", "center right", percentage=False, experimentalGroup=experimentalGroup, plotGroups=plotGroups, xlabel=xlabel)

def generateGroupInteractionLinePlot(models, dataset, totalTimesteps, outfile, column, label, positioning, xlabel="Timestep"):
    matplotlib.pyplot.rcParams["font.family"] = "serif"
    matplotlib.pyplot.rcParams["font.size"] = 18
    x = [i for i in range(totalTimesteps + 1)]
    y = [0 for i in range(totalTimesteps + 1)]
    modelStrings = {"asimov": "Asimov's Robot", "bentham": "Utilitarian", "egoist": "Egoist", "altruist": "Altruist", "none": "Raw Sugarscape", "rawSugarscape": "Raw Sugarscape",
                    "temperance": "Simple Temperance", "temperancePECS": "Complex Temperance", "multiple": "Multiple", "unknown": "Unknown"}
    interactionColumns = [
        (f"{column}ControlGroupToControlGroup", "Control to Control", "blue"),
        (f"{column}ControlGroupToExperimentalGroup", "Control to Experimental", "magenta"),
        (f"{column}ExperimentalGroupToControlGroup", "Experimental to Control", "cyan"),
        (f"{column}ExperimentalGroupToExperimentalGroup", "Experimental to Experimental", "gold")
    ]
    for model in dataset:
        figure, axes = matplotlib.pyplot.subplots()
        xlabel = "Timestep" if xlabel is None else xlabel
        axes.set(xlabel = xlabel, ylabel = label, xlim = [0, totalTimesteps])
        modelString = model
        if '_' in model:
            modelString = "multiple"
        elif model not in modelStrings:
            modelString = "unknown"
        axes.set_title(modelStrings[modelString])
        for interactionColumn, interactionLabel, color in interactionColumns:
            if interactionColumn in dataset[model]["aggregates"]:
                y = [dataset[model]["aggregates"][interactionColumn][i] for i in range(totalTimesteps + 1)]
                axes.plot(x, y, color=color, label=f"{interactionLabel}")
        axes.legend(loc=positioning, labelspacing=0.1, frameon=False, fontsize=16)
        modelOutfile = outfile.replace(".pdf", f"_{model}_model.pdf")
        figure.savefig(modelOutfile, format="pdf", bbox_inches="tight")
        matplotlib.pyplot.close(figure)

def generatePlotForBiases(dataset, totalTimesteps, outfile, label, positioning, experimentalGroup=None, xlabel="Timestep"):
    matplotlib.pyplot.rcParams["font.family"] = "serif"
    matplotlib.pyplot.rcParams["font.size"] = 18
    x = [i for i in range(totalTimesteps + 1)]
    y = [0 for i in range(totalTimesteps + 1)]
    modelStrings = {"asimov": "Asimov's Robot", "bentham": "Utilitarian", "egoist": "Egoist", "altruist": "Altruist", "none": "Raw Sugarscape", "rawSugarscape": "Raw Sugarscape",
                    "temperance": "Simple Temperance", "temperancePECS": "Complex Temperance", "multiple": "Multiple", "unknown": "Unknown"}
    biasColumns = [("meanAgeismFactor", "Ageism", "green"), ("meanRacismFactor", "Racism", "red"), ("meanSexismFactor", "Sexism", "purple")]

    for model in dataset:
        figure, axes = matplotlib.pyplot.subplots()
        xlabel = "Timestep" if xlabel is None else xlabel
        axes.set(xlabel = xlabel, ylabel = label, xlim = [0, totalTimesteps], ylim = [0, 1])
        modelString = model
        if '_' in model:
            modelString = "multiple"
        elif model not in modelStrings:
            modelString = "unknown"
        axes.set_title(modelStrings[modelString])
        if experimentalGroup != None:
            for column, biasLabel, color in biasColumns:
                controlGroupColumn = "control" + column[0].upper() + column[1:]
                controlGroupLabel = f"Control {biasLabel}"
                experimentalGroupColumn = experimentalGroup + column[0].upper() + column[1:]
                experimentalGroupLabel = experimentalGroup[0].upper() + experimentalGroup[1:] + f" {biasLabel}"
                # Prevent key error if all seeds went extinct for model
                if column in dataset[model]["aggregates"]:
                    y = [dataset[model]["aggregates"][controlGroupColumn][i] for i in range(totalTimesteps + 1)]
                    if not any(value == -1 for value in y):
                        axes.plot(x, y, color=color, label=controlGroupLabel)
                    y = [dataset[model]["aggregates"][experimentalGroupColumn][i] for i in range(totalTimesteps + 1)]
                    if not any(value == -1 for value in y):
                        axes.plot(x, y, color=color, label=experimentalGroupLabel, linestyle="dotted")
        else:
            for column, biasLabel, color in biasColumns:
                # Prevent key error if all seeds went extinct for model
                if column in dataset[model]["aggregates"]:
                    y = [dataset[model]["aggregates"][column][i] for i in range(totalTimesteps + 1)]
                    if not any(value == -1 for value in y):
                        axes.plot(x, y, color=color, label=biasLabel)
        axes.legend(loc=positioning, labelspacing=0.1, frameon=False, fontsize=16)
        modelOutfile = outfile.replace(".pdf", f"_{model}_model.pdf")
        figure.savefig(modelOutfile, format="pdf", bbox_inches="tight")
        matplotlib.pyplot.close(figure)

def generateSameGroupInteractionPercentageBarChart(dataset, configPrefixesWithExperimentalGroups, outfile, label, positioning, xlabel="Configuration"):
    # Loop through each config prefix, producing separate plots for each
    for configPrefix, experimentalGroup in configPrefixesWithExperimentalGroups.items():
        matplotlib.pyplot.rcParams["font.family"] = "serif"
        matplotlib.pyplot.rcParams["font.size"] = 18

        allNumberRanges = set()
        for model in dataset:
            for interaction_proportion_column in ["lending_same_group_proportion", "reproduction_same_group_proportion", "trade_same_group_proportion"]:
                if interaction_proportion_column not in dataset[model]["aggregates"]:
                    continue
                if configPrefix not in dataset[model]["aggregates"][interaction_proportion_column]:
                    continue
                allNumberRanges.update(dataset[model]["aggregates"][interaction_proportion_column][configPrefix].keys())
        allNumberRangesInOrder = sorted(list(allNumberRanges), key=lambda numRange: float(numRange.split("-")[0]))

        x = list(range(len(allNumberRangesInOrder)))
        labels = allNumberRangesInOrder
        xlabel = "Configuration" if xlabel is None else xlabel
        modelStrings = {"asimov": "Asimov's Robot", "bentham": "Utilitarian", "egoist": "Egoist", "altruist": "Altruist", "none": "Raw Sugarscape", "rawSugarscape": "Raw Sugarscape",
                        "temperance": "Simple Temperance", "temperancePECS": "Complex Temperance", "multiple": "Multiple", "unknown": "Unknown"}
        interactionColors = {"lending": "magenta", "reproduction": "gold", "trade": "cyan"}

        # Calculate bar width and positions based on number of bars being plotted to ensure bars fit within axis bounds
        group_width = 0.8
        number_of_bars = 3
        bar_width = group_width / max(1, number_of_bars)
        start_offset = -group_width / 2 + bar_width / 2
        
        for model in dataset:
            figure, axes = matplotlib.pyplot.subplots(figsize=(max(10, len(allNumberRangesInOrder) * 0.75), 7))
            axes.set(xlabel = xlabel, ylabel = label, xlim = [-0.5, len(allNumberRangesInOrder) - 0.5])
            axes.set_xticks(x)
            axes.set_xticklabels(labels, rotation=45, ha="right")
            modelString = model
            if '_' in model:
                modelString = "multiple"
            elif model not in modelStrings:
                modelString = "unknown"

            lendingColumn = "lending_same_group_proportion"
            lendingLabel = "Lending"
            reproductionColumn = "reproduction_same_group_proportion"
            reproductionLabel = "Reproduction"
            tradeColumn = "trade_same_group_proportion"
            tradeLabel = "Trade"

            if lendingColumn in dataset[model]["aggregates"]:
                bar_positions_experimental = [curr_x + start_offset for curr_x in x]
                y, y_err = [], []
                for numRange in allNumberRangesInOrder:
                    if numRange in dataset[model]["aggregates"][lendingColumn][configPrefix]:
                        y.append(dataset[model]["aggregates"][lendingColumn][configPrefix][numRange] * 100)
                        if numRange in dataset[model]["standardDeviations"][lendingColumn][configPrefix]:
                            y_err.append(dataset[model]["standardDeviations"][lendingColumn][configPrefix][numRange] * 100)
                        else:
                            y_err.append(0.0)
                    else:
                        y.append(0.0)
                        y_err.append(0.0)
                
                axes.bar(bar_positions_experimental, y, color=interactionColors["lending"], label=lendingLabel, width=bar_width)
                axes.errorbar(bar_positions_experimental, y, yerr=y_err, fmt="none", ecolor="black", capsize=10, elinewidth=2)
            
            if reproductionColumn in dataset[model]["aggregates"]:
                bar_positions_control = [curr_x + start_offset + bar_width for curr_x in x]
                y, y_err = [], []
                for numRange in allNumberRangesInOrder:
                    if numRange in dataset[model]["aggregates"][reproductionColumn][configPrefix]:
                        y.append(dataset[model]["aggregates"][reproductionColumn][configPrefix][numRange] * 100)
                        if numRange in dataset[model]["standardDeviations"][reproductionColumn][configPrefix]:
                            y_err.append(dataset[model]["standardDeviations"][reproductionColumn][configPrefix][numRange] * 100)
                        else:
                            y_err.append(0.0)
                    else:
                        y.append(0.0)
                        y_err.append(0.0)
                
                axes.bar(bar_positions_control, y, color=interactionColors["reproduction"], label=reproductionLabel, width=bar_width)
                axes.errorbar(bar_positions_control, y, yerr=y_err, fmt="none", ecolor="black", capsize=10, elinewidth=2)
            
            if tradeColumn in dataset[model]["aggregates"]:
                bar_positions_control = [curr_x + start_offset + (2 * bar_width) for curr_x in x]
                y, y_err = [], []
                for numRange in allNumberRangesInOrder:
                    if numRange in dataset[model]["aggregates"][tradeColumn][configPrefix]:
                        y.append(dataset[model]["aggregates"][tradeColumn][configPrefix][numRange] * 100)
                        if numRange in dataset[model]["standardDeviations"][tradeColumn][configPrefix]:
                            y_err.append(dataset[model]["standardDeviations"][tradeColumn][configPrefix][numRange] * 100)
                        else:
                            y_err.append(0.0)
                    else:
                        y.append(0.0)
                        y_err.append(0.0)
                
                axes.bar(bar_positions_control, y, color=interactionColors["trade"], label=tradeLabel, width=bar_width)
                axes.errorbar(bar_positions_control, y, yerr=y_err, fmt="none", ecolor="black", capsize=10, elinewidth=2)
            axes.legend(loc=positioning, labelspacing=0.1, frameon=True, fontsize=16, facecolor='white', framealpha=1.0)
            axes.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(xmax=100))
            modelOutfile = outfile.replace(".pdf", f"_{model}_model.pdf")
            figure.savefig(configPrefix + "_" + modelOutfile, format="pdf", bbox_inches="tight")
            matplotlib.pyplot.close(figure)

def generateSimpleBarChart(dataset, configPrefixesWithExperimentalGroups, outfile, column, label, positioning, percentage=False, plotGroups=False, xlabel="Configuration"):
    # Loop through each config prefix, producing separate plots for each
    for configPrefix, experimentalGroup in configPrefixesWithExperimentalGroups.items():
        matplotlib.pyplot.rcParams["font.family"] = "serif"
        matplotlib.pyplot.rcParams["font.size"] = 18

        allNumberRanges = set()
        for model in dataset:
            if column not in dataset[model]["aggregates"]:
                continue
            if configPrefix not in dataset[model]["aggregates"][column]:
                continue
            allNumberRanges.update(dataset[model]["aggregates"][column][configPrefix].keys())
        allNumberRangesInOrder = sorted(list(allNumberRanges), key=lambda numRange: float(numRange.split("-")[0]))

        x = list(range(len(allNumberRangesInOrder)))
        labels = allNumberRangesInOrder
        xlabel = "Configuration" if xlabel is None else xlabel
        modelStrings = {"asimov": "Asimov's Robot", "bentham": "Utilitarian", "egoist": "Egoist", "altruist": "Altruist", "none": "Raw Sugarscape", "rawSugarscape": "Raw Sugarscape",
                        "temperance": "Simple Temperance", "temperancePECS": "Complex Temperance", "multiple": "Multiple", "unknown": "Unknown"}
        modelColors = {"asimov": "blue", "bentham": "magenta", "egoist": "cyan", "altruist": "gold", "none": "black", "rawSugarscape": "black ", "temperance": "blue", "temperancePECS": "purple", "multiple": "red", "unknown": "green"}
        groupColors = {"experimental": "magenta", "control": "cyan"}

        # Calculate bar width and positions based on number of bars being plotted to ensure bars fit within axis bounds
        group_width = 0.8
        number_of_bars = 2 if experimentalGroup != None and plotGroups == True else len(dataset)
        bar_width = group_width / max(1, number_of_bars)
        start_offset = -group_width / 2 + bar_width / 2
        
        # If plotting separate groups, split up models into different charts to avoid overcrowding
        if experimentalGroup != None and plotGroups == True:
            for model in dataset:
                figure, axes = matplotlib.pyplot.subplots(figsize=(max(10, len(allNumberRangesInOrder) * 0.75), 7))
                axes.set(xlabel = xlabel, ylabel = label, xlim = [-0.5, len(allNumberRangesInOrder) - 0.5])
                axes.set_xticks(x)
                axes.set_xticklabels(labels, rotation=45, ha="right")
                modelString = model
                if '_' in model:
                    modelString = "multiple"
                elif model not in modelStrings:
                    modelString = "unknown"
                experimentalGroupColumn = experimentalGroup + column[0].upper() + column[1:]
                experimentalGroupLabel = experimentalGroup[0].upper() + experimentalGroup[1:] + f" {modelStrings[modelString]}"
                controlGroupColumn = "control" + column[0].upper() + column[1:]
                controlGroupLabel = f"Control {modelStrings[modelString]}"
                # Prevent key error if all seeds went extinct for model
                if experimentalGroupColumn in dataset[model]["aggregates"]:
                    bar_positions_experimental = [curr_x + start_offset for curr_x in x]
                    
                    y, y_err = [], []
                    for numRange in allNumberRangesInOrder:
                        if numRange in dataset[model]["aggregates"][experimentalGroupColumn][configPrefix]:
                            y.append(dataset[model]["aggregates"][experimentalGroupColumn][configPrefix][numRange])
                            if numRange in dataset[model]["standardDeviations"][experimentalGroupColumn][configPrefix]:
                                y_err.append(dataset[model]["standardDeviations"][experimentalGroupColumn][configPrefix][numRange])
                            else:
                                y_err.append(0.0)
                        else:
                            y.append(0.0)
                            y_err.append(0.0)
                    
                    axes.bar(bar_positions_experimental, y, color=groupColors["experimental"], label=experimentalGroupLabel, width=bar_width)
                    axes.errorbar(bar_positions_experimental, y, yerr=y_err, fmt="none", ecolor="black", elinewidth=2)
                if controlGroupColumn in dataset[model]["aggregates"]:
                    bar_positions_control = [curr_x + start_offset + bar_width for curr_x in x]
                    
                    y, y_err = [], []
                    for numRange in allNumberRangesInOrder:
                        if numRange in dataset[model]["aggregates"][controlGroupColumn][configPrefix]:
                            y.append(dataset[model]["aggregates"][controlGroupColumn][configPrefix][numRange])
                            if numRange in dataset[model]["standardDeviations"][controlGroupColumn][configPrefix]:
                                y_err.append(dataset[model]["standardDeviations"][controlGroupColumn][configPrefix][numRange])
                            else:
                                y_err.append(0.0)
                        else:
                            y.append(0.0)
                            y_err.append(0.0)
                    
                    axes.bar(bar_positions_control, y, color=groupColors["control"], label=controlGroupLabel, width=bar_width)
                    axes.errorbar(bar_positions_control, y, yerr=y_err, fmt="none", ecolor="black", elinewidth=2)
                axes.legend(loc=positioning, labelspacing=0.1, frameon=True, fontsize=16, facecolor='white', framealpha=1.0)
                if percentage == True:
                    axes.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter())
                modelOutfile = outfile.replace(".pdf", f"_{model}_model.pdf")
                figure.savefig(configPrefix + "_" + modelOutfile, format="pdf", bbox_inches="tight")
                matplotlib.pyplot.close(figure)
        else:
            figure, axes = matplotlib.pyplot.subplots(figsize=(max(10, len(allNumberRangesInOrder) * 0.75), 7))
            axes.set(xlabel = xlabel, ylabel = label, xlim = [-0.5, len(allNumberRangesInOrder) - 0.5])
            axes.set_xticks(x)
            axes.set_xticklabels(labels, rotation=45, ha="right")
            for index, model in enumerate(dataset):
                modelString = model
                if '_' in model:
                    modelString = "multiple"
                elif model not in modelStrings:
                    modelString = "unknown"
                # Prevent key error if all seeds went extinct for model
                if column in dataset[model]["aggregates"]:
                    bar_positions = [curr_x + start_offset + index * bar_width for curr_x in x]
                    
                    y, y_err = [], []
                    for numRange in allNumberRangesInOrder:
                        if numRange in dataset[model]["aggregates"][column][configPrefix]:
                            y.append(dataset[model]["aggregates"][column][configPrefix][numRange])
                            if numRange in dataset[model]["standardDeviations"][column][configPrefix]:
                                y_err.append(dataset[model]["standardDeviations"][column][configPrefix][numRange])
                            else:
                                y_err.append(0.0)
                        else:
                            y.append(0.0)
                            y_err.append(0.0)
                    
                    axes.bar(bar_positions, y, color=modelColors[modelString], label=modelStrings[modelString], width=bar_width)
                    axes.errorbar(bar_positions, y, yerr=y_err, fmt="none", ecolor="black", capsize=10, elinewidth=2)
            axes.legend(loc=positioning, labelspacing=0.1, frameon=True, fontsize=16, facecolor='white', framealpha=1.0)
            if percentage == True:
                axes.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter())
            figure.savefig(configPrefix + "_" + outfile, format="pdf", bbox_inches="tight")
            matplotlib.pyplot.close(figure)

def generateSimpleLinePlot(models, dataset, totalTimesteps, outfile, column, label, positioning, percentage=False, experimentalGroup=None, plotGroups=False, xlabel="Timestep"):
    matplotlib.pyplot.rcParams["font.family"] = "serif"
    matplotlib.pyplot.rcParams["font.size"] = 18
    figure, axes = matplotlib.pyplot.subplots()
    xlabel = "Timestep" if xlabel is None else xlabel
    axes.set(xlabel = xlabel, ylabel = label, xlim = [0, totalTimesteps])
    x = [i for i in range(totalTimesteps + 1)]
    y = [0 for i in range(totalTimesteps + 1)]
    lines = []
    modelStrings = {"asimov": "Asimov's Robot", "bentham": "Utilitarian", "egoist": "Egoist", "altruist": "Altruist", "none": "Raw Sugarscape", "rawSugarscape": "Raw Sugarscape",
                    "temperance": "Simple Temperance", "temperancePECS": "Complex Temperance", "multiple": "Multiple", "unknown": "Unknown"}
    colors = {"asimov": "blue", "bentham": "magenta", "egoist": "cyan", "altruist": "gold", "none": "black", "rawSugarscape": "black ", "temperance": "blue", "temperancePECS": "purple", "multiple": "red", "unknown": "green"}

    for model in dataset:
        modelString = model
        if '_' in model:
            modelString = "multiple"
        elif model not in modelStrings:
            modelString = "unknown"
        if experimentalGroup != None and plotGroups == True:
            controlGroupColumn = "control" + column[0].upper() + column[1:]
            controlGroupLabel = f"Control {modelStrings[modelString]}"
            experimentalGroupColumn = experimentalGroup + column[0].upper() + column[1:]
            experimentalGroupLabel = experimentalGroup[0].upper() + experimentalGroup[1:] + f" {modelStrings[modelString]}"
            # Prevent key error if all seeds went extinct for model
            if column in dataset[model]["aggregates"]:
                y = [dataset[model]["aggregates"][controlGroupColumn][i] for i in range(totalTimesteps + 1)]
                axes.plot(x, y, color=colors[modelString], label=controlGroupLabel)
                y = [dataset[model]["aggregates"][experimentalGroupColumn][i] for i in range(totalTimesteps + 1)]
                axes.plot(x, y, color=colors[modelString], label=experimentalGroupLabel, linestyle="dotted")
        # Prevent key error if all seeds went extinct for model
        elif column in dataset[model]["aggregates"]:
            y = [dataset[model]["aggregates"][column][i] for i in range(totalTimesteps + 1)]
            axes.plot(x, y, color=colors[modelString], label=modelStrings[modelString])
        axes.legend(loc=positioning, labelspacing=0.1, frameon=False, fontsize=16)
    if percentage == True:
        axes.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter())
    figure.savefig(outfile, format="pdf", bbox_inches="tight")

def parseDataset(path, dataset, totalTimesteps, statistic, configPrefixesWithExperimentalGroups=None, skipExtinct=False):
    encodedDir = os.fsencode(path)
    files = [f for f in os.listdir(encodedDir) if os.fsdecode(f).endswith("json") or os.fsdecode(f).endswith(".csv")]
    printFileLength = len(max(files, key=len))
    fileCount = 1
    totalFiles = len(files)
    for file in files:
        filename = os.fsdecode(file)
        filePath = path + filename
        # filename should not contain "_" other than to separate config prefix from rest of filename
        if "_" in filename:
            configPrefix, _, filenameExcludingPrefix = filename.partition("_")
            prefixMatch = re.match(r"^(?P<basePrefix>.+?)-(?P<int1>\d+)(?:-(?P<int2>\d+))?$", configPrefix)
            if prefixMatch:
                basePrefix = prefixMatch.group("basePrefix")
                num1 = int(prefixMatch.group("int1")) / 100
                num2 = int(prefixMatch.group("int2")) / 100 if prefixMatch.group("int2") else None
                configNumRange = f"{num1:.2f}-{num2:.2f}" if num2 is not None else f"{num1:.2f}"
            else:
                basePrefix = configPrefix
                configNumRange = ""
            if configPrefixesWithExperimentalGroups and basePrefix not in configPrefixesWithExperimentalGroups.keys() and statistic == "meansByConfig":
                print(f"Config prefix {basePrefix} not found in configPrefixesWithExperimentalGroups, skipping file {filename}")
                continue
        else:
            basePrefix = ""
            configNumRange = ""
            filenameExcludingPrefix = filename        
        fileDecisionModel = re.compile(r"^([A-z]*)(\d*)\.(json|csv)")
        fileSearch = re.search(fileDecisionModel, filenameExcludingPrefix)
        if fileSearch == None:
            continue
        model = fileSearch.group(1)
        if model not in dataset:
            continue
        seed = fileSearch.group(2)
        log = open(filePath)
        printProgress(filename, fileCount, totalFiles, printFileLength)
        fileCount += 1
        rawData = None
        if filename.endswith(".json"):
            rawData = json.loads(log.read())
        else:
            rawData = list(csv.DictReader(log))

        if int(rawData[-1]["population"]) == 0:
            dataset[model]["extinct"] += 1
            if skipExtinct == True:
                continue
        elif int(rawData[-1]["population"]) <= int(rawData[0]["population"]):
            dataset[model]["worse"] += 1
        else:
            dataset[model]["better"] += 1

        dataset[model]["runs"] += 1
        
        if statistic == "meansByConfig":
            if "metrics" not in dataset[model]:
                dataset[model]["metrics"] = {}
            # For each entry, compute average across timesteps for this single run            
            for entry in rawData[0].keys():
                if entry in ["agentWealths", "agentTimesToLive", "agentTimesToLiveAgeLimited", "agentTotalMetabolism"]:
                    continue
                findWeightedAverageAcrossTimesteps(dataset, model, rawData, entry, basePrefix, configNumRange, experimentalGroup=configPrefixesWithExperimentalGroups[basePrefix])
            # Compute total proportions of same-group interactions for lending, reproduction, and trade for this config
            findSameGroupInteractionProportionsAcrossTimesteps(dataset, model, rawData, basePrefix, configNumRange, experimentalGroup=configPrefixesWithExperimentalGroups[basePrefix])
            
            # Collect number of runs where control/experimental groups went extinct for each config prefix and number range
            if configPrefixesWithExperimentalGroups[basePrefix] != None:
                if "controlExtinctPerConfig" not in dataset[model]["metrics"]:
                    dataset[model]["metrics"]["controlExtinctPerConfig"] = {}
                if basePrefix not in dataset[model]["metrics"]["controlExtinctPerConfig"]:
                    dataset[model]["metrics"]["controlExtinctPerConfig"][basePrefix] = {}
                if configNumRange not in dataset[model]["metrics"]["controlExtinctPerConfig"][basePrefix]:
                    dataset[model]["metrics"]["controlExtinctPerConfig"][basePrefix][configNumRange] = 0
                if int(rawData[-1]["controlPopulation"]) == 0:
                    dataset[model]["metrics"]["controlExtinctPerConfig"][basePrefix][configNumRange] += 1
                
                experimentalGroup = configPrefixesWithExperimentalGroups[basePrefix]
                if f"{experimentalGroup}ExtinctPerConfig" not in dataset[model]["metrics"]:
                    dataset[model]["metrics"][f"{experimentalGroup}ExtinctPerConfig"] = {}
                if basePrefix not in dataset[model]["metrics"][f"{experimentalGroup}ExtinctPerConfig"]:
                    dataset[model]["metrics"][f"{experimentalGroup}ExtinctPerConfig"][basePrefix] = {}
                if configNumRange not in dataset[model]["metrics"][f"{experimentalGroup}ExtinctPerConfig"][basePrefix]:
                    dataset[model]["metrics"][f"{experimentalGroup}ExtinctPerConfig"][basePrefix][configNumRange] = 0
                if int(rawData[-1][f"{experimentalGroup}Population"]) == 0:
                    dataset[model]["metrics"][f"{experimentalGroup}ExtinctPerConfig"][basePrefix][configNumRange] += 1
            
            if "extinctPerConfig" not in dataset[model]["metrics"]:
                dataset[model]["metrics"]["extinctPerConfig"] = {}
            if basePrefix not in dataset[model]["metrics"]["extinctPerConfig"]:
                dataset[model]["metrics"]["extinctPerConfig"][basePrefix] = {}
            if configNumRange not in dataset[model]["metrics"]["extinctPerConfig"][basePrefix]:
                dataset[model]["metrics"]["extinctPerConfig"][basePrefix][configNumRange] = 0
            dataset[model]["metrics"]["extinctPerConfig"][basePrefix][configNumRange] += 1

            if "runsPerConfig" not in dataset[model]["metrics"]:
                dataset[model]["metrics"]["runsPerConfig"] = {}
            if basePrefix not in dataset[model]["metrics"]["runsPerConfig"]:
                dataset[model]["metrics"]["runsPerConfig"][basePrefix] = {}
            if configNumRange not in dataset[model]["metrics"]["runsPerConfig"][basePrefix]:
                dataset[model]["metrics"]["runsPerConfig"][basePrefix][configNumRange] = 0
            dataset[model]["metrics"]["runsPerConfig"][basePrefix][configNumRange] += 1
        else:       
            i = 1
            for item in rawData:
                if int(item["timestep"]) > totalTimesteps:
                    break
                if int(item["timestep"]) > dataset[model]["timesteps"]:
                    dataset[model]["timesteps"] += 1

                for entry in item:
                    if entry in ["agentWealths", "agentTimesToLive", "agentTimesToLiveAgeLimited", "agentTotalMetabolism"]:
                        continue
                    if entry not in dataset[model]["metrics"]:
                        dataset[model]["metrics"][entry] = [[] for j in range(totalTimesteps + 1)]
                    if item[entry] == "None":
                        item[entry] = 0
                    dataset[model]["metrics"][entry][i-1].append(float(item[entry]))
                i += 1
    print(f"\r{' ' * os.get_terminal_size().columns}", end='\r')
    for model in dataset:
        if dataset[model]["runs"] == 0:
            print(f"No simulation runs found for the {model} decision model")
    return dataset

def parseOptions():
    commandLineArgs = sys.argv[1:]
    shortOptions = "c:p:s:t:x:h"
    longOptions = ("conf=", "groups", "path=", "help", "skip", "xlabel=")
    options = {"config": None, "path": None, "plotGroups": False, "skip": False, "xlabel": None}
    try:
        args, vals = getopt.getopt(commandLineArgs, shortOptions, longOptions)
    except getopt.GetoptError as err:
        print(err)
        exit(0)
    for currArg, currVal in args:
        if currArg in ("-c", "--conf"):
            if currVal == "":
                print("No config file provided.")
                printHelp()
            options["config"] = currVal
        elif currArg in ("-g", "--groups"):
            options["plotGroups"] = True
        elif currArg in ("-p", "--path"):
            options["path"] = currVal
            if currVal == "":
                print("No dataset path provided.")
                printHelp()
        elif currArg in ("-h", "--help"):
            printHelp()
        elif currArg in ("-s", "--skip"):
            options["skip"] = True
        elif currArg in ("-x", "--xlabel"):
            if currVal == "":
                print("No x-axis label provided.")
                printHelp()
            options["xlabel"] = currVal
    flag = 0
    if options["path"] == None:
        print("Dataset path required.")
        flag = 1
    if options["config"] == None:
        print("Configuration file path required.")
        flag = 1
    if flag == 1:
        printHelp()
    return options

def printHelp():
    print("Usage:\n\tpython plot.py --path /path/to/data --conf /path/to/config > results.dat\n\nOptions:\n\t-c,--conf\tUse the specified path to configurable settings file.\n\t-p,--path\tUse the specified path to find dataset JSON files.\n\t-s,--skip\tSkip including extinct societies in produced graphs.\n\t-x,--xlabel\tSet the x-axis label for the plots.\n\t-h,--help\tDisplay this message.")
    exit(0)

def printProgress(filename, filesParsed, totalFiles, fileLength, decimals=2):
    barLength = os.get_terminal_size().columns // 2
    progress = round(((filesParsed / totalFiles) * 100), decimals)
    filledLength = (barLength * filesParsed) // totalFiles
    bar = '█' * filledLength + '-' * (barLength - filledLength)
    printString = f"\rParsing {filename:>{fileLength}}: |{bar}| {filesParsed} / {totalFiles} ({progress}%)"
    if filesParsed == totalFiles:
        print(f"\r{' ' * os.get_terminal_size().columns}", end='\r')
    else:
        print(f"\r{printString}", end='\r')

def printSummaryStats(dataset):
    print(f"Model population performance:\n{'Decision Model':^30} {'Extinct':^5} {'Worse':^5} {'Better':^5}")
    for model in dataset:
        print(f"{model:^30} {dataset[model]['extinct']:^5} {dataset[model]['worse']:^5} {dataset[model]['better']:^5}")

if __name__ == "__main__":
    options = parseOptions()
    path = options["path"]
    plotGroups = options["plotGroups"]
    config = options["config"]
    skipExtinct = options["skip"]
    xlabel = options["xlabel"]
    configFile = open(config)
    config = json.loads(configFile.read())
    configFile.close()
    experimentalGroup = config["sugarscapeOptions"]["experimentalGroup"] if "experimentalGroup" in config["sugarscapeOptions"] else None
    config = config["dataCollectionOptions"]
    totalTimesteps = config["plotTimesteps"]
    models = config["decisionModels"]
    statistic = config["plotStatistic"]
    configPrefixesWithExperimentalGroups = config["plotConfigPrefixesWithExperimentalGroups"] if "plotConfigPrefixesWithExperimentalGroups" in config else None
    dataset = {}
    for model in models:
        modelString = model
        if type(model) == list:
            modelString = '_'.join(model)
        dataset[modelString] = {"runs": 0, "extinct": 0, "worse": 0, "better": 0, "timesteps": 0, "aggregates": {}, "firstQuartiles": {}, "thirdQuartiles": {}, "standardDeviations": {}, "metrics": {}}

    if not os.path.exists(path):
        print(f"Path {path} not recognized.")
        printHelp()

    dataset = parseDataset(path, dataset, totalTimesteps, statistic, configPrefixesWithExperimentalGroups, skipExtinct)
    if statistic == "mean":
        dataset = findMeans(dataset)
    elif statistic == "median":
        dataset = findMedians(dataset)
    elif statistic == "meansByConfig":
        dataset = findMeansByConfig(dataset)
    else:
        print(f"Plotting statistic {statistic} not recognized.")
        printHelp()

    generatePlots(config, models, totalTimesteps, dataset, statistic, experimentalGroup, plotGroups, xlabel)
    printSummaryStats(dataset)
    exit(0)
