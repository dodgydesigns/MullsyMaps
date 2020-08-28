from PySide2.QtCore import QObject
import requests

from model.feature import Feature
import preferences


class WFS(QObject):
    '''
    Manages all the data required for a Web Feature Service layer. This typically consists of point data
    for features such as ports, airport and cities.
    '''
    def __init__(self, view):
        '''
        Constructor
        '''
        self.view = view
        self.layers = {}

    def getAirports(self):

        features = []
        response = requests.get('http://{}:{}/geoserver/wfs?'.format(preferences.GEOSERVER_IP, preferences.GEOSERVER_PORT) + \
                                'SERVICE=wfs&' + \
                                'VERSION=1.1.0&' + \
                                'REQUEST=GetFeature&' + \
                                'TYPENAME=Landmarks:Aust_Airports&' + \
                                'outputFormat=json  ')
        responseDict = response.json()
        for dictLists in responseDict['features']:
            level0 = dictLists['geometry']['coordinates']
            lat = float(level0[1])
            lon = float(level0[0])
            name = dictLists['properties']['name_en']
            
            newFeature = Feature(view=self.view,
                                 layerName='Aust_Airports',
                                 meta={'title': 'Landmarks:Austtralian Airports',
                                       'Name': '{}: '.format(name),
                                       'Location': '{:.2f}, {:.2f}: '.format(lat, lon)},
                                 lat=lat,
                                 lon=lon,
                                 iconPath=str(preferences.ICON_PATH / "airport.svg"),
                                 iconScale=10)    

            features.append(newFeature)
        self.layers['Australian Airports'] = features
        return features
    
    def getPorts(self):

        features = []
        response = requests.get('http://{}:{}/geoserver/wfs?'.format(preferences.GEOSERVER_IP, preferences.GEOSERVER_PORT) + \
                                'SERVICE=wfs&' + \
                                'VERSION=1.1.0&' + \
                                'REQUEST=GetFeature&' + \
                                'TYPENAME=Landmarks:Aust_Ports&' + \
                                'outputFormat=json')
        responseDict = response.json()
        for dictLists in responseDict['features']:
            level0 = dictLists['geometry']['coordinates']
            lat = float(level0[1])
            lon = float(level0[0])
            name = dictLists['properties']['PORT_NAME']
             
            newFeature = Feature(view=self.view,
                                 layerName='Aust_Ports',
                                 meta={'title': 'Landmarks:Australian Ports',
                                       'Name': '{}: '.format(name),
                                       'Location': '{:.2f}, {:.2f}: '.format(lat, lon)},
                                 lat=lat,
                                 lon=lon,
                                 iconPath=str(preferences.ICON_PATH / "port.svg"),
                                 iconScale=0.5)    
 
            features.append(newFeature)
        self.layers['Australian Ports'] = features
        return features
    
    def getCities(self):

        features = []
        response = requests.get('http://{}:{}/geoserver/wfs?'.format(preferences.GEOSERVER_IP, preferences.GEOSERVER_PORT) + \
                                'SERVICE=wfs&' + \
                                'VERSION=1.1.0&' + \
                                'REQUEST=GetFeature&' + \
                                'TYPENAME=Landmarks:Aust_Cities&' + \
                                'outputFormat=json')
        responseDict = response.json()
        for dictLists in responseDict['features']:
            level0 = dictLists['geometry']['coordinates']
            lat = float(level0[1])
            lon = float(level0[0])
            name = dictLists['properties']['name']
            state = dictLists['properties']['adm1name'] 
            country = dictLists['properties']['adm0name']  
            population = dictLists['properties']['pop_max'] 
            
            newFeature = Feature(view=self.view,
                                 layerName='Aust_Cities',
                                 meta={'title': 'Landmarks:Aust_Cities',
                                       'Name': '{}: '.format(name),
                                       'Country': '{}: '.format(country),
                                       'State': '{}: '.format(state),
                                       'Population': '{}: '.format(population),
                                       'Location': '{:.2f}, {:.2f}: '.format(lat, lon)},
                                 lat=lat,
                                 lon=lon,
                                 iconPath=str(preferences.ICON_PATH / "city.svg"),
                                 iconScale=0.5)    
 
            features.append(newFeature)
        self.layers['Cities'] = features
        return features
    
    def getLayerFeatures(self, layerName):
        return self.layers[layerName]
    
    def drawSpiroPolygons(self, layerName):
        for feature in self.layers[layerName]:
            feature.drawSpiroPolygons()
    
    def update(self, layerName):
        for feature in self.layers[layerName]:
            feature.update()

            
            
            
            
            