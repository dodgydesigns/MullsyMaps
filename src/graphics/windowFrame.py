import time

from PySide2.QtCore import Qt, QThread, Signal, Slot, QSize
from PySide2.QtGui import QIcon, QPixmap
from PySide2.QtWidgets import QWidget, QGridLayout, QSizePolicy, QHBoxLayout, QPushButton, QLabel, QSlider, \
    QPlainTextEdit

from graphics.map import Map
import preferences

from src.gis.mts_controller import distanceBetweenTwoPoints

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


class WindowFrame(QWidget):
    """
    The main container to hold the map.
    """

    def __init__(self):
        """
        Constructor
        """
        super().__init__()

        self.map = None
        self.viewInitialise = False
        self.progressUpdateThreadRunning = False

        self.statusValueLabel = QLabel()
        self.progressLabel = QPlainTextEdit()
        self.startRulerButton = QPushButton()
        self.rulerLabel = QLabel('0.00 yd\n0.0 hrs')
        self.map = Map(self)
        self.toolbox = self.map.toolbox

        self.menuButton = QPushButton('File')
        self.layersButton = QPushButton('Layers')
        self.latLonLabel = QLabel('Welcome')
        self.bearingLabel = QLabel('to')
        self.distanceLabel = QLabel('MullsyMaps')
        self.progress = ''
        self.progressUpdateThread = ProgressWorker()

    def initUi(self):

        layout = QGridLayout()

        self.progressLabel.setFixedHeight(40)
        self.progressLabel.setMaximumBlockCount(20)
        self.progressLabel.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.progressLabel.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.progressLabel.setStyleSheet(""" QPlainTextEdit {font-size: 10px;} """)

        layout.addWidget(self.createTopBar(), 0, 0, 1, 0)
        layout.addWidget(self.map, 1, 0, 1, 0)
        layout.addWidget(self.toolbox, 1, 0, 5, 0)
        layout.addWidget(self.createBottomBar(), 10, 0, 2, 0)

        self.toolbox.hide()
        self.setLayout(layout)
        self.setStyleSheet(CUSTOM_STYLE)
        self.show()

    def createTopBar(self):
        """ Bar at top of window. """
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

        self.layersButton.setFixedHeight(25)
        self.layersButton.clicked.connect(self.showHideToolBox)
        leftMenuLayout.addWidget(self.layersButton)

        zoomButton = QPushButton('ZoomOS')
        zoomButton.setFixedHeight(25)
        zoomButton.clicked.connect(self.zoomOwnship)
        leftMenuLayout.addWidget(zoomButton)

        rightMenuWidget = QWidget()
        rightMenuLayout = QHBoxLayout()
        rightMenuLayout.setContentsMargins(0, 0, 0, 0)
        rightMenuLayout.setAlignment(Qt.AlignRight)
        rightMenuWidget.setLayout(rightMenuLayout)

        self.latLonLabel.setFixedWidth(130)
        self.latLonLabel.setStyleSheet('.QLabel {padding-right: 20px;}')
        self.bearingLabel.setFixedWidth(110)
        self.bearingLabel.setStyleSheet('.QLabel {padding-right: 20px;}')
        self.distanceLabel.setFixedWidth(200)
        self.distanceLabel.setStyleSheet('.QLabel {padding-right: 20px;}')
        rightMenuLayout.addWidget(self.latLonLabel)
        rightMenuLayout.addWidget(self.bearingLabel)
        rightMenuLayout.addWidget(self.distanceLabel)

        messagePanelWidget = QWidget()

        menuLayout.addWidget(leftMenuWidget, 0, 0)
        menuLayout.addWidget(rightMenuWidget, 0, 1)
        menuLayout.addWidget(messagePanelWidget, 1, 0, 1, 2)
        menuWidget.setLayout(menuLayout)
        menuWidget.setStatusTip("""QWidget {background-color: black;}""")

        return menuWidget

    def createBottomBar(self):
        """ Bar at bottom of window. """
        bottomBarWidget = QWidget()
        bottomBarWidget.setFixedSize(preferences.SCREEN_RESOLUTION.width(), 50)
        bottomBarLayout = QGridLayout()
        bottomBarLayout.setContentsMargins(10, 0, 0, 0)
        bottomBarLayout.setAlignment(Qt.AlignLeft)

        iconOpacitySlider = QSlider(Qt.Horizontal)
        iconOpacitySlider.setMinimum(0)
        iconOpacitySlider.setMaximum(100)
        iconOpacitySlider.setValue(100)
        iconOpacitySlider.setFixedWidth(100)
        iconOpacitySlider.setFixedHeight(20)
        iconOpacitySlider.valueChanged.connect(lambda: self.opacityChange(iconOpacitySlider.value()))

        iconSizePlusButton = QPushButton('+')
        iconSizePlusButton.setMaximumWidth(20)
        iconSizeMinusButton = QPushButton('-')
        iconSizeMinusButton.setMaximumWidth(20)
        iconSizePlusButton.clicked.connect(lambda: self.changeIconSize(1.2))
        iconSizeMinusButton.clicked.connect(lambda: self.changeIconSize(0.8))

        self.startRulerButton.setFixedWidth(48)
        self.startRulerButton.setFixedHeight(48)
        self.startRulerButton.setIcon(QIcon(QPixmap(str(preferences.ICON_PATH) + '/ruler.svg')))
        self.startRulerButton.setIconSize(QSize(48, 48))
        self.startRulerButton.clicked.connect(self.createRulerLayer)

        bottomBarLayout.addWidget(QLabel('Icon Opacity'), 0, 2, 1, 2)
        bottomBarLayout.addWidget(iconOpacitySlider, 1, 2, 1, 2)

        bottomBarLayout.addWidget(QLabel('Icon Size'), 0, 4, 1, 2)
        bottomBarLayout.addWidget(iconSizeMinusButton, 1, 4, 1, 1)
        bottomBarLayout.addWidget(iconSizePlusButton, 1, 5, 1, 1)

        bottomBarLayout.addWidget(self.startRulerButton, 0, 6, 2, 2)
        bottomBarLayout.addWidget(self.rulerLabel, 0, 8, 2, 1)

        statusLabel = QLabel('Status')
        bottomBarLayout.addWidget(statusLabel, 0, 20, 1, 4)
        self.statusValueLabel.setStyleSheet(""" QLabel { border-style: solid;
                                                border-color: white;
                                                border-width: 1px;
                                                font-size: 11px; }""")
        bottomBarLayout.addWidget(self.statusValueLabel, 1, 20, 1, 4)
        bottomBarWidget.setLayout(bottomBarLayout)

        return bottomBarWidget

    def opacityChange(self, opacity):
        """
        Change the opacity of the SVG MIL-STD icon part of a contact.
        """
        self.map.setIconOpacity(opacity / 100)

    def createRulerLayer(self, end=None):
        """
        The ruler layer draws a line at each click point. It sums the total length of each line segment and
        determines how long it would take to traverse at current speed.
        """
        if self.map.rulerLayer.ruleExists:
            self.killRuler()

        self.map.rulerLayer.rulerEnabled = not self.map.rulerLayer.rulerEnabled
        if self.map.rulerLayer.rulerEnabled:
            self.startRulerButton.setIcon(QIcon(QPixmap(str(preferences.ICON_PATH) + 'ruler_green.svg')))
            self.map.rulerLayer.currentlyRuling = True
        else:
            self.startRulerButton.setIcon(QIcon(QPixmap(str(preferences.ICON_PATH) + 'ruler.svg')))

        if end == 'end':
            self.startRulerButton.setIcon(QIcon(QPixmap(str(preferences.ICON_PATH) + 'ruler_red.svg')))
            self.map.rulerLayer.ruleExists = True

    def killRuler(self):
        self.map.rulerLayer.clearRulerLines()

        self.updateRulerLabel([])
        self.map.rulerLayer.ruleExists = False
        self.map.rulerLayer.rulerEnabled = True

        self.map.spirographLayer.clear()

    def updateRulerLabel(self, lines):
        """ Shows the length of the ruler path and time to navigate at current speed. """

        distance = 0
        for line in lines:
            distance += distanceBetweenTwoPoints(line.startLatLon.x(),
                                                 line.startLatLon.y(),
                                                 line.endLatLon.x(),
                                                 line.endLatLon.y())

        osSpeedInMetersPerSecond = 0.514444 * self.map.ownship.speed
        distanceInMeters = distance * 0.9144
        timeInSeconds = distanceInMeters / osSpeedInMetersPerSecond
        m, s = divmod(timeInSeconds, 60)
        h, m = divmod(m, 60)
        self.rulerLabel.setText('{:.0f} yd\n{:.0f}:{:.0f}:{:.0f}'.format(distance, h, m, s))

    def startProgressUpdateThread(self):
        """
        Starts drawing and updating the progress bar to show that something is happening.
        """
        if not self.progressUpdateThreadRunning:
            self.progressUpdateThread.tickSignal.connect(self.updateProgress)
            self.progressUpdateThread.start()
            self.progressUpdateThreadRunning = True

    def stopProgressUpdateThread(self):
        """ Stops the progress bar when lengthy computations are complete. """
        if self.progressUpdateThreadRunning:
            self.progressUpdateThread.terminate()
            self.statusValueLabel.setText('')
            self.progressUpdateThreadRunning = False

    def updateProgress(self):
        """ Adds at 'tick' to the progress bar every half second. """
        self.progress += '|'
        if self.progress == '|||||||||||':
            self.progress = ''
        self.statusValueLabel.setText(self.progress)

    def changeIconSize(self, size):
        """
        Change the size of the SVG MIL-STD icon part of a contact.
        """
        self.map.setIconSize(size)

    def zoomOwnship(self):
        """ Move to centre of ownShip and zoom in. """
        self.map.zoomOwnship()

    def updateLocationLabel(self, mouseLat, mouseLon, bearing, distance):
        """
        Label at the top right of the COP shows lat/lon x/y etc. of the cursor.
        """
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

        self.latLonLabel.setText('{}, {}'.format(xText, yText))
        self.bearingLabel.setText(bearingText)
        self.distanceLabel.setText(distanceText)

    def showHideToolBox(self):
        """ Show/hide menu. """
        if self.toolbox.isVisible():
            self.toolbox.hide()
            self.toolbox.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            self.layersButton.setText('Menu')
            self.map.currentlyDrawing = False
            self.toolbox.tabBox.disableAnnotationLayers()
        else:
            self.toolbox.updateEntries()
            self.toolbox.show()
            self.layersButton.setText('Close')
            self.toolbox.setAttribute(Qt.WA_TransparentForMouseEvents, False)
            self.toolbox.tabBox.setCurrentIndex(0)  # always start with the layers tab.

    def doUpdate(self):
        """ Don't want to start creating the COP until we have ownShip. """
        if self.map is None:
            self.initUi()

        self.map.update()


class ProgressWorker(QThread):
    """ Thread to update the progress bar. """
    tickSignal = Signal()

    def __init__(self):
        QThread.__init__(self)

    @Slot()
    def run(self):
        while True:
            self.tickSignal.emit()
            time.sleep(0.5)
