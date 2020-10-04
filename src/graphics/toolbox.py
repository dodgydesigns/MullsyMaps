import collections
import os

from PySide2.QtCore import Qt
from PySide2.QtGui import QColor, QPainter, QIcon
from PySide2.QtWidgets import QFrame, QWidget, QSpacerItem, \
    QSizePolicy, QTabWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, \
    QSpinBox, QCheckBox, QHeaderView, QPushButton, \
    QHBoxLayout, QMainWindow, QDockWidget

from graphics.paint.annotation_tool import PaintToolBox
import preferences

APP_PATH = os.getcwd()
WIDTH = 400
HEIGHT = 600

SPINBOXSTYLE = """
                QSpinBox::up-button { width: 32px; }
                QSpinBox::down-button { width: 32px; }
"""


class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)


class CustomTreeItem(QTreeWidgetItem):
    """
    Custom QTreeWidgetItem with Widgets
    """

    def __init__(self, toolbox, parent, name):
        """
        parent (QTreeWidget) : Item's QTreeWidget parent.
        """
        super(CustomTreeItem, self).__init__(parent)

        self.opacity = 1
        self.visible = True
        self.zLevel = 1

        itemLayout = QHBoxLayout()
        itemLayout.setSpacing(0)
        itemLayout.setMargin(0)
        itemWidget = QWidget()
        itemWidget.setFixedHeight(30)
        itemWidget.setFixedWidth(WIDTH - 100)
        itemWidget.setLayout(itemLayout)
        self.check = QCheckBox()
        self.check.setText('{}'.format(name))
        self.check.setFixedWidth(200)
        itemLayout.addWidget(self.check)

        self.opacitySpinBox = QSpinBox()
        self.opacitySpinBox.setMaximum(100)
        self.opacitySpinBox.setMinimum(0)
        self.opacitySpinBox.setSingleStep(10)
        self.opacitySpinBox.setValue(100)
        self.opacitySpinBox.setStyleSheet(SPINBOXSTYLE)
        itemLayout.addWidget(self.opacitySpinBox)

        upDownWidget = QWidget()
        upDownWidget.setStyleSheet("""
                                    QWidget {
                                                margin: 0px;
                                                padding: 0px;
                                    }
        """)
        upDownWidget.setFixedHeight(22)
        self.upButton = QPushButton()
        self.upButton.setIcon(QIcon(preferences.ICON_PATH + '/button_up.svg'))
        self.downButton = QPushButton()
        self.downButton.setIcon(QIcon(preferences.ICON_PATH + '/button_down.svg'))
        buttonLayout = QVBoxLayout()
        buttonLayout.setSpacing(0)
        buttonLayout.setMargin(0)
        buttonLayout.addWidget(self.upButton)
        buttonLayout.addWidget(self.downButton)
        upDownWidget.setLayout(buttonLayout)
        itemLayout.addWidget(upDownWidget)

        self.treeWidget().setItemWidget(self, 0, itemWidget)

        self.check.toggled.connect(lambda: toolbox.showHideLayers(self, self.check.isChecked()))
        self.opacitySpinBox.valueChanged.connect(lambda: toolbox.changeLayerOpacity(self, self.opacitySpinBox.value()))
        self.downButton.clicked.connect(lambda: toolbox.moveLayerDown(self))
        self.upButton.clicked.connect(lambda: toolbox.moveLayerUp(self))

    def setChecked(self, checked):
        self.check.setCheckState(checked)

    def setOpacityValue(self, opacity):
        self.opacitySpinBox.setValue(100 * opacity)

    def setZLevelValue(self, zLevel):
        self.parent().insertChild(zLevel, self)


class Toolbox(QWidget):
    """
    Holder for the tabBox widget.
    """

    def __init__(self, map):
        super(Toolbox, self).__init__()

        self.map = map
        layout = QVBoxLayout()
        self.tabBox = TabBox(self, map)
        self.tabBox.setStyleSheet('''QWidget { background: transparent; }''')
        layout.addWidget(self.tabBox)
        layout.addStretch(-1)
        self.setLayout(layout)
        self.setFixedWidth(WIDTH)  # Limits horizontal size to enable map interaction on right.

    def updateEntries(self):
        self.tabBox.updateEntries()

    def createOwnshipMenu(self):
        self.tabBox.createOwnshipMenu()

    def createAnnotationsMenu(self):
        self.tabBox.createAnnotationsMenu()

    def paintEvent(self, event):
        """ Allows transparent widgets. """
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))


class TabBox(QTabWidget):

    def __init__(self, parent, view):

        super(TabBox, self).__init__()
        self.currentChanged.connect(self.tabChange)

        self.view = view
        self.parent = parent

        self.layersTab = QWidget()
        self.annotationsTab = QWidget()
        self.toolsWidget = None
        self.tacticalPictureTree = None
        self.annotationsTree = None

        self.bathyTree = None
        self.climateTree = None
        self.hydroTree = None
        self.landTree = None
        self.transportTree = None

        self.ownshipMenu = None
        self.ownshipEntity = None
        self.contactsMenu = None
        self.layersLayout = QVBoxLayout()

        self.addTab(self.layersTab, 'Layers')
        self.addTab(self.annotationsTab, 'Annotations')
        self.layersTree = QTreeWidget(self.layersTab)
        self.enableLayers(['Contacts', 'Tactical Picture', 'Landmarks', 'Navigation', 'Annotations',
                           'Bathymetric', 'Climate', 'Hydrographic', 'Landmass', 'Transport'])

        self.createOwnshipMenu()
        self.createMenus()

        self.layersTree.setFixedWidth(WIDTH)
        self.layersTree.setFixedHeight(HEIGHT - 20)
        self.layersTree.setStyleSheet('''
                                        QTreeView::branch:has-siblings:!adjoins-item {
                                            border-image: url(''' + preferences.ICON_PATH + '''vline.png) 0;
                                        }
                                        QTreeView::branch:has-siblings:adjoins-item {
                                            border-image: url(''' + preferences.ICON_PATH + '''branch-more.png) 0;
                                        }
                                        QTreeView::branch:!has-children:!has-siblings:adjoins-item {
                                            border-image: url(''' + preferences.ICON_PATH + '''branch-end.png) 0;
                                        }
                                        QTreeView::branch:has-children:!has-siblings:closed,
                                        QTreeView::branch:closed:has-children:has-siblings {
                                            border-image: none;
                                            image: url(''' + preferences.ICON_PATH + '''branch-closed.png);
                                        }
                                        QTreeView::branch:open:has-children:!has-siblings,
                                        QTreeView::branch:open:has-children:has-siblings  {
                                            border-image: none;
                                            image: url(''' + preferences.ICON_PATH + '''branch-open.png);
                                        }
                                        QTreeView::item { color: white }
        ''')

        self.setWindowTitle("Toolbox")
        closeButton = QPushButton('')
        closeButton.setIcon(QIcon(preferences.ICON_PATH + 'close-window.svg'))
        closeButton.clicked.connect(self.closeToolBox)
        self.setCornerWidget(closeButton, Qt.TopRightCorner)

    def tabChange(self, index):
        """ Enable drawing when on the Annotations tab otherwise, disable. """
        if self.tabText(index) == 'Annotations':
            self.view.currentlyDrawing = True
            self.createAnnotationsMenu()
            self.parent.setFixedWidth(200)
        else:
            self.view.currentlyDrawing = False
            self.updateAnnotationsLayers()
            self.parent.setFixedWidth(WIDTH)

    def closeToolBox(self):
        self.view.mainWindow.showHideToolBox()

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 15))

    def updateEntries(self):
        """
        Update the trees that contain suspected and known entities.
        """
        self.updateContactsTrees()
        self.updateAnnotationsLayers()

    def enableLayers(self, visibleLayers):

        self.layersTree.setHeaderHidden(True)
        self.tacticalPictureTree = QTreeWidgetItem(self.layersTree)
        self.tacticalPictureTree.setText(0, 'Tactical Picture')
        if 'Tactical Picture' not in visibleLayers:
            self.tacticalPictureTree.setHidden(True)

        self.annotationsTree = QTreeWidgetItem(self.layersTree)
        self.annotationsTree.setText(0, 'Annotations')
        if 'Annotations' not in visibleLayers:
            self.annotationsTree.setHidden(True)

        self.bathyTree = QTreeWidgetItem(self.layersTree)
        self.bathyTree.setText(0, 'Bathymetric')
        if 'Bathymetric' not in visibleLayers:
            self.bathyTree.setHidden(True)

        self.climateTree = QTreeWidgetItem(self.layersTree)
        self.climateTree.setText(0, 'Climate')
        if 'Climate' not in visibleLayers:
            self.climateTree.setHidden(True)

        self.hydroTree = QTreeWidgetItem(self.layersTree)
        self.hydroTree.setText(0, 'Hydrographic')
        if 'Hydrographic' not in visibleLayers:
            self.hydroTree.setHidden(True)

        self.landTree = QTreeWidgetItem(self.layersTree)
        self.landTree.setText(0, 'Landmass')
        if 'Landmass' not in visibleLayers:
            self.landTree.setHidden(True)

        self.transportTree = QTreeWidgetItem(self.layersTree)
        self.transportTree.setText(0, 'Transport')
        if 'Transport' not in visibleLayers:
            self.transportTree.setHidden(True)

        # self.nav = QTreeWidgetItem(self.layersTree)
        # self.landTree.setText(0, 'Navigation')
        # self.layersTree.addTopLevelItem(self.landTree)
        # if 'Navigation' not in visibleLayers:
        #     self.landTree.setHidden(True)

        header = self.layersTree.header()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)

    def createOwnshipMenu(self):

        if self.view.ownship is not None:
            self.ownshipEntity = self.view.ownship

            ownshipEntry = QTreeWidgetItem(self.ownshipMenu)
            ownshipEntry.setText(0, 'All Layers')
            ownshipEntry.setCheckState(0, Qt.Checked if self.ownshipEntity.visible else Qt.Unchecked)
            self.layersTree.itemClicked.connect(self.showHideLayers)

            # Qt.ItemIsSelectable | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsDragEnabled
            for layerName, layer in self.ownshipEntity.graphicsLayers.items():
                child = QTreeWidgetItem(ownshipEntry)
                child.setFlags(child.flags() | Qt.ItemIsDragEnabled)
                child.setText(0, layerName)
                child.setCheckState(0, Qt.Checked if layer.visible else Qt.Unchecked)

    def createContactsMenu(self):

        self.ownshipMenu = QTreeWidgetItem(self.tacticalPictureTree)
        self.ownshipMenu.setText(0, 'Ownship')

        self.contactsMenu = QTreeWidgetItem(self.tacticalPictureTree)
        self.contactsMenu.setText(0, 'Contacts')

    def createGisMenu(self):

        for key, layer in self.view.mapController.bathy.items():
            gisLayer = CustomTreeItem(self, self.bathyTree, key)
            gisLayer.setFlags(gisLayer.flags() | Qt.ItemIsDragEnabled)
            gisLayer.setChecked(Qt.Checked if layer.visible else Qt.Unchecked)
            gisLayer.setZLevelValue(layer.zLevel)

        for key, layer in self.view.mapController.climate.items():
            gisLayer = CustomTreeItem(self, self.climateTree, key)
            gisLayer.setChecked(Qt.Checked if layer.visible else Qt.Unchecked)
            gisLayer.setOpacityValue(layer.opacity)
            gisLayer.setZLevelValue(layer.zLevel)

        for key, layer in self.view.mapController.hydro.items():
            gisLayer = CustomTreeItem(self, self.hydroTree, key)
            gisLayer.setChecked(Qt.Checked if layer.visible else Qt.Unchecked)
            gisLayer.setZLevelValue(layer.zLevel)

        for key, layer in self.view.mapController.land.items():
            gisLayer = CustomTreeItem(self, self.landTree, key)
            gisLayer.setChecked(Qt.Checked if layer.visible else Qt.Unchecked)
            gisLayer.setZLevelValue(layer.zLevel)

        for key, layer in self.view.mapController.transport.items():
            gisLayer = CustomTreeItem(self, self.transportTree, key)
            gisLayer.setChecked(Qt.Checked if layer.visible else Qt.Unchecked)
            gisLayer.setZLevelValue(layer.zLevel)

    def updateGisLayers(self):

        for cb in [self.drawGisCheckboxes(key) for key in self.view.mapController.bathy]:
            self.gisLayersLayout.addWidget(cb)

        for cb in [self.drawGisCheckboxes(key) for key in self.mapController.climate]:
            self.gisLayersLayout.addWidget(cb)

        for cb in [self.drawGisCheckboxes(key) for key in self.mapController.hydro]:
            self.gisLayersLayout.addWidget(cb)

        for cb in [self.drawGisCheckboxes(key) for key in self.mapController.land]:
            self.gisLayersLayout.addWidget(cb)

    def createTacticalMenu(self):

        for key, layer in self.view.tacticalLayers.items():
            tacticalLayer = QTreeWidgetItem(self.annotationsTree)
            tacticalLayer.setFlags(tacticalLayer.flags() | Qt.ItemIsDragEnabled)
            tacticalLayer.setText(0, key)
            tacticalLayer.setCheckState(0, Qt.Checked if layer.visible else Qt.Unchecked)
            self.layersTree.itemClicked.connect(self.showHideLayers)

    def createAnnotationsMenu(self):
        if len(self.view.annotationLayers.layers) == 0:
            self.createNewAnnotationLayer()
        else:
            self.enableActiveAnnotationLayer()

    def createNewAnnotationLayer(self):
        """
        Drawing tool
        """
        paintLayout = QVBoxLayout()
        paintWindow = QMainWindow()
        paintLayout.addWidget(paintWindow)

        toolsDock = QDockWidget("COP Annotator", self)
        toolsDock.topLevelChanged.connect(lambda: self.setFloatWindow(toolsDock))
        toolsDock.setFeatures(QDockWidget.DockWidgetFloatable |
                              QDockWidget.DockWidgetMovable)
        toolsDock.setFloating(False)

        layerName = 'Local-{}'.format(len(self.view.annotationLayers.layers) + 1)
        self.view.annotationLayers.addAnnotationLayer(layerName)
        self.view.annotationLayers.activeLayerName = layerName

        self.view.annotationLayers.layers[layerName].initialise()
        self.view.annotationLayers.layers[layerName].setMouseTracking(True)
        self.view.annotationLayers.layers[layerName].setFocusPolicy(Qt.StrongFocus)

        toolsWidget = PaintToolBox(self, self.view.annotationLayers.layers['Local-1'])
        toolsDock.setWidget(toolsWidget)
        paintWindow.addDockWidget(Qt.RightDockWidgetArea, toolsDock)

        self.annotationsTab.setLayout(paintLayout)
        self.annotationsTab.setAttribute(Qt.WA_TranslucentBackground)

    def enableActiveAnnotationLayer(self):
        paintLayout = QVBoxLayout()
        paintWindow = QMainWindow()
        paintLayout.addWidget(paintWindow)

        toolsDock = QDockWidget("COP Annotator", self)
        toolsDock.topLevelChanged.connect(lambda: self.setFloatWindow(toolsDock))
        toolsDock.setFeatures(QDockWidget.DockWidgetFloatable |
                              QDockWidget.DockWidgetMovable)
        toolsDock.setFloating(False)

        toolsWidget = PaintToolBox(self, self.view.annotationLayers.layers[self.view.annotationLayers.activeLayerName])
        toolsDock.setWidget(toolsWidget)
        paintWindow.addDockWidget(Qt.RightDockWidgetArea, toolsDock)

        self.annotationsTab.setLayout(paintLayout)
        self.annotationsTab.setAttribute(Qt.WA_TranslucentBackground)

    def setFloatWindow(self, td):
        td.setStyleSheet('''QDockWidget {background: rgb(255, 255, 255); 
                                         color: rgb(0, 0, 0);}''')
        td.setFixedWidth(200)
        layerName = 'Local-{}'.format(self.view.annotationLayers.annotationLayerCount)
        toolsWidget = PaintToolBox(self.view.annotationLayers.layers[layerName])
        td.setWidget(toolsWidget)

        self.createNewAnnotationLayer()

    def updateAnnotationsLayers(self):
        """ Make sure all the annotation layers are visible in the menu tree. """
        if not self.annotationsTree:
            return

        # Clear the contents of the contact trees to keep synchronised with model
        for i in reversed(range(self.annotationsTree.childCount())):
            self.annotationsTree.removeChild(self.annotationsTree.child(i))

        for key, layer in self.view.annotationLayers.layers.items():
            annotationEntry = QTreeWidgetItem(self.annotationsTree)
            annotationEntry.setFlags(annotationEntry.flags() | Qt.ItemIsDragEnabled)
            annotationEntry.setText(0, key)
            annotationEntry.setCheckState(0, Qt.Checked if layer.visible else Qt.Unchecked)
            self.layersTree.itemClicked.connect(self.showHideLayers)

    def disableAnnotationLayers(self):
        """ Stop drawing. """
        for layer in self.view.annotationLayers.layers.values():
            layer.disableAnnotations()

    def createMenus(self):

        self.createContactsMenu()
        self.createGisMenu()
        self.createTacticalMenu()

        verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.layersLayout.addItem(verticalSpacer)
        self.layersTab.setLayout(self.layersLayout)

    def clearTacticalLayer(self):
        """ Delete all user drawings. """
        self.view.tacticalLayers.graphics.clear()

    def updateContactsTrees(self):
        """
        This propagates the contact tree with all the contacts.
        """
        # Clear the contents of the contact trees to keep synchronised with model
        for i in reversed(range(self.contactsMenu.childCount())):
            self.contactsMenu.removeChild(self.contactsMenu.child(i))

        for entityDesignation, entity in self.view.contacts.items():
            if entityDesignation != self.view.ownShip.designation:
                entityEntry = QTreeWidgetItem(self.contactsMenu)
                entityEntry.setText(0, str(entityDesignation))
                entityEntry.setCheckState(0, Qt.Checked if entity.visible else Qt.Unchecked)
                entityEntry.setFlags(entityEntry.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
                self.layersTree.itemClicked.connect(self.showHideLayers)

                for layerName, layer in entity.graphicsLayers.items():
                    child = QTreeWidgetItem(entityEntry)
                    child.setFlags(child.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
                    child.setText(0, layerName)
                    child.setCheckState(0, Qt.Checked if layer.visible else Qt.Unchecked)

    def moveLayerUp(self, item):
        """
        Moves tree items up in the list and raises their Z-Level.
        """
        selectionRow = self.layersTree.indexFromItem(item).row()
        parent = item.parent()
        if selectionRow > 0:
            clickedIndex = parent.indexOfChild(item)
            newIndex = clickedIndex - 1

            taken = {}
            for childIndex in range(parent.childCount() - 1, -1, -1):
                taken[childIndex] = parent.takeChild(childIndex)

            clicked = taken[clickedIndex]
            above = taken[newIndex]

            taken[newIndex] = clicked
            taken[clickedIndex] = above

            od = collections.OrderedDict(sorted(taken.items()))
            for index, child in od.items():
                newCustomTreeItem = CustomTreeItem(self, parent, child.check.text())
                newCustomTreeItem.setOpacityValue(child.opacitySpinBox.value())
                newCustomTreeItem.setChecked(Qt.Checked if child.check.isChecked() else Qt.Unchecked)
                parent.insertChild(index, newCustomTreeItem)
                if index == clickedIndex:
                    self.changeLayerZLevel(child, parent, -1)
                elif index == newIndex:
                    self.changeLayerZLevel(child, parent, 1)
                else:
                    self.changeLayerZLevel(child, parent, 0)

    def moveLayerDown(self, item):
        """
        Moves tree items down in the list and lowers their Z-Level.
        """
        selectionRow = self.layersTree.indexFromItem(item).row()
        parent = item.parent()

        if selectionRow < parent.childCount():
            clickedIndex = parent.indexOfChild(item)
            newIndex = clickedIndex + 1

            taken = {}
            for childIndex in range(parent.childCount() - 1, -1, -1):
                taken[childIndex] = parent.takeChild(childIndex)

            clicked = taken[clickedIndex]
            above = taken[newIndex]

            taken[newIndex] = clicked
            taken[clickedIndex] = above

            od = collections.OrderedDict(sorted(taken.items()))
            for index, child in od.items():
                newCustomTreeItem = CustomTreeItem(self, parent, child.check.text())
                newCustomTreeItem.setOpacityValue(child.opacitySpinBox.value())
                newCustomTreeItem.setChecked(Qt.Checked if child.check.isChecked() else Qt.Unchecked)
                parent.insertChild(index, newCustomTreeItem)
                if index == clickedIndex:
                    self.changeLayerZLevel(child, parent, 1)
                elif index == newIndex:
                    self.changeLayerZLevel(child, parent, -1)
                else:
                    self.changeLayerZLevel(child, parent, 0)

    def showHideLayers(self, item, checked):
        """
        Show and hide layers.
        """
        if item.parent() is not None:
            if item.parent().text(0) == 'Tactical Picture':
                if item.checkState(0) == Qt.Checked:
                    self.view.tacticalLayers[item.text(0)].showHide('show')
                elif item.checkState(0) == Qt.Unchecked:
                    self.view.tacticalLayers[item.text(0)].showHide('hide')

            elif item.parent().text(0) == 'Navigation':
                if checked:
                    self.view.mapController.land[item.check.text()].showHide('show')
                elif item.checkState(0) == Qt.Unchecked:
                    self.view.mapController.land[item.check.text()].showHide('hide')
            elif item.parent().text(0) == 'Annotations':
                self.view.annotationLayers.activeLayerName = item.text(0)
                self.view.annotationLayers.zoomToLayer(item.text(0))
                if item.checkState(0) == Qt.Checked:
                    self.view.annotationLayers.layers[item.text(0)].showHide('show')
                elif item.checkState(0) == Qt.Unchecked:
                    self.view.annotationLayers.layers[item.text(0)].showHide('hide')

            elif item.parent().text(0) == 'Bathymetric':
                if checked:
                    self.view.mapController.bathy[item.check.text()].showHide('show')
                elif item.checkState(0) == Qt.Unchecked:
                    self.view.mapController.bathy[item.check.text()].showHide('hide')
            elif item.parent().text(0) == 'Climate':
                if checked:
                    self.view.mapController.climate[item.check.text()].showHide('show')
                elif item.checkState(0) == Qt.Unchecked:
                    self.view.mapController.climate[item.check.text()].showHide('hide')
            elif item.parent().text(0) == 'Hydrographic':
                if checked:
                    self.view.mapController.hydro[item.check.text()].showHide('show')
                elif item.checkState(0) == Qt.Unchecked:
                    self.view.mapController.hydro[item.check.text()].showHide('hide')
            elif item.parent().text(0) == 'Landmass':
                if checked:
                    self.view.mapController.land[item.check.text()].showHide('show')
                elif item.checkState(0) == Qt.Unchecked:
                    self.view.mapController.land[item.check.text()].showHide('hide')
            elif item.parent().text(0) == 'Transport':
                if checked:
                    self.view.mapController.transport[item.check.text()].showHide('show')
                elif item.checkState(0) == Qt.Unchecked:
                    self.view.mapController.transport[item.check.text()].showHide('hide')

            # Show/Hide entity layer
            elif item.parent().text(0) in self.view.contacts:
                if item.checkState(0) == Qt.Checked:
                    self.view.contacts[item.parent().text(0)].showHideLayer(item.text(0), 'show')
                elif item.checkState(0) == Qt.Unchecked:
                    self.view.contacts[item.parent().text(0)].showHideLayer(item.text(0), 'hide')

            if item.parent().parent() is not None:
                # Show/Hide ownShip or ownShip layer
                if item.parent().text(0) == 'Ownship' or item.parent().parent().text(0) == 'Ownship':
                    if item.checkState(0) == Qt.Checked:
                        self.ownshipEntity.showHide(item.text(0), 'show')
                    elif item.checkState(0) == Qt.Unchecked:
                        self.ownshipEntity.showHide(item.text(0), 'hide')

                if item.parent().parent().text(0) == 'Contacts':
                    if item.checkState(0) == Qt.Checked:
                        self.view.contacts[int(item.parent().text(0))].showHide(item.text(0), 'show')
                    elif item.checkState(0) == Qt.Unchecked:
                        self.view.contacts[int(item.parent().text(0))].showHide(item.text(0), 'hide')

                if item.parent().text(0) == 'Contacts':
                    if item.checkState(0) == Qt.Checked:
                        self.view.contacts[int(item.text(0))].showHide('All Layers', 'show')
                    else:
                        self.view.contacts[int(item.text(0))].showHide('All Layers', 'hide')

    def changeLayerOpacity(self, item, opacity):
        """ Change the transparency of a layer. """
        if item.parent() is not None:
            if item.parent().text(0) == 'Navigation':
                self.view.mapController.land[item.check.text()].setOpacity(opacity)
            elif item.parent().text(0) == 'Bathymetric':
                self.view.mapController.bathy[item.check.text()].setOpacity(opacity)
            elif item.parent().text(0) == 'Climate':
                self.view.mapController.climate[item.check.text()].setOpacity(opacity)
            elif item.parent().text(0) == 'Hydrographic':
                self.view.mapController.hydro[item.check.text()].setOpacity(opacity)
            elif item.parent().text(0) == 'Landmass':
                self.view.mapController.land[item.check.text()].setOpacity(opacity)
            elif item.parent().text(0) == 'Transport':
                self.view.mapController.transport[item.check.text()].setOpacity(opacity)

    def changeLayerZLevel(self, child, parent, zLevel):
        """ Raise above or lower a layer with respect to the other layers. """
        if parent is not None:
            if parent.text(0) == 'Navigation':
                layer = self.view.mapController.land[child.check.text()]
                layer.setLayerZLevel(layer.zLevel + zLevel)
            elif parent.text(0) == 'Bathymetric':
                layer = self.view.mapController.bathy[child.check.text()]
                layer.setLayerZLevel(layer.zLevel + zLevel)
            elif parent.text(0) == 'Climate':
                layer = self.view.mapController.climate[child.check.text()]
                layer.setLayerZLevel(layer.zLevel + zLevel)
            elif parent.text(0) == 'Hydrographic':
                layer = self.view.mapController.hydro[child.check.text()]
                layer.setLayerZLevel(layer.zLevel + zLevel)
            elif parent.text(0) == 'Landmass':
                layer = self.view.mapController.land[child.check.text()]
                layer.setLayerZLevel(layer.zLevel + zLevel)
            elif parent.text(0) == 'Transport':
                layer = self.view.mapController.transport[child.check.text()]
                layer.setLayerZLevel(layer.zLevel + zLevel)