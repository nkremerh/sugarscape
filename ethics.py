def findBenthamActUtilitarianValueOfCell(agent, cell):
    cellSiteWealth = cell.sugar + cell.spice
    cellMaxSiteWealth = cell.maxSugar + cell.maxSpice
    cellNeighborWealth = cell.findNeighborWealth()
    globalMaxWealth = cell.environment.globalMaxSugar + cell.environment.globalMaxSpice
    cellValue = 0
    for neighbor in agent.neighborhood:
        # TODO: Factor potentialNice into intensity, duration, and purity/fecundity
        #potentialNice = neighbor.findPotentialNiceOfCell(cell)
        # Timesteps to reach cell, currently 1 since agent vision and movement are equal
        timestepDistance = 1
        neighborMetabolism = neighbor.sugarMetabolism + neighbor.spiceMetabolism
        # If agent does not have metabolism, set duration to seemingly infinite
        cellDuration = cellSiteWealth / neighborMetabolism if neighborMetabolism > 0 else 0
        certainty = 1 if neighbor.canReachCell(cell) == True else 0
        proximity = 1 / timestepDistance
        intensity = (1 / (1 + neighbor.findDaysToDeath()) / (1 + cell.pollution))
        duration = cellDuration / cellMaxSiteWealth if cellMaxSiteWealth > 0 else 0
        # Agent discount, futureDuration, and futureIntensity implement Bentham's purity and fecundity
        discount = 0.5
        futureDuration = (cellSiteWealth - neighborMetabolism) / neighborMetabolism if neighborMetabolism > 0 else cellSiteWealth
        futureDuration = futureDuration / cellMaxSiteWealth if cellMaxSiteWealth > 0 else 0
        futureIntensity = cellNeighborWealth / (globalMaxWealth * 4)
        # Assuming agent can only see in four cardinal directions
        extent = len(agent.neighborhood) / (neighbor.vision * 4) if neighbor.vision > 0 else 1
        # If not the agent moving, consider these as opportunity costs
        if neighbor != agent:
            duration = -1 * duration
            intensity = -1 * intensity
            futureDuration = -1 * futureDuration
            futureIntensity = -1 * futureIntensity
        # TODO: intensity + duration + extent + discount * (futureIntensity + futureDuration + futureExtent)
        #neighborValueOfCell = neighbor.ethicalFactor * (certainty * ((10 * potentialNice) + (5 * intensity) + (4 * duration) + (3 * proximity) + (2 * (discount * futureDuration * futureIntensity)) + extent))
        neighborValueOfCell = neighbor.ethicalFactor * (certainty * proximity * (intensity + duration + (discount * futureDuration * futureIntensity) + extent))
        # If move will kill this neighbor, consider this a penalty
        if cell == neighbor.cell and neighbor != agent:
            neighborValueOfCell = -1
        cellValue += neighborValueOfCell
    return cellValue
