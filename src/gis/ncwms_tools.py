import urllib.request

from cachetools import cached, TTLCache

import preferences
import xml.etree.ElementTree as ET


soundSpeedCache = TTLCache(maxsize=1000, ttl=300)
depthCache = TTLCache(maxsize=1000, ttl=300)

class NCWMSTools():
    '''
    These tools are used to interrogate an ncWMS or NetCDF data source and return values that can be used, 
    for example, to determine the speed of sound at a specified location and depth.
    '''
    def __init__(self, view):
        '''
        Constructor
        '''
        self.view = view

        self.maxDepth = 155
        self.visible = True

        canvasRect = view.mapToScene(view.viewport().geometry()).boundingRect()
        self.width = int(canvasRect.width())
        self.height = int(canvasRect.height())
        self.lonMin = view.mapController.toGeographicalCoordinates(canvasRect.x(), 0).y()
        self.lonMax = view.mapController.toGeographicalCoordinates(canvasRect.x()+canvasRect.width(), 0).y()
        self.latMax = view.mapController.toGeographicalCoordinates(canvasRect.x(), 0).x()
        self.latMin = view.mapController.toGeographicalCoordinates(canvasRect.x(), 0+canvasRect.height()).x()
        
    def getMaxDepth(self, latLonList):
        ''' Use the getDepth() function to determine the maximum depth of a location. '''
        dataList = []

        for latLon in latLonList:
            xy = self.view.mapController.toCanvasCoordinates(latLon.x(), latLon.y())
            depth = self.getDepth(xy.x(), xy.y())
            if depth > 1:
                dataList.append(depth)
                
        # it is possible that there are no data points available e.g. over land.
        if len(dataList) > 0:
            self.maxDepth = max(dataList)
        
        return self.maxDepth
        
    @cached(depthCache)
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
            print('NCWMSTools.getDepth {}'.format(xmlRequest))
        return depth
 
    @cached(soundSpeedCache)
    def getSoundSpeedForPoint(self, depth, x, y):
        
        '''
        Get the probability of detection based on the current depth for a certain location.
        '''
        speed = -1
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
                     'ELEVATION={}'.format(depth)
        try:
#             print(xmlRequest)
            url = urllib.request.urlopen(xmlRequest)
            tree = ET.fromstring(url.read())
            speed = float(tree.findall("./Feature/FeatureInfo/value")[0].text)
        except:
            print('NCWMSTools.getSoundSpeedForPoint {}'.format(xmlRequest))
        return speed
