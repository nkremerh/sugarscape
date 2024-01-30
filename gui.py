import math
import tkinter

class GUI:
    def __init__(self, sugarscape, screenHeight=1000, screenWidth=900):
        self.sugarscape = sugarscape
        self.screenHeight = screenHeight
        self.screenWidth = screenWidth
        self.window = None
        self.canvas = None
        self.grid = [[None for j in range(self.sugarscape.environmentWidth)]for i in range(self.sugarscape.environmentHeight)]
        self.colors = {"sugar": "#F2FA00", "spice": "#9B4722", "sugarAndSpice": "#CFB20E", "noSex": "#FA3232", "female": "#FA32FA", "male": "#3232FA", "pollution": "#803280",
                         "green": "#32FA32", "blue": "#3232FA", "red": "#FA3232", "pink": "#FA32FA", "yellow": "#FAFA32", "teal": "#32FAFA", "purple": "#6432FA", "orange": "#FA6432",
                         "salmon": "#FA6464", "mint": "#64FA64", "blue2": "#3264FA"}
        self.widgets = {}
        self.lastSelectedAgentColor = None
        self.lastSelectedEnvironmentColor = None
        self.lastSelectedCell = None
        self.activeColorOptions = {"agent": None, "environment": None}
        self.menuTrayColumns = 4
        self.menuTrayOffset = 110
        self.windowBorderOffset = 10
        self.borderEdge = 5
        self.siteHeight = (self.screenHeight - self.menuTrayOffset) / self.sugarscape.environmentHeight
        self.siteWidth = (self.screenWidth - self.windowBorderOffset) / self.sugarscape.environmentWidth
        self.configureWindow()
        self.stopSimulation = False

    def configureAgentColorNames(self):
        return ["Disease", "Sex", "Tribes"]

    def configureButtons(self, window):
        playButton = tkinter.Button(window, text="Play Simulation", command=self.doPlayButton)
        playButton.grid(row=0, column=0, sticky="nsew")
        stepButton = tkinter.Button(window, text="Step Forward", command=self.doStepForwardButton, relief=tkinter.RAISED)
        stepButton.grid(row=0, column=1, sticky="nsew")

        agentColorButton = tkinter.Menubutton(window, text="Agent Coloring", relief=tkinter.RAISED)
        agentColorMenu = tkinter.Menu(agentColorButton, tearoff=0)
        agentColorButton.configure(menu=agentColorMenu)
        agentColorNames = self.configureAgentColorNames()
        agentColorNames.sort()
        agentColorNames.insert(0, "Default")
        self.lastSelectedAgentColor = tkinter.StringVar(window)
        self.lastSelectedAgentColor.set(agentColorNames[0])  # Default
        for name in agentColorNames:
            agentColorMenu.add_checkbutton(label=name, onvalue=name, offvalue=name, variable=self.lastSelectedAgentColor, command=self.doAgentColorMenu, indicatoron=True)
        agentColorButton.grid(row=0, column=2, sticky="nsew")

        environmentColorButton = tkinter.Menubutton(window, text="Environment Coloring", relief=tkinter.RAISED)
        environmentColorMenu = tkinter.Menu(environmentColorButton, tearoff=0)
        environmentColorButton.configure(menu=environmentColorMenu)
        environmentColorNames = self.configureEnvironmentColorNames()
        environmentColorNames.sort()
        environmentColorNames.insert(0, "Default")
        self.lastSelectedEnvironmentColor = tkinter.StringVar(window)
        self.lastSelectedEnvironmentColor.set(environmentColorNames[0])  # Default
        for name in environmentColorNames:
            environmentColorMenu.add_checkbutton(label=name, onvalue=name, offvalue=name, variable=self.lastSelectedEnvironmentColor, command=self.doEnvironmentColorMenu, indicatoron=True)
        environmentColorButton.grid(row=0, column=3, sticky="nsew")

        statsLabel = tkinter.Label(window, text="Timestep: - | Population: - | Metabolism: - | Movement: - | Vision: - | Gini: - | Trade Price: - | Trade Volume: -", font="Roboto 10", justify=tkinter.CENTER)
        statsLabel.grid(row=1, column=0, columnspan = self.menuTrayColumns, sticky="nsew")
        cellLabel = tkinter.Label(window, text="Cell: - | Sugar: - | Spice: - | Pollution: - | Season: -\nAgent: - | Age: - | Sex: - | Sugar: - | Spice: - ", font="Roboto 10", justify=tkinter.CENTER)
        cellLabel.grid(row=2, column=0, columnspan = self.menuTrayColumns, sticky="nsew")

        self.widgets["playButton"] = playButton
        self.widgets["stepButton"] = stepButton
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
        self.canvas = canvas

    def configureEnvironment(self):
        for i in range(self.sugarscape.environmentHeight):
            for j in range(self.sugarscape.environmentWidth):
                cell = self.sugarscape.environment.findCell(i, j)
                fillColor = self.lookupFillColor(cell)
                x1 = self.borderEdge + (0.50 * self.siteWidth) + i * self.siteWidth - (0.50 * self.siteWidth) # Upper right x coordinate
                y1 = self.borderEdge + (0.50 * self.siteHeight) + j * self.siteHeight - (0.50 * self.siteHeight) # Upper right y coordinate
                x2 = self.borderEdge + (0.50 * self.siteWidth) + i * self.siteWidth + (0.50 * self.siteWidth) # Lower left x coordinate
                y2 = self.borderEdge + (0.50 * self.siteHeight) + j * self.siteHeight + (0.50 * self.siteHeight) # Lower left y coordinate
                self.grid[i][j] = {"rectangle": self.canvas.create_rectangle(x1, y1, x2, y2, fill=fillColor, outline="#c0c0c0"), "color": fillColor}

    def configureEnvironmentColorNames(self):
        return ["Pollution"]

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
        self.canvas.bind("<Button-1>", self.doClick)

        # Adjust for slight deviations from initially configured window size
        self.resizeInterface()
        window.update()

    def destroyCanvas(self):
        self.canvas.destroy()

    def doAgentColorMenu(self, *args):
        self.activeColorOptions["agent"] = self.lastSelectedAgentColor.get()
        self.doTimestep()

    def doClick(self, event):
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

        cellString = self.findCellStats(gridX, gridY)
        label = self.widgets["cellLabel"]
        label.config(text=cellString)
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
        elif len(self.sugarscape.agents) == 0:
            self.sugarscape.toggleEnd()
        else:
            self.sugarscape.doTimestep()
            self.doTimestep()

    def doTimestep(self):
        if self.stopSimulation == True:
            self.sugarscape.toggleEnd()
            return
        if self.screenHeight != self.window.winfo_height() or self.screenWidth != self.window.winfo_width():
            self.resizeInterface()
        for i in range(self.sugarscape.environmentHeight):
            for j in range(self.sugarscape.environmentWidth):
                cell = self.sugarscape.environment.findCell(i, j)
                fillColor = self.lookupFillColor(cell)
                if self.grid[i][j]["color"] != fillColor:
                    self.canvas.itemconfig(self.grid[i][j]["rectangle"], fill=fillColor, outline="#C0C0C0")
                    self.grid[i][j] = {"rectangle": self.grid[i][j]["rectangle"], "color": fillColor}
        self.updateLabels()
        self.window.update()

    def doWindowClose(self, *args):
        # Indicate to per-timestep rendering to stop rendering
        self.stopSimulation = True
        self.window.destroy()
        self.sugarscape.toggleEnd()

    def findCellStats(self, cellX, cellY):
        cell = self.sugarscape.environment.findCell(cellX, cellY)
        cellSeason = cell.season
        if cell.season == None:
            cellSeason = '-'
        cellStats = "Cell: ({0},{1}) | Sugar: {2}/{3} | Spice: {4}/{5} | Pollution: {6} | Season: {7}".format(cellX, cellY, cell.sugar, cell.maxSugar, cell.spice, cell.maxSpice, round(cell.pollution, 2), cellSeason)
        agentStats = "Agent: - | Age: - | Sex: - | Vision: - | Movement: - | Sugar: - | Spice: - | Metabolism: -"
        agent = cell.agent
        if agent != None:
            agentStats = "Agent: {0} | Age: {1} | Sex: {2} | Vision: {3} | Movement: {4} | Sugar: {5} | Spice: {6} | Metabolism: {7}".format(str(agent), agent.age, agent.sex, round(agent.vision, 2), round(agent.movement, 2),
                                                                                                                                    round(agent.sugar, 2), round(agent.spice, 2), round(((agent.sugarMetabolism + agent.spiceMetabolism) / 2), 2))
        cellStats += "\n  {0}".format(agentStats)
        self.lastSelectedCell = {'x': cellX, 'y': cellY}
        return cellStats

    def hexToInt(self, hexval):
        intvals = []
        hexval = hexval.lstrip('#')
        for i in range(0, len(hexval), 2):
            subval = hexval[i:i + 2]
            intvals.append(int(subval, 16))
        return intvals

    def intToHex(self, intvals):
        hexval = "#"
        for i in intvals:
            subhex = "%0.2X" % i
            hexval = hexval + subhex
        return hexval

    def lookupFillColor(self, cell):
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
            return self.colors[agent.tribe]
        elif len(agent.diseases) > 0 and self.activeColorOptions["agent"] == "Disease":
            return self.colors["red"]
        elif len(agent.diseases) == 0 and self.activeColorOptions["agent"] == "Disease":
            return self.colors["blue"]
        return self.colors["noSex"]

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
        statsString = "Timestep: {0} | Agents: {1} | Metabolism: {2:.2f} | Movement: {3:.2f} | Vision: {4:.2f} | Gini: {5:.2f} | Trade Price: {6:.2f} | Trade Volume: {7:.2f}".format(
                self.sugarscape.timestep, stats["population"], stats["meanMetabolism"], stats["meanMovement"], stats["meanVision"], stats["giniCoefficient"], stats["meanTradePrice"], stats["tradeVolume"])
        label = self.widgets["statsLabel"]
        label.config(text=statsString)
        if self.lastSelectedCell != None:
            cellString = self.findCellStats(self.lastSelectedCell['x'], self.lastSelectedCell['y'])
            label = self.widgets["cellLabel"]
            label.config(text=cellString)

    def updateScreenDimensions(self):
        self.screenHeight = self.window.winfo_height()
        self.screenWidth = self.window.winfo_width()

    def updateSiteDimensions(self):
        self.siteHeight = (self.screenHeight - self.menuTrayOffset) / self.sugarscape.environmentHeight
        self.siteWidth = (self.screenWidth - self.windowBorderOffset) / self.sugarscape.environmentWidth
