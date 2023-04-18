#import itertools
#import matplotlib
#import matplotlib.pyplot
import tkinter

class GUI:
    def __init__(self, sugarscape, screenHeight=500, screenWidth=500):
        self.__sugarscape = sugarscape
        self.__screenHeight = screenHeight
        self.__screenWidth = screenWidth
        self.__window = self.configureWindow()

    def getSugarscape(self):
        return self.__sugarscape

    def getScreenHeight(self):
        return self.__screenHeight

    def getscreenWidth(self):
        return self.__screenWidth

    def getWindow(self):
        return self.__window

    def setSugarscape(self, sugarscape):
        self.__sugarscape = sugarscape

    def setScreenHeight(self, screenHeight):
        self.__screenHeight = screenHeight

    def setScreenWidth(self, screenWidth):
        self.__screenWidth = screenWidth

    def setWindow(self, window):
        self.__window = window

    def mainLoop(self):
        self.drawSugarscape()

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

    def configureWindow(self):
        borderEdge = 5
        window = tkinter.Tk()
        window.title("Sugarscape")
        window.geometry("%dx%d" % (self.__screenWidth + borderEdge, self.__screenHeight + borderEdge))
        window.resizable(True, True)
        window.configure(background="white")
        return window

    def mainLoop(self):
        return
