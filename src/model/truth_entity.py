from math import sin, radians, cos, sqrt

from PySide2.QtCore import QPoint, QLineF, Qt, QPointF
from PySide2.QtGui import QPen, QFont, QColor, QBrush
from PySide2.QtWidgets import QLabel, QGraphicsEllipseItem

from Views.COPView.src.model.UIObject import UIObject
from Views.COPView.src.model.layers import GraphicsLayer
import enums

class TruthEntity(UIObject):
    '''
    This is a form of an entity that is only used for OSConsole to denote ground truth of the entities in 
    the scenario.
    '''
    def __init__(self, view, designation, x, y, speed, course, rnge, bearing, classification):
        UIObject.__init__(self, view, designation, None, classification, x, y, speed, course)
        
        self.view = view
        self.classification = classification
        self.range = rnge
        self.bearing = bearing
        self.iconScale = enums.ICON_SCALE
        
        self.graphicsLayers = {}
        self.graphicsLayers[enums.ICON] = GraphicsLayer(view, True)
        self.graphicsLayers[enums.ANNOTATIONS] = GraphicsLayer(view, True)
        self.previousLocations = []
        self.graphicsLayers[enums.HISTORICAL_COURSE] = GraphicsLayer(view, True)
        self.graphicsLayers[enums.PREDICTED_COURSE] = GraphicsLayer(view, True)
        
        self.drawSpiroPolygons()
        
    def drawSpiroPolygons(self):
        '''
        Initial creation of entity graphics. Handled by update() after this.
        '''
        self.calculateIconCentres()

        self.icon = QGraphicsEllipseItem(0, 0, 100, 100)
        self.icon.setPen(QPen(Qt.white, 1))
        self.icon.setBrush(QBrush(Qt.black))
        self.icon.setScale(self.iconScale)        
        self.icon.setPos(QPointF(self.x, self.y))
        self.icon.setZValue(enums.ZVALUE_Icons)
        self.view.scene.addItem(self.icon)
        self.graphicsLayers[enums.ICON].addGraphicsObject(self.icon)

        designationText = self.view.scene.addText(str(self.designation))
        designationText.setFont(QFont('Arial', 10))
        designationText.setDefaultTextColor(QColor('white'))
        designationText.setZValue(enums.ZVALUE_Icons)
        designationText.setPos(QPointF(self.x+5, self.y-5))
        self.graphicsLayers[enums.ANNOTATIONS].addGraphicsObject(designationText)
        self.graphicsLayers[enums.ICON].addGraphicsObject(designationText)
        
        halfWidth = self.icon.boundingRect().width()/2
        halfHeight = self.icon.boundingRect().height()/2
        lineX = self.iconCenterX+(halfWidth*self.iconScale)
        lineY = self.iconCenterY+(halfHeight*self.iconScale)
        courseLine = self.view.scene.addLine(QLineF(lineX,
                                                    lineY, 
                                                    (lineX + sin(radians(self.course)) * self.speed * enums.PREDICTED_COURSE_SCALE),
                                                    (lineY - cos(radians(self.course)) * self.speed * enums.PREDICTED_COURSE_SCALE)))
        courseLine.setPen(QPen(QColor('white'), enums.CIRCLE_PEN))
        courseLine.setZValue(enums.ZVALUE_Icons-1)
        self.graphicsLayers[enums.PREDICTED_COURSE].addGraphicsObject(courseLine)

    def calculateIconCentres(self):
        '''
        Qt uses the top left corner of the bounding box of graphics to position them. This works out where
        the centre is so graphics are positioned on the centre.
        '''
        self.iconCenterX = self.x - (self.icon.boundingRect().center().x() * self.iconScale)        
        self.iconCenterY = self.y - (self.icon.boundingRect().center().y() * self.iconScale)

    def update(self, x, y, speed, course):

        halfWidth = self.icon.boundingRect().width()/2
        halfHeight = self.icon.boundingRect().height()/2
        lineX = self.iconCenterX + (halfWidth*self.iconScale)
        lineY = self.iconCenterY + (halfHeight*self.iconScale)
         
        self.graphicsLayers[enums.HISTORICAL_COURSE].removeAllGraphicsObjects()
        
        # add bread crumbs to show previous locations if entity has moved sufficiently.
        if (sqrt((self.x - x)**2 + (self.y - y)**2)) > 2:
            ll = self.view.mapController.toGeographicalCoordinates(lineX, lineY)
            point = (ll.x(), ll.y())
            self.previousLocations.append(point)

            self.lat = self.view.mapController.toGeographicalCoordinates(x, y).x()
            self.lon = self.view.mapController.toGeographicalCoordinates(x, y).y()
            self.x = x
            self.y = y
            self.speed = speed
            self.course = course
                
        self.zoom()  
        self.calculateIconCentres()
        self.icon.setPos(QPointF(self.iconCenterX, self.iconCenterY))   
        
        for annotation in self.graphicsLayers[enums.ANNOTATIONS].graphicObjects:
            annotation.setPos(self.iconCenterX+3, self.iconCenterY-2)

        for courseLine in self.graphicsLayers[enums.PREDICTED_COURSE].graphicObjects:
            courseLine.setLine(lineX,
                               lineY, 
                               (lineX + sin(radians(self.course)) * self.speed * enums.PREDICTED_COURSE_SCALE),
                               (lineY - cos(radians(self.course)) * self.speed * enums.PREDICTED_COURSE_SCALE))
    
    def showHideLayer(self, layerName, showHide):        
        '''
        Used to show/hide the entity icon and graphicsLayers separately.
        '''
        if showHide == 'show':
            self.graphicsLayers[layerName].show()
        if showHide == 'hide':
            self.graphicsLayers[layerName].hide()
            
    def showHideAllLayers(self):        
        '''
        Used to show/hide the entity icon and all graphicsLayers.
        '''
        for key, grapicLayer in self.graphicsLayers.items():
            if self.visible:
                grapicLayer.showHide('hide')
                self.visible = False
            else:
                grapicLayer.showHide('show')
                self.visible = True

    def hideAllLayers(self):        
        '''
        Used to show/hide the entity icon and all graphicsLayers.
        '''
        for grapicLayer in self.graphicsLayers.values():
            grapicLayer.showHide('hide')
            self.visible = False
               
    def zoom(self):
        '''
        Scale the entity icon using Qt. All graphicsLayers scale automatically but hide/show graphicsLayers at certain zoom levels.
        '''
        if self.view.vectorZoom < 8:
            for name, layer in self.graphicsLayers.items():
                if name != enums.ICON:
                    if not layer.visible:
                        layer.showHide('hide')
        else:
            for name, layer in self.graphicsLayers.items():
                if name != enums.ICON:
                    if layer.visible:
                        layer.showHide('show')  
    
    def showHideMetaDialog(self, showMetaDialog):
        '''
        Shows a dialog with information about this object when it is clicked.
        '''
        self.vectorZoom = self.view.vectorZoom
        
        if showMetaDialog:
            self.metadata = '\n'
            self.metadata += 'Bearing: {:.2f}°\nRange: {:.2f}Yds\nCourse: {:.2f}°\nSpeed: {:.2f}Kt\nLocation: {}\n'.format(self.bearing,
                                                                                                                             self.range,
                                                                                                                             self.course,
                                                                                                                             self.speed,
                                                                                                                             self.locationLabel())
            
            text = self.metadata.rstrip('\n')
            
            self.metaDialog = QLabel(text)
            self.metaDialog.move(QPoint(self.x, self.y))
            self.metaDialog.setStyleSheet("""QLabel {color: rgb(255,255,255);
                                                     background-color: rgba(0,0,0,50);
                                                     padding: 5px;
                                                     border: 1px solid white;}
                                        """)     
            self.metaDialogProxy = self.view.scene.addWidget(self.metaDialog)
            self.metaDialogProxy.setZValue(enums.ZVALUE_MetaDialogs) 
            self.metaDialogProxy.setScale(enums.METADIALOGSCALE)
        else:
            self.metaDialogProxy.hide()
            
    def hideMetaDialog(self):       
        '''
        Hide the meta-data dialog when some other object is clicked.
        '''
        pass 
