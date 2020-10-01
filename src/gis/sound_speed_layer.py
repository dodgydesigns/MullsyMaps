import operator
import urllib.request

from PySide2.QtCore import Qt
from PySide2.QtGui import QPen, QBrush, QColor
from PySide2.QtWidgets import QGraphicsItemGroup, QGraphicsBlurEffect
import numpy

import enums
import preferences
import xml.etree.ElementTree as ET


class SoundSpeedLayer():
    '''

    '''
    def __init__(self, view):
        '''
        Constructor
        '''
        self.view = view
        self.tileCount = 5

        self.depth = 0
        self.maxDepth = 0
        self.graphicsGroup = QGraphicsItemGroup(scene=self.view.scene)
#         self.map.scene.addItem(self.graphicsGroup)
#         self.graphicsGroup.setValue(1)
        
        self.visible = True
        self.dataMap = {}

        canvasRect = view.mapToScene(view.viewport().geometry()).boundingRect()
        self.width = int(canvasRect.width())
        self.height = int(canvasRect.height())
        self.lonMin = view.mapController.toGeographicalCoordinates(canvasRect.x(), 0).y()
        self.lonMax = view.mapController.toGeographicalCoordinates(canvasRect.x()+canvasRect.width(), 0).y()
        self.latMax = view.mapController.toGeographicalCoordinates(canvasRect.x(), 0).x()
        self.latMin = view.mapController.toGeographicalCoordinates(canvasRect.x(), 0+canvasRect.height()).x()

        self.dLat = abs(self.latMax-self.latMin) / self.tileCount
        self.dLon = abs(self.lonMax-self.lonMin) / self.tileCount
        self.startLat, self.startLon = self.latMax, self.lonMin
        self.endLat, self.endLon = self.latMin, self.lonMax
        self.signLat = self.latMax/abs(self.startLat)
        self.signLon = self.lonMax/abs(self.startLon)
                   
    def getMaxDepth(self):
        ''' Use the getDepth() function to determine the maximum depth of a location. '''
        lat, lon = self.startLat, self.startLon        
        dataList = []
        
        for lat in numpy.arange(abs(self.startLat), abs(self.endLat), self.dLat):
            for lon in numpy.arange(abs(self.startLon), abs(self.endLon), self.dLon):
                xy = self.view.mapController.toCanvasCoordinates(self.signLat*lat, self.signLon*lon)
                depth = self.getDepth(xy.x()-self.width, xy.y())
                if depth > 1:
                    dataList.append(depth)
                
        maxDepth = max(dataList)
        self.maxDepth = maxDepth
        
        return maxDepth
        
    def getDepth(self, x, y):
        ''' 
        Get the maximum depth of a location. This is used to set the limit the depth
        the user can enter and build the ratio for probability of detection.
        '''
        depth = 1
        xmlRequest = 'http://{}:{}/ncWMS2/wms?'.format(preferences.GEOSERVER_IP, preferences.GEOSERVER_PORT) + \
                     'LAYERS=003/max_depth&' + \
                     'QUERY_LAYERS=003/max_depth&' + \
                     'STYLES=default-scalar/default&' + \
                     'SERVICE=WMS&' + \
                     'VERSION=1.1.1&' + \
                     'REQUEST=GetFeatureInfo&' + \
                     'BBOX={},{},{},{}&'.format(self.lonMin, self.latMin, self.lonMax, self.latMax) + \
                     'FEATURE_COUNT=5&' + \
                     'HEIGHT={}&'.format(self.height) + \
                     'WIDTH={}&'.format(self.width) + \
                     'FORMAT=image/png&' + \
                     'INFO_FORMAT=text/xml&' + \
                     'SRS=EPSG:4326&' + \
                     'X={}&'.format(round(x)) + \
                     'Y={}&'.format(round(y)) + \
                     'TIME=2017-06-28T00:00:00.000Z&' + \
                     'ELEVATION={}'.format(depth)  

        try:
            url = urllib.request.urlopen(xmlRequest)
            tree = ET.fromstring(url.read())
                
            depth = float(tree.findall("./Feature/FeatureInfo/value")[0].text)
        except:
#             print(xmlRequest)
            pass
        return depth
 
    def getSoundSpeedForPoint(self, x, y):
        
        '''
        Get the probability of detection based on the current depth for a certain location.
        '''
        speed = 1
        xmlRequest = 'http://{}:{}/ncWMS2/wms?'.format(preferences.GEOSERVER_IP, preferences.GEOSERVER_PORT) + \
                     'LAYERS=003/soundspeed&' + \
                     'QUERY_LAYERS=003/soundspeed&' + \
                     'STYLES=default-scalar/default&' + \
                     'SERVICE=WMS&' + \
                     'VERSION=1.1.1&' + \
                     'REQUEST=GetFeatureInfo&' + \
                     'BBOX={},{},{},{}&'.format(self.lonMin, self.latMin, self.lonMax, self.latMax) + \
                     'FEATURE_COUNT=5&' + \
                     'HEIGHT={}&'.format(self.height) + \
                     'WIDTH={}&'.format(self.width) + \
                     'FORMAT=image/png&' + \
                     'INFO_FORMAT=text/xml&' + \
                     'SRS=EPSG:4326&' + \
                     'X={}&'.format(round(x)) + \
                     'Y={}&'.format(round(y)) + \
                     'TIME=2017-06-28T00:00:00.000Z&' + \
                     'ELEVATION={}'.format(self.depth)
        try:
            url = urllib.request.urlopen(xmlRequest)
            tree = ET.fromstring(url.read())
            speed = float(tree.findall("./Feature/FeatureInfo/value")[0].text)
        except:
#             print(xmlRequest)
            pass
        return speed
 
    def updateDepth(self, depthChange):
        ''' Get the probability of detection based on an increase or decrease of depth. '''
        if self.depth == 0:
            self.depth = self.maxDepth / 2
        else:    
            if depthChange == 'up':
                if (self.depth + (self.getMaxDepth() / 10)) <= self.maxDepth:
                    self.depth += (self.getMaxDepth() / 10)
            else:
                if (self.depth - (self.getMaxDepth() / 10)) >= 0:
                    self.depth -= (self.getMaxDepth() / 10)
        self.getSoundSpeedData()

    def updateDepthByValue(self, depth):
        ''' Get the probability of detection based on a depth entered in the depth text box. '''

        if (self.depth + (self.getMaxDepth() / 10)) <= self.maxDepth and \
           (self.depth - (self.getMaxDepth() / 10)) >= 0:
            self.depth = depth
            
        self.getSoundSpeedData()
        
    def getSoundSpeedData(self):
        ''' Get the probability of detection (sound speed atm) based on lat/lon and depth. '''
        lat, lon = self.startLat, self.startLon
        for lat in numpy.arange(abs(self.startLat), abs(self.endLat), self.dLat):
            for lon in numpy.arange(abs(self.startLon), abs(self.endLon), self.dLon):
                xy = self.view.mapController.toCanvasCoordinates(self.signLat*lat, self.signLon*lon)
                ss = self.getSoundSpeedForPoint(xy.x()-self.width, xy.y())
                if ss > 1:
                    self.dataMap[(xy.x(), xy.y())] = ss        
        
    def drawSoundSpeed(self):
        ''' Fill in the circles around a ruler path based on the probability of detection. '''
        pen=QPen(Qt.transparent, 1)

        # It is possible that there is no data for a particular location/depth.
        if len(self.dataMap) > 0:
            maxSoundSpeed = max(self.dataMap.items(), key=operator.itemgetter(1))[1]
            minSoundSpeed = min(self.dataMap.items(), key=operator.itemgetter(1))[1]
            endDelta = maxSoundSpeed - minSoundSpeed
            for xy, ss in self.dataMap.items():            
                markerValue = (ss - minSoundSpeed) / (endDelta if endDelta > 0 else 1)
                r = self.view.scene.addRect(xy[0]-self.width, 
                                            xy[1], 
                                            self.width/(self.tileCount/1.05),
                                            self.height/self.tileCount)
                
                rgb = self.getColourForRatio(markerValue)
                brush = QBrush(QColor(rgb[0], rgb[1], rgb[2]))
                r.setBrush(brush)
                r.setOpacity((markerValue/2))
                r.setPen(pen)
                self.graphicsGroup.addToGroup(r)

            self.graphicsGroup.setZValue(enums.ZVALUE_MetaDialogs-1)
            self.effect = QGraphicsBlurEffect()
            self.effect.setBlurRadius(50)
            self.graphicsGroup.setGraphicsEffect(self.effect)
            self.show()

        self.view.mainWindow.netDataLabel.setText('Sound Speed')
        
    def show(self):
        self.graphicsGroup.show()
        self.visible = True

    def hide(self):
        self.graphicsGroup.hide()
        self.visible = False

    def getColourForRatio(self, ratio):
        '''
        Select a colour between green and red to denote the probability of detection.
        '''
        if 0 < ratio <= 0.25:
            rgb = (49, 173, 0)
        if 0.25 < ratio <= 0.5: 
            rgb = (232, 228, 13)
        if 0.5 < ratio <= 0.75: 
            rgb = (232, 228, 13)
        else:
            rgb = (232, 11, 11)
             
        return rgb
