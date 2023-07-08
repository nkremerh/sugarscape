def findBenthamActUtilitarianValueOfCell(agent, cell):
    cellSiteWealth = cell.sugar + cell.spice
    # Max combat loot for sugar and spice
    globalMaxCombatLoot = cell.environment.maxCombatLoot * 2
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
        #intensity = cellSiteWealth
        #if cell.agent != None and cell.agent != neighbor:
        #    intensity += min(cell.agent.wealth, globalMaxCombatLoot)
        #intensity = intensity / (globalMaxWealth + globalMaxCombatLoot)
        duration = cellDuration / cellMaxSiteWealth if cellMaxSiteWealth > 0 else 0
        # Agent discount, futureDuration, and futureIntensity implement Bentham's purity and fecundity
        discount = 0.5
        futureDuration = (cellSiteWealth - neighborMetabolism) / neighborMetabolism if neighborMetabolism > 0 else cellSiteWealth
        futureDuration = futureDuration / cellMaxSiteWealth if cellMaxSiteWealth > 0 else 0
        futureIntensity = cellNeighborWealth / (globalMaxWealth * 4)
        # Assuming agent can only see in four cardinal directions
        extent = len(agent.neighborhood) / (neighbor.vision * 4) if neighbor.vision > 0 else 1
        neighborValueOfCell = 0
        # If not the agent moving, consider these as opportunity costs
        if neighbor != agent and cell != neighbor.cell:
            duration = -1 * duration
            intensity = -1 * intensity
            futureDuration = -1 * futureDuration
            futureIntensity = -1 * futureIntensity
            neighborValueOfCell = neighbor.ethicalFactor * (certainty * proximity * (intensity + duration + (discount * futureDuration * futureIntensity) + extent))
        # If move will kill this neighbor, consider this a penalty
        elif neighbor != agent and cell == neighbor.cell:
            neighborValueOfCell = -1 * (certainty * proximity * (intensity + duration + (discount * futureDuration * futureIntensity) + extent))
            # If penalty is too slight, make it more severe
            if neighborValueOfCell > -1:
                neighborValueOfCell = -1
        else:
            # TODO: intensity + duration + extent + discount * (futureIntensity + futureDuration + futureExtent)
            #neighborValueOfCell = neighbor.ethicalFactor * (certainty * ((10 * potentialNice) + (5 * intensity) + (4 * duration) + (3 * proximity) + (2 * (discount * futureDuration * futureIntensity)) + extent))
            neighborValueOfCell = neighbor.ethicalFactor * (certainty * proximity * (intensity + duration + (discount * futureDuration * futureIntensity) + extent))
        cellValue += neighborValueOfCell
    return cellValue

def findModifiedActUtilitarianValueOfCell(agent, cell):
    cellSiteWealth = cell.sugar + cell.spice
    # Max combat loot for sugar and spice
    globalMaxCombatLoot = cell.environment.maxCombatLoot * 2
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
        #intensity = cellSiteWealth
        #if cell.agent != None and cell.agent != neighbor:
        #    intensity += min(cell.agent.wealth, globalMaxCombatLoot)
        #intensity = intensity / (globalMaxWealth + globalMaxCombatLoot)
        duration = cellDuration / cellMaxSiteWealth if cellMaxSiteWealth > 0 else 0
        # Agent discount, futureDuration, and futureIntensity implement Bentham's purity and fecundity
        discount = 0.5
        futureDuration = (cellSiteWealth - neighborMetabolism) / neighborMetabolism if neighborMetabolism > 0 else cellSiteWealth
        futureDuration = futureDuration / cellMaxSiteWealth if cellMaxSiteWealth > 0 else 0
        futureIntensity = cellNeighborWealth / (globalMaxWealth * 4)
        # Assuming agent can only see in four cardinal directions
        extent = len(agent.neighborhood) / (neighbor.vision * 4) if neighbor.vision > 0 else 1
        neighborValueOfCell = 0
        # If not the agent moving, consider these as opportunity costs
        if neighbor != agent and cell != neighbor.cell:
            duration = -1 * duration
            intensity = -1 * intensity
            futureDuration = -1 * futureDuration
            futureIntensity = -1 * futureIntensity
            neighborValueOfCell = neighbor.ethicalFactor * (certainty * proximity * (intensity * duration) + (discount * futureDuration * futureIntensity) * extent)
        # If move will kill this neighbor, consider this a penalty
        elif neighbor != agent and cell == neighbor.cell:
            neighborValueOfCell = -1 * (certainty * proximity * (intensity * duration) + (discount * futureDuration * futureIntensity) * extent)
            # If penalty is too slight, make it more severe
            if neighborValueOfCell > -1:
                neighborValueOfCell = -1
        else:
            # TODO: intensity + duration + extent + discount * (futureIntensity + futureDuration + futureExtent)
            #neighborValueOfCell = neighbor.ethicalFactor * (certainty * ((10 * potentialNice) + (5 * intensity) + (4 * duration) + (3 * proximity) + (2 * (discount * futureDuration * futureIntensity)) + extent))
            neighborValueOfCell = neighbor.ethicalFactor * (certainty * proximity * (intensity * duration) + (discount * futureDuration * futureIntensity) * extent)
        cellValue += neighborValueOfCell
    return cellValue

def findAltruisticActUtilitarianValueOfCell(agent, cell):
    cellSiteWealth = cell.sugar + cell.spice
    # Max combat loot for sugar and spice
    globalMaxCombatLoot = cell.environment.maxCombatLoot * 2
    cellMaxSiteWealth = cell.maxSugar + cell.maxSpice
    cellNeighborWealth = cell.findNeighborWealth()
    globalMaxWealth = cell.environment.globalMaxSugar + cell.environment.globalMaxSpice
    cellValue = 0
    for neighbor in agent.neighborhood:
        if neighbor == agent:
            continue
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
        neighborValueOfCell = 0
        # If not the agent moving, consider these as opportunity costs
        if neighbor != agent and cell != neighbor.cell:
            duration = -1 * duration
            intensity = -1 * intensity
            futureDuration = -1 * futureDuration
            futureIntensity = -1 * futureIntensity
            neighborValueOfCell = neighbor.ethicalFactor * (certainty * proximity * (intensity + duration + (discount * futureDuration * futureIntensity) + extent))
        # If move will kill this neighbor, consider this a penalty
        elif neighbor != agent and cell == neighbor.cell:
            neighborValueOfCell = -1 * (certainty * proximity * (intensity + duration + (discount * futureDuration * futureIntensity) + extent))
            # If penalty is too slight, make it more severe
            if neighborValueOfCell > -1:
                neighborValueOfCell = -1
        else:
            # TODO: intensity + duration + extent + discount * (futureIntensity + futureDuration + futureExtent)
            #neighborValueOfCell = neighbor.ethicalFactor * (certainty * ((10 * potentialNice) + (5 * intensity) + (4 * duration) + (3 * proximity) + (2 * (discount * futureDuration * futureIntensity)) + extent))
            neighborValueOfCell = neighbor.ethicalFactor * (certainty * proximity * (intensity + duration + (discount * futureDuration * futureIntensity) + extent))
        cellValue += neighborValueOfCell
    return cellValue

def findEgoisticActUtilitarianValueOfCell(agent, cell):
    cellSiteWealth = cell.sugar + cell.spice
    globalMaxCombatLoot = cell.environment.maxCombatLoot * 2
    cellMaxSiteWealth = cell.maxSugar + cell.maxSpice
    if cell.agent != None:
        cellSiteWealth += min(cell.agent.wealth, globalMaxCombatLoot)
        cellMaxSiteWealth += min(cell.agent.wealth, globalMaxCombatLoot)
    cellNeighborWealth = cell.findNeighborWealth()
    globalMaxWealth = cell.environment.globalMaxSugar + cell.environment.globalMaxSpice
    cellValue = 0
    canSee = 0
    for neighbor in agent.neighborhood:
        if neighbor.canReachCell(cell) == True:
            canSee += 1
    timestepDistance = 1
    neighborMetabolism = neighbor.sugarMetabolism + neighbor.spiceMetabolism
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
    extent = canSee / (neighbor.vision * 4) if neighbor.vision > 0 else 1
    neighborValueOfCell = neighbor.ethicalFactor * (certainty * proximity * (intensity + duration + (discount * futureDuration * futureIntensity) + extent))
    cellValue += neighborValueOfCell
    return cellValue
