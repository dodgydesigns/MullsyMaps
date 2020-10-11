from PySide2.QtSvg import QGraphicsSvgItem
from PySide2.QtWidgets import QLabel

import preferences


class Feature(QGraphicsSvgItem):
    """
    This represents a Web Feature Service (WFS) item on the map. It consists of an icon (SVG) that when clicked,
    displays a dialog with some information about the Feature.
    """

    def __init__(self, view, layerName, meta, lat, lon, iconPath, iconScale):
        """
        Constructor
        """
        QGraphicsSvgItem.__init__(self, str(iconPath), parent=None)
        self.view = view
        self.metadata = ''
        self.metaDialogProxy = None
        self.processMetadata(meta)

        self.layerName = layerName
        self.visible = True
        self.lat = lat
        self.long = lon
        self.iconScale = iconScale / 3

    def draw(self):
        self.scaleIcon(self.iconScale)
        self.setZValue(preferences.ZVALUE_WFS)
        self.view.scene.addItem(self)
        canvasPoint = self.view.mapController.toCanvasCoordinates(self.lat, self.long)
        self.setPos(canvasPoint)

    def update(self):
        canvasPoint = self.view.mapController.toCanvasCoordinates(self.lat, self.long)
        self.setPos(canvasPoint)

    def scaleIcon(self, scale):
        self.iconScale = scale / 3
        self.setScale(self.iconScale)

    def processMetadata(self, meta):
        """
        Tidy up the text for Feature pop-up dialogs.
        """
        for key, data in meta.items():
            if key == 'title':
                self.metadata += data.split(':')[1]
                self.metadata += '\n' + u'\u2501' + u'\u2501' + u'\u2501' + u'\u2501' + u'\u2501' + u'\u2501' + '\n'
            else:
                self.metadata += '{} {}\n'.format(key, data)

    def showHideMetaDialog(self, showMetaDialog):

        if showMetaDialog:
            text = self.metadata.rstrip('\n')
            metaDialog = QLabel(text)
            metaDialog.setStyleSheet("""QLabel {color: rgb(255,255,255);
                                                background-color: rgba(0,0,0,150);
                                                padding: 5px;
                                                border: 1px solid white;}
                                        """)
            self.metaDialogProxy = self.view.scene.addWidget(metaDialog)
            self.metaDialogProxy.setZValue(preferences.ZVALUE_MetaDialogs)
            self.metaDialogProxy.setScale(preferences.METADIALOGSCALE)
            canvasPoint = self.view.mapController.toCanvasCoordinates(self.lat, self.long)
            self.metaDialogProxy.setPos(canvasPoint)
        else:
            self.metaDialogProxy.hide()
