from math import sqrt

from PySide2.QtCore import Qt
from PySide2.QtGui import QPolygonF, QColor, QPen, QBrush
from PySide2.QtWidgets import QGraphicsItemGroup

import preferences

SEGMENT_ANGLE = 20  # how many segments in a Spirograph


class SpirographSegment:
    def __init__(self, polygonLatLonList, segmentCentreLatLon, proxy):

        self.polygonLatLonList = polygonLatLonList
        self.segmentCentreLatLon = segmentCentreLatLon
        self.soundSpeed = -1
        self.soundSpeedColour = (0, 0, 0)
        self.proxy = proxy

    def fillWithColourForRatio(self, ratio):
        """
        Select a colour between green and red to denote the probability of detection.
        """
        if 0 <= ratio <= 0.25:
            rgb = (49, 173, 0)
        elif 0.25 < ratio <= 0.5:
            rgb = (232, 228, 13)
        elif 0.5 < ratio <= 0.75:
            rgb = (232, 228, 13)
        else:
            rgb = (232, 11, 11)

        self.proxy.setBrush(QBrush(QColor(rgb[0], rgb[1], rgb[2])))
        self.soundSpeedColour = rgb

    def refillWithColourForRatio(self):
        self.proxy.setBrush(
            QBrush(QColor(self.soundSpeedColour[0], self.soundSpeedColour[1], self.soundSpeedColour[2])))


class Spirograph:
    """
    This class encompasses all the segments that make up the probability of detection circle.
    """

    def __init__(self, view, centreLatLon, rangeOfTheDayRadiusLatLon, multiplier):

        self.view = view
        self.centreLatLon = centreLatLon
        self.view = view
        self.rangeOfTheDayRadiusLatLon = rangeOfTheDayRadiusLatLon
        self.multiplier = multiplier
        self.spiroSegmentList = []
        self.zoomIndex = 1
        self.maxDepth = 155
        self.spiroSegmentGraphicsGroup = QGraphicsItemGroup()
        self.rangeOfTheDayRadiusXY = 0
        self.newCentreXY = 0

    def drawSpiroPolygons(self):
        """ Draws the outline of each segment required to create a Spirograph. """

        self.spiroSegmentGraphicsGroup.setZValue(preferences.ZVALUE_MetaDialogs + 1)
        self.view.scene.addItem(self.spiroSegmentGraphicsGroup)

        self.newCentreXY = self.view.mapController.toCanvasCoordinates(self.centreLatLon.x(),
                                                                       self.centreLatLon.y())

        self.rangeOfTheDayRadiusXY = self.view.mapController.toCanvasCoordinates(self.rangeOfTheDayRadiusLatLon.x(),
                                                                                 self.rangeOfTheDayRadiusLatLon.y())
        diameter = (sqrt((self.newCentreXY.x() - self.rangeOfTheDayRadiusXY.x()) ** 2 +
                         (self.newCentreXY.y() - self.rangeOfTheDayRadiusXY.y()) ** 2) / self.multiplier) * 4
        diameter *= self.zoomIndex

        # Divide a circle into SEGMENT_ANGLE pie pieces and then radiusDivisor number of co-centric circles to form 
        # a shape that approximates a cirlcel made of individual polygons that will be coloured based on the 
        # speed of sound each polygon's region.
        for radiusDivisor in range(2, 6):
            for angle in range(0, 360, SEGMENT_ANGLE):
                innerCCWSegmentLatLon = self.view.mapController.vincentyDirect(self.rangeOfTheDayRadiusLatLon.x(),
                                                                               self.rangeOfTheDayRadiusLatLon.y(),
                                                                               angle - (0.5 * SEGMENT_ANGLE),
                                                                               (radiusDivisor - 1) ** 2 * diameter * 2)
                innerCCWSegmentXY = self.view.mapController.toCanvasCoordinates(innerCCWSegmentLatLon.x(),
                                                                                innerCCWSegmentLatLon.y())
                innerCWSegmentLatLon = self.view.mapController.vincentyDirect(self.rangeOfTheDayRadiusLatLon.x(),
                                                                              self.rangeOfTheDayRadiusLatLon.y(),
                                                                              angle + (0.5 * SEGMENT_ANGLE),
                                                                              (radiusDivisor - 1) ** 2 * diameter * 2)
                innerCWSegmentXY = self.view.mapController.toCanvasCoordinates(innerCWSegmentLatLon.x(),
                                                                               innerCWSegmentLatLon.y())

                outerCCWSegmentLatLon = self.view.mapController.vincentyDirect(self.rangeOfTheDayRadiusLatLon.x(),
                                                                               self.rangeOfTheDayRadiusLatLon.y(),
                                                                               angle - (0.5 * SEGMENT_ANGLE),
                                                                               radiusDivisor ** 2 * diameter * 2)
                outerCCWSegmentXY = self.view.mapController.toCanvasCoordinates(outerCCWSegmentLatLon.x(),
                                                                                outerCCWSegmentLatLon.y())
                outerCWSegmentLatLon = self.view.mapController.vincentyDirect(self.rangeOfTheDayRadiusLatLon.x(),
                                                                              self.rangeOfTheDayRadiusLatLon.y(),
                                                                              angle + (0.5 * SEGMENT_ANGLE),
                                                                              radiusDivisor ** 2 * diameter * 2)
                outerCWSegmentXY = self.view.mapController.toCanvasCoordinates(outerCWSegmentLatLon.x(),
                                                                               outerCWSegmentLatLon.y())

                segmentCentreLatLon = self.view.mapController.vincentyDirect(self.rangeOfTheDayRadiusLatLon.x(),
                                                                             self.rangeOfTheDayRadiusLatLon.y(),
                                                                             angle,
                                                                             radiusDivisor ** 2 * diameter * 0.9)

                polyPoints = QPolygonF([outerCCWSegmentXY,
                                        outerCWSegmentXY,
                                        innerCWSegmentXY,
                                        innerCCWSegmentXY])
                polygon = self.view.scene.addPolygon(polyPoints)
                penCol = QColor(Qt.black)
                penCol.setAlphaF(0.3)
                polygon.setPen(QPen(penCol))
                polygon.setZValue(preferences.ZVALUE_MetaDialogs - 1)
                polygon.setOpacity(0.4)
                spiroSegment = SpirographSegment({'a': outerCCWSegmentLatLon,
                                                  'b': outerCWSegmentLatLon,
                                                  'c': innerCWSegmentLatLon,
                                                  'd': innerCCWSegmentLatLon},
                                                 segmentCentreLatLon,
                                                 polygon)
                self.spiroSegmentGraphicsGroup.addToGroup(polygon)
                self.spiroSegmentList.append(spiroSegment)

    def redrawSpiroPolygons(self):

        for segment in self.spiroSegmentList:
            self.spiroSegmentGraphicsGroup.removeFromGroup(segment.proxy)
            self.view.scene.removeItem(segment.proxy)

        for segment in self.spiroSegmentList:
            innerCCWSegmentXY = self.view.mapController.toCanvasCoordinates(segment.polygonLatLonList['b'].x(),
                                                                            segment.polygonLatLonList['b'].y())
            innerCWSegmentXY = self.view.mapController.toCanvasCoordinates(segment.polygonLatLonList['a'].x(),
                                                                           segment.polygonLatLonList['a'].y())
            outerCCWSegmentXY = self.view.mapController.toCanvasCoordinates(segment.polygonLatLonList['c'].x(),
                                                                            segment.polygonLatLonList['c'].y())
            outerCWSegmentXY = self.view.mapController.toCanvasCoordinates(segment.polygonLatLonList['d'].x(),
                                                                           segment.polygonLatLonList['d'].y())

            polyPoints = QPolygonF([outerCCWSegmentXY,
                                    outerCWSegmentXY,
                                    innerCWSegmentXY,
                                    innerCCWSegmentXY])
            polygon = self.view.scene.addPolygon(polyPoints)
            penCol = QColor(Qt.black)
            penCol.setAlphaF(0.3)
            polygon.setPen(QPen(penCol))
            polygon.setBrush(
                QColor(segment.soundSpeedColour[0], segment.soundSpeedColour[1], segment.soundSpeedColour[2]))
            polygon.setZValue(preferences.ZVALUE_MetaDialogs - 1)
            polygon.setOpacity(0.4)
            segment.proxy = polygon
            self.spiroSegmentGraphicsGroup.addToGroup(polygon)

    def clearSpiroPolygons(self):
        """ Make every segment in a Spirograph transparent so it can be redrawn and re-coloured. """
        for segment in self.spiroSegmentList:
            segment.soundSpeed = 0
            segment.proxy.setBrush(QBrush(Qt.transparent))
