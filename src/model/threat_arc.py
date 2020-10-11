"""
Created on 12 Sep. 2018

@author: mullsy
"""
from math import atan2, pi, degrees

from PySide2.QtCore import QPointF, Qt, QPoint
from PySide2.QtGui import QPainterPath, QPen, QFont, QColor
from PySide2.QtWidgets import QWidget, QGraphicsPathItem, QGraphicsItemGroup, \
    QLabel

import preferences

TEXTBOX_SCALE = 3
THREAT_ARC_SCALE = 1


class ThreatArc(QWidget):

    def __init__(self, view, designation, reportedLat, reportedLon, toi, course, speed, eir, *args, **kwargs):
        """
        Draw an arc on the map relative to ownShip that shows a reported threat.
        designation
        reportedX, reportedY
        toi: Time of Intercept - when the threat was detected.
        course, speed
        eir: Expected in Range - based on course, speed.
        """
        super().__init__(*args, **kwargs)
        self.view = view
        self.designation = designation
        self.reportedLat = reportedLat
        self.reportedLon = reportedLon
        self.reportedLocationOnCanvas = None
        self.toi = toi
        self.course = course
        self.speed = speed
        self.eir = eir

        self.visible = True
        self.graphicsGroup = None
        self.metaDialogProxy = None

        self.draw()

    def draw(self):
        """
        Clear any existing graphics item and drawSpiroPolygons at the appropriate location.
        """
        if self.graphicsGroup is not None:
            self.view.scene.removeItem(self.graphicsGroup)

        self.reportedLocationOnCanvas = self.view.mapController.toCanvasCoordinates(self.reportedLat, self.reportedLon)

        path = QPainterPath()
        path.quadTo(QPointF(35, -35),
                    QPointF(45, 0))

        arc = QGraphicsPathItem(path)
        angleToOwnship = atan2(self.view.ownShip.y - self.reportedLocationOnCanvas.y(),
                               self.view.ownShip.x - self.reportedLocationOnCanvas.x()) - pi / 2
        arc.setPos(self.reportedLocationOnCanvas.x(), self.reportedLocationOnCanvas.y())
        arc.setRotation(degrees(angleToOwnship))
        arc.setPen(QPen(Qt.red, THREAT_ARC_SCALE))
        self.view.scene.addItem(arc)

        text = self.view.scene.addText(self.designation + '\n' +
                                       'Time of Intercept:\t' + str(self.toi) + 'Z\n' +
                                       'Course:\t\t\t' + str(self.course) + '°\n' +
                                       'Speed:\t\t\t' + str(self.speed) + 'KT\n' +
                                       'Expected in Range:\t' + str(self.eir) + 'MIN\n',
                                       QFont("Arial", 24))
        if self.view.vectorZoom <= 7:
            text.hide()
        else:
            text.setScale(TEXTBOX_SCALE / 10)
        text.setDefaultTextColor(QColor('red'))

        if angleToOwnship < 0:
            angleToOwnship += 2 * pi
        if 0 < angleToOwnship <= pi / 2:
            text.setPos(self.reportedLocationOnCanvas.x() - 100, self.reportedLocationOnCanvas.y())
        elif pi / 2 < angleToOwnship <= pi:
            text.setPos(self.reportedLocationOnCanvas.x() - 120, self.reportedLocationOnCanvas.y())
        elif pi < angleToOwnship <= 1.5 * pi:
            text.setPos(self.reportedLocationOnCanvas.x() + 15, self.reportedLocationOnCanvas.y() - 50)
        elif 1.5 * pi < angleToOwnship <= 2 * pi:
            text.setPos(self.reportedLocationOnCanvas.x() + 20, self.reportedLocationOnCanvas.y() - 30)

        self.graphicsGroup = QGraphicsItemGroup(scene=self.view.scene)
        self.view.scene.addItem(self.graphicsGroup)
        self.graphicsGroup.setZValue(preferences.ZVALUE_MetaDialogs)
        self.graphicsGroup.addToGroup(arc)
        self.graphicsGroup.addToGroup(text)

    def show(self):
        self.graphicsGroup.show()
        self.visible = True

    def hide(self):
        self.graphicsGroup.hide()
        self.visible = False

    def showHideMetaDialog(self, showMetaDialog):
        """
        Shows a dialog with information about this object when it is clicked.
        """
        if showMetaDialog:
            metadata = self.designation
            metadata += '\n' + u'\u2501' + u'\u2501' + u'\u2501' + u'\u2501' + u'\u2501' + u'\u2501' + '\n'
            metadata += 'Time of Intercept: ' + str(self.toi) + ' Z\n' + \
                        'Course: ' + str(self.course) + ' °\n' + \
                        'Speed: ' + str(self.speed) + ' KT\n' + \
                        'Expected in Range: ' + str(self.eir) + ' MIN\n'
            text = metadata.rstrip('\n')

            metaDialog = QLabel(text)
            metaDialog.move(QPoint(self.reportedLocationOnCanvas.x(), self.reportedLocationOnCanvas.y()))
            metaDialog.setStyleSheet(""" QLabel {color: rgb(255,255,255);
                                                 background-color: rgba(0,0,0,50);
                                                 padding: 5px;
                                                 border: 1px solid white;}
                                          """)
            self.metaDialogProxy = self.view.scene.addWidget(metaDialog)
            self.metaDialogProxy.setZValue(preferences.ZVALUE_MetaDialogs)
            self.metaDialogProxy.setScale(preferences.METADIALOGSCALE)
        else:
            self.metaDialogProxy.hide()
