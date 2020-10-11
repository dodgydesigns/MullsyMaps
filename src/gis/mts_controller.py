import json
from math import trunc, floor, radians, sin, cos, atan2, sqrt, atan, tan
from urllib import request

from PySide2.QtCore import QPointF, Qt, QRect
from PySide2.QtWidgets import QGraphicsView
from bs4 import BeautifulSoup
from owslib.wms import WebMapService
import pyproj
from shapely.affinity import scale

import preferences

# tile size in pixels
TILE_DIMENSION = 256


def distanceBetweenTwoPoints(lat1, lon1, lat2, lon2):
    """
    Calculates the distance between two points.

    :Parameters:
      - `pointA: The tuple representing the latitude/longitude for the
        first point. Latitude and longitude must be in decimal degrees
      - `pointB: The tuple representing the latitude/longitude for the
        second point. Latitude and longitude must be in decimal degrees
    :Returns:
      The distance
    :Returns Type:
      float
    """
    # WGS 84
    a = 6378137.0
    f = 0.003352810681  # 1/298.25722210
    b = 6356752.314245  # meters; b = (1 - f)a

    MAX_ITERATIONS = 200
    CONVERGENCE_THRESHOLD = 1e-12  # .000,000,000,001

    U1 = atan((1 - f) * tan(radians(lat1)))
    U2 = atan((1 - f) * tan(radians(lat2)))
    L = radians(lon2 - lon1)
    Lambda = L

    sinU1 = sin(U1)
    cosU1 = cos(U1)
    sinU2 = sin(U2)
    cosU2 = cos(U2)

    for _ in range(MAX_ITERATIONS):
        sinLambda = sin(Lambda)
        cosLambda = cos(Lambda)
        sinSigma = sqrt((cosU2 * sinLambda) ** 2 +
                        (cosU1 * sinU2 - sinU1 * cosU2 * cosLambda) ** 2)
        if sinSigma == 0:
            return 0.0  # coincident points
        cosSigma = sinU1 * sinU2 + cosU1 * cosU2 * cosLambda
        sigma = atan2(sinSigma, cosSigma)
        sinAlpha = cosU1 * cosU2 * sinLambda / sinSigma
        cosSqAlpha = 1 - sinAlpha ** 2
        try:
            cos2SigmaM = cosSigma - 2 * sinU1 * sinU2 / cosSqAlpha
        except ZeroDivisionError:
            cos2SigmaM = 0
        C = f / 16 * cosSqAlpha * (4 + f * (4 - 3 * cosSqAlpha))
        LambdaPrev = Lambda
        Lambda = L + (1 - C) * f * sinAlpha * (sigma + C * sinSigma *
                                               (cos2SigmaM + C * cosSigma *
                                                (-1 + 2 * cos2SigmaM ** 2)))
        if abs(Lambda - LambdaPrev) < CONVERGENCE_THRESHOLD:
            break  # successful convergence
    else:
        return None  # failure to converge

    uSq = cosSqAlpha * (a ** 2 - b ** 2) / (b ** 2)
    A = 1 + uSq / 16384 * (4096 + uSq * (-768 + uSq * (320 - 175 * uSq)))
    B = uSq / 1024 * (256 + uSq * (-128 + uSq * (74 - 47 * uSq)))
    deltaSigma = B * sinSigma * (cos2SigmaM + B / 4 * (cosSigma *
                                                       (-1 + 2 * cos2SigmaM ** 2) - B / 6 * cos2SigmaM *
                                                       (-3 + 4 * sinSigma ** 2) * (-3 + 4 * cos2SigmaM ** 2)))
    s = b * A * (sigma - deltaSigma)

    return s


def angleBetweenTwoPoints(lat1, lon1, lat2, lon2):
    """
    Calculate the bearing from one location to another.
    """
    g = pyproj.Geod(ellps='WGS84')
    (az12, _, _) = g.inv(lon1, lat1, lon2, lat2)

    return az12


def vincentyDirect(phi1, lembda1, alpha12, s):
    """
    Returns the lat and long of projected point and reverse azimuth
    given a reference point and a distance and azimuth to project.
    lats, longs and azimuths are passed in decimal degrees
    Returns QPointF(phi2,  lambda2)
    Parameters:
    ===========
        f: flattening of the ellipsoid
        a: radius of the ellipsoid, metres
        phil: latitude of the start point, decimal degrees
        lembda1: longitude of the start point, decimal degrees
        alpha12: bearing, decimal degrees
        s: Distance to endpoint, meters
    NOTE: This code could have some license issues. It has been obtained
    from a forum and its license is not clear. I'll reimplement with
    GPL3 as soon as possible.
    The code has been taken from
    https://isis.astrogeology.usgs.gov/IsisSupport/index.php?topic=408.0
    and refers to (broken link)
    http://wegener.mechanik.tu-darmstadt.de/GMT-Help/Archiv/att-8710/Geodetic_py
    """
    two_sigma_m = 0
    a = 6378137.0
    f = 0.003352810681  # 1/298.25722210

    piD4 = atan(1.0)
    two_pi = piD4 * 8.0
    phi1 = phi1 * piD4 / 45.0
    lembda1 = lembda1 * piD4 / 45.0
    alpha12 = alpha12 * piD4 / 45.0
    if alpha12 < 0.0:
        alpha12 = alpha12 + two_pi
    if alpha12 > two_pi:
        alpha12 = alpha12 - two_pi
    b = a * (1.0 - f)
    TanU1 = (1 - f) * tan(phi1)
    U1 = atan(TanU1)
    sigma1 = atan2(TanU1, cos(alpha12))
    Sinalpha = cos(U1) * sin(alpha12)
    cosalpha_sq = 1.0 - Sinalpha * Sinalpha
    u2 = cosalpha_sq * (a * a - b * b) / (b * b)
    A = 1.0 + (u2 / 16384) * (4096 + u2 * (-768 + u2 * (320 - 175 * u2)))
    B = (u2 / 1024) * (256 + u2 * (-128 + u2 * (74 - 47 * u2)))
    # Starting with the approximate value
    sigma = (s / (b * A))
    last_sigma = 2.0 * sigma + 2.0  # something impossible

    # Iterate the following 3 equations until no sign change in sigma
    # two_sigma_m , delta_sigma
    while abs((last_sigma - sigma) / sigma) > 1.0e-9:
        two_sigma_m = 2 * sigma1 + sigma
        delta_sigma = B * sin(sigma) * (cos(two_sigma_m)
                                        + (B / 4) * (cos(sigma) *
                                                     (-1 + 2 * pow(cos(two_sigma_m), 2) -
                                                      (B / 6) * cos(two_sigma_m) *
                                                      (-3 + 4 * pow(sin(sigma), 2)) *
                                                      (-3 + 4 * pow(cos(two_sigma_m), 2)))))
        last_sigma = sigma
        sigma = (s / (b * A)) + delta_sigma
    phi2 = atan2((sin(U1) * cos(sigma) +
                  cos(U1) * sin(sigma) * cos(alpha12)),
                 ((1 - f) * sqrt(pow(Sinalpha, 2) +
                                 pow(sin(U1) * sin(sigma) - cos(U1) *
                                     cos(sigma) * cos(alpha12), 2))))
    lembda = atan2((sin(sigma) * sin(alpha12)),
                   (cos(U1) * cos(sigma) -
                    sin(U1) * sin(sigma) * cos(alpha12)))
    C = (f / 16) * cosalpha_sq * (4 + f * (4 - 3 * cosalpha_sq))
    omega = lembda - (1 - C) * f * Sinalpha * \
            (sigma + C * sin(sigma) * (cos(two_sigma_m) + C * cos(sigma) * (-1 + 2 * pow(cos(two_sigma_m), 2))))
    lambda2 = lembda1 + omega
    # alpha21 = atan2(Sinalpha, (-sin(U1) *
    #                            sin(sigma) + cos(U1) * cos(sigma) * cos(alpha12)))
    # alpha21 = alpha21 + two_pi / 2.0
    # if alpha21 < 0.0:
    #     alpha21 = alpha21 + two_pi
    # if alpha21 > two_pi:
    #     alpha21 = alpha21 - two_pi
    phi2 = phi2 * 45.0 / piD4
    lambda2 = lambda2 * 45.0 / piD4

    return QPointF(phi2, lambda2)


def tileToGeographic(tx, ty, zoom):
    """
    :param tx: floating point x coordinate, integer part is the tile number,
    decimal part is the proportion across that tile
    :param ty: floating point y coordinate, integer part is the tile number,
    decimal part is the proportion across that tile
    :param zoom:
    :return: Latitude and longitude in degrees
    :Note: x,y origin is bottom left, (lat, long) origin is map centre
    i.e. map is TL (85.05112877, -180) BR (-85.05112877, 180)
            Uses self.zoom as the current zoom level. There are 2^(zoom+1) x tiles and 2^(zoom) y tiles
    """
    znx = float(1 << (zoom + 1))
    lon = tx / znx * 360.0 - 180.0

    zny = float(1 << zoom)
    lat = ty / zny * 180.0 - 90.0

    return QPointF(lat, lon)


def geographicToTile(latitude, longitude, zoom):
    """
    :param latitude: world coordinates latitude (degrees)
    :param longitude: world coordinates longitude (degrees)
    :param zoom:
    :return: QPointF(x,y) tile coordinates. Integer part is the tile number,
    decimal part is the proportion across that tile
    :Note: x,y origin is bottom left, (lat, long) origin is map centre
    i.e. map is TL (85.05112877, -180) BR (-85.05112877, 180)
        Uses self.zoom as the current zoom level. There are 2^(zoom+1) x tiles and 2^(zoom) y tiles
    """
    zn = float(1 << zoom)
    tx = float(longitude + 180.0) / 360.0
    ty = float(latitude + 90.0) / 180.0

    return QPointF(tx * zn * 2, ty * zn)


class MTSController:

    def __init__(self, view, canvasSize, centreCoordinate):

        self.view = view
        self.canvasSize = canvasSize
        self.centreCoordinate = centreCoordinate
        self.view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setZoomBounds()
        self.panLimiter = 1
        self.tileZoomIndex = 1
        self.minZoom = 3
        self.maxZoom = 19
        self.centrePoint = None
        self.requiredTiles = None

        self.wfsLayers = {}
        self.aust = {}
        self.perth = {}
        self.bathy = {}
        self.climate = {}
        self.hydro = {}
        self.land = {}
        self.transport = {}
        self.allLayers = []
        self.layerParameters = {}

        self.getLayerParameters()
        self.getTiles()

    def getLayerParameters(self):

        if preferences.USE_GEOSERVER:
            contents = request.urlopen(
                'http://mullsysmedia.local:7070/geoserver/gwc/service/'
                'wmts?REQUEST=GetCapabilities&Version=2.0.0&TileMatrixSet=EPSG:4326').read()
            xml = BeautifulSoup(contents, features='xml')
            for layer in xml.find_all('Layer'):
                layerList = layer.find_all('Identifier')
                self.layerParameters[layerList[0].contents[0]] = {}
                if layer.Title.string == 'World':

                    tileMatrixSetLinks = layer.find_all('TileMatrixSetLink')
                    for tileMatrixSetLink in tileMatrixSetLinks:
                        tileMatrixSetLimits = tileMatrixSetLink.find_all('TileMatrixSetLimits')
                        for tileMatrixSetLimit in tileMatrixSetLimits:
                            tileMatrixLimits = tileMatrixSetLimit.find_all('TileMatrixLimits')
                            boundsForZoom = {}
                            for tileMatrixLimit in tileMatrixLimits:
                                zoom = tileMatrixLimit.find('TileMatrix').string.replace('EPSG:4326:', '')
                                bounds = {'MinTileRow': int(tileMatrixLimit.find('MinTileRow').string),
                                          'MaxTileRow': int(tileMatrixLimit.find('MaxTileRow').string),
                                          'MinTileCol': int(tileMatrixLimit.find('MinTileCol').string),
                                          'MaxTileCol': int(tileMatrixLimit.find('MaxTileCol').string)}
                                boundsForZoom[zoom] = bounds
                            self.layerParameters[layerList[0].contents[0]] = boundsForZoom

    def setZoomBounds(self):
        """
        This makes sure the tile graphics fill the available space and that we don't
        zoom further in than the tile data allows.
        """
        zoom = 3
        while (2 ** (zoom + 1) * TILE_DIMENSION) < self.canvasSize.width():
            zoom += 1
        self.minZoom = zoom

        self.tileZoomIndex = floor(self.view.vectorZoom)
        # Make sure not to exceed a reasonable zoom level to prevent pixelation.
        self.maxZoom = 19

    def addNavChartTemplate(self, layer):
        """ Not really a tile layer, just rectangles that outline and label each chart area. """
        self.land['Navigation Chart Outlines'] = layer

    def addLayer(self, tileLayerGroup, tileLayerName, tileLayer):
        """
        Add a tile layer that may fill the whole available area or just a small
        geographic location. Regardless, each layer will cover the whole world.
        """
        tileLayer.setGeometry(self.canvasSize.x(),
                              self.canvasSize.y(),
                              self.canvasSize.width(),
                              self.canvasSize.height())
        tileLayer.show() if tileLayer.visible else tileLayer.hide()
        if tileLayerGroup == 'aust':
            self.aust[tileLayerName] = tileLayer
        elif tileLayerGroup == 'perth':
            self.perth[tileLayerName] = tileLayer
        elif tileLayerGroup == 'bathy':
            self.bathy[tileLayerName] = tileLayer
        elif tileLayerGroup == 'climate':
            self.climate[tileLayerName] = tileLayer
        elif tileLayerGroup == 'hydro':
            self.hydro[tileLayerName] = tileLayer
        elif tileLayerGroup == 'land':
            self.land[tileLayerName] = tileLayer
        elif tileLayerGroup == 'transport':
            self.transport[tileLayerName] = tileLayer

        self.allLayers.append(tileLayer)

    def updateZoom(self):
        """
        As the vecor zoom changes, the required raster zoom may also change. This might
        cause a new set of tiles to be required so download them (or read from memory or
        disk cache) and disply.
        """
        self.tileZoomIndex = floor(self.view.vectorZoom)
        self.getTiles()
        self.update()

    def updateCentre(self, centre):
        """
        With each zoom, the centre location of the map must be updated so that the
        zoom occurs under the mouse.
        """
        self.centreCoordinate = centre
        self.getTiles()
        self.update()

    def updateCanvasSize(self, width, height):
        """
        If the size of the container holding the COP tiles is changed, the centre
        and therefore required tiles might change as well.
        """
        self.canvasSize = QRect(0, 0, width, height)
        self.update()

    def update(self):
        """ Download and render all layers based on current lat/lon, zoom and canvas size. """
        for tileLayer in self.allLayers:
            if tileLayer.visible:
                tileLayer.download()
                tileLayer.update()
        self.view.scene.update()
        self.view.mainWindow.stopProgressUpdateThread()

    def getTiles(self):
        """
        Based on the location of the mouse and the current raster zoom level,
        determine the bounds of the tiles that are required to be displayed.
        """
        self.centrePoint = geographicToTile(self.centreCoordinate.x(),
                                            self.centreCoordinate.y(),
                                            self.tileZoomIndex)

        left = trunc(self.centrePoint.x() - self.canvasSize.width() / (TILE_DIMENSION * 2))
        right = trunc(self.centrePoint.x() + self.canvasSize.width() / (TILE_DIMENSION * 2))
        bottom = trunc(self.centrePoint.y() - self.canvasSize.height() / (TILE_DIMENSION * 2))
        top = trunc(self.centrePoint.y() + self.canvasSize.height() / (TILE_DIMENSION * 2))

        self.requiredTiles = {'left': left,
                              'right': right,
                              'top': top,
                              'bottom': bottom}

    def getBoundary(self):
        """ The lat/lon of the visible map. """
        return QRect(self.requiredTiles['left'],
                     self.requiredTiles['top'],
                     (self.requiredTiles['right'] - self.requiredTiles['left']) * 256,
                     (self.requiredTiles['top'] - self.requiredTiles['bottom']) * 256)

    def toCanvasCoordinates(self, lat, lng):
        """ Convert canvas x, y to geographic lat/lon. """
        tcX = self.requiredTiles['left']
        tcY = self.requiredTiles['top']
        offsetX = self.canvasSize.width() / 2 - (self.centrePoint.x() - tcX) * TILE_DIMENSION
        offsetY = self.canvasSize.height() / 2 + (self.centrePoint.y() - (tcY + 1)) * TILE_DIMENSION

        pt = geographicToTile(lat, lng, self.tileZoomIndex)

        x = ((pt.x() - self.requiredTiles['left']) * TILE_DIMENSION) + offsetX
        y = ((self.requiredTiles['top'] - pt.y() + 1) * TILE_DIMENSION) + offsetY

        return QPointF(x, y)

    def toGeographicalCoordinates(self, x, y):
        """
        Convert a given canvas x,y coordinate into latitude/longitude.
        """
        tcX = self.requiredTiles['left']
        tcY = self.requiredTiles['top']
        offsetX = self.canvasSize.width() / 2 - (self.centrePoint.x() - tcX) * TILE_DIMENSION
        offsetY = self.canvasSize.height() / 2 + (self.centrePoint.y() - (tcY + 1)) * TILE_DIMENSION

        ptX = ((x - offsetX) / TILE_DIMENSION) + self.requiredTiles['left']
        ptY = 1 + self.requiredTiles['top'] - ((y - offsetY) / TILE_DIMENSION)

        pt = tileToGeographic(ptX, ptY, self.tileZoomIndex)

        return QPointF(pt.x(), pt.y())

    def depthAtLatLon(self, lat, lon):
        """
        Uses bathymetric heightmap database from GeoServer to determine depth at a location.
        """
        wms = WebMapService('http://{}:{}/geoserver/wms'.format(preferences.GEOSERVER_IP, preferences.GEOSERVER_PORT))
        response = wms.getfeatureinfo(layers=['Oceanographic:World_Bathymetric_Heightmap'],
                                      srs='EPSG:4326',
                                      bbox=(lon, lat - 1.1096191406, lon + 1.1096191406, lat),
                                      # 1.1096191406 is a magic number
                                      size=(self.canvasSize.width(), self.canvasSize.height()),
                                      format='image/jpeg',
                                      query_layers=['Oceanographic:World_Bathymetric_Heightmap'],
                                      info_format='application/json',
                                      xy=(50, 50))
        info = json.loads(response.read())

        return info['features'][0]['properties']['Elevation_relative_to_sea_level']

    def moveToGeographicLocation(self, lat, lon):
        """
        Moves the map at the current zoom level to the location specified.
        """
        self.centreCoordinate = QPointF(lat, lon)
        self.updateCentre(self.centreCoordinate)

    def moveToCanvasLocation(self, x, y):
        """
        Moves the map at the current zoom level to the location specified.
        """
        pt = tileToGeographic(x, y, self.tileZoomIndex)
        self.centreCoordinate = QPointF(pt.x(), pt.y())
        self.updateCentre(self.centreCoordinate)

    ''' ------------------------------------------------------------------------------------------------
                                            MOUSE/KEYBOARD FUNCTIONS
        ------------------------------------------------------------------------------------------------ '''

    def keyPressEvent(self, event):
        """
        Allow arrow keys for panning..
        """
        if event.key() == Qt.Key_Left:
            self.centreCoordinate = QPointF(self.centreCoordinate.x(),
                                            self.centreCoordinate.y() - (self.tileZoomIndex / 100))
            self.updateCentre(self.centreCoordinate)
        if event.key() == Qt.Key_Right:
            self.centreCoordinate = QPointF(self.centreCoordinate.x(),
                                            self.centreCoordinate.y() + (self.tileZoomIndex / 100))
            self.updateCentre(self.centreCoordinate)
        if event.key() == Qt.Key_Up:
            self.centreCoordinate = QPointF(self.centreCoordinate.x() + (self.tileZoomIndex / 100),
                                            self.centreCoordinate.y())
            self.updateCentre(self.centreCoordinate)
        if event.key() == Qt.Key_Down:
            self.centreCoordinate = QPointF(self.centreCoordinate.x() - (self.tileZoomIndex / 100),
                                            self.centreCoordinate.y())
            self.updateCentre(self.centreCoordinate)

        self.updateCanvasSize(self.canvasSize.width(), self.canvasSize.height())
        self.view.scene.update()

    def keyReleaseEvent(self, event):
        pass

    def wheelEvent(self, event):
        """
        Only used for zooming.
        """
        if self.minZoom < self.view.vectorZoom < self.maxZoom:
            currentTileZoomIndex = self.tileZoomIndex
            eventDelta = event.delta()
            if eventDelta > 0:
                if eventDelta > 120:
                    eventDelta = 120
                self.view.vectorZoom *= (1 + (eventDelta / 120) * 0.01)
                newScale = 1 + (self.view.vectorZoom % floor(self.view.vectorZoom))

            else:
                if eventDelta < -120:
                    eventDelta = -120
                self.view.vectorZoom *= (1 + (eventDelta / 120) * 0.01)
                newScale = self.view.vectorZoom % floor(self.view.vectorZoom)

            self.tileZoomIndex = floor(self.view.vectorZoom)

            if currentTileZoomIndex != floor(self.view.vectorZoom):
                self.updateZoom()
                self.view.annotationLayers.updateZoom(newScale)

        self.view.update()

    def mouseMoveEvent(self, event):
        pass

    def mousePressEvent(self, event):
        pass

    def mouseReleaseEvent(self, event):
        pass

    def dragEnterEvent(self, event):
        pass

    def moveMap(self, delta):
        """
        Allow panning of map.
        """
        # 2.4 is good but slow
        factor = 2.0
        panRestrictor = factor ** self.view.vectorZoom
        dxDy = QPointF(delta)
        self.centreCoordinate = QPointF(self.centreCoordinate.x() + dxDy.y() / panRestrictor,
                                        self.centreCoordinate.y() - dxDy.x() / panRestrictor)
        self.updateCentre(self.centreCoordinate)

        self.view.update()
