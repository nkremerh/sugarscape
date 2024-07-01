import math
import tkinter

class GUI:
    def __init__(self, sugarscape, screenHeight=1000, screenWidth=900):
        self.sugarscape = sugarscape
        self.screenHeight = screenHeight
        self.screenWidth = screenWidth
        self.window = None
        self.canvas = None
        self.grid = [[None for j in range(self.sugarscape.environmentHeight)]for i in range(self.sugarscape.environmentWidth)]
        self.colors = {"sugar": "#F2FA00", "spice": "#9B4722", "sugarAndSpice": "#CFB20E", "noSex": "#FA3232", "female": "#FA32FA", "male": "#3232FA", "pollution": "#803280", "healthy": "#3232FA", "sick": "#FA3232"}
        self.palette = ["#FA3232", "#3232FA", "#32FA32", "#32FAFA", "#FA32FA", "#AA3232", "#3232AA", "#32AA32", "#32AAAA", "#AA32AA", "#FA8800", "#00FA88", "#8800FA", "#FA8888", "#8888FA", "#88FA88", "#FA3288", "#3288FA", "#88FA32", "#AA66AA", "#66AAAA", "#3ED06E", "#6E3ED0", "#D06E3E", "#000000"]
        numTribes = self.sugarscape.configuration["environmentMaxTribes"]
        numDecisionModels = len(self.sugarscape.configuration["agentDecisionModels"])
        for i in range(numTribes):
            self.colors[str(i)] = self.palette[i]
        for i in range(numDecisionModels):
            self.colors[self.sugarscape.configuration["agentDecisionModels"][i]] = self.palette[i]
        self.widgets = {}
        self.lastSelectedAgentColor = None
        self.lastSelectedEnvironmentColor = None
        self.activeColorOptions = {"agent": None, "environment": None}
        self.activeNetwork = None
        self.highlightedCell = None
        self.highlightedAgent = None
        self.highlightRectangle = None
        self.menuTrayColumns = 5
        self.menuTrayOffset = 110
        self.windowBorderOffset = 10
        self.borderEdge = 5
        self.siteHeight = (self.screenHeight - self.menuTrayOffset) / self.sugarscape.environmentHeight
        self.siteWidth = (self.screenWidth - self.windowBorderOffset) / self.sugarscape.environmentWidth
        self.configureWindow()
        self.stopSimulation = False

    def clearHighlight(self):
        self.highlightedAgent = None
        self.highlightedCell = None
        if self.highlightRectangle != None:
            self.canvas.delete(self.highlightRectangle)
            self.highlightRectangle = None
        self.updateHighlightedCellStats()

    def configureAgentColorNames(self):
        return ["Disease", "Sex", "Tribes", "Decision Models"]

    def configureButtons(self, window):
        playButton = tkinter.Button(window, text="Play Simulation", command=self.doPlayButton)
        playButton.grid(row=0, column=0, sticky="nsew")
        stepButton = tkinter.Button(window, text="Step Forward", command=self.doStepForwardButton, relief=tkinter.RAISED)
        stepButton.grid(row=0, column=1, sticky="nsew")

        networkButton = tkinter.Menubutton(window, text="Networks", relief=tkinter.RAISED)
        networkMenu = tkinter.Menu(networkButton, tearoff=0)
        networkButton.configure(menu=networkMenu)
        networkNames = self.configureNetworkNames()
        networkNames.insert(0, "None")
        self.activeNetwork = tkinter.StringVar(window)
        # Use first item as default name
        self.activeNetwork.set(networkNames[0])
        for network in networkNames:
            networkMenu.add_checkbutton(label=network, onvalue=network, offvalue=network, variable=self.activeNetwork, command=self.doNetworkMenu, indicatoron=True)
        networkButton.grid(row=0, column=2, sticky="nsew") 

        agentColorButton = tkinter.Menubutton(window, text="Agent Coloring", relief=tkinter.RAISED)
        agentColorMenu = tkinter.Menu(agentColorButton, tearoff=0)
        agentColorButton.configure(menu=agentColorMenu)
        agentColorNames = self.configureAgentColorNames()
        agentColorNames.sort()
        agentColorNames.insert(0, "Default")
        self.lastSelectedAgentColor = tkinter.StringVar(window)
        # Use first item as default name
        self.lastSelectedAgentColor.set(agentColorNames[0])
        for name in agentColorNames:
            agentColorMenu.add_checkbutton(label=name, onvalue=name, offvalue=name, variable=self.lastSelectedAgentColor, command=self.doAgentColorMenu, indicatoron=True)
        agentColorButton.grid(row=0, column=3, sticky="nsew")

        environmentColorButton = tkinter.Menubutton(window, text="Environment Coloring", relief=tkinter.RAISED)
        environmentColorMenu = tkinter.Menu(environmentColorButton, tearoff=0)
        environmentColorButton.configure(menu=environmentColorMenu)
        environmentColorNames = self.configureEnvironmentColorNames()
        environmentColorNames.sort()
        environmentColorNames.insert(0, "Default")
        self.lastSelectedEnvironmentColor = tkinter.StringVar(window)
        # Use first item as default name
        self.lastSelectedEnvironmentColor.set(environmentColorNames[0])
        for name in environmentColorNames:
            environmentColorMenu.add_checkbutton(label=name, onvalue=name, offvalue=name, variable=self.lastSelectedEnvironmentColor, command=self.doEnvironmentColorMenu, indicatoron=True)
        environmentColorButton.grid(row=0, column=4, sticky="nsew")

        statsLabel = tkinter.Label(window, text="Timestep: - | Population: - | Metabolism: - | Movement: - | Vision: - | Gini: - | Trade Price: - | Trade Volume: -", font="Roboto 10", justify=tkinter.CENTER)
        statsLabel.grid(row=1, column=0, columnspan=self.menuTrayColumns, sticky="nsew")
        cellLabel = tkinter.Label(window, text="Cell: - | Sugar: - | Spice: - | Pollution: - | Season: -\nAgent: - | Age: - | Vision: - | Movement: - | Sugar: - | Spice: - | Metabolism: - | Decision Model: -", font="Roboto 10", justify=tkinter.CENTER)
        cellLabel.grid(row=2, column=0, columnspan=self.menuTrayColumns, sticky="nsew")

        self.widgets["playButton"] = playButton
        self.widgets["stepButton"] = stepButton
        self.widgets["networkButton"] = networkButton
        self.widgets["agentColorButton"] = agentColorButton
        self.widgets["environmentColorButton"] = environmentColorButton
        self.widgets["agentColorMenu"] = agentColorMenu
        self.widgets["environmentColorMenu"] = environmentColorMenu
        self.widgets["statsLabel"] = statsLabel
        self.widgets["cellLabel"] = cellLabel

    def configureCanvas(self):
        canvas = tkinter.Canvas(self.window, width=self.screenWidth, height=self.screenHeight, bg="white")
        canvas.grid(row=3, column=0, columnspan=self.menuTrayColumns, sticky="nsew")
        canvas.bind("<Button-1>", self.doClick)
        canvas.bind("<Double-Button-1>", self.doDoubleClick)
        canvas.bind("<Control-Button-1>", self.doControlClick)
        self.doubleClick = False
        self.canvas = canvas

    def configureEnvironment(self):
        if self.activeNetwork.get() != "None":
            for i in range(self.sugarscape.environmentWidth):
                for j in range(self.sugarscape.environmentHeight):
                    cell = self.sugarscape.environment.findCell(i, j)
                    fillColor = self.lookupFillColor(cell)
                    # Determine upper left x and y coordinates
                    x1 = self.borderEdge + (i + 0.2) * self.siteWidth
                    y1 = self.borderEdge + (j + 0.2) * self.siteHeight
                    # Determine lower rightt x and y coordinates
                    x2 = self.borderEdge + (i + 0.8) * self.siteWidth
                    y2 = self.borderEdge + (j + 0.8) * self.siteHeight
                    self.grid[i][j] = {"object": self.canvas.create_oval(x1, y1, x2, y2, fill=fillColor, outline=""), "color": fillColor}
            self.drawLines()
        else:
            for i in range(self.sugarscape.environmentWidth):
                for j in range(self.sugarscape.environmentHeight):
                    cell = self.sugarscape.environment.findCell(i, j)
                    fillColor = self.lookupFillColor(cell)
                    # Determine upper left x and y coordinates
                    x1 = self.borderEdge + i * self.siteWidth
                    y1 = self.borderEdge + j * self.siteHeight
                    # Determine lower rightt x and y coordinates
                    x2 = self.borderEdge + (i + 1) * self.siteWidth
                    y2 = self.borderEdge + (j + 1) * self.siteHeight
                    self.grid[i][j] = {"object": self.canvas.create_rectangle(x1, y1, x2, y2, fill=fillColor, outline="#c0c0c0", activestipple="gray50"), "color": fillColor}

        if self.highlightedCell != None:
            self.highlightCell(self.highlightedCell)

    def configureEnvironmentColorNames(self):
        return ["Pollution"]
    
    def configureNetworkNames(self):
        return ["Neighbors", "Family", "Friends", "Trade", "Loans", "Disease"]

    def configureWindow(self):
        window = tkinter.Tk()
        self.window = window
        window.title("Sugarscape")
        # Do one-quarter window sizing only after initial window object is created to get user's monitor dimensions
        if self.screenWidth < 0:
            self.screenWidth = math.ceil(window.winfo_screenwidth() / 2) - self.borderEdge
        if self.screenHeight < 0:
            self.screenHeight = math.ceil(window.winfo_screenheight() / 2) - self.borderEdge
        self.updateSiteDimensions()
        window.geometry("%dx%d" % (self.screenWidth + self.borderEdge, self.screenHeight + self.borderEdge))
        window.resizable(True, True)
        window.configure(background="white")
        window.option_add("*font", "Roboto 10")
        self.configureButtons(window)
        self.configureCanvas()
        window.update()

        self.configureEnvironment()
        buttonsOffset = self.widgets["playButton"].winfo_height()
        window.geometry("%dx%d" % (self.screenWidth + self.borderEdge, self.screenHeight + self.borderEdge + buttonsOffset))
        window.update()

        self.window.protocol("WM_DELETE_WINDOW", self.doWindowClose)
        self.window.bind("<Escape>", self.doWindowClose)
        self.window.bind("<space>", self.doPlayButton)
        self.window.bind("<Right>", self.doStepForwardButton)
        self.window.bind("<Configure>", self.resizeInterface)

        # Adjust for slight deviations from initially configured window size
        self.resizeInterface()
        window.update()

    def deleteLines(self):
        self.canvas.delete("line")

    def destroyCanvas(self):
        self.canvas.destroy()

    def doAgentColorMenu(self, *args):
        self.activeColorOptions["agent"] = self.lastSelectedAgentColor.get()
        self.doTimestep()

    def doControlClick(self, event):
        self.doubleClick = False
        cell = self.findClickedCell(event)
        if cell == self.highlightedCell or cell.agent == None:
            self.clearHighlight()
        else:
            self.highlightedCell = cell
            self.highlightedAgent = cell.agent
            self.highlightCell(cell)
        self.doTimestep()

    def doClick(self, event):
        self.canvas.after(300, self.doClickAction, event)

    def doDoubleClick(self, event):
        self.doubleClick = True

    def doClickAction(self, event):
        if self.doubleClick == True:
            cell = self.findClickedCell(event)
            if cell == self.highlightedCell or cell.agent == None:
                self.clearHighlight()
            else:
                self.highlightedCell = cell
                self.highlightedAgent = cell.agent
                self.highlightCell(cell)
            self.doubleClick = False
        else:
            cell = self.findClickedCell(event)
            if cell == self.highlightedCell and self.highlightedAgent == None:
                self.clearHighlight()
            else:
                self.highlightedCell = cell
                self.highlightedAgent = None
                self.highlightCell(cell)
        self.doTimestep()

    def doEnvironmentColorMenu(self):
        self.activeColorOptions["environment"] = self.lastSelectedEnvironmentColor.get()
        self.doTimestep()

    def doPlayButton(self, *args):
        self.sugarscape.toggleRun()
        self.widgets["playButton"].config(text="  Play Simulation  " if self.sugarscape.run == False else "Pause Simulation")
        self.doTimestep()

    def doStepForwardButton(self, *args):
        if self.sugarscape.end == True:
            self.sugarscape.endSimulation()
        elif len(self.sugarscape.agents) == 0 and self.sugarscape.keepAlive == False:
            self.sugarscape.toggleEnd()
        else:
            self.sugarscape.doTimestep()

    def doTimestep(self):
        if self.stopSimulation == True:
            self.sugarscape.toggleEnd()
            return
        if self.screenHeight != self.window.winfo_height() or self.screenWidth != self.window.winfo_width():
            self.resizeInterface()
        for i in range(self.sugarscape.environmentWidth):
            for j in range(self.sugarscape.environmentHeight):
                cell = self.sugarscape.environment.findCell(i, j)
                fillColor = self.lookupFillColor(cell)
                if self.activeNetwork.get() == "None" and self.grid[i][j]["color"] != fillColor:
                    self.canvas.itemconfig(self.grid[i][j]["object"], fill=fillColor, outline="#C0C0C0")
                elif self.grid[i][j]["color"] != fillColor:
                    self.canvas.itemconfig(self.grid[i][j]["object"], fill=fillColor)
                self.grid[i][j]["color"] = fillColor

        if self.activeNetwork.get() != "None":
            self.deleteLines()
            self.drawLines()

        if self.highlightedAgent != None:
            if self.highlightedAgent.isAlive() == True:
                self.highlightedCell = self.highlightedAgent.cell
                self.highlightCell(self.highlightedCell)
            else:
                self.clearHighlight()

        self.updateLabels()
        self.window.update()

    def doNetworkMenu(self, *args):
        if self.activeNetwork.get() != "None":
            self.widgets["agentColorButton"].configure(state="disabled")
            self.widgets["environmentColorButton"].configure(state="disabled")
        else:
            self.widgets["agentColorButton"].configure(state="normal")
            self.widgets["environmentColorButton"].configure(state="normal")
        self.destroyCanvas()
        self.configureCanvas()
        self.configureEnvironment()
        self.window.update()

    def doWindowClose(self, *args):
        self.stopSimulation = True
        self.window.destroy()
        self.sugarscape.toggleEnd()

    def drawLines(self):
        lineCoordinates = set()
        if self.activeNetwork.get() == "Neighbors":
            for agent in self.sugarscape.agents:
                for neighbor in agent.neighbors:
                    if neighbor != None and neighbor.isAlive() == True:
                        lineEndpointsPair = frozenset([(agent.cell.x, agent.cell.y), (neighbor.cell.x, neighbor.cell.y)])
                        lineCoordinates.add(lineEndpointsPair)

        elif self.activeNetwork.get() == "Family":
            for agent in self.sugarscape.agents:
                family = [agent.socialNetwork["mother"], agent.socialNetwork["father"]] + agent.socialNetwork["children"]
                for familyMember in family:
                    if familyMember != None and familyMember.isAlive() == True:
                        lineEndpointsPair = frozenset([(agent.cell.x, agent.cell.y), (familyMember.cell.x, familyMember.cell.y)])
                        lineCoordinates.add(lineEndpointsPair)

        elif self.activeNetwork.get() == "Friends":
            for agent in self.sugarscape.agents:
                for friendRecord in agent.socialNetwork["friends"]:
                    friend = friendRecord["friend"]
                    if friend.isAlive() == True:
                        lineEndpointsPair = frozenset([(agent.cell.x, agent.cell.y), (friend.cell.x, friend.cell.y)])
                        lineCoordinates.add(lineEndpointsPair)

        elif self.activeNetwork.get() == "Trade":
            for agent in self.sugarscape.agents:
                nonTraders = ["bestFriend", "children", "creditors", "debtors", "father", "friends", "mother"]
                for other in agent.socialNetwork:
                    if other in nonTraders:
                        continue
                    trader = agent.socialNetwork[other]
                    if trader != None and trader["agent"].isAlive() == True and trader["lastSeen"] == self.sugarscape.timestep and trader["timesTraded"] > 0:
                        trader = trader["agent"]
                        lineEndpointsPair = frozenset([(agent.cell.x, agent.cell.y), (trader.cell.x, trader.cell.y)])
                        lineCoordinates.add(lineEndpointsPair)

        elif self.activeNetwork.get() == "Loans":
            for agent in self.sugarscape.agents:
                # Loan records are always kept on both sides, so only one side is needed
                for loanRecord in agent.socialNetwork["creditors"]:
                    creditor = agent.socialNetwork[loanRecord["creditor"]]["agent"]
                    if creditor.isAlive() == True:
                        lineEndpointsPair = frozenset([(agent.cell.x, agent.cell.y), (creditor.cell.x, creditor.cell.y)])
                        lineCoordinates.add(lineEndpointsPair)

        elif self.activeNetwork.get() == "Disease":
            for agent in self.sugarscape.agents:
                if agent.isSick() == True:
                    for diseaseRecord in agent.diseases:
                        # Starting diseases without an infector are not considered
                        if "infector" not in diseaseRecord:
                            continue
                        infector = diseaseRecord["infector"]
                        if infector != None and infector.isAlive() == True:
                            lineEndpointsPair = frozenset([(agent.cell.x, agent.cell.y), (infector.cell.x, infector.cell.y)])
                            lineCoordinates.add(lineEndpointsPair)

        for lineEndpointsPair in lineCoordinates:
            coordList = list(lineEndpointsPair)
            (x1, y1), (x2, y2) = coordList[0], coordList[1]
            x1 = (x1 + 0.5) * self.siteWidth + self.borderEdge
            y1 = (y1 + 0.5) * self.siteHeight + self.borderEdge
            x2 = (x2 + 0.5) * self.siteWidth + self.borderEdge
            y2 = (y2 + 0.5) * self.siteHeight + self.borderEdge
            self.canvas.create_line(x1, y1, x2, y2, fill="black", width="2", tag="line")

    def findClickedCell(self, event):
        # Account for padding in GUI cells
        eventX = event.x - self.borderEdge
        eventY = event.y - self.borderEdge
        gridX = math.floor(eventX / self.siteWidth)
        gridY = math.floor(eventY / self.siteHeight)
        # Handle clicking just outside edge cells
        if gridX < 0:
            gridX = 0
        elif gridX > self.sugarscape.environmentWidth - 1:
            gridX = self.sugarscape.environmentWidth - 1
        if gridY < 0:
            gridY = 0
        elif gridY > self.sugarscape.environmentHeight - 1:
            gridY = self.sugarscape.environmentHeight - 1
        cell = self.sugarscape.environment.findCell(gridX, gridY)
        return cell

    def updateHighlightedCellStats(self):
        cell = self.highlightedCell
        if cell != None:
            cellSeason = cell.season if cell.season != None else '-'
            cellStats = f"Cell: ({cell.x},{cell.y}) | Sugar: {cell.sugar}/{cell.maxSugar} | Spice: {cell.spice}/{cell.maxSpice} | Pollution: {round(cell.pollution, 2)} | Season: {cellSeason}"
            agent = cell.agent
            if agent != None:
                agentStats = f"Agent: {str(agent)} | Age: {agent.age} | Vision: {round(agent.findVision(), 2)} | Movement: {round(agent.findMovement(), 2)} | "
                agentStats += f"Sugar: {round(agent.sugar, 2)} | Spice: {round(agent.spice, 2)} | "
                agentStats += f"Metabolism: {round(((agent.findSugarMetabolism() + agent.findSpiceMetabolism()) / 2), 2)} | Decision Model: {agent.decisionModel}"
            else:
                agentStats = "Agent: - | Age: - | Vision: - | Movement: - | Sugar: - | Spice: - | Metabolism: - | Decision Model: -"
            cellStats += f"\n  {agentStats}"
        else:
            cellStats = "Cell: - | Sugar: - | Spice: - | Pollution: - | Season: -\nAgent: - | Age: - | Sugar: - | Spice: - "
        
        label = self.widgets["cellLabel"]
        label.config(text=cellStats)

    def hexToInt(self, hexval):
        intvals = []
        hexval = hexval.lstrip('#')
        for i in range(0, len(hexval), 2):
            subval = hexval[i:i + 2]
            intvals.append(int(subval, 16))
        return intvals
    
    def highlightCell(self, cell):
        x = cell.x
        y = cell.y
        x1 = self.borderEdge + x * self.siteWidth
        y1 = self.borderEdge + y * self.siteHeight
        x2 = self.borderEdge + (x + 1) * self.siteWidth
        y2 = self.borderEdge + (y + 1) * self.siteHeight

        if self.highlightRectangle != None:
            self.canvas.delete(self.highlightRectangle)
        self.highlightRectangle = self.canvas.create_rectangle(x1, y1, x2, y2, fill="", activefill="#88cafc", outline="black", width=5)

    def intToHex(self, intvals):
        hexval = "#"
        for i in intvals:
            subhex = "%0.2X" % i
            hexval = hexval + subhex
        return hexval

    def lookupFillColor(self, cell):
        if self.activeNetwork.get() != "None":
            return self.lookupNetworkColor(cell)
        
        agent = cell.agent
        if agent == None:
            if self.activeColorOptions["environment"] == "Pollution":
                return self.recolorByResourceAmount(cell, self.colors["pollution"])
            else:
                if cell.sugar > 0 and cell.spice == 0:
                    return self.recolorByResourceAmount(cell, self.colors["sugar"])
                elif cell.spice > 0 and cell.sugar == 0:
                    return self.recolorByResourceAmount(cell, self.colors["spice"])
                else:
                    return self.recolorByResourceAmount(cell, self.colors["sugarAndSpice"])
        elif agent.sex != None and self.activeColorOptions["agent"] == "Sex":
            return self.colors[agent.sex]
        elif agent.tribe != None and self.activeColorOptions["agent"] == "Tribes":
            return self.colors[str(agent.tribe)]
        elif agent.decisionModel != None and self.activeColorOptions["agent"] == "Decision Models":
            return self.colors[agent.decisionModel]
        elif len(agent.diseases) > 0 and self.activeColorOptions["agent"] == "Disease":
            return self.colors["sick"]
        elif len(agent.diseases) == 0 and self.activeColorOptions["agent"] == "Disease":
            return self.colors["healthy"]
        return self.colors["noSex"]

    def lookupNetworkColor(self, cell):
        agent = cell.agent
        if agent == None:
            return "white"
        elif self.activeNetwork.get() in ["Neighbors", "Friends", "Trade"]:
            return "black"
        elif self.activeNetwork.get() == "Family":
            isChild = agent.socialNetwork["father"] != None or agent.socialNetwork["mother"] != None
            isParent = len(agent.socialNetwork["children"]) > 0
            if isChild == False and isParent == False:
                return "black"
            elif isChild == False and isParent == True:
                return "red"
            elif isChild == True and isParent == False:
                return "green"
            else: # isChild == True and isParent == True
                return "yellow"            
        elif self.activeNetwork.get() == "Loans":
            isLender = len(agent.socialNetwork["debtors"]) > 0
            isBorrower = len(agent.socialNetwork["creditors"]) > 0
            if isLender == True:
                return "yellow" if isBorrower == True else "green"
            elif isBorrower == True:
                return "red"
            else:
                return "black"
        elif self.activeNetwork.get() == "Disease":
            return self.colors["sick"] if agent.isSick() == True else self.colors["healthy"]
        return "black"

    def recolorByResourceAmount(self, cell, fillColor):
        recolorFactor = 0
        if self.activeColorOptions["environment"] == "Pollution":
            # Since global max pollution changes at each timestep, set constant to prevent misleading recoloring of cells
            maxPollution = 20
            # Once a cell has exceeded the number of colors made possible with maxPollution, keep using the max color
            recolorFactor = min(1, cell.pollution / maxPollution)
        else:
            maxSugar = self.sugarscape.environment.globalMaxSugar
            maxSpice = self.sugarscape.environment.globalMaxSpice
            if maxSugar == 0 and maxSpice == 0:
                recolorFactor = 0
            elif cell.sugar > 0 and cell.spice == 0 and maxSugar > 0:
                recolorFactor = cell.sugar / maxSugar
            elif cell.spice > 0 and cell.sugar == 0 and maxSpice > 0:
                recolorFactor = cell.spice / maxSpice
            else:
                recolorFactor = (cell.sugar + cell.spice) / (maxSugar + maxSpice)
        subcolors = self.hexToInt(fillColor)
        i = 0
        for color in subcolors:
            color = int(color + (255 - color) * (1 - recolorFactor))
            subcolors[i] = color
            i += 1
        fillColor = self.intToHex(subcolors)
        return fillColor

    def resizeInterface(self, event=None):
        # Do not do resizing if capturing a user input event but the event does not come from the GUI window
        if event != None and (event.widget != self.window or (event.widget == self.window and (self.screenHeight == event.height and self.screenWidth == event.width))):
            return
        self.updateScreenDimensions()
        self.updateSiteDimensions()
        self.destroyCanvas()
        self.configureCanvas()
        self.configureEnvironment()

    def updateLabels(self):
        stats = self.sugarscape.runtimeStats
        statsString = f"Timestep: {self.sugarscape.timestep} | Agents: {stats['population']} | Metabolism: {stats['meanMetabolism']} | Movement: {stats['meanMovement']} | Vision: {stats['meanVision']} | Gini: {stats['giniCoefficient']} | Trade Price: {stats['meanTradePrice']} | Trade Volume: {stats['tradeVolume']}"
        label = self.widgets["statsLabel"]
        label.config(text=statsString)
        if self.highlightedCell != None:
            cellString = self.updateHighlightedCellStats()
            label = self.widgets["cellLabel"]
            label.config(text=cellString)

    def updateScreenDimensions(self):
        self.screenHeight = self.window.winfo_height()
        self.screenWidth = self.window.winfo_width()

    def updateSiteDimensions(self):
        self.siteHeight = (self.screenHeight - self.menuTrayOffset) / self.sugarscape.environmentHeight
        self.siteWidth = (self.screenWidth - self.windowBorderOffset) / self.sugarscape.environmentWidth
