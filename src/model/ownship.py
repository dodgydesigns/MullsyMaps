"""
Created on 30 Aug. 2018

@author: mullsy
"""
from math import sin, radians, cos, atan2, pi

from PySide2.QtCore import QLineF, Qt, QPointF, QPoint
from PySide2.QtGui import QPen, QColor
from PySide2.QtWidgets import QLabel

from model.UIObject import UIObject
from model.layers import GraphicsLayer
import preferences


class Ownship(UIObject):
    """
    Used to represent the entity the user is controlling.
    """
    def __init__(self, view, designation, affiliation, x, y, speed, course):
        """
        Constructor
        """
        UIObject.__init__(self, 
                          map
                          =view,
                          designation=designation, 
                          affiliation=affiliation, 
                          classification=preferences.OWNSHIP, 
                          x=x, 
                          y=y, 
                          speed=speed, 
                          course=speed)
        
        self.view = view
        self.iconScale = preferences.ICON_SCALE
        self.view.mapController.updateZoom()
        self.graphicsLayers = {preferences.ICON: GraphicsLayer(view, True),
                               preferences.ANNOTATIONS: GraphicsLayer(view, True),
                               preferences.HISTORICAL_COURSE: GraphicsLayer(view, True),
                               preferences.PREDICTED_COURSE: GraphicsLayer(view, True),
                               preferences.DISTANCE_MARKERS: GraphicsLayer(view, True)}

        self.drawSpiroPolygons()
        
    def drawSpiroPolygons(self):
        """
        Create all graphic elements including entity icon and all decorations.
        """
        self.calculateIconCentres()
        
        self.icon.setScale(self.iconScale)
        self.icon.setPos(QPointF(self.iconCenterX, self.iconCenterY))
        self.icon.setZValue(preferences.ZVALUE_Ownship)
        self.view.scene.addItem(self.icon)
        self.graphicsLayers[preferences.ICON].addGraphicsObject(self.icon)
        
        halfWidth = self.icon.boundingRect().width()/2
        halfHeight = self.icon.boundingRect().height()/2
        lineX = self.iconCenterX+(halfWidth*self.iconScale)
        lineY = self.iconCenterY+(halfHeight*self.iconScale)
        courseLine = self.view.scene.addLine(QLineF(lineX,
                                                    lineY, 
                                                    (lineX + sin(radians(self.course)) * self.speed * preferences.PREDICTED_COURSE_SCALE),
                                                    (lineY - cos(radians(self.course)) * self.speed * preferences.PREDICTED_COURSE_SCALE)))
        courseLine.setPen(QPen(QColor('gray'), preferences.CIRCLE_PEN))
        courseLine.setZValue(preferences.ZVALUE_Ownship)
        self.graphicsLayers[preferences.PREDICTED_COURSE].addGraphicsObject(courseLine)

        fivekydsLatLon = self.view.mapController.vincentyDirect(self.lat, self.lon, 0.0, 4572)  #4572m = 5kyds
        fivekydsInPixels = self.view.mapController.toCanvasCoordinates(fivekydsLatLon.x(), fivekydsLatLon.y()).y()
        halfWidth = self.icon.boundingRect().width()/2
        halfHeight = self.icon.boundingRect().height()/2
        lineX = self.iconCenterX+(halfWidth*self.iconScale)
        lineY = self.iconCenterY+(halfHeight*self.iconScale) 

        self.graphicsLayers[preferences.DISTANCE_MARKERS].addGraphicsObject(DistanceMarker(name='fiveKy', 
                                                                           proxy=self.view.scene.addEllipse(0, 0, preferences.FIVE_KY_RADIUS, preferences.FIVE_KY_RADIUS),
                                                                           circleCentreX=self.iconCenterX + preferences.FIVE_KY_RADIUS / 2,
                                                                           circleCentreY=self.iconCenterY - preferences.FIVE_KY_RADIUS / 2,
                                                                           radius=fivekydsInPixels * preferences.FIVE_KY_RADIUS,
                                                                           radiusMultiplier=preferences.FIVE_KY_RADIUS,
                                                                           pen=QPen(Qt.red, preferences.CIRCLE_PEN)))
                
        self.graphicsLayers[preferences.DISTANCE_MARKERS].addGraphicsObject(DistanceMarker(name='tenKy', 
                                                                           proxy=self.view.scene.addEllipse(0, 0, preferences.TEN_KY_RADIUS, preferences.TEN_KY_RADIUS),
                                                                           circleCentreX=self.iconCenterX - preferences.TEN_KY_RADIUS / 2, 
                                                                           circleCentreY=self.iconCenterY - preferences.FIVE_KY_RADIUS / 2,
                                                                           radius=fivekydsInPixels * preferences.TEN_KY_RADIUS,
                                                                           radiusMultiplier=preferences.TEN_KY_RADIUS,
                                                                           pen=QPen(Qt.gray, preferences.CIRCLE_PEN)))

        self.graphicsLayers[preferences.DISTANCE_MARKERS].addGraphicsObject(DistanceMarker(name='fifteenKy', 
                                                                           proxy=self.view.scene.addEllipse(0, 0, preferences.FIFTEEN_KY_RADIUS, preferences.FIFTEEN_KY_RADIUS),
                                                                           circleCentreX=self.iconCenterX - preferences.FIFTEEN_KY_RADIUS / 2, 
                                                                           circleCentreY=self.iconCenterY - preferences.FIVE_KY_RADIUS / 2,
                                                                           radius=fivekydsInPixels * preferences.FIFTEEN_KY_RADIUS,
                                                                           radiusMultiplier=preferences.FIFTEEN_KY_RADIUS,
                                                                           pen=QPen(Qt.gray, preferences.CIRCLE_PEN)))

        self.graphicsLayers[preferences.DISTANCE_MARKERS].addGraphicsObject(DistanceMarker(name='twentyKy', 
                                                                           proxy=self.view.scene.addEllipse(0, 0, preferences.TWENTY_KY_RADIUS, preferences.TWENTY_KY_RADIUS),
                                                                           circleCentreX=self.iconCenterX - preferences.TWENTY_KY_RADIUS / 2, 
                                                                           circleCentreY=self.iconCenterY - preferences.FIVE_KY_RADIUS / 2,
                                                                           radius=fivekydsInPixels * preferences.TWENTY_KY_RADIUS,
                                                                           radiusMultiplier=preferences.TWENTY_KY_RADIUS,
                                                                           pen=QPen(Qt.gray, preferences.CIRCLE_PEN)))

        self.graphicsLayers[preferences.DISTANCE_MARKERS].addGraphicsObject(DistanceMarker(name='twentyFiveKy', 
                                                                           proxy=self.view.scene.addEllipse(0, 0, preferences.TWENTYFIVE_KY_RADIUS, preferences.TWENTYFIVE_KY_RADIUS),
                                                                           circleCentreX=self.iconCenterX - preferences.TWENTYFIVE_KY_RADIUS / 2, 
                                                                           circleCentreY=self.iconCenterY - preferences.FIVE_KY_RADIUS / 2,
                                                                           radius=fivekydsInPixels * preferences.TWENTYFIVE_KY_RADIUS,
                                                                           radiusMultiplier=preferences.TWENTYFIVE_KY_RADIUS,
                                                                           pen=QPen(Qt.green, preferences.CIRCLE_PEN)))
        
    def update(self, x, y, speed, course):
        """
        Move or update the entity icon and all graphicsLayers.
        """
        self.x = x
        self.y = y   
        self.speed = speed
        self.course = course  
            
        self.zoom()  
        self.calculateIconCentres()

        self.icon.setPos(QPointF(self.iconCenterX, self.iconCenterY))
        
        fivekydsLatLon = self.view.mapController.vincentyDirect(self.lat, self.lon, 0.0, 5468)  #4572m = 5kyds
        fivekydsInPixels = self.view.mapController.toCanvasCoordinates(fivekydsLatLon.x(), fivekydsLatLon.y()).y() - self.y

        halfWidth = self.icon.boundingRect().width()/2
        halfHeight = self.icon.boundingRect().height()/2
        lineX = self.iconCenterX+(halfWidth*self.iconScale)
        lineY = self.iconCenterY+(halfHeight*self.iconScale)        
        for distanceMarker in self.graphicsLayers[preferences.DISTANCE_MARKERS].graphicObjects:
            distanceMarker.radius = fivekydsInPixels * distanceMarker.radiusMultiplier * 2
            distanceMarker.circleCentreX = lineX - (distanceMarker.radius/2)
            distanceMarker.circleCentreY = lineY - (distanceMarker.radius/2)
            distanceMarker.move()

        bearing = atan2(self.y - y, self.x - x) - pi / 2
        halfWidth = self.icon.boundingRect().width()/2
        halfHeight = self.icon.boundingRect().height()/2
        lineX = self.iconCenterX+(halfWidth*self.iconScale)
        lineY = self.iconCenterY+(halfHeight*self.iconScale)
        for courseLine in self.graphicsLayers[preferences.PREDICTED_COURSE].graphicObjects:
            courseLine.setLine(lineX,
                               lineY, 
                               (lineX + sin(radians(bearing)) * self.speed * preferences.PREDICTED_COURSE_SCALE),
                               (lineY - cos(radians(bearing)) * self.speed * preferences.PREDICTED_COURSE_SCALE))

        for layer in self.graphicsLayers.values():
            if layer.visible:
                layer.showHide('show')
            else: 
                layer.showHide('hide')
                
    def showHide(self, layerName, showHide):
        """
        Used to show/hide the entity or entity icon and graphicsLayers separately.
        """
        if layerName == 'All Layers':
            for name, layer in self.graphicsLayers.items():
                if showHide == 'show':
                    layer.showHide('show')
                else:
                    if name != preferences.ICON:
                        layer.showHide('hide')
        else:
            if showHide == 'show':
                self.graphicsLayers[layerName].showHide('show')
            else:
                if layerName != preferences.ICON:
                    self.graphicsLayers[layerName].showHide('hide')

    def zoom(self):
        """
        Scale the entity icon using Qt. All graphicsLayers scale automatically but hide/show graphicsLayers at certain zoom levels.
        """
        if self.view.vectorZoom < 8:
            for name, layer in self.graphicsLayers.items():
                if name != preferences.ICON:
                    if not layer.visible:
                        layer.showHide('hide')
        else:
            for name, layer in self.graphicsLayers.items():
                if name != preferences.ICON:
                    if layer.visible:
                        layer.showHide('show')     
        
    def showHideMetaDialog(self, showMetaDialog):
        """
        Shows a dialog with information about this object when it is clicked.
        """
        self.vectorZoom = self.view.vectorZoom
        if showMetaDialog:
            text = """<html>
                        {}
                        <hr>
                        <table'>
                            <tr><td>Course:</td><td>{:.0f}°</td></tr>
                            <tr><td>Speed:</td><td>{:.1f}Kts</td></tr>
                            <tr><td>Location:</td><td>{}</td></tr>
                        </table>
                      </html>""".format('OWNSHIP', self.course, self.speed, self.locationLabel())
            
            self.metaDialog = QLabel(text)
            self.metaDialog.move(QPoint(self.x, self.y))
            self.metaDialog.setStyleSheet("""
                                             QLabel {color: rgb(255,255,255);
                                                     background-color: rgba(0,0,0,50);
                                                     padding: 5px;
                                                     border: 1px solid white;}
                                          """)     
            self.metaDialogProxy = self.view.scene.addWidget(self.metaDialog)
            self.metaDialogProxy.setZValue(preferences.ZVALUE_Ownship)
            self.metaDialogProxy.setScale(preferences.METADIALOGSCALE)
        else:
            self.metaDialogProxy.hide()
            
    #----------------------------------------------------------------------------------------------
    #        OBJECT SPECIFIC FUNCTIONS
    #----------------------------------------------------------------------------------------------
    def calculateIconCentres(self):
        """
        Qt uses the top left corner of the bounding box of graphics to position them. This works out where
        the centre is so graphics are positioned on the centre.
        """
        self.iconCenterX = self.x - (self.icon.boundingRect().center().x() * self.iconScale)        
        self.iconCenterY = self.y - (self.icon.boundingRect().center().y() * self.iconScale)

class DistanceMarker():
    """
    This holds all the details for a single circle that surrounds ownShip to denote various
    distances from the ship.
    """
    def __init__(self, name, proxy, circleCentreX, circleCentreY, radius, radiusMultiplier, pen):
    
        self.name = name
        self.proxy = proxy
        self.circleCentreX = circleCentreX
        self.circleCentreY = circleCentreY
        self.radius = radius
        self.radiusMultiplier = radiusMultiplier
        self.pen = pen
        
        self.pen.setStyle(Qt.DotLine)
        self.proxy.setPen(pen)
        self.proxy.setZValue(preferences.ZVALUE_Icons)    
       
    def move(self):
        self.proxy.setRect(self.circleCentreX, self.circleCentreY, self.radius, self.radius) 
       
    def show(self):
        self.proxy.show()
        
    def hide(self):
        self.proxy.hide()
