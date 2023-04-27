import tkinter

class GUI:
    def __init__(self, sugarscape, screenHeight=800, screenWidth=800):
        self.__sugarscape = sugarscape
        self.__screenHeight = screenHeight
        self.__screenWidth = screenWidth
        self.__window = None
        self.__canvas = None
        self.__grid = [[None for j in range(screenWidth)]for i in range(screenHeight)]
        self.__colors = {"sugar": "#F2FA00", "spice": "#9B4722", "sugarAndSpice": "#CFB20E", "noSex": "#FA3232", "female": "#FA32FA", "male": "#3232FA", "pollution": "#803280",
                         "green": "#32FA32", "blue": "#3232FA", "red": "#FA3232"}
        self.__widgets = {}
        self.__lastSelectedAgentColor = None
        self.__lastSelectedEnvironmentColor = None
        self.__activeColorOptions = {"agent": None, "environment": None}
        self.configureWindow()

    def configureAgentColorNames(self):
        return ["Sex", "Tribes"]

    def configureButtons(self, window):
        playButton = tkinter.Button(window, text="Play Simulation", command=self.doPlayButton)
        playButton.grid(row=0, column=0, sticky="nsew")
        stepButton = tkinter.Button(window, text="Step Backward", command=self.doStepBackwardButton, relief=tkinter.RAISED)
        stepButton.grid(row=0, column=1, sticky="nsew")
        stepButton = tkinter.Button(window, text="Step Forward", command=self.doStepForwardButton, relief=tkinter.RAISED)
        stepButton.grid(row=0, column=2, sticky="nsew")

        agentColorButton = tkinter.Menubutton(window, text="Agent Coloring", relief=tkinter.RAISED)
        agentColorMenu = tkinter.Menu(agentColorButton, tearoff=0)
        agentColorButton.configure(menu=agentColorMenu)
        agentColorNames = self.configureAgentColorNames()
        agentColorNames.sort()
        agentColorNames.insert(0, "Default")
        self.__lastSelectedAgentColor = tkinter.StringVar(window)
        self.__lastSelectedAgentColor.set(agentColorNames[0])  # Default 
        for name in agentColorNames:
            agentColorMenu.add_checkbutton(label=name, onvalue=name, offvalue=name, variable=self.__lastSelectedAgentColor, command=self.doAgentColorMenu, indicatoron=True)
        agentColorButton.grid(row=0, column=3, sticky="nsew")

        environmentColorButton = tkinter.Menubutton(window, text="Environment Coloring", relief=tkinter.RAISED)
        environmentColorMenu = tkinter.Menu(environmentColorButton, tearoff=0)
        environmentColorButton.configure(menu=environmentColorMenu)
        environmentColorNames = self.configureEnvironmentColorNames()
        environmentColorNames.sort()
        environmentColorNames.insert(0, "Default")
        self.__lastSelectedEnvironmentColor = tkinter.StringVar(window)
        self.__lastSelectedEnvironmentColor.set(environmentColorNames[0])  # Default 
        for name in environmentColorNames:
            environmentColorMenu.add_checkbutton(label=name, onvalue=name, offvalue=name, variable=self.__lastSelectedEnvironmentColor, command=self.doEnvironmentColorMenu, indicatoron=True)
        environmentColorButton.grid(row=0, column=4, sticky="nsew")

        statsLabel = tkinter.Label(window, text="Timestep: - | Population: - | Metabolism: - | Vision: - | Gini: - | Trade Price: - | Trade Volume: -", font="Roboto 10", justify=tkinter.LEFT)
        statsLabel.grid(row=1, column=0, columnspan=5, sticky="nsew")

        self.__widgets["playButton"] = playButton
        self.__widgets["stepButton"] = stepButton
        self.__widgets["agentColorButton"] = agentColorButton
        self.__widgets["environmentColorButton"] = environmentColorButton
        self.__widgets["agentColorMenu"] = agentColorMenu
        self.__widgets["environmentColorMenu"] = environmentColorMenu
        self.__widgets["statsLabel"] = statsLabel
 
    def configureEnvironment(self):
        borderOffset = 10
        siteSize = (self.__screenHeight - borderOffset) / self.__sugarscape.getEnvironmentWidth()
        for i in range(self.__sugarscape.getEnvironmentHeight()):
            for j in range(self.__sugarscape.getEnvironmentWidth()):
                cell = self.__sugarscape.getEnvironment().getCell(i, j)
                fillColor = self.lookupFillColor(cell)
                x1 = 5 + (0.50 * siteSize) + i * siteSize - (0.50 * siteSize) # Upper right x coordinate
                y1 = 5 + (0.50 * siteSize) + j * siteSize - (0.50 * siteSize) # Upper right y coordinate
                x2 = 5 + (0.50 * siteSize) + i * siteSize + (0.50 * siteSize) # Lower left x coordinate
                y2 = 5 + (0.50 * siteSize) + j * siteSize + (0.50 * siteSize) # Lower left y coordinate
                self.__grid[i][j] = {"rectangle": self.__canvas.create_rectangle(x1, y1, x2, y2, fill=fillColor, outline="#c0c0c0"), "color": fillColor}

    def configureEnvironmentColorNames(self):
        return ["Pollution"]

    def configureWindow(self):
        numMenuColumns = 5
        borderEdge = 5
        window = tkinter.Tk()
        self.__window = window
        window.title("Sugarscape")
        window.geometry("%dx%d" % (self.__screenWidth + borderEdge, self.__screenHeight + borderEdge))
        window.resizable(True, True)
        window.configure(background="white")
        window.option_add("*font", "Roboto 10")

        canvas = tkinter.Canvas(window, width=self.__screenWidth, height=self.__screenHeight, bg="white")
        self.__canvas = canvas
        self.configureButtons(window)
        canvas.grid(row=2, column=0, columnspan=numMenuColumns, sticky="nsew")
        window.update()

        self.configureEnvironment()
        buttonsOffset = self.__widgets["playButton"].winfo_height()
        window.geometry("%dx%d" % (self.__screenWidth + borderEdge, self.__screenHeight + borderEdge + buttonsOffset))
        window.update()

        window.protocol("WM_DELETE_WINDOW", self.doWindowClose)
        window.bind("<Escape>", self.doWindowClose)
        window.bind("<space>", self.doPlayButton)
        canvas.bind("<Button-1>", self.doClick)

    def destroyGUI(self):
        self.__window.destroy()

    def doAgentColorMenu(self, *args):
        self.__activeColorOptions["agent"] = self.__lastSelectedAgentColor.get()

    def doClick(self, event):
        return

    def doEnvironmentColorMenu(self):
        self.__activeColorOptions["environment"] = self.__lastSelectedEnvironmentColor.get()

    def doPlayButton(self, *args):
        self.__sugarscape.setRun()
        self.__widgets["playButton"].config(text="  Play Simulation  " if self.__sugarscape.getRun() == False else "Pause Simulation")

    def doRenderButton(self):
        return

    def doStatsButton(self):
        return

    def doStepBackwardButton(self):
        return

    def doStepForwardButton(self):
        self.__sugarscape.doTimestep()

    def doTimestep(self):
        for i in range(self.__sugarscape.getEnvironmentHeight()):
            for j in range(self.__sugarscape.getEnvironmentWidth()):
                cell = self.__sugarscape.getEnvironment().getCell(i, j)
                fillColor = self.lookupFillColor(cell)
                if self.__grid[i][j]["color"] != fillColor:
                    self.__canvas.itemconfig(self.__grid[i][j]["rectangle"], fill=fillColor, outline="#C0C0C0")
                    self.__grid[i][j] = {"rectangle": self.__grid[i][j]["rectangle"], "color": fillColor}
        self.updateLabel()
        self.__window.update()

    def doWindowClose(self, event=None):
        self.__window.destroy()
        self.__sugarscape.setEnd()

    def getCanvas(self):
        return self.__canvas

    def getScreenHeight(self):
        return self.__screenHeight

    def getscreenWidth(self):
        return self.__screenWidth

    def getSugarscape(self):
        return self.__sugarscape
 
    def getWidgets(self):
        return self.__widgets

    def getWindow(self):
        return self.__window

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
        agent = cell.getAgent()
        if agent == None:
            if self.__activeColorOptions["environment"] == "Pollution":
                return self.recolorByResourceAmount(cell, self.__colors["pollution"])
            else:
                currSugar = cell.getCurrSugar()
                currSpice = cell.getCurrSpice()
                if currSugar > 0 and currSpice == 0:
                    return self.recolorByResourceAmount(cell, self.__colors["sugar"])
                elif currSpice > 0 and currSugar == 0:
                    return self.recolorByResourceAmount(cell, self.__colors["spice"])
                else:
                    return self.recolorByResourceAmount(cell, self.__colors["sugarAndSpice"])
        elif agent.getSex() != None and self.__activeColorOptions["agent"] == "Sex":
            return self.__colors[agent.getSex()]
        elif agent.getTribe() != None and self.__activeColorOptions["agent"] == "Tribes":
            return self.__colors[agent.getTribe()]
        return self.__colors["noSex"]

    def recolorByResourceAmount(self, cell, fillColor):
        recolorFactor = 0
        if self.__activeColorOptions["environment"] == "Pollution":
            # Since global max pollution changes at each timestep, set constant to prevent misleading recoloring of cells
            maxPollution = 20
            # Once a cell has exceeded the number of colors made possible with maxPollution, keep using the max color
            recolorFactor = min(1, cell.getCurrPollution() / maxPollution)
        else:
            currSugar = cell.getCurrSugar()
            currSpice = cell.getCurrSpice()
            maxSugar = self.__sugarscape.getEnvironment().getGlobalMaxSugar()
            maxSpice = self.__sugarscape.getEnvironment().getGlobalMaxSpice()
            if currSugar > 0 and currSpice == 0:
                recolorFactor = currSugar / maxSugar
            elif currSpice > 0 and currSugar == 0:
                recolorFactor = currSpice / maxSpice
            else:
                recolorFactor = (currSugar + currSpice) / (maxSugar + maxSpice)
        subcolors = self.hexToInt(fillColor)
        i = 0
        for color in subcolors:
            color = int(color + (255 - color) * (1 - recolorFactor))
            subcolors[i] = color
            i += 1
        fillColor = self.intToHex(subcolors)
        return fillColor

    def setCanvas(self, canvas):
        self.__canvas = canvas

    def setScreenHeight(self, screenHeight):
        self.__screenHeight = screenHeight

    def setScreenWidth(self, screenWidth):
        self.__screenWidth = screenWidth

    def setSugarscape(self, sugarscape):
        self.__sugarscape = sugarscape
 
    def setWidgets(self, widgets):
        self.__widgets = widgets

    def setWindow(self, window):
        self.__window = window

    def updateLabel(self):
        stats = self.__sugarscape.getRuntimeStats()
        statsString = "Timestep: {0} | Agents: {1} | Metabolism: {2:.2f} | Vision: {3:.2f} | Gini: {4:.2f} | Trade Price: {5:.2f} | Trade Volume: {6:.2f}".format(
                self.__sugarscape.getTimestep(), stats["agents"], stats["meanMetabolism"], stats["meanVision"], stats["giniCoefficient"], stats["meanTradePrice"], stats["meanTradeVolume"])
        label = self.__widgets["statsLabel"]
        label.config(text=statsString)
