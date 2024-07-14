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
        self.activeNetwork = None
        self.activeGraph = None
        self.graphObjects = {}
        self.graphBorder = 90
        self.xTicks = 10
        self.yTicks = 2
        self.lastSelectedAgentColor = None
        self.lastSelectedEnvironmentColor = None
        self.activeColorOptions = {"agent": None, "environment": None}
        self.highlightedCell = None
        self.highlightedAgent = None
        self.highlightRectangle = None
        self.menuTrayColumns = 6
        self.borderEdge = 5
        self.siteHeight = (self.screenHeight - 2 * self.borderEdge) / self.sugarscape.environmentHeight
        self.siteWidth = (self.screenWidth - 2 * self.borderEdge) / self.sugarscape.environmentWidth
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

        graphButton = tkinter.Menubutton(window, text="Graphs", relief=tkinter.RAISED)
        graphMenu = tkinter.Menu(graphButton, tearoff=0)
        graphButton.configure(menu=graphMenu)
        graphNames = self.configureGraphNames()
        graphNames.insert(0, "None")
        self.activeGraph = tkinter.StringVar(window)
        # Use first item as default name
        self.activeGraph.set(graphNames[0])
        for graph in graphNames:
            graphMenu.add_checkbutton(label=graph, onvalue=graph, offvalue=graph, variable=self.activeGraph, command=self.doGraphMenu, indicatoron=True)
        graphButton.grid(row=0, column=3, sticky="nsew") 

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
        agentColorButton.grid(row=0, column=4, sticky="nsew")

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
        environmentColorButton.grid(row=0, column=5, sticky="nsew")

        statsLabel = tkinter.Label(window, text="Timestep: - | Population: - | Metabolism: - | Movement: - | Vision: - | Gini: - | Trade Price: - | Trade Volume: -", font="Roboto 10", justify=tkinter.CENTER)
        statsLabel.grid(row=1, column=0, columnspan=self.menuTrayColumns, sticky="nsew")
        cellLabel = tkinter.Label(window, text="Cell: - | Sugar: - | Spice: - | Pollution: - | Season: -\nAgent: - | Age: - | Vision: - | Movement: - | Sugar: - | Spice: - | Metabolism: - | Decision Model: -", font="Roboto 10", justify=tkinter.CENTER)
        cellLabel.grid(row=2, column=0, columnspan=self.menuTrayColumns, sticky="nsew")

        self.widgets["playButton"] = playButton
        self.widgets["stepButton"] = stepButton
        self.widgets["networkButton"] = networkButton
        self.widgets["graphButton"] = graphButton
        self.widgets["agentColorButton"] = agentColorButton
        self.widgets["environmentColorButton"] = environmentColorButton
        self.widgets["agentColorMenu"] = agentColorMenu
        self.widgets["environmentColorMenu"] = environmentColorMenu
        self.widgets["statsLabel"] = statsLabel
        self.widgets["cellLabel"] = cellLabel

    def configureCanvas(self):
        canvas = tkinter.Canvas(self.window, background="white")
        canvas.grid(row=3, column=0, columnspan=self.menuTrayColumns, sticky="nsew")
        if self.activeGraph.get() == "None":
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
                    # Determine lower right x and y coordinates
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
                    # Determine lower right x and y coordinates
                    x2 = self.borderEdge + (i + 1) * self.siteWidth
                    y2 = self.borderEdge + (j + 1) * self.siteHeight
                    self.grid[i][j] = {"object": self.canvas.create_rectangle(x1, y1, x2, y2, fill=fillColor, outline="#c0c0c0", activestipple="gray50"), "color": fillColor}

        if self.highlightedCell != None:
            self.highlightCell(self.highlightedCell)

    def configureEnvironmentColorNames(self):
        return ["Pollution"]

    def configureGraphNames(self):
        return ["Age Histogram", "Gini Coefficient", "Spice Histogram", "Sugar Histogram", "Tag Histogram"]
    
    def configureNetworkNames(self):
        return ["Disease", "Family", "Friends", "Loans", "Neighbors", "Trade"]

    def configureWindow(self):
        window = tkinter.Tk()
        self.window = window
        window.title("Sugarscape")
        window.minsize(width=150, height=250)
        # Do one-quarter window sizing only after initial window object is created to get user's monitor dimensions
        if self.screenWidth < 0:
            self.screenWidth = math.ceil(window.winfo_screenwidth() / 2) - self.borderEdge
        if self.screenHeight < 0:
            self.screenHeight = math.ceil(window.winfo_screenheight() / 2) - self.borderEdge
        window.geometry(f"{self.screenWidth + self.borderEdge}x{self.screenHeight + self.borderEdge}")
        window.option_add("*font", "Roboto 10")
        # Make the canvas and buttons fill the window
        window.grid_rowconfigure(3, weight=1)
        window.grid_columnconfigure(list(range(self.menuTrayColumns)), weight=1)
        self.configureButtons(window)
        self.configureCanvas()

        self.updateSiteDimensions()
        self.configureEnvironment()

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

    def doGraphMenu(self):
        self.destroyCanvas()
        self.configureCanvas()
        if self.activeGraph.get() != "None":
            self.clearHighlight()
            self.configureGraph()
            self.widgets["networkButton"].configure(state="disabled")
            self.widgets["agentColorButton"].configure(state="disabled")
            self.widgets["environmentColorButton"].configure(state="disabled")
        else:
            self.configureEnvironment()
            self.widgets["networkButton"].configure(state="normal")
            self.widgets["agentColorButton"].configure(state="normal")
            self.widgets["environmentColorButton"].configure(state="normal")
        self.window.update()

    def configureGraph(self):
        self.updateGraphDimensions()
        self.graphObjects = {"xAxis": None, "xAxisLabel": None, "xTicks": {}, "xTickLabels": {},
                             "yAxis": None, "yAxisLabel": None, "yTicks": {}, "yTickLabels": {}}
        activeGraph = self.activeGraph.get()
        if activeGraph == "Gini Coefficient":
            self.configureLorenzCurve()
        else:
            self.configureHistogram()

    def configureGraphAxes(self):
        activeGraph = self.activeGraph.get()
        axisLabels = {
            "Sugar Histogram": ("Sugar Wealth", "Frequency"),
            "Spice Histogram": ("Spice Wealth", "Frequency"),
            "Tag Histogram": ("Tag Position", "% of Tags Set to 1"),
            "Age Histogram": ("Age", "Frequency"),
            "Gini Coefficient": ("% Population", "% Wealth")
        }
        self.graphObjects["xAxisLabel"] = self.canvas.create_text(self.graphStartX + (self.graphWidth / 2), self.graphStartY + self.graphHeight + 40,
                                                                  fill="black", text=axisLabels[activeGraph][0])
        self.graphObjects["yAxisLabel"] = self.canvas.create_text(self.graphStartX - 60, self.graphStartY + (self.graphHeight / 2),
                                                                  angle=90, fill="black", text=axisLabels[activeGraph][1])

        self.graphObjects["xAxis"] = self.canvas.create_line(self.graphStartX, self.graphStartY + self.graphHeight,
                                                             self.graphStartX + self.graphWidth, self.graphStartY + self.graphHeight,
                                                             fill="black", width=2)
        if activeGraph == "Gini Coefficient":
            self.graphObjects["upperXAxis"] = self.canvas.create_line(self.graphStartX, self.graphStartY,
                                                                      self.graphStartX + self.graphWidth, self.graphStartY,
                                                                      fill="black", width=2)
            xTicks = 10
        elif activeGraph == "Tag Histogram":
            xTicks = self.sugarscape.configuration["agentTagStringLength"]
        else:
            xTicks = self.xTicks
        xTickOffset = 0 if activeGraph != "Tag Histogram" or xTicks == 0 else -1 * self.graphWidth / xTicks / 2
        for i in range(1, xTicks + 1):
            x0 = x1 = self.graphStartX + (self.graphWidth * i / xTicks) + xTickOffset
            y0 = self.graphStartY + self.graphHeight
            y1 = y0 + 10
            self.graphObjects["xTicks"][i / xTicks] = self.canvas.create_line(x0, y0, x1, y1, fill="black", width=2)
            y0 = y1 + 10
            self.graphObjects["xTickLabels"][i / xTicks] = self.canvas.create_text(x0, y0, fill="black")

        self.graphObjects["yAxis"] = self.canvas.create_line(self.graphStartX, self.graphStartY,
                                                             self.graphStartX, self.graphStartY + self.graphHeight,
                                                             fill="black", width=2)
        if activeGraph == "Gini Coefficient":
            self.graphObjects["rightYAxis"] = self.canvas.create_line(self.graphStartX + self.graphWidth, self.graphStartY,
                                                                      self.graphStartX + self.graphWidth, self.graphStartY + self.graphHeight,
                                                                      fill="black", width=2)
        yTicks = self.yTicks if activeGraph != "Gini Coefficient" else 10
        for i in range(1, yTicks + 1):
            x0 = self.graphStartX - 10
            x1 = self.graphStartX
            y0 = y1 = self.graphStartY + (self.graphHeight * (yTicks - i) / yTicks)
            self.graphObjects["yTicks"][i / yTicks] = self.canvas.create_line(x0, y0, x1, y1, fill="black", width=2)
            x0 = self.graphStartX - 20
            self.graphObjects["yTickLabels"][i / yTicks] = self.canvas.create_text(x0, y0, fill="black", anchor="e")

        if activeGraph == "Gini Coefficient":
             self.updateGraphAxes(100, 100)
             self.graphObjects["equalityLine"] = self.canvas.create_line(self.graphStartX, self.graphStartY + self.graphHeight,
                                                                         self.graphStartX + self.graphWidth, self.graphStartY,
                                                                         fill="black", width=2)

    def configureHistogram(self):
        activeGraph = self.activeGraph.get()
        histogramBins = self.xTicks if activeGraph != "Tag Histogram" else self.sugarscape.configuration["agentTagStringLength"]
        self.configureGraphAxes()

        self.graphObjects["bins"] = {}
        self.graphObjects["binLabels"] = {}
        for i in range(histogramBins):
            x0, y0 = self.graphStartX + i * self.graphWidth / histogramBins, self.graphStartY + self.graphHeight
            x1, y1 = self.graphStartX + (i + 1) * self.graphWidth / histogramBins, self.graphStartY + self.graphHeight
            self.graphObjects["bins"][i] = self.canvas.create_rectangle(x0, y0, x1, y1, fill="magenta", outline="black", width=2)
            x0, y0 = self.graphStartX + (i + 0.5) * self.graphWidth / histogramBins, self.graphStartY + self.graphHeight - 10
            self.graphObjects["binLabels"][i] = self.canvas.create_text(x0, y0, fill="black")
        if self.sugarscape.timestep != 0:
            self.updateHistogram()

    def configureLorenzCurve(self):
        self.configureGraphAxes()
        self.graphObjects["giniCoefficientLabel"] = self.canvas.create_text(
            self.graphStartX + 20, self.graphStartY + 20, anchor="nw", fill="black", text="Gini coefficient:")
        if self.sugarscape.timestep != 0:
            self.updateLorenzCurve()

    def doGraphTimestep(self):
        activeGraph = self.activeGraph.get()
        if activeGraph == "Gini Coefficient":
            self.updateLorenzCurve()
        else:
            self.updateHistogram()

    def doPlayButton(self, *args):
        self.sugarscape.toggleRun()
        self.widgets["playButton"].config(text="Play Simulation" if self.sugarscape.run == False else "Pause Simulation")
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
        if self.activeGraph.get() != "None" and self.widgets["graphButton"].cget("state") != "disabled":
            self.doGraphTimestep()
        else:
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

    def doNetworkMenu(self):
        if self.activeNetwork.get() != "None":
            self.widgets["graphButton"].configure(state="disabled")
            self.widgets["agentColorButton"].configure(state="disabled")
            self.widgets["environmentColorButton"].configure(state="disabled")
        else:
            self.widgets["graphButton"].configure(state="normal")
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
            cellStats += f"\n{agentStats}"
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
        if event != None and (event.widget != self.window or (self.screenHeight == event.height and self.screenWidth == event.width)):
            return
        self.updateScreenDimensions()
        self.updateSiteDimensions()
        self.destroyCanvas()
        self.configureCanvas()
        if self.activeGraph.get() != "None" and self.widgets["graphButton"].cget("state") != "disabled":
            self.configureGraph()
        else:
            self.configureEnvironment()

    def updateGraphAxes(self, maxX, maxY):
        xTicks = len(self.graphObjects["xTickLabels"])
        for i in range(1, xTicks + 1):
            self.canvas.itemconfigure(self.graphObjects["xTickLabels"][i / xTicks], text=round(i / xTicks * maxX))
        yTicks = len(self.graphObjects["yTickLabels"])
        for i in range(1, yTicks + 1):
            self.canvas.itemconfigure(self.graphObjects["yTickLabels"][i / yTicks], text=round(i / yTicks * maxY))

    def updateGraphDimensions(self):
        self.window.update_idletasks()
        canvasWidth = self.canvas.winfo_width()
        canvasHeight = self.canvas.winfo_height()
        self.graphStartX = self.graphBorder
        self.graphWidth = max(canvasWidth - 2 * self.graphBorder, 0)
        self.graphStartY = self.graphBorder
        self.graphHeight = max(canvasHeight - 2 * self.graphBorder, 0)

    def updateHistogram(self):
        bins = self.graphObjects["bins"]
        labels = self.graphObjects["binLabels"]
        graphStats = {
            "Tag Histogram": (self.sugarscape.graphStats["meanTribeTags"], self.sugarscape.configuration["agentTagStringLength"]),
            "Age Histogram": (self.sugarscape.graphStats["ageBins"], self.sugarscape.configuration["agentMaxAge"][1]),
            "Sugar Histogram": (self.sugarscape.graphStats["sugarBins"], self.sugarscape.graphStats["maxSugar"]),
            "Spice Histogram": (self.sugarscape.graphStats["spiceBins"], self.sugarscape.graphStats["maxSpice"]),
        }
        activeGraph = self.activeGraph.get()
        binValues = graphStats[activeGraph][0]
        maxX = graphStats[activeGraph][1]
        if len(binValues) == 0:
            maxBinHeight = 0
        elif activeGraph == "Tag Histogram":
            maxBinHeight = 100
        else:
            maxBinHeight = max(binValues)

        if maxBinHeight != 0:
            self.updateGraphAxes(maxX, maxBinHeight)
            for i in range(len(bins)):
                x0, y0, x1, y1 = self.canvas.coords(bins[i])
                y0 = y1 - (binValues[i] / maxBinHeight) * self.graphHeight
                self.canvas.coords(bins[i], x0, y0, x1, y1)
                x2, y2 = self.canvas.coords(labels[i])
                y2 = y0 - 10
                self.canvas.itemconfigure(labels[i], text=round(binValues[i]))
                self.canvas.coords(labels[i], x2, y2)

    def updateLabels(self):
        stats = self.sugarscape.runtimeStats
        statsString = f"Timestep: {self.sugarscape.timestep} | Agents: {stats['population']} | Metabolism: {stats['meanMetabolism']} | Movement: {stats['meanMovement']} | Vision: {stats['meanVision']} | Gini: {stats['giniCoefficient']} | Trade Price: {stats['meanTradePrice']} | Trade Volume: {stats['tradeVolume']}"
        label = self.widgets["statsLabel"]
        label.config(text=statsString)
        if self.highlightedCell != None:
            self.updateHighlightedCellStats()

    def updateLorenzCurve(self):
        self.canvas.itemconfigure(self.graphObjects["giniCoefficientLabel"], text=f"Gini coefficient: {self.sugarscape.runtimeStats['giniCoefficient']}")
        self.canvas.delete("lorenzCurve")
        points = self.sugarscape.graphStats["lorenzCurvePoints"]
        points.append((1, 0))
        points = [(self.graphStartX + (x * self.graphWidth), self.graphStartY + ((1 - y) * self.graphHeight)) for x, y in points]
        self.canvas.create_polygon(points, fill="magenta", tag="lorenzCurve")
        self.canvas.tag_lower("lorenzCurve")

    def updateScreenDimensions(self):
        self.window.update_idletasks()
        self.screenWidth = self.window.winfo_width()
        self.screenHeight = self.window.winfo_height()

    def updateSiteDimensions(self):
        self.siteWidth = (self.screenWidth - 2 * self.borderEdge) / self.sugarscape.environmentWidth
        self.siteHeight = (self.canvas.winfo_height() - 2 * self.borderEdge) / self.sugarscape.environmentHeight
