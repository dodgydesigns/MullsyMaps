import os
from pathlib import Path
import string
import time

from PySide2.QtCore import Qt, QThread, Signal, Slot, QSize
from PySide2.QtGui import QIcon, QPixmap
from PySide2.QtWidgets import QWidget, QApplication, QStyleFactory, \
    QGridLayout, QSizePolicy, QHBoxLayout, QPushButton, QLabel, QSlider, \
    QPlainTextEdit, QLineEdit

from graphics.view import View
import preferences


CUSTOM_STYLE = '''

            .QWidget {
                background-color: rgba(0, 0, 0, 100);
                color: white;
            }
            .QPushButton {
                background-color: rgb(0, 0, 0);
                color: white;
            }
            .QPushButton:hover {
                background-color: rgb(100, 100, 100);
                color: white;
            }
            .QLabel {
                background-color: rgba(0, 0, 0, 100);
                color: white;
            }
 
            .QTabWidget::pane {
                border: 1px solid black;
                background-color: rgba(50, 50, 150, 10);
                color: white;
            }
               
            .QTabWidget::tab-bar:top {
                top: 1px;
            }
               
            .QTabWidget::tab-bar:bottom {
                bottom: 1px;
            }
               
            .QTabWidget::tab-bar:left {
                right: 1px;
            }
   
            .QTabWidget::tab-bar:right {
                left: 1px;
            }
   
            .QTabBar::tab:selected {
                background-color: rgba(50,50,50, 200);
                color: white;
            }
               
            .QTabBar::tab:!selected {
                background-color: rgba(50,50,50, 100);
                color: gray;
            }
   
            .QTabBar::tab:!selected:hover {
                background-color: rgba(150,150,150, 200);
                color: #DDDDDD;
            }
               
            .QTabBar::tab:top:!selected {
                margin-top: 0px;
            }
                
            .QTabBar::tab:bottom:!selected {
                margin-bottom: 0px;
            }
                
            .QTabBar::tab:top, 
            .QTabBar::tab:bottom {
                min-width: 8ex;
                margin-right: 1px;
                padding: 5px 10px 5px 0px;
            }
     
            .QTabBar::tab:top:selected {
                border-bottom-color: none;
            }
                
            .QTabBar::tab:bottom:selected {
                border-top-color: none;
            }
                
            .QTabBar::tab:left:!selected {
                margin-right: 3px;
            }
                
            .QTabBar::tab:right:!selected {
                margin-left: 3px;
            }
                
            .QTabBar::tab:left, QTabBar::tab:right {
                min-height: 8ex;
                margin-bottom: -1px;
                padding: 10px 5px 10px 5px;
            }
                
            .QTabBar::tab:left:selected {
                border-left-color: none;
            }
                
            .QTabBar::tab:right:selected {
                border-right-color: none;
            }
 
            .QCheckBox {
                color: white;
                background-color: rgba(50,50,50, 100);
                spacing: 5px;
            }
            QCheckBox::indicator {
                color: white;
                width: 13px;
                height: 13px;
            }
'''

class COPView(QWidget):
    '''
    The main container to hold the COP.
    '''
    def __init__(self):
        '''
        Constructor
        '''
        super().__init__()
        
        self.view = None
        self.viewInitialise = False
        self.netCdfEnabled = False
        self.progressUpdateThreadRunning = False
        
        # This needs to be available from the start.
        self.statusValueLabel = QLabel()
        self.progressLabel = QPlainTextEdit()
        self.progressLabel.setFixedHeight(40)
        self.progressLabel.setMaximumBlockCount(20)
        self.progressLabel.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.progressLabel.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.progressLabel.setStyleSheet(""" QPlainTextEdit {font-size: 10px;} """)
                
    def initUi(self, width, height):

        layout = QGridLayout()
        layout.setSpacing(0)
        layout.setMargin(0)

        self.view = View(self, width, height)
        self.toolbox = self.view.toolbox
        self.toolbox.hide()

        menuBar = self.createMenuBar()
        toolBar = self.createToolBar(width)
         
        layout.addWidget(menuBar, 0, 0, 1, 0)
        layout.addWidget(self.view, 1, 0, 1, 0)
        layout.addWidget(self.toolbox, 1, 0, 5, 0)
        layout.addWidget(toolBar, 2, 0, 2, 0)

        self.setLayout(layout)
        QApplication.setStyle(QStyleFactory.create('Cleanlooks'))
                
        self.show()
        
        self.setStyleSheet(CUSTOM_STYLE)
        
        self.update()
        
    def createMenuBar(self):
        ''' Bar at top of window. '''
        menuWidget = QWidget()
        menuWidget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        menuLayout = QGridLayout()
        menuLayout.setSpacing(0)
        menuLayout.setContentsMargins(0, 0, 0, 0)
        
        leftMenuWidget = QWidget()
        leftMenuLayout = QHBoxLayout()
        leftMenuLayout.setContentsMargins(0, 0, 0, 0)
        leftMenuLayout.setAlignment(Qt.AlignLeft)
        leftMenuWidget.setLayout(leftMenuLayout)
        
        self.showHideButton = QPushButton('Menu')
        self.showHideButton.setFixedHeight(25)
        self.showHideButton.clicked.connect(self.showHideToolBox)
        leftMenuLayout.addWidget(self.showHideButton)
        
        zoomButton = QPushButton('ZoomOS')
        zoomButton.setFixedHeight(25)
        zoomButton.clicked.connect(self.zoomOwnship)
        leftMenuLayout.addWidget(zoomButton)        
                
        rightMenuWidget = QWidget()
        rightMenuLayout = QHBoxLayout()
        rightMenuLayout.setContentsMargins(0, 0, 0, 0)
        rightMenuLayout.setAlignment(Qt.AlignRight)
        rightMenuWidget.setLayout(rightMenuLayout)

        self.latLonLabel = QLabel('Welcome')
        self.latLonLabel.setFixedWidth(130)
        self.latLonLabel.setStyleSheet('.QLabel {padding-right: 20px;}')
        self.bearingLabel = QLabel('to')
        self.bearingLabel.setFixedWidth(110)
        self.bearingLabel.setStyleSheet('.QLabel {padding-right: 20px;}')
        self.distanceLabel = QLabel('MullsyMaps')
        self.distanceLabel.setFixedWidth(200)
        self.distanceLabel.setStyleSheet('.QLabel {padding-right: 20px;}')
        rightMenuLayout.addWidget(self.latLonLabel)
        rightMenuLayout.addWidget(self.bearingLabel)
        rightMenuLayout.addWidget(self.distanceLabel)
        
        messagePanelWidget = QWidget()
        self.messagePanelLayout = QHBoxLayout()
        self.messagePanelLayout.setContentsMargins(0,0,0,5)
        messagePanelWidget.setLayout(self.messagePanelLayout)

        menuLayout.addWidget(leftMenuWidget, 0, 0)
        menuLayout.addWidget(rightMenuWidget, 0, 1)
        menuLayout.addWidget(messagePanelWidget, 1, 0, 1, 2)
        menuWidget.setLayout(menuLayout)
        menuWidget.setStatusTip("""QWidget {background-color: black;}""")
        
        return menuWidget
    
    def createToolBar(self, width):
        ''' Bar at bottom of window. '''
        menuWidget = QWidget()
        menuWidget.setFixedHeight(40)
        menuWidget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        menuLayout = QGridLayout()
        menuLayout.setContentsMargins(0, 0, 0, 0)  
        menuLayout.setAlignment(Qt.AlignLeft)     
                
        iconOpacitySlider = QSlider(Qt.Horizontal)
        iconOpacitySlider.setMinimum(0)
        iconOpacitySlider.setMaximum(100)
        iconOpacitySlider.setValue(100)
        iconOpacitySlider.setFixedWidth(100)
        iconOpacitySlider.setFixedHeight(20)
        iconOpacitySlider.setStyleSheet('''
                                        .QSlider {
                                            padding: 10px;
                                            margin-left: 10px;
                                        }
                                    ''')
        iconOpacitySlider.valueChanged.connect(lambda: self.opacityChange(iconOpacitySlider.value()))

        iconSizePlusButton = QPushButton('+')
        iconSizePlusButton.setMaximumWidth(20)
        iconSizeMinusButton = QPushButton('-')
        iconSizeMinusButton.setMaximumWidth(20)
        iconSizePlusButton.clicked.connect(lambda: self.changeIconSize(1.2))
        iconSizeMinusButton.clicked.connect(lambda: self.changeIconSize(0.8))
        
        self.netDataLabel = QLabel('Sound Speed')
        self.depthLabel = QLabel('00.0/000.0m')
        self.depthPlusButton = QPushButton('+')
        self.depthMinusButton = QPushButton('-')
        self.depthPlusButton.clicked.connect(lambda: self.updateDepth('up'))
        self.depthMinusButton.clicked.connect(lambda: self.updateDepth('down'))
        self.depthTextBox = QLineEdit()
        self.depthTextBox.setMaximumWidth(90)
        self.depthTextBox.setStyleSheet(""" QLineEdit { background-color: gray; border-style: solid; border-color: white; border-width: }""")
        self.depthTextBox.returnPressed.connect(self.depthTextEntered)
        self.startNetCdfButton = QPushButton()
        self.startNetCdfButton.setFixedWidth(48)
        self.startNetCdfButton.setFixedHeight(48)

        path = str(Path(preferences.ICON_PATH)) + os.sep
        
        self.startNetCdfButton.setIcon(QIcon(QPixmap(path + 'radar.svg')))
        self.startNetCdfButton.setIconSize(QSize(48, 48))
        self.startNetCdfButton.clicked.connect(self.startNetCdf)

        self.startRulerButton = QPushButton()
        self.startRulerButton.setFixedWidth(48)
        self.startRulerButton.setFixedHeight(48)
        self.startRulerButton.setIcon(QIcon(QPixmap(path + 'ruler.svg')))
        self.startRulerButton.setIconSize(QSize(48, 48))
        self.startRulerButton.clicked.connect(self.createRulerLayer)
        self.rulerLabel = QLabel('0.00 yd\n0.0 hrs')
        
        menuLayout.addWidget(QLabel('Icon Opacity'),        0, 0, 1, 2)
        menuLayout.addWidget(iconOpacitySlider,             1, 0, 1, 2)
        menuLayout.addWidget(QLabel('   '),                 0, 2, 1, 1)
        
        menuLayout.addWidget(QLabel('Icon Size'),           0, 3, 1, 2)
        menuLayout.addWidget(iconSizeMinusButton,           1, 3, 1, 1)
        menuLayout.addWidget(iconSizePlusButton,            1, 4, 1, 1)
        menuLayout.addWidget(QLabel('   '),                 0, 5, 1, 1)

        menuLayout.addWidget(self.startNetCdfButton,        0, 6, 2, 2)
        menuLayout.addWidget(self.netDataLabel,             0, 7, 1, 2)
        menuLayout.addWidget(self.depthLabel,               0, 9, 1, 1)
        menuLayout.addWidget(self.depthMinusButton,         1, 7, 1, 1)
        menuLayout.addWidget(self.depthPlusButton,          1, 8, 1, 1)
        menuLayout.addWidget(self.depthTextBox,             1, 9, 1, 1)
        menuLayout.addWidget(QLabel('   '),                 0, 10, 1, 1)
        menuLayout.addWidget(self.startRulerButton,         0, 11, 2, 1)
        menuLayout.addWidget(self.rulerLabel,               0, 12, 2, 1)

        statusLabel = QLabel('Status')
        statusLabel.setStyleSheet(""" QLabel { margin-left: """ + str(0.5*self.view.canvasWidth) + """px; }""")
        menuLayout.addWidget(statusLabel,                   0, 11, 1, 4)
        self.statusValueLabel.setStyleSheet(""" QLabel { border-style: solid; border-color: white; border-width: 1px; font-size: 11px; margin-left: """ + str(0.5*self.view.canvasWidth) + """px; }""")
        menuLayout.addWidget(self.statusValueLabel,         1, 11, 1, 4)
        menuWidget.setLayout(menuLayout)
        
        self.enableNetCdfControls(False)

        return menuWidget

    def opacityChange(self, opacity):
        '''
        Change the opacity of the SVG MIL-STD icon part of a contact.
        '''
        self.view.setIconOpacity(opacity/100)
        
    def startNetCdf(self):
        '''
        Starts the process of computing the sound speed for all the spirographs required to cover the
        ruler line entered by the user.
        '''
        self.netCdfEnabled = not self.netCdfEnabled
        if self.netCdfEnabled:
            path = os.getcwd().replace('\\', '/') + '/../cruse-common/source/Views/COPView/images/'
            self.startNetCdfButton.setIcon(QIcon(QPixmap(path + 'radar_green.svg'))) 
            self.enableNetCdfControls(False)

            self.view.spirographLayer.addProbOfDetectionBoundaries()
            self.ncWmsWorkerThread = DepthChangeWorker(self)
            self.ncWmsWorkerThread.finishedSignal.connect(self.view.mainWindow.depthChangeComplete)
            self.ncWmsWorkerThread.start()
            
            self.startRulerButton.setEnabled(False)
            
            self.startProgressUpdateThread()
            
        else:
            self.depthLabel.setText('00.0/000.0m')
            self.enableNetCdfControls(True)
            path = os.getcwd().replace('\\', '/') + '/../cruse-common/source/Views/COPView/images/'
            self.startNetCdfButton.setIcon(QIcon(QPixmap(path + 'radar.svg')))    
            
            self.view.spirographLayer.clear()
            
    def createRulerLayer(self, end=None):
        '''
        The ruler layer draws a line at each click point. It sums the total length of each line segment and
        determines how long it would take to traverse at current speed.
        
        The ruler layer is also the basis of the sound speed spirographs which are used to show the probability
        of detection for a location/depth.
        ''' 
        path = os.getcwd().replace('\\', '/') + '/../cruse-common/source/Views/COPView/images/'
        
        if self.view.rulerLayer.ruleExists:
            self.killRuler()
            
        self.view.rulerLayer.rulerEnabled = not self.view.rulerLayer.rulerEnabled
        if self.view.rulerLayer.rulerEnabled:
            self.startRulerButton.setIcon(QIcon(QPixmap(path + 'ruler_green.svg')))
            self.view.rulerLayer.currentlyRuling = True
        else:
            self.startRulerButton.setIcon(QIcon(QPixmap(path + 'ruler.svg')))
            
        if end == 'end':
            self.startRulerButton.setIcon(QIcon(QPixmap(path + 'ruler_red.svg')))
            self.view.rulerLayer.ruleExists = True
            self.enableNetCdfControls(True)

            
    def killRuler(self):
        self.view.rulerLayer.clearRulerLines()
            
        self.updateRulerLabel([])
        self.view.rulerLayer.ruleExists = False
        self.view.rulerLayer.rulerEnabled = True
        
        self.view.spirographLayer.clear()
        self.enableNetCdfControls(False)
        self.netCdfEnabled = False
        path = os.getcwd().replace('\\', '/') + '/../cruse-common/source/Views/COPView/images/'
        self.startNetCdfButton.setIcon(QIcon(QPixmap(path + 'radar.svg'))) 
        
    def updateRulerLabel(self, lines):
        ''' Shows the length of the ruler path and time to navigate at current speed. '''

        distance = 0
        for line in lines:
            distance += self.view.mapController.distanceBetweenTwoPoints(line.startLatLon.x(),
                                                                         line.startLatLon.y(),
                                                                         line.endLatLon.x(),
                                                                         line.endLatLon.y())
        
        osSpeedInMetersPerSecond = 0.514444 * self.view.ownship.speed
        distanceInMeters = distance * 0.9144
        timeInSeconds = distanceInMeters / osSpeedInMetersPerSecond
        m, s = divmod(timeInSeconds, 60)
        h, m = divmod(m, 60)
        self.rulerLabel.setText('{:.0f} yd\n{:.0f}:{:.0f}:{:.0f}'.format(distance, h, m, s))
        
    def updateDepth(self, change):
        '''
        Updates depth based on +/- buttons.
        '''
        if change == 'up' and self.view.rulerLayer.depth < 145:
                self.updateDepthByValue(self.view.spirographLayer.depth + 10)
        elif change == 'down' and self.view.spirographLayer.depth > 10:
                self.updateDepthByValue(self.view.rulerLayer.depth - 10)
        else:
            self.updateDepthByValue(0)

    def updateDepthByValue(self, depth):
        '''
        When a depth is added in the text box or modified by the +/- buttons,
        this function updates all spirographs with the new values(depth).
        '''
        self.view.spirographLayer.depth = depth
        self.view.spirographLayer.clear()
        self.netCdfEnabled = False
        self.startNetCdf()
        
    def depthChangeComplete(self):        
        ''' 
        It takes a long time to recompute all the sound speed values so this waits for the
        computations to be complete and updates the UI.
        '''
        self.statusValueLabel.setText('')
        self.enableNetCdfControls(True)
        self.stopProgressUpdateThread()
        self.startRulerButton.setEnabled(True)
        self.setDepthLabel()

    def setDepthLabel(self):
        self.depthLabel.setText('{}/{}m'.format(self.view.spirographLayer.depth, self.view.spirographLayer.maxDepth))
        
    def enableNetCdfControls(self, enable):
        ''' 
        These controls are disabled when sound speed data is being calculated so the process
        (which is in its own thread) cannot be interrupted.
        '''
        self.depthLabel.setEnabled(enable)
        self.depthTextBox.setEnabled(enable)
        self.netDataLabel.setEnabled(enable)
        self.depthPlusButton.setEnabled(enable)
        self.depthMinusButton.setEnabled(enable) 
        self.startNetCdfButton.setEnabled(enable)
        
    def startProgressUpdateThread(self):
        '''
        Starts drawing and updating the progress bar to show that something is happening.
        '''
        if not self.progressUpdateThreadRunning:
            self.progress = ''
            self.progressUpdateThread = ProgressWorker()
            self.progressUpdateThread.tickSignal.connect(self.updateProgress)
            self.progressUpdateThread.start()
            self.progressUpdateThreadRunning = True
        
    def stopProgressUpdateThread(self):
        ''' Stops the progress bar when lengthy computations are complete. '''
        if self.progressUpdateThreadRunning:
            self.progressUpdateThread.terminate()
            self.statusValueLabel.setText('')
            self.progressUpdateThreadRunning = False

    def updateProgress(self):
        ''' Adds at 'tick' to the progress bar every half second. '''
        self.progress += '|'
        if self.progress == '|||||||||||':
            self.progress = ''
        self.statusValueLabel.setText(self.progress)
        
    def changeIconSize(self, size):
        '''
        Change the size of the SVG MIL-STD icon part of a contact.
        '''
        self.view.setIconSize(size)

    def zoomOwnship(self):
        ''' Move to centre of ownship and zoom in. '''
        self.view.zoomOwnship()

    def updateLocationLabel(self, mouseLat, mouseLon, bearing, distance):
        """
        Label at the top right of the COP shows lat/lon x/y etc. of the cursor.
        """
        mouse = self.view.mapController.toCanvasCoordinates(mouseLat, mouseLon)

        if mouseLat < 0:
            xText = '{0:.2f}°S'.format(-mouseLat)
        else:
            xText = '{0:.2f}°N'.format(mouseLat)

        if mouseLon > 180:
            yText = '{0:.2f}°W'.format(mouseLon)
        else:
            yText = '{0:.2f}°E'.format(mouseLon)

        if bearing >= 0:
            bearingText = '<font color="#00FF00">   Bearing: {:3.1f}°</font>'.format(bearing)
        else:
            bearingText = '<font color="#FF0000">   Bearing: {:3.1f}°</font>'.format(abs(bearing))

        # TODO: make this available
        # distance /= 0.9144 # convert to yards
        if distance >= 1000:
            distanceText = 'Distance: {:.2f}{}s'.format(distance / 1000, preferences.DISTANCE_UNITS_HIGH)
        else:
            distanceText = 'Distance: {:.0f}{}'.format(distance, preferences.DISTANCE_UNITS_LOW)

        # self.latLonLabel.setText('{}, {}'.format(xText, yText))
        # self.bearingLabel.setText(bearingText)
        # self.distanceLabel.setText(distanceText)
        # self.locationLabel.setText(bearingText)
        
    def showHideToolBox(self):
        ''' Show/hide menu. '''
        if self.toolbox.isVisible():
            self.toolbox.hide()
            self.toolbox.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            self.showHideButton.setText('Menu')
            self.view.currentlyDrawing = False
            self.toolbox.tabBox.disableAnnotationLayers()
        else:
            self.toolbox.updateEntries()
            self.toolbox.show()
            self.showHideButton.setText('Close')
            self.toolbox.setAttribute(Qt.WA_TransparentForMouseEvents, False)
            self.toolbox.tabBox.setCurrentIndex(0) # always start with the layers tab.
                
    def depthTextEntered(self):
        '''
        Listen for Enter or Return and set depth if depth text box is not empty.
        '''
        if len(self.depthTextBox.text()) >= 0:
            if float(self.depthTextBox.text()) < 0:
                self.updateDepthByValue(0)
            elif float(self.depthTextBox.text()) > self.view.spirographLayer.maxDepth:
                self.updateDepthByValue(self.view.spirographLayer.maxDepth)
            else:
                self.updateDepthByValue(self.depthTextBox.text())

            self.depthTextBox.setText('')
            self.depthTextBox.update()

    def doupdate(self, width, height):
        ''' Don't want to start creating the COP until we have ownship. '''
        if self.view is None:
            self.initUi(width, height)

        self.view.update()

class DepthChangeWorker(QThread):
    '''
    Thread to compute the sound speed for all required location points.
    '''
    finishedSignal = Signal(string, int)
    
    def __init__(self, copView):
        QThread.__init__(self)
        self.view = copView.view

    @Slot()
    def run(self):
        self.view.spirographLayer.fill()
        self.finishedSignal.emit('done')
        
class ProgressWorker(QThread):
    ''' Thread to update the progress bar. '''
    tickSignal = Signal()
    
    def __init__(self):
        QThread.__init__(self)

    @Slot()
    def run(self):
        while True:
            self.tickSignal.emit()
            time.sleep(0.5)