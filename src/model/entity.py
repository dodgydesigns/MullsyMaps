import datetime
from math import sin, radians, cos

from PySide2.QtCore import QPoint, QLineF, Qt, QPointF
from PySide2.QtGui import QPen, QFont, QColor, QTransform
from PySide2.QtWidgets import QLabel

from Views.COPView.src.model.UIObject import UIObject
from Views.COPView.src.model.layers import GraphicsLayer, BreadcrumbLayer
import enums


class Entity(UIObject):
    '''move
    This represents a solution that has been entered by users on Sonar and refined by Track Motion Analysis/Optix and Track Manager.
    '''
    def __init__(self, view, designation, affiliation, x, y, speed, course, rnge, bearing, classification, certainty):
        '''
        Constructor
        '''
        super().__init__(view, designation, affiliation, classification, x, y, speed, course)
        
        self.bearingRateTimer = 0
        
        self.view = view
        self.designation = designation
        self.classification = classification
        self.range = rnge
        self.bearing = bearing
        self.certainty = certainty

        # stuff to calculate bearing rate
        self.lastBearingTime = datetime.datetime.now()
        self.lastBearing = bearing
        self.bearingRate = '0'
        self.bearingTimer = 0
        
        self.iconScale = enums.ICON_SCALE
        
        self.graphicsLayers = {}
        self.graphicsLayers[enums.ICON] = GraphicsLayer(view, True)
        self.graphicsLayers[enums.ICON].name = self.designation
        self.graphicsLayers[enums.ANNOTATIONS] = GraphicsLayer(view, True)
        self.graphicsLayers[enums.HISTORICAL_COURSE] = BreadcrumbLayer(view, self, True)
        self.graphicsLayers[enums.PREDICTED_COURSE] = GraphicsLayer(view, True)
        self.graphicsLayers[enums.CERTAINTY_CIRCLE] = GraphicsLayer(view, True)
        
        self.deadCrumbs = []
        self.draw()
    
        # stuff to calculate bearing rate
        self.lastBearingTime = datetime.datetime.now()
        self.lastBearing = bearing
        self.bearingRate = '0'
        
    def __str__(self):
        
        return '{} {} {}\nSPDE:{} CRSE{} RNGE{} BRNG{}\n{}, {}\n{}, {}'.format(self.designation,
                                                             self.classification,
                                                             self.affiliation,
                                                             self.speed,
                                                             self.course,
                                                             self.range,
                                                             self.bearing,
                                                             self.x,
                                                             self.y,
                                                             self.lat,
                                                             self.lon)

    def draw(self):
        '''
        Initial creation of entity graphics. Handled by update() after this.
        '''
        self.calculateIconCentres()

        halfWidth = self.icon.boundingRect().width()/2
        halfHeight = self.icon.boundingRect().height()/2
        lineX = self.iconCenterX+(halfWidth*self.iconScale)
        lineY = self.iconCenterY+(halfHeight*self.iconScale)
        
        self.icon.setScale(self.iconScale)        
        self.icon.setPos(QPointF(self.iconCenterX, self.iconCenterY))
        self.icon.setZValue(enums.ZVALUE_Icons)
        self.view.scene.addItem(self.icon)
        self.graphicsLayers[enums.ICON].addGraphicsObject(self.icon)

        certainty = 1 - self.certainty * enums.CERTAINTY_CIRCLE_SCALE
        if certainty >= 0:
            certaintyCircle = self.view.scene.addEllipse(0, 0, certainty, certainty)
            certaintyCircle.setRect(self.certaintyCircleCircleX, 
                                    self.certaintyCircleCircleY, 
                                    certainty, 
                                    certainty)
            pen = QPen(Qt.yellow, enums.CIRCLE_PEN)
            pen.setStyle(Qt.SolidLine)
            certaintyCircle.setPen(pen)
            certaintyCircle.setZValue(enums.ZVALUE_Icons)
            self.graphicsLayers[enums.CERTAINTY_CIRCLE].addGraphicsObject(certaintyCircle)
            
        designationText = self.view.scene.addText(self.designation)
        designationText.setFont(QFont('Arial', 10))
        designationText.setDefaultTextColor(QColor('white'))
        designationText.setZValue(enums.ZVALUE_Icons)
        designationText.setPos(QPointF(self.x, self.y))
        self.graphicsLayers[enums.ANNOTATIONS].addGraphicsObject(designationText)

        t = QTransform()
        t.rotate(self.course)
        x, y = self.correctOrientation(self.course, lineX-self.icon.pos().x(), lineY-self.icon.pos().y())
        t.translate(x, y)
        self.icon.setTransform(t)

        courseLine = self.view.scene.addLine(QLineF(lineX,
                                                    lineY, 
                                                    (lineX + sin(radians(self.course)) * self.speed * enums.PREDICTED_COURSE_SCALE),
                                                    (lineY - cos(radians(self.course)) * self.speed * enums.PREDICTED_COURSE_SCALE)))
        courseLine.setPen(QPen(QColor('white'), enums.CIRCLE_PEN))
        courseLine.setZValue(enums.ZVALUE_Icons)
        self.graphicsLayers[enums.PREDICTED_COURSE].addGraphicsObject(courseLine)

    def calculateIconCentres(self):
        '''
        Qt uses the top left corner of the bounding box of graphics to position them. This works out where
        the centre is so graphics are positioned on the centre.
        '''
        self.iconCenterX = self.x - (self.icon.boundingRect().center().x() * self.iconScale)        
        self.iconCenterY = self.y - (self.icon.boundingRect().center().y() * self.iconScale)
        self.certaintyCircleCircleX = self.iconCenterX - (1 - int(self.certainty) * enums.CERTAINTY_CIRCLE_SCALE)
        self.certaintyCircleCircleY = self.iconCenterY - (1 - int(self.certainty) * enums.CERTAINTY_CIRCLE_SCALE)

    def calculateBearingRate(self):
        ''' 
        Update bearing rate based on elapsed time since last measurement and change in bearing. 
        '''
        currentTime = datetime.datetime.now()
        deltaTimeMin = (currentTime - self.lastBearingTime).microseconds / 1000000
        self.bearingTimer += deltaTimeMin
        self.lastBearingTime = currentTime
        
        if self.bearingTimer >= 6:
            relativeBearing = self.view.ownship.course - self.bearing
            deltaBearing = self.lastBearing - relativeBearing
            bearingRate = ((deltaBearing*self.bearingTimer) / 6) * 10
            self.lastBearing = relativeBearing
            self.bearingTimer = 0

            if bearingRate > 0:
                if 0 < bearingRate <= 90:
                    self.bearingRate = '{:.1f}R'.format(bearingRate)
                elif 90 < bearingRate <= 180:
                    self.bearingRate = '{:.1f}L'.format(bearingRate) 
                elif 180 < bearingRate <= 270:
                    self.bearingRate = '{:.1f}L'.format(bearingRate)
                elif 270 < bearingRate <= 360:
                    self.bearingRate = '{:.1f}R'.format(bearingRate)     
            else:
                br = abs(bearingRate)
                if 0 < br <= 90:
                    self.bearingRate = '{:.1f}L'.format(br)
                elif 90 < bearingRate <= 180:
                    self.bearingRate = '{:.1f}R'.format(br)
                elif 180 < bearingRate <= 270:
                    self.bearingRate = '{:.1f}R'.format(br)
                elif 270 < bearingRate <= 360:
                    self.bearingRate = '{:.1f}L'.format(br)
        
    def update(self, affiliation, x, y, speed, course, rnge, bearing, classification, certainty):

        self.x = x
        self.y = y
        self.lat = self.view.mapController.toGeographicalCoordinates(self.x, self.y).x()
        self.lon = self.view.mapController.toGeographicalCoordinates(self.x, self.y).y()
        self.speed = speed
        self.course = course
        self.range = rnge
        self.bearing = bearing
        self.affiliation = affiliation
        self.classification = classification
        
        halfWidth = self.icon.boundingRect().width()/2
        halfHeight = self.icon.boundingRect().height()/2
        lineX = self.iconCenterX+(halfWidth*self.iconScale)
        lineY = self.iconCenterY+(halfHeight*self.iconScale)

        # update bearing rate
        self.calculateBearingRate()
        
        # Update historical course lines
        currentLine = self.graphicsLayers[enums.HISTORICAL_COURSE].graphicObjects[-1]
        if self.course != self.previousCourse:
            self.graphicsLayers[enums.HISTORICAL_COURSE].endLine(QPointF(self.lat, self.lon))
            self.graphicsLayers[enums.HISTORICAL_COURSE].startLine(QPointF(self.lat, self.lon))
            self.previousCourse = self.course
        else:
            currentLine.endLatLon = QPointF(self.lat, self.lon) 
               
        self.graphicsLayers[enums.HISTORICAL_COURSE].updateLines()

        # update icon orientation
        t = QTransform()
        t.rotate(self.course)
        x, y = self.correctOrientation(self.course, lineX-self.icon.pos().x(), lineY-self.icon.pos().y())
        t.translate(x, y)
        self.icon.setTransform(t)
        
        self.zoom() 
        self.calculateIconCentres()
        self.icon.setPos(QPointF(self.iconCenterX, self.iconCenterY)) 
                
        # update certainty circles
        certainty = (1 - self.certainty) * enums.CERTAINTY_CIRCLE_SCALE
        for certaintyCircle in self.graphicsLayers[enums.CERTAINTY_CIRCLE].graphicObjects:
            certaintyCircle.setRect(self.certaintyCircleCircleX, self.certaintyCircleCircleY, certainty, certainty) 
 
        if self.view.vectorZoom < 1:
            for annotation in self.graphicsLayers[enums.ANNOTATIONS].graphicObjects:
                annotation.setPos(self.x, self.y)
        else:
            for annotation in self.graphicsLayers[enums.ANNOTATIONS].graphicObjects:
                annotation.setPos(self.x + (self.iconScale * 20), self.y + (self.iconScale * 50))

        for courseLine in self.graphicsLayers[enums.PREDICTED_COURSE].graphicObjects:
            courseLine.setLine(lineX,
                               lineY, 
                               (lineX + sin(radians(self.course)) * self.speed * enums.PREDICTED_COURSE_SCALE),
                               (lineY - cos(radians(self.course)) * self.speed * enums.PREDICTED_COURSE_SCALE))
            
        # update visibility
        for layer in self.graphicsLayers.values():
            if layer.visible:
                layer.showHide('show')
            else: 
                layer.showHide('hide')
                    
    def correctOrientation(self, angle, tlx=-1, tly=1):
        ''' Correct the angle of rotation for the icon. '''
        rangle = radians(angle)
        x = (cos(rangle) * tlx + sin(rangle) * tly) - tlx
        y = (-sin(rangle) * tlx + cos(rangle) * tly) - tly
    
        return x, y 
    
    def showHideAllLayers(self):        
        '''
        Used to show/hide the entity icon and all graphicsLayers.
        '''
        if self.visible:
            self.showHide('All Layers', 'hide')
        else:
            self.showHide('All Layers', 'show')
                
    def showHide(self, layerName, showHide): 
        '''
        Used to show/hide the entity icon and graphicsLayers separately.
        '''
        if layerName == 'All Layers':
            for layer in self.graphicsLayers.values():
                if showHide == 'show':
                    layer.showHide('show')
                    layer.visible = True
                else:
                    layer.showHide('hide')
                    layer.visible = False
        else:
            if showHide == 'show':
                self.graphicsLayers[layerName].visible = True
                self.graphicsLayers[layerName].showHide('show')
            else:
                self.graphicsLayers[layerName].visible = False
                self.graphicsLayers[layerName].showHide('hide')
               
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
            text = """<html>
                        <br>
                        <hr>
                        <table'>
                            <tr><td>Bearing:</td><td>{:.0f}°</td></tr>
                            <tr><td>Range:</td><td>{:.0f}Yds</td></tr>
                            <tr><td>Course:</td><td>{:.0f}°</td></tr>
                            <tr><td>Speed:</td><td>{:.1f}Kts</td></tr>
                            <tr><td>Bearing Rate:</td><td>{}</td></tr>
                            <tr><td>Location:</td><td>{}</td></tr>
                        </table>
                      </html>""".format(self.bearing,
                                        self.range,
                                        self.course,
                                        self.speed,
                                        self.bearingRate,
                                        self.locationLabel())
            self.metaDialog = QLabel(text)
            self.metaDialog.move(QPoint(self.x, self.y))
            self.metaDialog.setStyleSheet("""QLabel {color: rgb(255,255,255);
                                                     background-color: rgba(0,0,0,40);
                                                     padding: 5px;
                                                     border: 1px solid white;}
                                            table {  border-spacing: 10px 10px 10px 10px;}
                                        """)     
            self.metaDialogProxy = self.view.scene.addWidget(self.metaDialog)
            self.metaDialogProxy.setZValue(enums.ZVALUE_MetaDialogs)
            self.metaDialogProxy.setScale(enums.METADIALOGSCALE)
        else:
            self.metaDialogProxy.hide()