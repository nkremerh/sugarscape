#import itertools
import matplotlib
import matplotlib.pyplot
import tkinter

class GUI:
    def __init__(self, sugarscape, screenHeight=800, screenWidth=800):
        self.__sugarscape = sugarscape
        self.__screenHeight = screenHeight
        self.__screenWidth = screenWidth
        self.__window = None
        self.__canvas = None
        self.__grid = []
        self.__widgets = {}
        self.configureWindow()

    def getSugarscape(self):
        return self.__sugarscape

    def getScreenHeight(self):
        return self.__screenHeight

    def getscreenWidth(self):
        return self.__screenWidth

    def getWindow(self):
        return self.__window

    def getCanvas(self):
        return self.__canvas

    def getWidgets(self):
        return self.__widgets

    def setSugarscape(self, sugarscape):
        self.__sugarscape = sugarscape

    def setScreenHeight(self, screenHeight):
        self.__screenHeight = screenHeight

    def setScreenWidth(self, screenWidth):
        self.__screenWidth = screenWidth

    def setWindow(self, window):
        self.__window = window

    def setCanvas(self, canvas):
        self.__canvas = canvas

    def setWidgets(self, widgets):
        self.__widgets = widgets

    def drawAgent(self, agent):
        return

    def drawCell(self, cell):
        agent = cell.getAgent()
        if agent != None:
            self.drawAgent(agent)

    def drawEnvironment(self, environment):
        return

    def drawSugarscape(self):
        environment = self.__sugarscape.getEnvironment()
        self.drawEnvironment(environment)
        for i in range(environment.getHeight()):
            for j in range(environment.getWidth()):
                self.drawCell(environment.getCell(i, j))

    def doPlayButton(self):
        self.__sugarscape.setRun()
        self.__widgets["playButton"].config(text="Play Simulation" if self.__sugarscape.getRun() == False else "Pause Simulation")

    def doRenderButton(self):
        return

    def doStepButton(self):
        self.__sugarscape.doTimestep()

    def doGraphButton(self):
        return

    def doStatsButton(self):
        return

    def doGraphMenu(self):
        return

    def doAgentColorMenu(self):
        return

    def doEnvironmentColorMenu(self):
        return

    def doWindowClose(self, event=None):
        self.__window.destroy()
        self.__sugarscape.setEnd()

    def configureGraphNames(self):
        return ["TEST"]

    def configureAgentColorNames(self):
        return ["TEST"]

    def configureEnvironmentColorNames(self):
        return ["TEST"]

    def configureButtons(self, window):
        playButton = tkinter.Button(window, text="Play Simulation", command=self.doPlayButton)
        playButton.grid(row=0, column=0, sticky="nsew")
        renderButton = tkinter.Button(window, text="Pause Render ", command=self.doRenderButton)
        renderButton.grid(row=0, column=1, sticky="nsew")
        stepButton = tkinter.Button(window, text="Step Forward", command=self.doStepButton, relief=tkinter.RAISED)
        stepButton.grid(row=0, column=2, sticky="nsew")

        graphButton = tkinter.Menubutton(window, text="Graphs", relief=tkinter.RAISED)
        graphMenu = tkinter.Menu(graphButton, tearoff=0)
        graphButton.configure(menu=graphMenu)
        graphNames = self.configureGraphNames()
        graphNames.sort()
        lastSelectedGraph = tkinter.StringVar(window)
        lastSelectedGraph.set(graphNames[0]) # Default
        for name in graphNames:
            graphMenu.add_checkbutton(label=name, onvalue=name, offvalue=name, variable=lastSelectedGraph, command=self.doGraphMenu, indicatoron=True)
        graphButton.grid(row=0, column=3, sticky="nsew")

        agentColorButton = tkinter.Menubutton(window, text="Agent Coloring", relief=tkinter.RAISED)
        agentColorMenu = tkinter.Menu(agentColorButton, tearoff=0)
        agentColorButton.configure(menu=agentColorMenu)
        agentColorNames = self.configureAgentColorNames()
        agentColorNames.sort()
        agentColorNames.insert(0, "Default")
        lastSelectedAgentColor = tkinter.StringVar(window)
        lastSelectedAgentColor.set(agentColorNames[0])  # Default 
        for name in agentColorNames:
            agentColorMenu.add_checkbutton(label=name, onvalue=name, offvalue=name, variable=lastSelectedAgentColor, command=self.doAgentColorMenu, indicatoron=True)
        agentColorButton.grid(row=0, column=4, sticky="nsew")

        environmentColorButton = tkinter.Menubutton(window, text="Environment Coloring", relief=tkinter.RAISED)
        environmentColorMenu = tkinter.Menu(environmentColorButton, tearoff=0)
        environmentColorButton.configure(menu=environmentColorMenu)
        environmentColorNames = self.configureEnvironmentColorNames()
        environmentColorNames.sort()
        environmentColorNames.insert(0, "Default")
        lastSelectedEnvironmentColor = tkinter.StringVar(window)
        lastSelectedEnvironmentColor.set(environmentColorNames[0])  # Default 
        for name in environmentColorNames:
            environmentColorMenu.add_checkbutton(label=name, onvalue=name, offvalue=name, variable=lastSelectedEnvironmentColor, command=self.doEnvironmentColorMenu, indicatoron=True)
        environmentColorButton.grid(row=0, column=5, sticky="nsew")

        statsButton = tkinter.Button(window, text="Statistics", command=self.doStatsButton)
        statsButton.grid(row=0, column=6, sticky="nsew")

        self.__widgets["playButton"] = playButton
        self.__widgets["renderButton"] = renderButton
        self.__widgets["stepButton"] = stepButton
        self.__widgets["graphButton"] = graphButton
        self.__widgets["statsButton"] = statsButton
        self.__widgets["agentColorButton"] = agentColorButton
        self.__widgets["environmentColorButton"] = environmentColorButton
        self.__widgets["agentColorMenu"] = agentColorMenu
        self.__widgets["environmentColorMenu"] = environmentColorMenu
        self.__widgets["graphMenu"] = graphMenu
        self.__widgets["graphNames"] = graphNames
        self.__widgets["lastSelectedGraph"] = lastSelectedGraph

    def configureEnvironment(self):
        siteSize = self.__screenHeight / self.__sugarscape.getEnvironmentWidth()
        for i in range(self.__screenHeight):
            self.__grid.append([])
            for j in range(self.__screenWidth):
                fillColor = "green" # TODO: Replace with environment check for agent/sugar/spice at given cell coordinates i,j
                #x1 = 5 + (.5 * siteSize) + i * siteSize - (.5 * siteSize) # Upper right x coordinate
                #y1 = 5 + (.5 * siteSize) + j * siteSize - (.5 * siteSize) # Upper right y coordinate
                #x2 = 5 + (.5 * siteSize) + i * siteSize + (.5 * siteSize) # Lower left x coordinate
                #y2 = 5 + (.5 * siteSize) + j * siteSize + (.5 * siteSize) # Lower left y coordinate
                x1 = i * siteSize
                y1 = j * siteSize
                x2 = i * siteSize + (0.5 * siteSize)
                y2 = j * siteSize + (0.5 * siteSize)
                #self.__grid[i][j] = {"rectangle": self.__canvas.create_rectangle(x1, y1, x2, y2, fill=fillColor, outline="#c0c0c0"), "color": fillColor}
                self.__grid[i].append({"rectangle": self.__canvas.create_rectangle(x1, y1, x2, y2, fill=fillColor, outline="#c0c0c0"), "color": fillColor})

    def configureWindow(self):
        numMenuColumns = 7
        borderEdge = 5
        window = tkinter.Tk()
        self.__window = window
        window.title("Sugarscape")
        window.geometry("%dx%d" % (self.__screenWidth + borderEdge, self.__screenHeight + borderEdge))
        window.resizable(True, True)
        window.configure(background="white")
        window.option_add("*font", "Roboto 10")

        matplotlib.use("TkAgg") # Use Tk backend for matplotlib
        canvas = tkinter.Canvas(window, width=self.__screenWidth, height=self.__screenHeight, bg="white")
        self.__canvas = canvas
        self.configureButtons(window)
        canvas.grid(row=1, column=0, columnspan=numMenuColumns, sticky="nsew")

        self.configureEnvironment() # TODO: List index out of range error

        window.protocol("WM_DELETE_WINDOW", self.doWindowClose)
        window.bind("<Escape>", self.doWindowClose)
        #canvas.bind("<Button-1>", self.onClick)
