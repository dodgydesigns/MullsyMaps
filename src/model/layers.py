from PySide2.QtCore import QPointF, Qt
from PySide2.QtGui import QPen, QFont, QColor, QTransform
from PySide2.QtWidgets import QGraphicsLineItem
import pyproj

from gis.ncwms_tools import NCWMSTools
from graphics.paint.annotation_tool import AnnotationCanvas
from model.spirograph import Spirograph
import preferences


SONAR_RANGE_OF_THE_DAY = 25000  # yards


class PolygonLayer():
    """
    Used for map polygons in non-Geoserver mode.
    """
    def __init__(self, polygons, visible):
        self.polygons = polygons
        self.visible = visible
        self.zLevel = 398
        
    def showHide(self, showHide):
        
        if showHide == 'show':
            self.polygons.show()
            self.visible = True
        else:
            self.polygons.hide()
            self.visible = False
                    
class AnnotationsLayer():
    """ Layer for user annotations and drawings. """
    
    class PaintToolConfig():
        """ Hold all the current tool settings. """
        def __init__(self):    
            
            self.primaryColour = QColor(Qt.black)
            self.secondaryColour = QColor(Qt.white)
            self.currentDrawingTool = 'brush'
        
    def __init__(self, view):
        self.view = view
        self.toolsConfig = self.PaintToolConfig()
        self.layers = {}
        self.activeLayerName = ''
            
    def addAnnotationLayer(self, layerName):
        """ Drawing tool. """
                
        layer = AnnotationCanvas(self.view, self.toolsConfig)
        layer.proxy = self.view.scene.addWidget(layer)
        layer.reset()
        layer.proxy.setZValue(preferences.ZVALUE_Annotations)
        self.layers[layerName] = layer
        
    def showHide(self, showHide):
        
        if showHide == 'show':
            for annotationLists in self.annotations.values():
                for annotation in annotationLists:
                    annotation.show()
            self.visible = True
        else:
            for annotationLists in self.annotations.values():
                for annotation in annotationLists:
                    annotation.hide()
            self.visible = False

    def updatePosition(self):
        """ Move each layer with the map. """
        for layer in self.layers.values():
            canvasPoint = self.view.mapController.toCanvasCoordinates(layer.lat, layer.lon) - \
                          QPointF(layer.width/2, layer.height/2)
            layer.move(canvasPoint.x(), canvasPoint.y())
            
    def updateZoom(self, scale):
        """ Scale annotations with map. """
        for layer in self.view.annotationLayers.layers.values():
    
            tl = self.view.mapController.toCanvasCoordinates(layer.lat, layer.lon) - QPointF(layer.width/2, layer.height/2)             
            transform = QTransform()
            if scale < 1:
                layer.scale *= 0.5
                transform.scale(layer.scale, layer.scale)
                layer.proxy.setTransform(transform)
                layer.move(tl.x() + layer.width/4, tl.y() + layer.height/4)
                layer.width *= 0.5
                layer.height *= 0.5
            else:
                layer.scale *= 2
                transform.scale(layer.scale, layer.scale)
                layer.proxy.setTransform(transform)
                layer.move(tl.x() + layer.width/4, tl.y() + layer.height/4)
                layer.width *= 2
                layer.height *= 2  
                            
    def zoomToLayer(self, layerName):
        """
        Moves the canvas to be centred over a layer.
        """
        # move the annotation layer to the right place
        layer = self.layers[layerName]
        while layer.scale != 1:
            scale = layer.initialZoom / self.view.vectorZoom
            self.updateZoom(scale)

        # move the map to the right position
        self.view.vectorZoom = layer.initialZoom
        self.view.mapController.updateZoom()
        canvasCoords = self.view.mapController.toCanvasCoordinates(layer.lat, layer.lon)
        geoCoords = self.view.mapController.toGeographicalCoordinates(canvasCoords.x(), canvasCoords.y() + 35)
        self.view.mapController.moveToGeographicLocation(geoCoords.x(), geoCoords.y())

        self.view.scene.update()
                                
class RulerLayer():
    """
    Used to create paths on the map which displays total path length and time to perambulate
    the path at current speed.
    """
    class Line():
        def __init__(self, view, startLatLon, proxy):
                        
            self.segmentNumber = 0
            self.view = view
            self.startLatLon = startLatLon
            self.startX = self.view.mapController.toCanvasCoordinates(startLatLon.x(), startLatLon.y()).x()
            self.startY = self.view.mapController.toCanvasCoordinates(startLatLon.x(), startLatLon.y()).y()
            self.endX = 0
            self.endY = 0
            self.endLatLon = QPointF()
            self.proxy = proxy
            
        def updatePosition(self):
            """ Move each line with the map. """
            start = self.view.mapController.toCanvasCoordinates(self.startLatLon.x(), self.startLatLon.y())
            end = self.view.mapController.toCanvasCoordinates(self.endLatLon.x(), self.endLatLon.y())
            self.proxy.setLine(start.x(),
                               start.y(),
                               end.x(),
                               end.y())
                
    def __init__(self, view):
                        
        self.view = view
        self.lineObject = None
        self.lineSegmentList = []
        self.visible = True
        self.rulerEnabled = False
        self.ruleExists = False
        self.currentlyRuling = False

    def setStartPoint(self, startX, startY):
        """ Set the first point of a line segment. """
        # store coordinates in lat/lon for correct translation/scale with pan/zoom.
        self.latLonStart = self.view.mapController.toGeographicalCoordinates(startX, startY)
        line = QGraphicsLineItem(startX,
                                 startY,
                                 startX,
                                 startY)
        line.setPen(QPen(Qt.yellow, 2))
        self.view.scene.addItem(line)
        line.setZValue(preferences.ZVALUE_MetaDialogs-1)
        self.lineObject = self.Line(self.view, self.latLonStart, line)   

    def updateLines(self):
        """ Move lines with map. """
        for line in self.lineSegmentList:
            line.updatePosition() 
            
    def updateLine(self, endX, endY):
        """ Allows preview of line to move with mouse. """
        self.lineObject.proxy.setLine(self.lineObject.startX,
                                      self.lineObject.startY,
                                      endX,
                                      endY)

    def endLine(self, endPos):
        """ End the line drawing and save the line object to the layer's list. """
        self.lineObject.endLatLon = self.view.mapController.toGeographicalCoordinates(endPos.x(), endPos.y())
        self.lineObject.proxy.setLine(self.lineObject.startX,
                                      self.lineObject.startY,
                                      endPos.x(),
                                      endPos.y())
        self.lineObject.endX = endPos.x()
        self.lineObject.endY = endPos.y()
        self.lineSegmentList.append(self.lineObject)

        # Update details for ruler label
        self.view.mainWindow.updateRulerLabel(self.lineSegmentList)
        
    def showHide(self, showHide):
        if showHide == 'show':
            for line in self.lineSegmentList:
                    line.proxy.show()
            self.visible = True
        else:
            for line in self.lineSegmentList:
                line.proxy.hide()
            self.visible = False

    def clearRulerLines(self):
        """ Remove lineSegmentList and clear the ruler lineSegmentList list. """
        for line in self.view.rulerLayer.lineSegmentList:
            self.view.scene.removeItem(line.proxy)
        self.view.rulerLayer.lineSegmentList.clear()
        self.lineObject = None
        
class SpirographLayer():
    
    def __init__(self, view):
        
        self.view = view
        
        self.spirographList = []
        self.depth = 0
        self.maxDepth = 0
        
    def fill(self):
        """
        Once each segment that comprises each Spirograph is determined, it can be coloured based on the speed of sound
        for that region. The speed of sound value is saved with the segment so each Spirograph can be redrawn quickly
        without having to poll the server for the speed of sound.
        """
        ncwmsTools = NCWMSTools(self.view)
        
        for spiro in self.spirographList:
            segmentList = [segment.segmentCentreLatLon for segment in spiro.spiroSegmentList]
            spiro.maxDepth = ncwmsTools.getMaxDepth(segmentList)
            self.maxDepth = max([spiro.maxDepth, self.maxDepth])
         
            # If the ncWMS data does not have a value for this location, do not include it.
            validSegments = []
            for segment in spiro.spiroSegmentList:
                segmentCentreXY = self.view.mapController.toCanvasCoordinates(segment.segmentCentreLatLon.x(), 
                                                                              segment.segmentCentreLatLon.y())
                segment.soundSpeed = ncwmsTools.getSoundSpeedForPoint(self.depth, segmentCentreXY.x(), segmentCentreXY.y())
                if segment.soundSpeed > 0:
                    validSegments.append(segment)
                 
            maxSoundSpeed = max([segment.soundSpeed for segment in spiro.spiroSegmentList])
            minSoundSpeed = min([segment.soundSpeed for segment in spiro.spiroSegmentList])
            for segment in validSegments:
                endDelta = maxSoundSpeed - minSoundSpeed
                markerValue = (segment.soundSpeed - minSoundSpeed) / (endDelta if endDelta > 0 else 1)
                segment.fillWithColourForRatio(markerValue)
        
            self.view.mainWindow.setDepthLabel()
            
    def update(self):
        """
        Called when the map is zoomed. The Spirographs are redrawn using the sound speed determined when they were created. This
        saves having to repeat the expensive call to the ncMWS server. """
        for spiro in self.spirographList:
            spiro.redrawSpiroPolygons() 

    def clear(self):
        """ Removed all p(detection) circles and their fills. """
        for spiro in self.spirographList:
            self.view.scene.removeItem(spiro.spiroSegmentGraphicsGroup)
            spiro.spiroSegmentList.clear()
        self.spirographList.clear()
            
    def addProbOfDetectionBoundaries(self):
        """
        Draws circles (with a diameter=sonar range of the day) covering a ruler lineSegment entered. Circles
        are filled to denote probability of detection.
        """
        for spiro in self.spirographList:
            self.view.scene.removeItem(spiro.spiroSegmentGraphicsGroup)
            
        for lineSegment in self.view.rulerLayer.lineSegmentList:
            lengthCount = 1

            g = pyproj.Geod(ellps='WGS84')
            (radialBearing, _, dist) = g.inv(lineSegment.startLatLon.y(),
                                             lineSegment.startLatLon.x(), 
                                             lineSegment.endLatLon.y(), 
                                             lineSegment.endLatLon.x())
            
            # Put a spirograph at each point of each lineSegment segment that is half the range of the day in length.
            while (lengthCount*SONAR_RANGE_OF_THE_DAY*0.5) < dist:
                rangeOfTheDayRadiusLatLon = self.view.mapController.vincentyDirect(lineSegment.startLatLon.x(),
                                                                                   lineSegment.startLatLon.y(),
                                                                                   radialBearing,
                                                                                   lengthCount*SONAR_RANGE_OF_THE_DAY*0.5)         
                spiro = Spirograph(self.view,
                                   lineSegment.startLatLon,
                                   rangeOfTheDayRadiusLatLon,
                                   lengthCount)
                lengthCount += 2
                
                self.spirographList.append(spiro)

        for spiro in self.spirographList:
            spiro.drawSpiroPolygons()
        
class TacticalLayer():

    def __init__(self, view):
        self.view = view
        self.graphics = []
        self.threatArcs = []
        self.visible = True   

    def showHide(self, showHide):
        
        if showHide == 'show':
            for threatArc in self.threatArcs:
                threatArc.show()
                self.visible = True
        else:
            for threatArc in self.threatArcs:
                threatArc.hide()
                self.visible = False
                
    def clear(self):
        for graphic in self.graphics:
            self.view.scene.removeItem(graphic)
        self.graphics.clear()

class FeatureLayer():
    """ SVGs that denote airports, ports, cities etcl. """
    def __init__(self, view, features, visible):
        self.view = view
        self.features = features
        self.visible = visible
        
    def draw(self):
        for feature in self.features:
            feature.draw()
            
    def update(self):
        for feature in self.features:
            feature.update()

    def showHide(self, showHide):
        self.visible = True if showHide == 'show' else False
        for feature in self.features:
            feature.show() if self.visible else feature.hide()
            
    def setGeometry(self):
        pass

class EntityLayer():
    def __init__(self, view, visible):
        self.view = view
        self.truthEntities = []
        self.visible = visible

    def showHide(self):
        for entity in self.truthEntities:
            entity.showHide(self.visible)

class GraphicsLayer():
    """
    Groups like graphics items together so they can be handled like a 'single' item.
    """
    def __init__(self, view, visible):
        self.view = view
        self.graphicObjects = []
        self.visible = visible
        
    def addGraphicsObject(self, obj):
        """
        Add any icons, graphics view items etc. to this layer object.
        """
        self.graphicObjects.append(obj)
        
    def removeGraphicsObject(self, obj):
        """
        Remove an icon, graphics view item etc. from this layer object.
        """
        self.graphicObjects.remove(obj)
        
    def removeAllGraphicsObjects(self):
        """
        Remove all graphics from the view and graphicsObjectList.
        """
        for obj in self.graphicObjects:
            self.view.scene.removeItem(obj)
        self.graphicObjects.clear()

    def showHide(self, showHide):
        """
        Make all graphics items on this layer visible.
        """
        if showHide == 'show':
            self.visible = True
            for item in self.graphicObjects:
                item.show()    
        else:
            self.visible = False
            for item in self.graphicObjects:
                item.hide()    
    

class BreadcrumbLayer():
    
    class Line():
        def __init__(self, view, startLatLon, proxy):
                        
            self.view = view
            self.startLatLon = startLatLon
            self.endLatLon = QPointF()
            self.proxy = proxy

        def updatePosition(self):
            """ Move each line with the map. """
            start = self.view.mapController.toCanvasCoordinates(self.startLatLon.x(), self.startLatLon.y())
            end = self.view.mapController.toCanvasCoordinates(self.endLatLon.x(), self.endLatLon.y())
            self.proxy.setLine(start.x(),
                               start.y(),
                               end.x(),
                               end.y())

    # BreadcrumbLayer Constructor #
    def __init__(self, view, entity, visible):
        self.view = view
        self.visible = visible
        self.graphicObjects = []
        
        self.startLine(QPointF(entity.lat, entity.lon))
        
    def startLine(self, latLon):
        """ Start a new line showing current course history. """
        start = self.view.mapController.toCanvasCoordinates(latLon.x(), latLon.y())
        proxy = self.view.scene.addLine(start.x(), start.y(), start.x(), start.y())
        proxy.setZValue(preferences.ZVALUE_Icons)
        pen = QPen(QColor(0, 0, 0))
        pen.setWidth(1)
        pen.setDashPattern([5, 5])
        proxy.setPen(pen)
        line = self.Line(self.view, latLon, proxy)
        
        self.graphicObjects.append(line)
        
    def endLine(self, latLon):
        """ End course history line e.g. due to course change. """
        self.graphicObjects[-1].endLatLon = QPointF(latLon.x(), latLon.y())
        
    def updateLines(self):
        """ Ensure all lines update with map pan/zoom. """
        for line in self.graphicObjects:
            line.updatePosition()

    def showHide(self, showHide):
        """
        Make all graphics items on this layer visible.
        """
        if showHide == 'show':
            self.visible = True
            for line in self.graphicObjects:
                line.proxy.show()        
        else:
            self.visible = False
            for line in self.graphicObjects:
                line.proxy.hide()


class NavChartsTemplateLayer():
    """ Draws and labels outlines for each chart. """
    def __init__(self, view):
        
        self.view = view
        self.mapController = view.mapController
        self.visible = False
        self.chartOutlines = {}
        self.rectangles = {}
        self.chartNames = {}
        self.zLevel = 399
        
        self.chartOutlines['AUS00111P0'] = (115.67178994467334, -32.255049939198756, 115.72476925338074, -32.18514286687904)
        self.chartOutlines['AUS00111P1'] = (115.67398200849902, -32.18514991811797,  115.68981583872339, -32.17214993911571)
        self.chartOutlines['AUS00114P1'] = (115.73333022129219, -32.26388987184614,  115.7600043579987,  -32.24222204006769)
        self.chartOutlines['AUS00114P0'] = (115.69994738308844, -32.24694949354819,  115.7867245026005,  -32.1305528125873)
        self.chartOutlines['AUS00113P0'] = (115.68164733325914, -32.072674243475596, 115.76385406845286, -32.02849897906623)
        self.chartOutlines['AUS00117P0'] = (115.59978316828143, -32.28336893515372,  115.77857152703865, -32.04998801900059)
        self.chartOutlines['AUS00112P0'] = (115.4259400743493,  -32.078144013356045, 115.83690500989755, -31.857167891674703)
            
        pen = QPen(QColor(255, 0, 0))
        pen.setWidth(1)
                    
        for text, rectPoints in self.chartOutlines.items():
            tl = QPointF(self.mapController.toCanvasCoordinates(rectPoints[3], rectPoints[0]))
            br = QPointF(self.mapController.toCanvasCoordinates(rectPoints[1], rectPoints[2]))
            rectangle = self.view.scene.addRect(tl.x(), tl.y(), abs(br.x()-tl.x()), abs(br.y()-tl.y()))
            rectangle.setPen(pen)
            rectangle.setZValue(self.zLevel)
            self.rectangles[text] = rectangle
            chartName = self.view.scene.addText(text, QFont('Arial', 10, 10, False))
            chartName.setPos(tl)
            chartName.setZValue(self.zLevel)
            self.chartNames[text] = chartName
                        
    def update(self):
        """ Relocate the graphics with pan/zoom. """
        if self.visible:
            for text, rectPoints in self.chartOutlines.items():
                tl = QPointF(self.mapController.toCanvasCoordinates(rectPoints[3], rectPoints[0]))
                br = QPointF(self.mapController.toCanvasCoordinates(rectPoints[1], rectPoints[2]))
                self.rectangles[text].setRect(tl.x(), tl.y(), abs(br.x()-tl.x()), abs(br.y()-tl.y()))
                self.chartNames[text].setPos(tl)
            self.showHide('show')
        else:
            self.showHide('hide')
                
    def setOpacity(self, opacity):
        pass
    
    def showHide(self, showHide):
        
        self.visible = True if showHide == 'show' else False

        if self.visible:
            for rect in self.rectangles.values():
                rect.show()
            for name in self.chartNames.values():
                name.show() 
        else:
            for rect in self.rectangles.values():
                rect.hide()
            for name in self.chartNames.values():
                name.hide()             
