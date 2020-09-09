'''
Created on 6 Aug. 2020

@author: mullsy
'''
import os
from pathlib import Path

        # Use GeoServer for COP data.
USE_GEOSERVER = True
GEOSERVER_IP = "192.168.1.112"#"127.0.0.1"#HOME:"192.168.1.122" #SRCE:"10.57.88.65" #"172.16.130.133"
GEOSERVER_PORT = "7070"
           
# Commonly used relative paths for COP
COMMON_ROOT = Path(os.path.dirname("./"))
CACHE_PATH = str(Path.home()) + '/cache'

APP_PATH = os.getcwd()
ICON_PATH = '../images/'
DEFAULT_CACHE_PATH = Path(COMMON_ROOT / '../default_cache')

DISTANCE_UNITS_LOW = 'm'
DISTANCE_UNITS_HIGH = 'km'

##-------------------------------- Constants --------------------------------------
SCENARIO_LAT_LNG = [-32.12673, 115.25]
VESSEL_OWNSHIP_ID = -1


AFFILIATION_UNKNOWN = 0
AFFILIATION_NEUTRAL = 1
AFFILIATION_FRIENDLY = 2
AFFILIATION_HOSTILE = 3
AFFILIATION_CIVILIAN = 4
    
# Constants for the COP
ZVALUE_Oceanographic    = 100
ZVALUE_GISLayers        = 200
ZVALUE_Navigation       = 300
ZVALUE_Annotations      = 400
ZVALUE_WFS              = 500
ZVALUE_Icons            = 600
ZVALUE_Ownship          = 700
ZVALUE_MetaDialogs      = 800
 
OWNSHIP = 'OWNSHIP'
 
DIMENSION_SEA_SURFACE = 'surface'
DIMENSION_SUB_SEA_SURFACE = 'sub_surface'
 
# FUNCTION_PASSENGER = 'passenger'                        #S_SPXMP
FUNCTION_MERCHANT = 'Merchant A'                          #S_SPXM
FUNCTION_MERCHANT_B = 'Merchant B'                        #S_SPXM
FUNCTION_MERCHANT_C = 'Merchant C'                        #S_SPXM
FUNCTION_WARSHIP = 'Warship A'                            #S_SPCL
# FUNCTION_CARRIER = 'carrier'                            #S_SPCLCV
FUNCTION_FISHING = 'Fishing A'                            #S_SPXF
FUNCTION_SUBMARINE = 'Submarine'                          #S_UPSNA
# FUNCTION_SUB_CONVENTIONAL = 'sub_conventional'          #N_PSCA
 
SHIPWRECK = 'WA_Shipwrecks'
CITY = 'Places'
PORT = 'Ports'
AIRPORT = 'Airports'
  
ICON = 'Icon'
HISTORICAL_COURSE = 'Historical Course'
PREDICTED_COURSE = 'Predicted Course'
ANNOTATIONS = 'Annotations'
CERTAINTY_CIRCLE = 'Certainty Circle'
 
RECTANGLE = 'rectangle'
CIRCLE = 'circle'
POLYLINE = 'polyline'
TEXT = 'text'
 
CERTAINTY_CIRCLE_SCALE = 50
ANNOTATIONSSCALE = 20
METADIALOGSCALE = 1
BREADCRUMB_PEN = 1
ICON_SCALE = 0.2
PREDICTED_COURSE_SCALE = 10
CIRCLE_PEN = 1
 
DISTANCE_MARKERS = 'Distance Markers'
FIVE_KY_RADIUS = 1
TEN_KY_RADIUS = 2
FIFTEEN_KY_RADIUS = 3
TWENTY_KY_RADIUS = 4
TWENTYFIVE_KY_RADIUS = 5

LOW_SENSITIVITY = 'Low'
MEDIUM_SENSITIVITY = 'Medium'
HIGH_SENSITIVITY = 'High'