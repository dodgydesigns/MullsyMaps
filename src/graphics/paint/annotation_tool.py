import os

from PySide2.QtCore import QSize, Qt, Signal, QTimer, QEvent
from PySide2.QtGui import QIcon, QPixmap, QPen, QColor, QFont, QPainter, QBrush, \
    QMouseEvent
from PySide2.QtWidgets import QWidget, QGridLayout, QPushButton, QSizePolicy, QComboBox, \
    QLabel, QMainWindow, QSlider, QButtonGroup, QColorDialog

import preferences


BRUSHMULT = 3

FONTSIZES = [7, 10, 13, 18, 36, 64, 96]

MODES = [
    'eraser', 
    'stamp', 
    'text',
    'pen', 
    'brush', 
    'polyline', 
    'polygon',
]

PREVIEWPEN = QPen(QColor(0xff, 0xff, 0xff), 2, Qt.SolidLine)

def buildFont(preferences):
    """
    Construct a complete font from the configuration options
    :param self:
    :param preferences:
    :return: QFont
    """
    font = preferences['font']
    font.setPointSize(preferences['fontsize'])
    font.setBold(preferences['bold'])
    font.setItalic(preferences['italic'])
    font.setUnderline(preferences['underline'])
    return font

class AnnotationTools(QWidget):
    ''' All the buttons for the annotation tool box. '''
    def __init__(self, tabBox, canvas):
        super(AnnotationTools, self).__init__()
        self.tabBox = tabBox
        self.canvas = canvas
        
    def buttonClicked(self, button):
        ''' Just to highlight the current button and make things look pretty. '''
        button.setStyleSheet('''QPushButton {background: white;}
                            ''')
        for b in self.modeButtonGroup.buttons():
            b.setStyleSheet('''QPushButton {background: white; font-size: 10px}''')
        button.setStyleSheet('''QPushButton {background: rgb(98, 211, 162); font-size: 10px}''')
        
    def createLayout(self):
        
        self.setStyleSheet('''QWidget {background: rgb(255, 255, 255); 
                                       color: rgb(0, 0, 0);}
                              QPushButton:pressed { background-color: rgb(98, 211, 162);}
                        ''')
        self.gridLayout = QGridLayout()
        
        self.iconPath = str(preferences.ICON_PATH) + os.sep

        self.modeButtonGroup = QButtonGroup(self)
        self.modeButtonGroup.setExclusive(True)
        self.modeButtonGroup.buttonClicked.connect(self.buttonClicked)
 
        self.newCanvasButton = QPushButton('New')
        self.newCanvasButton.setMinimumSize(QSize(80, 30))
        self.newCanvasButton.setMaximumSize(QSize(80, 30))
        self.newCanvasButton.clicked.connect(self.newCanvas)
        self.gridLayout.addWidget(self.newCanvasButton, 0, 0, 1, 2)
        
        self.stampButton = QPushButton(self)
        self.stampButton.setMinimumSize(QSize(30, 30))
        self.stampButton.setMaximumSize(QSize(30, 30))
        stampIcon = QIcon()
        stampIcon.addPixmap(QPixmap(self.iconPath+"stamp.png"), QIcon.Normal, QIcon.Off)
        self.stampButton.setIcon(stampIcon)
        self.stampButton.setCheckable(True)
        self.stampButton.setObjectName("stampButton")
        self.modeButtonGroup.addButton(self.stampButton, 1)
        self.gridLayout.addWidget(self.stampButton, 1, 0, 1, 1)
        
        self.stampnextButton = QPushButton(self)
        self.stampnextButton.setMinimumSize(QSize(30, 30))
        self.stampnextButton.setMaximumSize(QSize(30, 30))
        stampNextIcon = QIcon()
        stampNextIcon.addPixmap(QPixmap(self.iconPath+"/stamps/dock.svg"), QIcon.Normal, QIcon.Off)
        self.stampnextButton.setIcon(stampNextIcon)
        self.stampnextButton.setCheckable(True)
        self.stampnextButton.setObjectName("stampnextButton")
        self.modeButtonGroup.addButton(self.stampnextButton, 2)
        self.gridLayout.addWidget(self.stampnextButton, 1, 1, 1, 1)

        self.textButton = QPushButton(self)
        self.textButton.setMinimumSize(QSize(30, 30))
        self.textButton.setMaximumSize(QSize(30, 30))
        textIcon = QIcon()
        textIcon.addPixmap(QPixmap(self.iconPath+"edit.png"), QIcon.Normal, QIcon.Off)
        self.textButton.setIcon(textIcon)
        self.textButton.setCheckable(True)
        self.textButton.setObjectName("textButton")
        self.modeButtonGroup.addButton(self.textButton, 3)
        self.gridLayout.addWidget(self.textButton, 2, 0, 1, 1)
         
        self.fontsize = QComboBox()
        self.fontsize.addItems([str(s) for s in FONTSIZES])
        self.fontsize.setStyleSheet(''' QComboBox {background: transparent;
                                                font-size: 10px}''')
        self.fontsize.setFixedWidth(30)
        self.fontsize.setFixedHeight(30)        
        self.fontsize.view().setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.gridLayout.addWidget(self.fontsize, 2, 1, 1, 1)

        self.penButton = QPushButton(self)
        self.penButton.setMinimumSize(QSize(30, 30))
        self.penButton.setMaximumSize(QSize(30, 30))
        penIcon = QIcon()
        penIcon.addPixmap(QPixmap(self.iconPath+"pencil.png"), QIcon.Normal, QIcon.Off)
        self.penButton.setIcon(penIcon)
        self.penButton.setCheckable(True)
        self.penButton.setObjectName("penButton")
        self.modeButtonGroup.addButton(self.penButton, 4)
        self.gridLayout.addWidget(self.penButton, 3, 0, 1, 1)
         
        self.brushButton = QPushButton(self)
        self.brushButton.setMinimumSize(QSize(30, 30))
        self.brushButton.setMaximumSize(QSize(30, 30))
        brushIcon = QIcon()
        brushIcon.addPixmap(QPixmap(self.iconPath+"paint-brush.png"), QIcon.Normal, QIcon.Off)
        self.brushButton.setIcon(brushIcon)
        self.brushButton.setCheckable(True)
        self.brushButton.setObjectName("brushButton")
        self.modeButtonGroup.addButton(self.brushButton, 5)
        self.gridLayout.addWidget(self.brushButton, 3, 1, 1, 1)        
         
        self.polylineButton = QPushButton(self)
        self.polylineButton.setMinimumSize(QSize(30, 30))
        self.polylineButton.setMaximumSize(QSize(30, 30))
        polyLineIcon = QIcon()
        polyLineIcon.addPixmap(QPixmap(self.iconPath+"layer-shape-polyline.png"), QIcon.Normal, QIcon.Off)
        self.polylineButton.setIcon(polyLineIcon)
        self.polylineButton.setCheckable(True)
        self.polylineButton.setObjectName("polylineButton")
        self.modeButtonGroup.addButton(self.polylineButton, 6)
        self.gridLayout.addWidget(self.polylineButton, 4, 0, 1, 1)
         
        self.polygonButton = QPushButton(self)
        self.polygonButton.setMinimumSize(QSize(30, 30))
        self.polygonButton.setMaximumSize(QSize(30, 30))
        polygonIcon1 = QIcon()
        polygonIcon1.addPixmap(QPixmap(self.iconPath+"layer-shape-polygon.png"), QIcon.Normal, QIcon.Off)
        self.polygonButton.setIcon(polygonIcon1)
        self.polygonButton.setCheckable(True)
        self.polygonButton.setObjectName("polygonButton")
        self.modeButtonGroup.addButton(self.polygonButton, 7)
        self.gridLayout.addWidget(self.polygonButton, 4, 1, 1, 1)        

        self.eraserButton = QPushButton(self)
        self.eraserButton.setMinimumSize(QSize(30, 30))
        self.eraserButton.setMaximumSize(QSize(30, 30))
        eraserIcon = QIcon()
        eraserIcon.addPixmap(QPixmap(self.iconPath+"eraser.png"), QIcon.Normal, QIcon.Off)
        self.eraserButton.setIcon(eraserIcon)
        self.eraserButton.setCheckable(True)
        self.eraserButton.setObjectName("eraserButton")
        self.modeButtonGroup.addButton(self.eraserButton, 8)
        self.gridLayout.addWidget(self.eraserButton, 5, 0, 1, 1)
 
        self.eraserAllButton = QPushButton(self)
        self.eraserAllButton.setMinimumSize(QSize(30, 30))
        self.eraserAllButton.setMaximumSize(QSize(30, 30))
        eraserIcon = QIcon()
        eraserIcon.addPixmap(QPixmap(self.iconPath+"eraser.png"), QIcon.Normal, QIcon.Off)
        self.eraserAllButton.setText('Clear')
        
        self.eraserAllButton.setCheckable(True)
        self.eraserAllButton.setObjectName("eraserAllButton")
        self.gridLayout.addWidget(self.eraserAllButton, 5, 1, 1, 1)
        self.eraserAllButton.setStyleSheet(''' QPushButton {font-size: 10px}''')
        
        self.sizeselect = QSlider()
        self.sizeselect.setRange(1, 20)
        self.sizeselect.setOrientation(Qt.Horizontal)
        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        self.sizeselect.setSizePolicy(sizePolicy)
        self.sizeselect.setFixedHeight(20)
        self.gridLayout.addWidget(self.sizeselect, 6, 0, 1, 2)

        penSizeLabel = QLabel('Pen and Line Size')
        penSizeLabel.setStyleSheet(''' QLabel {background: transparent;
                                               font-size: 10px}''')
        penSizeLabel.setFixedHeight(15)
        self.gridLayout.addWidget(penSizeLabel, 7, 0, 1, 2)

        self.primaryButton = QPushButton(self)
        self.primaryButton.setMinimumSize(QSize(30, 30))
        self.primaryButton.setMaximumSize(QSize(30, 30))
        self.primaryButton.setObjectName("primaryButton")
        self.primaryButton.setStyleSheet('QPushButton { background-color: %s; margin: 5px; }' % 'black')
        self.gridLayout.addWidget(self.primaryButton, 8, 0, 1, 1)
 
        primaryLabel = QLabel('Fore')
        primaryLabel.setStyleSheet(''' QLabel {background: transparent;
                                               font-size: 10px}''')
        primaryLabel.setFixedHeight(15)
        self.gridLayout.addWidget(primaryLabel, 9, 0, 1, 2)

        self.secondaryButton = QPushButton(self)
        self.secondaryButton.setMinimumSize(QSize(30, 30))
        self.secondaryButton.setMaximumSize(QSize(30, 30))
        self.secondaryButton.setObjectName("secondaryButton")
        self.secondaryButton.setStyleSheet('QPushButton { background-color: %s; margin: 5px; }' % 'white')
        self.gridLayout.addWidget(self.secondaryButton, 8, 1, 1, 1)

        secondaryLabel = QLabel('Back')
        secondaryLabel.setStyleSheet(''' QLabel {background: transparent;
                                               font-size: 10px}''')
        secondaryLabel.setFixedHeight(15)
        self.gridLayout.addWidget(secondaryLabel, 9, 1, 1, 2)
        
        self.setLayout(self.gridLayout)
        self.setFixedWidth(500)
        
        for mode in MODES:
            btn = getattr(self, '%sButton' % mode)
            btn.pressed.connect(lambda mode=mode: self.setCanvasMode(mode))
            self.modeButtonGroup.addButton(btn)

        # Setup the color selection buttons.
        self.primaryButton.pressed.connect(lambda: self.chooseColour(self.setPrimaryColour))
        self.secondaryButton.pressed.connect(lambda: self.chooseColour(self.setSecondaryColour))
 
        # Initialize animation timer.
        self.timer = QTimer()
        self.timer.timeout.connect(self.canvas.onTimer)
        self.timer.setInterval(100)
        self.timer.start()
  
        stampDir = str(preferences.ICON_PATH) + '/stamps'
        self.stamps = [os.path.join(stampDir, f) for f in os.listdir(stampDir)]
         
        self.fontsize.currentTextChanged.connect(lambda f: self.canvas.setConfig('fontsize', int(f)))
        self.sizeselect.valueChanged.connect(lambda s: self.canvas.setConfig('size', s))
        
        # Setup the stamp state.
        self.currentStampNumber = -1
        self.nextStamp()
        self.stampnextButton.pressed.connect(self.nextStamp)
 
    def setCanvasMode(self, mode):
        self.canvas.setMode(mode)
        
    def chooseColour(self, callback):
        dlg = QColorDialog(self)
        if dlg.exec():
            callback(dlg.selectedColor().name())
 
    def setPrimaryColour(self, hx):
        self.canvas.setPrimaryColour(hx)
        self.primaryButton.setStyleSheet('QPushButton { background-color: %s; margin: 5px;}' % hx)
 
    def setSecondaryColour(self, hx):
        self.canvas.setSecondaryColour(hx)
        self.secondaryButton.setStyleSheet('QPushButton { background-color: %s; margin: 5px; }' % hx)        
        
    def nextStamp(self):
        self.currentStampNumber += 1
        if self.currentStampNumber >= len(self.stamps):
            self.currentStampNumber = 0

        pixmap = QPixmap(self.stamps[self.currentStampNumber])
        self.stampnextButton.setIcon(QIcon(pixmap))
        self.canvas.setCurrentStamp(pixmap)

    def newCanvas(self):
        self.tabBox.createNewAnnotationLayer()
        
class AnnotationCanvas(QLabel):
    ''' A QLabel with a QPixmap that holds all the drawing for a layer. '''

    primaryColourUpdated = Signal(str)
    secondaryColourUpdated = Signal(str)

    # Store configuration settings, including pen width, fonts etc.
    preferences = {
        # Drawing options.
        'size': 1,
        'fill': True,
        # Font options.
        'font': QFont('Times'),
        'fontsize': 12,
        'bold': False,
        'italic': False,
        'underline': False,
    }

    activeColour = None
    previewPen = None
    timerEvent = None
    currentStamp = None

    def __init__(self, view, toolsConfig):
        super(AnnotationCanvas, self).__init__()
        
        self.view = view
        controller = view.mapController
        self.toolsConfig = toolsConfig
        
        self.width = view.canvasWidth - 1
        self.height = view.canvasHeight - 70
        centre = controller.toGeographicalCoordinates(self.width/2, self.height/2)
        self.lat = centre.x()
        self.lon = centre.y()                
        
        self.initialZoom = self.view.vectorZoom
        self.scale = 1.0
        
        self.proxy = None
        
        self.visible = True
        self.setStyleSheet(""" QLabel { border: 1px solid yellow; background-color: transparent; }""")
        
        self.setPrimaryColour(self.toolsConfig.primaryColour.name())
        self.setSecondaryColour(self.toolsConfig.secondaryColour.name())
        self.setMode(self.toolsConfig.currentDrawingTool)
    
    def initialise(self):
        self.backgroundColour = QColor(255, 255, 255, 255)
        self.eraserColour = QColor(Qt.transparent)
        self.eraserColour.setAlpha(255)
        self.setMode(self.toolsConfig.currentDrawingTool)
        
    def reset(self):
        # Create the pixmap for display.
        self.pixMap = QPixmap(self.width, self.height)
        self.setPixmap(self.pixMap)

        # Clear the canvas.
        self.pixmap().fill(QColor(Qt.transparent))
        
    def setPrimaryColour(self, hx):
        self.toolsConfig.primaryColour = QColor(hx)

    def setSecondaryColour(self, hx):
        self.toolsConfig.secondaryColour = QColor(hx)

    def setConfig(self, key, value):
        self.config[key] = value

    def setMode(self, mode):

        # Clean up active timer animations.
        self.timerCleanup()
        # Reset mode-specific vars (all)
        self.activeShapeFn = None
        self.activeShapeArgs = ()

        self.originPos = None

        self.currentPos = None
        self.lastPos = None

        self.historyPos = None
        self.lastHistory = []

        self.currentText = ""
        self.lastText = ""

        self.lastConfig = {}

        self.dashOffset = 0
        self.locked = False
        # Apply the mode
        self.toolsConfig.currentDrawingTool = mode
        
    def disableAnnotations(self):
        ''' Stop drawing. '''
        self.setMode('')
        
    def resetMode(self):
        self.setMode(self.toolsConfig.currentDrawingTool)

    def onTimer(self):
        if self.timerEvent:
            self.timerEvent()

    def timerCleanup(self):
        if self.timerEvent:
            # Stop the timer, then trigger cleanup.
            timerEvent = self.timerEvent
            self.timerEvent = None
            timerEvent(final=True)
        
    def showHide(self, show):
        
        if show == 'show':
            self.proxy.show()
        else:
            self.proxy.hide()
            
    # Mouse events.
    def mousePressEvent(self, e):
        fn = getattr(self, "%sMousePressEvent" % self.toolsConfig.currentDrawingTool, None)
        if fn:
            return fn(e)

    def mouseMoveEvent(self, e):
        fn = getattr(self, "%sMouseMoveEvent" % self.toolsConfig.currentDrawingTool, None)
        if fn:
            return fn(e)

    def mouseReleaseEvent(self, e):
        fn = getattr(self, "%sMouseReleaseEvent" % self.toolsConfig.currentDrawingTool, None)
        if fn:
            return fn(e)

    def mouseDoubleClickEvent(self, e):
        fn = getattr(self, "%sMouseDoubleClickEvent" % self.toolsConfig.currentDrawingTool, None)
        if fn:
            return fn(e)

    # Generic events (shared by brush-like tools)
    def genericMousePressEvent(self, e):
        self.lastPos = e.pos()

        if e.button() == Qt.LeftButton:
            self.activeColour = self.toolsConfig.primaryColour
        else:
            self.activeColour = self.toolsConfig.secondaryColour

    def genericMouseReleaseEvent(self, e):
        self.lastPos = None

    # Mode-specific events.
    # Eraser events
    def eraserMousePressEvent(self, e):
        self.genericMousePressEvent(e)

    def eraserMouseMoveEvent(self, e):
        if self.lastPos and self.view.currentlyDrawing:

            p = QPainter(self.pixmap())
            p.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
            p.setCompositionMode(QPainter.CompositionMode_Clear)
            p.setPen(QPen(self.eraserColour, 30, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            p.drawLine(self.lastPos, e.pos())

            self.lastPos = e.pos()
            self.update()

    def eraserMouseReleaseEvent(self, e):
        self.genericMouseReleaseEvent(e)
        
    # Pen events
    def penMousePressEvent(self, e):
        self.genericMousePressEvent(e)

    def penMouseMoveEvent(self, e):
        if self.lastPos and self.view.currentlyDrawing:
            p = QPainter(self.pixmap())
            p.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
            p.setPen(QPen(self.activeColour, self.config['size'], Qt.SolidLine, Qt.SquareCap, Qt.RoundJoin))
            p.drawLine(self.lastPos, e.pos())

            self.lastPos = e.pos()
            self.update()

    def penMouseReleaseEvent(self, e):
        self.genericMouseReleaseEvent(e)

    # Brush events
    def brushMousePressEvent(self, e):
        self.genericMousePressEvent(e)

    def brushMouseMoveEvent(self, e):

        if self.lastPos and self.view.currentlyDrawing:
            p = QPainter(self.pixmap())
            p.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
            p.setPen(QPen(self.activeColour, self.config['size'] * BRUSHMULT, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            p.drawLine(self.lastPos, e.pos())

            self.lastPos = e.pos()
            self.update()

    def brushMouseReleaseEvent(self, e):
        self.genericMouseReleaseEvent(e)

    # Text events
    def keyPressEvent(self, e):

        if self.toolsConfig.currentDrawingTool == 'text':
            if e.key() == Qt.Key_Backspace:
                self.currentText = self.currentText[:-1]
            elif e.key() == Qt.Key_Enter or e.key() == Qt.Key_Return:
                self.textMousePressEvent(QMouseEvent(QEvent.MouseButtonPress,
                                                     self.currentPos, 
                                                     Qt.LeftButton, 
                                                     Qt.LeftButton, 
                                                     Qt.NoModifier))
            else:
                self.currentText = self.currentText + e.text()

    def textMousePressEvent(self, e):

        if e.button() == Qt.LeftButton and self.currentPos is None:
            self.currentPos = e.pos()
            self.currentText = ''
            self.timerEvent = self.textTimerEvent

        elif e.button() == Qt.LeftButton:
            self.timerCleanup()
            # Draw the text to the image
            p = QPainter(self.pixmap())
            p.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
            font = buildFont(self.config)
            p.setFont(font)
            pen = QPen(self.toolsConfig.primaryColour, 1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            p.setPen(pen)
            p.drawText(self.currentPos, self.currentText)
            self.update()

            self.resetMode()

        elif e.button() == Qt.RightButton and self.currentPos:
            self.resetMode()

    def textTimerEvent(self, final=False):
        p = QPainter(self.pixmap())
        pen = PREVIEWPEN
        p.setPen(pen)
        if self.lastText:
            font = buildFont(self.lastConfig)
            p.setFont(font)
            p.drawText(self.currentPos, self.lastText)

        if not final:
            font = buildFont(self.config)
            p.setFont(font)
            p.drawText(self.currentPos, self.currentText)

        self.lastText = self.currentText
        self.lastConfig = self.config.copy()
        self.update()

    # Line events
    def lineMousePressEvent(self, e):
        self.originPos = e.pos()
        self.currentPos = e.pos()
        self.previewPen = PREVIEWPEN
        self.timerEvent = self.lineTimerEvent

    def lineTimerEvent(self, final=False):
        p = QPainter(self.pixmap())
        p.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        p.setCompositionMode(QPainter.RasterOp_SourceXorDestination)
        pen = self.previewPen
        p.setPen(pen)
        if self.lastPos:
            p.drawLine(self.originPos, self.lastPos)

        if not final:
            p.drawLine(self.originPos, self.currentPos)

        self.update()
        self.lastPos = self.currentPos

    def lineMouseMoveEvent(self, e):
        self.currentPos = e.pos()

    def lineMouseReleaseEvent(self, e):
        if self.lastPos:
            # Clear up indicator.
            self.timerCleanup()

            p = QPainter(self.pixmap())
            p.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
            p.setPen(QPen(self.toolsConfig.primaryColour, self.config['size'], Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))

            p.drawLine(self.originPos, e.pos())
            self.update()

        self.resetMode()

    # Generic polygon events
    def genericPolyMousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            if self.historyPos:
                self.historyPos.append(e.pos())
            else:
                self.historyPos = [e.pos()]
                self.currentPos = e.pos()
                self.timerEvent = self.genericPolyTimerEvent

        elif e.button() == Qt.RightButton and self.historyPos:
            # Clean up, we're not drawing
            self.timerCleanup()
            self.resetMode()

    def genericPolyTimerEvent(self, final=False):
        p = QPainter(self.pixmap())
        p.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        p.setCompositionMode(QPainter.RasterOp_SourceXorDestination)
        pen = self.previewPen
        pen.setDashOffset(self.dashOffset)
        p.setPen(pen)
        if self.lastHistory:
            getattr(p, self.activeShapeFn)(self.lastHistory)

        if not final:
            self.dashOffset -= 1
            pen.setDashOffset(self.dashOffset)
            p.setPen(pen)
            t = self.historyPos + [self.currentPos]
            getattr(p, self.activeShapeFn)(t)
 
        self.update()
        self.lastPos = self.currentPos
        self.lastHistory = self.historyPos + [self.currentPos]

    def genericPolyMouseMoveEvent(self, e):
        self.currentPos = e.pos()

    def genericPolyMouseDoubleClickEvent(self, e):
        self.timerCleanup()
        p = QPainter(self.pixmap())
        p.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        p.setPen(QPen(self.toolsConfig.primaryColour, self.config['size'], Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))

        # Note the brush is ignored for polylines.
        if self.toolsConfig.secondaryColour:
            p.setBrush(QBrush(self.toolsConfig.secondaryColour))

        getattr(p, self.activeShapeFn)(self.historyPos + [e.pos()])
        self.update()
        self.resetMode()

    # Polyline events
    def polylineMousePressEvent(self, e):
        self.activeShapeFn = 'drawPolyline'
        self.previewPen = PREVIEWPEN
        self.genericPolyMousePressEvent(e)

    def polylineTimerEvent(self, final=False):
        self.genericPolyTimerEvent(final)

    def polylineMouseMoveEvent(self, e):
        self.genericPolyMouseMoveEvent(e)

    def polylineMouseDoubleClickEvent(self, e):
        self.genericPolyMouseDoubleClickEvent(e)

    # Polygon events
    def polygonMousePressEvent(self, e):
        self.activeShapeFn = 'drawPolygon'
        self.previewPen = PREVIEWPEN
        self.genericPolyMousePressEvent(e)

    def polygonTimerEvent(self, final=False):
        self.genericPolyTimerEvent(final)

    def polygonMouseMoveEvent(self, e):
        self.genericPolyMouseMoveEvent(e)

    def polygonMouseDoubleClickEvent(self, e):
        self.genericPolyMouseDoubleClickEvent(e)

    # Stamp events
    def stampMousePressEvent(self, e):
        p = QPainter(self.pixmap())
        stamp = self.currentStamp if self.currentStamp else 'dock'
        stamp = stamp.scaledToWidth(32) #TODO: put in preferences
        p.drawPixmap(e.x() - stamp.width() // 2, e.y() - stamp.height() // 2, stamp)
        self.update()     

    def setCurrentStamp(self, stamp):
        print(stamp)
        self.currentStamp = stamp
        
class PaintToolBox(QMainWindow):
    '''  '''
    def __init__(self, tabBox, canvas):
        super(PaintToolBox, self).__init__()
        self.canvas = canvas
 
        self.paintTool = AnnotationTools(tabBox, self.canvas)
        self.paintTool.createLayout() 
        self.setCentralWidget(self.paintTool)
