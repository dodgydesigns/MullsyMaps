from PySide2.QtCore import QObject
from PySide2.QtSvg import QGraphicsSvgItem

from graphics.mil_std_icon import MilStdIcon


class UIObject(QObject):
    """
    Abstract class of a UI element that represents an entity type: OwnShip, Contact, Solution.
    """

    def __init__(self, map, designation, affiliation, classification, x, y, speed, course):
        """
        Constructor
        """
        super(UIObject, self).__init__()
        self.map = map
        self.icon = QGraphicsSvgItem(str(MilStdIcon(affiliation, classification).getIconPath()), parent = None)
        self.decorators = {}
        self.designation = designation
        self.affiliation = affiliation
        self.classification = classification
        self.x = x
        self.y = y  
        self.lat = self.map.mapController.toGeographicalCoordinates(self.x, self.y).x()
        self.lon = self.map.mapController.toGeographicalCoordinates(self.x, self.y).y()
        self.vectorZoom = map.vectorZoom
        self.visible = True
        self.speed = speed
        self.course = course
        self.previousCourse = course
        
    def drawSpiroPolygons(self):
        
        pass
    
    def update(self):
        
        pass
    
    def showHide(self):
        
        pass
    
    def zoom(self):
        
        pass

    def showMetaDialog(self):
        """
        Shows a dialog with information about this object when it is clicked.
        """
        pass

    def hideMetaDialog(self):
        """
        Hide the meta-data dialog when some other object is clicked.
        """
        pass 

    def locationLabel(self):
        """
        Generates a pretty version of the lat/lon of an entity for display in the meta-data dialog.
        """
        if self.lat < 0:
            xText = '{0:.2f}°S'.format(-self.lat)
        else:
            xText = '{0:.2f}°N'.format(self.lat)
            
        if self.lon < 0:
            yText = '{0:.2f}°W'.format(-self.lon)
        else:
            yText = '{0:.2f}°E'.format(self.lon)
            
        return '{0:}, {1:}'.format(xText, yText)