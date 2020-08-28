from builtins import str
import json
from math import radians
import random

from PySide2.QtCore import QPoint, Qt, QPointF, QRect, QEvent, QTimer, Signal
from PySide2.QtGui import QPainter
from PySide2.QtWidgets import QGraphicsView, QGraphicsScene, QLabel, QFrame, \
    QGraphicsSceneMouseEvent
from owslib.wms import WebMapService

from gis.mts import MTSLayer
from gis.mts_controller import MTSController
from gis.wfs import WFS
from graphics.toolbox import Toolbox
from model.feature import Feature
from model.layers import TacticalLayer, AnnotationsLayer, RulerLayer, \
    SpirographLayer, NavChartsTemplateLayer
from model.ownship import Ownship
from model.threat_arc import ThreatArc
import preferences


TEXTBOX_SCALE = 144*12
THREAT_ARC_SCALE = 1
WAYPOINT_POINT_SIZE = 0.01
TILE_DIMENSION = 256
TILE_OFFSET = 10, 10-TILE_DIMENSION

class View(QGraphicsView):
    '''
    This forms all the graphics elements for the COP.
    '''
    # A signal to send click information to any listeners
    rightClickSignal = Signal(list)
    keyPressSignal = Signal(str)
    leftClickSignal = Signal(QGraphicsSceneMouseEvent)
    mapMovedSignal = Signal(list)

    def __init__(self, mainWindow, canvasX, canvasY):
        '''
        Constructor
        '''
        super().__init__()

        self.mainWindow = mainWindow
        self.canvasWidth = canvasX
        self.canvasHeight = canvasY

        # View determines how much of the scene is visible.
        # if the scene is bigger, you get scroll bars
        self.scene = QGraphicsScene(self)
        self.setContextMenuPolicy(Qt.DefaultContextMenu)
        self.setScene(self.scene)
        self.setSceneRect(0, 0, self.canvasWidth, self.canvasHeight)
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet("border: 0px")

        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setRenderHint(QPainter.Antialiasing)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
 
        self.metaDialogVisible = False
        self.contextMenuVisible = False
        self.previousItem = None
        self.currentlyDrawing = False
       
        self.cursorPosition = QPoint(self.canvasWidth/2, self.canvasHeight/2)
        self.vectorZoom = 1
        self.rasterZoom = 2

        self.tacticalLayers = {}
        self.tacticalLayers['Threat Arcs'] = TacticalLayer(self)

        self.gisLayers = {}
        
        self.ownship = None
        self.truthEntities = {}
        self.contacts = {}
       
        self.createGisLayers()
        
        self.annotationLayers = AnnotationsLayer(self)
        self.rulerLayer = RulerLayer(self)
        self.spirographLayer = SpirographLayer(self)
        self.toolbox = Toolbox(self)
        
        self.viewport().installEventFilter(self)

        self.update()
        
        self.runCacheBuilder = False
        self.cacheBuilder()
        self.demoRunning = False
        self.runDemos()
 
    def eventFilter(self, _, event):
        """
        This is to catch all mouse wheel events and use them only for zooming
        i.e. not for scrolling.
        """
        if event.type() == QEvent.Wheel:
            # Only used for zooming
            self.mapController.wheelEvent(event)
            return True
        else:
            return False

    def resize(self, width, height):
        ''' If the container is resized, resize the maps. '''
        
        self.setGeometry(0, 0, width, height)
        self.mapController.updateCanvasSize(width, height)
        self.setSceneRect(0, 0, self.frameSize().width(), self.frameSize().height())
        
    def update(self):

        self.updateAllGraphicsLayers()
        self.updateOwnship()
#         self.updateSolutions()
#         if preferences.getHMIName() == 'OS-CONSOLE':
#             self.updateTruth()
 
    def updateOwnship(self):
        
        osSpeed = 18
        osCourse = 0
        
        lat, lng = (preferences.SCENARIO_LAT_LNG[0], 
                    preferences.SCENARIO_LAT_LNG[1])
                      
        if not self.ownship:
            # quick access to ownship
            ownship = Ownship(self,
                              'OS',
                              preferences.AFFILIATION_FRIENDLY,
                              self.mapController.toCanvasCoordinates(lat, lng).x(),
                              self.mapController.toCanvasCoordinates(lat, lng).y(),
                              osSpeed,
                              osCourse)
             
            self.truthEntities['OS'] = ownship
            self.ownship = ownship
            self.toolbox.createOwnshipMenu()
             
            self.zoomOwnship()
 
        # we have OS so just need to maintain its parameters
        else:
            # update model with correct position information etc.
            self.truthEntities['OS'].update(self.mapController.toCanvasCoordinates(lat, lng).x(),
                                            self.mapController.toCanvasCoordinates(lat, lng).y(),
                                            osSpeed,
                                            osCourse)

#     def updateTruth(self):
# 
#         # get all current entities
#         entities = {}
#         for entityId in self.combatSystem.getTruthEntityIds():
#             entities[entityId] = self.combatSystem.getTruthEntity(entityId)
# 
#         for entity in entities.values():
#             entityId = str(entity.getEntityId())
# 
#             lat, lng = Algorithms.llFromEN(entity.getEasting(), 
#                                            entity.getNorthing(), 
#                                            preferences.user.main.SCENARIO_LAT_LNG[0], 
#                                            preferences.user.main.SCENARIO_LAT_LNG[1])
#             bearing, rnge = self.combatSystem.getBR(entity.getEasting(), entity.getNorthing())
#             classification = entity.getDescription()
#          
#             # entityId, timestamp, easting, northing, course, speed, depth, tonals, demon, acousticPower
#             # This is a new entity
#             if entityId not in self.truthEntities:
#                 # If this is not us, add
#                 if entity.entityId != preferences.user.vessel.VESSEL_OWNSHIP_ID:
#                     self.truthEntities[entityId] = TruthEntity(self,
#                                                                str(entityId),
#                                                                self.mapController.toCanvasCoordinates(lat, lng).x(),
#                                                                self.mapController.toCanvasCoordinates(lat, lng).y(),
#                                                                entity.speed,
#                                                                entity.course,
#                                                                rnge,
#                                                                bearing, 
#                                                                classification)
#    
#             # we have a record of this entity so just need to maintain its parameters
#             else:
#                 # update model with correct position information etc.
#                 self.truthEntities[entityId].update(self.mapController.toCanvasCoordinates(lat, lng).x(),
#                                                     self.mapController.toCanvasCoordinates(lat, lng).y(),
#                                                     entity.speed,
#                                                     entity.course)
    
#     def updateSolutions(self):
#         
#         for contact in self.cruseData.getContacts():
# 
#             contactId = contact.getId()
#             latLon = self.mapController.vincentyDirect(self.ownship.lat, 
#                                                        self.ownship.lon, 
#                                                        contact.getBearing(), 
#                                                        contact.getRange())  #4572m = 5kyds            
#             xy = self.mapController.toCanvasCoordinates(latLon.x(), latLon.y())
#             
#             # This is a new entity
#             if contactId not in self.contacts:
#                 # If this is not us, add
#                 if contactId != preferences.user.vessel.VESSEL_OWNSHIP_ID:
#                     self.contacts[contactId] = Entity(self,
#                                                       'S{}'.format(contactId),
#                                                       contact.getAffiliation(),
#                                                       xy.x(),
#                                                       xy.y(),
#                                                       contact.getSpeed(),
#                                                       contact.getCourse(),
#                                                       contact.getRange(),
#                                                       contact.getBearing(), 
#                                                       contact.getClassification(),
#                                                       30)
#                 
#             # we have a record of this entity so just need to maintain its parameters
#             else:
#                 # update model with correct position information etc.
#                 self.contacts[contactId].update(contact.getAffiliation(),
#                                                 xy.x(),
#                                                 xy.y(),
#                                                 contact.getSpeed(),
#                                                 contact.getCourse(),
#                                                 contact.getRange(),
#                                                 contact.getBearing(),
#                                                 contact.getClassification(),
#                                                 30)

    def updateAllGraphicsLayers(self):
        
        # Don't update if we're still working
        if not self.rulerLayer.currentlyRuling and not self.mainWindow.progressUpdateThreadRunning:               
            for spiro in self.spirographLayer.spirographList:
                newCentre = self.mapController.toCanvasCoordinates(spiro.rangeOfTheDayRadiusLatLon.x(), spiro.rangeOfTheDayRadiusLatLon.y())
                spiroBound = spiro.spiroSegmentGraphicsGroup.boundingRect()
                spiro.spiroSegmentGraphicsGroup.setPos(newCentre.x()-(spiroBound.width()/2) - spiroBound.x(),
                                                       newCentre.y()-(spiroBound.height()/2) - spiroBound.y())
            
            self.rulerLayer.updateLines()

        # Redraw each annotation to ensure they are in the correct location with each zoom.
        if not self.currentlyDrawing:
            self.annotationLayers.updatePosition()
                        
        # Update location of threat arcs
        for threatarc in self.tacticalLayers['Threat Arcs'].threatArcs:
            if threatarc.visible:
                threatarc.draw()

        self.navChartTemplates.update()
            
        # Update location of all WFS icons
        for key in self.gisLayers:
            self.gisLayers[key].update()
            
    ''' ------------------------------------------------------------------------------------------------
                                            GIS FUNCTIONS
        ------------------------------------------------------------------------------------------------ '''
    def createGisLayers(self):
        ''' Load all layer tiles and features. '''
#         try:
        self.mapController = MTSController(self, 
                                           QRect(0, 0, self.canvasWidth, self.canvasHeight), 
                                           QPointF(-32.2138204, 115.0387413))
             
        # add Web Map Service layers
        self.loadLayers()
        # features are not available without a GeoServer. Will fail gracefully.
        if preferences.USE_GEOSERVER:
            self.wfsLoader()
#         except Exception as e:
#             print('Could not create Map Controller. {}'.format(e))
#             print('Please check the availability of the GeoServer.')
         
    def wfsLoader(self):
        
        wfsConnection = WFS(self)
        
#         self.gisLayers['Australian Airports'] = FeatureLayer(self, wfsConnection.getAirports(), True)
#         self.gisLayers['Australian Airports'].draw()
#         
#         self.gisLayers['Australian Ports'] = FeatureLayer(self, wfsConnection.getPorts(), True)
#         self.gisLayers['Australian Ports'].draw()
#         
#         self.gisLayers['Cities'] = FeatureLayer(self, wfsConnection.getCities(), True)
#         self.gisLayers['Cities'].draw()

    def loadLayers(self):
    
        self.navChartTemplates = NavChartsTemplateLayer(self)
#         self.mapController.addNavChartTemplate(self.navChartTemplates)                 
                
#         osm2 = MTSLayer(self, 'Land', 'OSM-WMS', 9, False, 1.0)
#         self.mapController.addLayer('gisLayers', 'OSM', osm2)
  
        osmRoads = MTSLayer(self, 'OSM', 'Roads', 8, False, 1.0)
        self.mapController.addLayer('gisLayers', 'Roads', osmRoads)
            
        waterways = MTSLayer(self, 'OSM', 'Waterways', 7, True, 1.0)
        self.mapController.addLayer('gisLayers', 'Waterways', waterways)
            
        water = MTSLayer(self, 'OSM', 'Water', 6, True, 1.0)
        self.mapController.addLayer('gisLayers', 'Water', water)
          
#         osmLandUse = MTSLayer(self, 'OSM', 'Land_Use', 5, True, 1.0)
#         self.mapController.addLayer('gisLayers', 'Land Use', osmLandUse)
#
#         osmNatural = MTSLayer(self, 'OSM', 'Natural Space', 4, True, 1.0)
#         self.mapController.addLayer('gisLayers', 'Natural', osmNatural)
          
        hillshade = MTSLayer(self, 'Land', 'SRTM30-Coloured-Hillshade', 3, True, 1.0)
        self.mapController.addLayer('gisLayers', 'Hill Shade', hillshade)

        austLandmass = MTSLayer(self, 'Land', 'Aust_Landmasses', 3, False, 1.0)
        self.mapController.addLayer('gisLayers', 'Australia', austLandmass)     
                       
        contours = MTSLayer(self, 'Oceanographic', 'World_Bathymetric_Contours', 2, False, 1.0)
        self.mapController.addLayer('oceanographicLayers', 'Bathymetric Contours', contours)
             
        heights = MTSLayer(self, 'Oceanographic', 'World_Bathymetric_Heightmap', 1, True, 1.0)
        self.mapController.addLayer('oceanographicLayers', 'Bathymetric Heightmap', heights)

        benthic = MTSLayer(self, 'Oceanographic', 'Benthic_Substrate', 0, False, 1.0)
        self.mapController.addLayer('oceanographicLayers', 'Benthic Substrate', benthic)
        
        worldLandmass = MTSLayer(self, 'Land', 'World_Landmasses', 98, False, 1.0)
        self.mapController.addLayer('gisLayers', 'World Land Masses', worldLandmass)
# 
#         # chartsArray = ['AUS00111P0', 'AUS00111P1', 'AUS00112P0', 'AUS00113P0', 'AUS00114P0', 'AUS00114P1', 'AUS00116P1', 'AUS00116P2', 'AUS00116P3', 'AUS00116P4', 'AUS00116P5', 'AUS00116P6', 'AUS00116P7', 'AUS00117P0', 'AUS00755P0', 'AUS00331P0', 'AUS00331P1', 'AUS00331P2', 'AUS00331P3', 'AUS00332P0', 'AUS00745P0', 'AUS00746P0', 'AUS00752P0', 'AUS00753P0', 'AUS00754P0', 'AUS00756P0', 'AUS00757P0', 'AUS00758P0', 'AUS00759P0', 'AUS00774P0']
#         chartsArray = ['AUS00111P0', 'AUS00111P1', 'AUS00112P0', 'AUS00113P0', 'AUS00114P0', 'AUS00114P1', 'AUS00117P0']
#         for chart in chartsArray:
#             chartLayer = MTSLayer(self, 'Navigation', chart, 151, False, 1.0)
#             self.mapController.addLayer('navigationLayers', chart, chartLayer)                     
#             chartLayer.setLayerZLevel(101)
 
        for layer in self.mapController.allLayers:
            layer.setLayerZLevel(layer.zLevel)
            
    ''' ------------------------------------------------------------------------------------------------
                                            GRAPHICS FUNCTIONS
        ------------------------------------------------------------------------------------------------ '''
    def createThreatArc(self, designation, reportedLat, reportedLon, toi, course, speed, eir):
        '''
        Draw an arc on the map relative to ownship that shows a reported threat.
        designation
        reportedX, reportedY
        toi: Time of Intercept - when the threat was detected.
        course, speed
        eir: Expected in Range - based on course, speed.
        '''
        arc = ThreatArc(self, designation, reportedLat, reportedLon, toi, course, speed, eir)
        self.tacticalLayers['Threat Arcs'].threatArcs.append(arc)
        
    def setIconOpacity(self, opacity):
        for entity in self.contacts.values():
            entity.icon.setOpacity(opacity)
            
    def setIconSize(self, size):
        for entity in self.contacts.values():
            entity.iconScale *= size
            entity.icon.setScale(entity.iconScale)
 
    ''' ------------------------------------------------------------------------------------------------
                                            MOUSE/KEYBOARD FUNCTIONS
        ------------------------------------------------------------------------------------------------ '''
    def keyPressEvent(self, event):
        '''
        End text entering.
        '''
        self.keyPressSignal.emit(event.text())
            
        if event.key() == 90:
            self.annotationLayers.zoomToLayer('Local-1')
           
        self.mapController.keyPressEvent(event)
        if self.currentlyDrawing:
            self.annotationLayers.layers[self.annotationLayers.activeLayerName].keyPressEvent(event)

    def keyReleaseEvent(self, event):
        pass

    def mouseMoveEvent(self, event):
        '''
        Move map around or start drawing.
        '''
        # update location label
        ll = self.mapController.toGeographicalCoordinates(event.pos().x(), event.pos().y())
        mouseLat, mouseLon = ll.x(), ll.y()
            
        if self.currentlyDrawing:
            self.annotationLayers.layers[self.annotationLayers.activeLayerName].mouseMoveEvent(event)
        elif self.rulerLayer.currentlyRuling and self.rulerLayer.lineObject is not None:
            endX = event.pos().x()
            endY = event.pos().y()
            self.rulerLayer.updateLine(endX, endY)
        elif self.ownship:
            bearing = self.mapController.angleBetweenTwoPoints(radians(self.ownship.lat),
                                                               radians(self.ownship.lon),
                                                               radians(mouseLat),
                                                               radians(mouseLon))
            distance = self.mapController.distanceBetweenTwoPoints(self.ownship.lat,
                                                                   self.ownship.lon,
                                                                   mouseLat,
                                                                   mouseLon)
            self.mainWindow.updateLocationLabel(mouseLat, mouseLon, bearing, distance)
            
        if event.buttons() == Qt.LeftButton:
            # scroll map around
            self.mapController.moveMap(event.pos() - self.cursorPosition)

            offset = self.cursorPosition - event.pos()
            self.cursorPosition = event.pos()
            x = offset.x()
            y = offset.y()
            self.horizontalScrollBar().setValue(x)
            self.verticalScrollBar().setValue(y)
                 
        self.mapMovedSignal.emit([event])

                 
    def mousePressEvent(self, event):
        '''
        Move map around or start drawing.
        '''
        clickedItem = self.itemAt(event.pos())

        allEntities = list(self.contacts.values()) + list(self.truthEntities.values())
        # Set start and end points of lineSegmentList in the ruler tool if ruling.
        if self.rulerLayer.currentlyRuling:
            if self.rulerLayer.lineObject is not None:
                self.rulerLayer.endLine(event.pos())
            self.rulerLayer.setStartPoint(event.pos().x(), event.pos().y())
 
        if self.currentlyDrawing:
            self.annotationLayers.layers[self.annotationLayers.activeLayerName].mousePressEvent(event)
        else:
            # hide any visible metadataDialog
            if self.metaDialogVisible:
                self.metaDialogVisible = False
                if self.previousItem:
                    self.previousItem.showHideMetaDialog(False)
                
            if event.buttons() == Qt.LeftButton:
                if type(clickedItem) == Feature:
                    self.metaDialogVisible = True
                    self.previousItem = clickedItem
                    clickedItem.showHideMetaDialog(True)
                     
                for entity in allEntities:
                    if clickedItem in entity.graphicsLayers[preferences.ICON].graphicObjects:
                        self.metaDialogVisible = True
                        self.previousItem = entity
                        entity.showHideMetaDialog(self.metaDialogVisible)
                        break
                             
                for threatArc in self.tacticalLayers['Threat Arcs'].threatArcs:
                    if clickedItem == threatArc.graphicsGroup:
                        self.metaDialogVisible = True
                        self.previousItem = threatArc
                        threatArc.showHideMetaDialog(self.metaDialogVisible)
 
                self.leftClickSignal.emit(event)
                 
            elif event.buttons() == Qt.RightButton:
                clickedEntity = False
                for entity in allEntities:
                    if clickedItem in entity.graphicsLayers[preferences.ICON].graphicObjects:
                        clickedEntity = True
                        self.rightClickSignal.emit([event, entity])
                        self.previousItem = entity
                        break
                if not clickedEntity:
                    self.rightClickSignal.emit([event, None])
                     
        self.cursorPosition = event.pos()
        super().mousePressEvent(event)
        
    def testUrl(self, location):
    
        # CRUSE:Aust_Benthic_Substrate
        # CRUSE:World_Bathymetric_Heightmap
        wms = WebMapService('http://{}:{}/geoserver/wms'.format(preferences.GEOSERVER_IP, preferences.GEOSERVER_PORT))
        response = wms.getfeatureinfo(
            layers=['CRUSE:World_Bathymetric_Heightmap'],
            srs='EPSG:4326',
            bbox=(-180, -90, 180, 90),
            size=(self.canvasWidth, self.canvasHeight),
            format='image/png',
            query_layers=['CRUSE:World_Bathymetric_Heightmap'],
            info_format='application/json',
            xy=(location.x(), location.y()))
        
        info = json.loads(response.read())
        depth = info['features'][0]['properties']['Elevation_relative_to_sea_level']

#         response = wms.getfeatureinfo(
#             layers=['CRUSE:Aust_Benthic_Substrate'],
#             srs='EPSG:4326',
#             bbox=(99.69917295458612, -55.980399892638445, 170.4556884483281, -4.318218428155205),
#             size=(self.canvasWidth, self.canvasHeight),
#             format='image/png',
#             query_layers=['CRUSE:Aust_Benthic_Substrate'],
#             info_format='application/json',
#             xy=(location.x(), location.y()))
#         
#         info = json.loads(response.read())        
#         print('{}'.format(info))
# 
#         response = wms.getfeatureinfo(
#             layers=['CRUSE:WA_Landmass'],
#             srs='EPSG:4326',
#             bbox=(-180, -90, 180, 90),
#             size=(self.canvasWidth, self.canvasHeight),
#             format='image/png',
#             query_layers=['CRUSE:WA_Landmass'],
#             info_format='application/json',
#             xy=(location.x(), location.y()))
#         
#         info = json.loads(response.read())        
#         print('{}'.format(info))  

        self.showHideMetaDialog(True, location, depth)
    
    def showHideMetaDialog(self, showMetaDialog, xy, depth):
             
        if showMetaDialog:
            ll = self.mapController.toGeographicalCoordinates(xy.x(), xy.y())
            text = 'X:{}, Y:{}\nLat:{:.2f}, Lon:{:.2f}\nDepth: {}m'.format(xy.x(), xy.y(), ll.x(), ll.y(), depth)

            self.metaDialog = QLabel(text)
            self.metaDialog.move(QPoint(int(xy.x()), int(xy.y())))
            self.metaDialog.setStyleSheet("""QLabel {color: rgb(255,255,255);
                                                     background-color: rgba(0,0,0,150);
                                                     padding: 5px;
                                                     border: 1px solid white;}
                                        """)
            self.metaDialogProxy = self.scene.addWidget(self.metaDialog)
            self.metaDialogProxy.setZValue(preferences.ZVALUE_MetaDialogs)
            self.metaDialogProxy.setScale(10/self.vectorZoom)
        else:
            self.metaDialogProxy.hide()

    def processRightClick(self, event, entity=None):
        """ Emit a signal to listers that a right-click occurred. """
        self.rightClickSignal.emit([event, entity])

    def mouseReleaseEvent(self, event):

        if self.currentlyDrawing:
            self.annotationLayers.layers[self.annotationLayers.activeLayerName].mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        
        # Terminate the polyline ruler tool.
        if self.rulerLayer.currentlyRuling:
            self.rulerLayer.endLine(event.pos())
            self.rulerLayer.currentlyRuling = False
            self.mainWindow.createRulerLayer('end')
        
        if self.currentlyDrawing:
            self.annotationLayers.layers[self.annotationLayers.activeLayerName].mouseDoubleClickEvent(event)
                        
    ''' ------------------------------------------------------------------------------------------------
                                            NAVIGATION FUNCTIONS
        ------------------------------------------------------------------------------------------------ '''
    def zoomOwnship(self):
        '''
        Moves the canvas to be centred over OWNSHIP at a suitable zoom level.
        '''
        self.vectorZoom = 8
        self.rasterZoom = 8
        while self.vectorZoom < 9:
            self.mapController.moveToGeographicLocation(self.ownship.lat, self.ownship.lon)
            self.vectorZoom *= 1.1
            self.mapController.updateZoom()

        self.ownship.update(self.ownship.x,
                            self.ownship.y,
                            self.ownship.speed,
                            self.ownship.course)
        self.scene.update()

    ''' ------------------------------------------------------------------------------------------------
                                            UTILITY FUNCTIONS
        ------------------------------------------------------------------------------------------------ '''      
    def cacheBuilder(self):
        ''' Creates all the tiles required for a specific area at all zoom levels. '''
        if self.runCacheBuilder:
            print('START CACHE BUILDER')
            for northing in [northing / 10.0 for northing in range(1122, 1250, 1)]:
                for easting in [easting / -10.0 for easting in range(270, 360, 1)]:
                    self.mapController.moveToGeographicLocation(easting, northing)
                    for zoom in range(1, 19, 1):
                        print('{}, {} @ {}'.format(easting, northing, zoom))
                        self.mapController.tileZoomIndex = zoom
                        self.mapController.updateZoom()
                        
    ''' ------------------------------------------------------------------------------------------------
                                            TEST/DEMO FUNCTIONS
        ------------------------------------------------------------------------------------------------ '''      
    def runDemos(self):
        
        if not self.demoRunning:
            self.timer = QTimer()
            self.timer.start(2000)
    
#             self.timer.timeout.connect(lambda: self.drawRandomThreatArc(False))
#             self.timer.timeout.connect(lambda: self.createContacts())
        
        self.demoRunning = True
             
    def createContacts(self):

#         self.ct1 = self.cruseData.createContact(preferences.SensorType.VIS,     # sensorType
#                                                 45,                       # brg
#                                                 5000,                     # rng=None
#                                                 30,                       # cse=None
#                                                 50,                       # spd=None
#                                                 1,                        # brgrt=None
#                                                 2,                        # rngrt=None
#                                                 None                      # timestamp=None
#                                           )
# 
#         self.ct2 = self.cruseData.createContact(preferences.SensorType.VIS,     # sensorType
#                                                 55,                       # brg
#                                                 5000,                     # rng=None
#                                                 30,                       # cse=None
#                                                 50,                       # spd=None
#                                                 1,                        # brgrt=None
#                                                 2,                        # rngrt=None
#                                                 None                      # timestamp=None
#                                           )
# 
#         self.ct3 = self.cruseData.createContact(preferences.SensorType.VIS,     # sensorType
#                                                 35,                       # brg
#                                                 5000,                     # rng=None
#                                                 30,                       # cse=None
#                                                 50,                       # spd=None
#                                                 1,                        # brgrt=None
#                                                 2,                        # rngrt=None
#                                                 None                      # timestamp=None
#                                           )
# 
#         self.ct4 = self.cruseData.createContact(preferences.SensorType.VIS,     # sensorType
#                                                 45,                       # brg
#                                                 4500,                     # rng=None
#                                                 30,                       # cse=None
#                                                 50,                       # spd=None
#                                                 1,                        # brgrt=None
#                                                 2,                        # rngrt=None
#                                                 None                      # timestamp=None
#                                           )
# 
#         self.ct5 = self.cruseData.createContact(preferences.SensorType.VIS,     # sensorType
#                                                 45,                       # brg
#                                                 5500,                     # rng=None
#                                                 30,                       # cse=None
#                                                 50,                       # spd=None
#                                                 1,                        # brgrt=None
#                                                 2,                        # rngrt=None
#                                                 None                      # timestamp=None
#                                           )
#         self.ct1._contactId = 1
#         self.ct1.affiliation = preferences.ThreatType.Hostile
#         self.ct2._contactId = 2
#         self.ct2.affiliation = preferences.ThreatType.Hostile
#         self.ct3._contactId = 3
#         self.ct3.affiliation = preferences.ThreatType.Hostile
#         self.ct4._contactId = 4
#         self.ct4.affiliation = preferences.ThreatType.Hostile
#         self.ct5._contactId = 5
#         self.ct5.affiliation = preferences.ThreatType.Hostile
#         # contactId, time, brg, rng, cse, spd, des, cls, afl, col, master, priority, dropped, par
        self.timer.stop()

    def updateContact(self):
        pass
#         self.ct._classification = 'AU'
#         '''
#         Unknown
#         Neutral
#         Friendly
#         Hostile
#         Civilian
#         '''
#         self.ct._affiliation = preferences.ThreatType.Hostile

    def moveToRandomLocation(self):
        '''
        Demo to test navigation.
        '''
        r = random.randint(0, 3)
        if r == 0:
            # Perth
            self.moveToGeographicLocation(-32.2138204, 115.0387413)
            print('Perth')
        elif r == 1:
            # Adelaide
            self.moveToGeographicLocation(-35.09138204, 138.07387413)
            print('Adelaide')
        elif r == 2:
        # London
            self.moveToGeographicLocation(51.5074, 0.1278)
            print('London')       
        
    def drawRandomThreatArc(self, move):
        '''
        Demo to test threat arc.
        '''
        r = random.randint(0, 4)
        if r == 0:
            # Perth
            print('Perth')
            self.createThreatArc('PER: 247', -32.2138204, 115.0387413, 1400, 135, 3, 30)
            if move:
                self.mapController.moveToGeographicLocation(-32.2138204, 115.0387413)
        elif r == 1:
            # Adelaide
            print('Adelaide')
            self.createThreatArc('ADL: 97', -35.09138204, 138.07387413, 1400, 135, 3, 30)
            if move:
                self.mapController.moveToGeographicLocation(-35.09138204, 138.07387413)
        elif r == 2:
            # London
            print('London')
            self.createThreatArc('LON: 305', 51.5074, 0.1278, 1400, 135, 3, 30)
            if move:
                self.mapController.moveToGeographicLocation(51.5074, 0.1278)
        elif r == 3:
            # Random
            print('QLD')
            self.createThreatArc('QLD: 62', -16.595414, 145.038023, 1400, 135, 3, 30)
            if move:
                self.mapController.moveToGeographicLocation(-16.595414, 145.038023)