import os
from urllib import request

from PySide2.QtCore import QRect, Qt, QThread
from PySide2.QtGui import QImage, QPixmap, QPainter, QPen
from PySide2.QtWidgets import QWidget

import preferences

TILE_DIMENSION = 256


class TileKey:
    """ This is used for identifying the required tile and help with caching. """

    def __init__(self, tileZoomIndex, x, y):
        self.tileZoomIndex = tileZoomIndex
        self.x = x
        self.y = y

    def key(self):
        return '{}_{}_{}'.format(self.tileZoomIndex, self.x, self.y)

    def __hash__(self):
        return hash((self.tileZoomIndex, self.x, self.y))

    def __eq__(self, other):
        return (self.tileZoomIndex, self.x, self.y) == (other.tileZoomIndex, other.x, other.y)

    def __ne__(self, other):
        return not (self == other)


class ShowHiddenLayer(QThread):
    """ Updating the map takes a long time and blocks the GUI so put it in a separate thread. """

    def __init__(self):
        QThread.__init__(self)
        self.called = False
        self.controller = None

    def setController(self, controller):
        self.controller = controller

    def run(self):
        if not self.called:
            self.update()

    def update(self):
        self.controller.update()
        self.called = True


class MTSLayer(QWidget):
    """
    This holds all the tiles for a TMS (Tile Map Service) layer together. Each layer can then be controlled
    i.e. pan, zoom, hide via the MTSController.
    """

    def __init__(self, view, workspace, layerName, zLevel, visible, opacity):
        super(MTSLayer, self).__init__()

        self.setStyleSheet("background: transparent")
        self.setMouseTracking(True)

        self.drawGrid = False

        self.view = view
        self.controller = self.view.mapController
        self.workspace = workspace
        self.layerName = layerName
        self.visible = visible
        self.opacity = opacity
        self.zLevel = zLevel
        self.tilePixmaps = {}
        self.download()
        self.handle = self.view.scene.addWidget(self)
        self.proxyControl = self.view.scene.addRect(500, 500, 10, 10)
        self.proxyControl.setPen(QPen(Qt.transparent))
        self.handle.setParentItem(self.proxyControl)

        self.showHiddenLayer = ShowHiddenLayer()
        self.showHiddenLayer.setController(self.controller)

        self.painter = QPainter()

    def download(self):

        if not self.visible:
            return  # TODO: check if obscured by another higher z layer -> dont show
        for xTile in range(self.controller.requiredTiles['left'], self.controller.requiredTiles['right'] + 1):
            for yTile in range(self.controller.requiredTiles['bottom'], self.controller.requiredTiles['top'] + 1):
                layerParameters = self.controller.layerParameters[self.workspace + ':' + self.layerName]
                # Some layers don't have capabilities details so just use World bounds
                if len(layerParameters) == 0:
                    bounds = self.controller.layerParameters['land:World'][str(self.controller.tileZoomIndex)]
                else:
                    bounds = layerParameters[str(self.controller.tileZoomIndex)]
                if bounds['MinTileCol'] < xTile < bounds['MaxTileCol'] and \
                        bounds['MinTileRow'] < yTile < bounds['MaxTileRow']:
                    grab = TileKey(self.controller.tileZoomIndex, xTile, yTile)
                    if grab not in self.tilePixmaps:
                        if preferences.USE_GEOSERVER:
                            tilePath = f'{preferences.CACHE_PATH}{os.sep}' + \
                                       self.layerName + \
                                       os.sep + \
                                       str(grab.tileZoomIndex) + \
                                       os.sep + \
                                       str(grab.x) + \
                                       os.sep
                        else:
                            tilePath = f'{preferences.DEFAULT_CACHE_PATH}{os.sep}' + \
                                       self.layerName + \
                                       os.sep + \
                                       str(grab.tileZoomIndex) + \
                                       os.sep + \
                                       str(grab.x) + \
                                       os.sep
                        fullTilePath = tilePath + str(grab.y) + '.png'
                        if os.path.exists(fullTilePath):
                            self.tilePixmaps[grab] = QPixmap(fullTilePath)
                        elif preferences.USE_GEOSERVER:
                            path = 'http://{}:{}/geoserver/'.format(preferences.GEOSERVER_IP,
                                                                    preferences.GEOSERVER_PORT) + \
                                   'gwc/' + \
                                   'service/' + \
                                   'tms/' + \
                                   '1.0.0/' + \
                                   self.workspace + ':' + \
                                   self.layerName + \
                                   '@EPSG:4326' + \
                                   '@png' + \
                                   '/{}/{}/{}.png'.format(grab.tileZoomIndex, grab.x, grab.y)
                            try:
                                contents = request.urlopen(path).read()
                                img = QImage.fromData(contents, "PNG")
                                pic = QPixmap.fromImage(img)
                                self.tilePixmaps[grab] = pic
                                if not os.path.exists(tilePath):
                                    os.makedirs(tilePath)
                                pic.save(fullTilePath, 'png')
                                # self.view.mainWindow.startProgressUpdateThread()
                                print('downloading: {}/{}/{}/{}.png'.format(self.layerName,
                                                                            grab.tileZoomIndex,
                                                                            grab.x,
                                                                            grab.y))
                            except Exception as e:
                                print('DL error: {} -- {}'.format(path, e))

    def paintEvent(self, event):
        """ Override to allow transparency. """
        self.painter.begin(self)
        self.painter.setOpacity(self.opacity)
        self.render()
        self.painter.end()

    def render(self):
        """
        This takes whatever tiles are in the range of tiles for GPS coordinates and fills them IF
        the tile lies within the the canvas size.
        """
        width = self.controller.canvasSize.width()
        height = self.controller.canvasSize.height()
        for tileKey, pic in self.tilePixmaps.items():
            # only draw if it's in the visible map
            if self.controller.requiredTiles['left'] <= tileKey.x <= self.controller.requiredTiles['right'] and \
                    self.controller.requiredTiles['bottom'] <= tileKey.y <= self.controller.requiredTiles['top']:
                tcX = self.controller.requiredTiles['left']
                tcY = self.controller.requiredTiles['top']
                offsetX = width / 2 - (self.controller.centrePoint.x() - tcX) * TILE_DIMENSION
                offsetY = height / 2 + (self.controller.centrePoint.y() - (tcY + 1)) * TILE_DIMENSION

                xPos = (tileKey.x - self.controller.requiredTiles['left']) * TILE_DIMENSION
                yPos = (self.controller.requiredTiles['top'] - tileKey.y) * TILE_DIMENSION
                box = QRect(xPos + offsetX, yPos + offsetY, TILE_DIMENSION, TILE_DIMENSION)
                self.painter.drawPixmap(box, pic)

    def showHide(self, showHide):
        """ Show or hide this layer."""
        self.visible = True if showHide == 'show' else False
        if self.visible:
            self.showHiddenLayer.run()
            self.show()
        else:
            self.hide()

    def setOpacity(self, opacity):
        """ Change the level of opacity for this layer. """
        self.opacity = opacity / 100
        self.view.scene.update()

    def setLayerZLevel(self, zLevel):
        """ Change the z level for this layer. """
        self.zLevel = zLevel
        self.proxyControl.setZValue(zLevel)
        self.view.scene.update()
