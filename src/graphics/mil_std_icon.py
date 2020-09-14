'''
Created on 30 Aug. 2018

@author: mullsy
'''
import os
import preferences

class MilStdIcon(object):
    '''
    Uses Affiliation and classification to generate the appropriate Mil-Std-2525D iconography.
    Icons are SVG (vectors) so will display and scale nicely.
    '''
    def __init__(self, affiliation, classification):
        '''
        Constructor
        '''

        self.iconPath = str(preferences.ICON_PATH)

        if affiliation is None:
            self.affiliation = preferences.AFFILIATION_UNKNOWN
        else:
            self.affiliation = affiliation
            
        if classification is None:
            self.classification = preferences.FUNCTION_WARSHIP
        else:
            self.classification = classification
            
    def getIconPath(self):

        if self.classification == preferences.OWNSHIP:
            self.iconPath = self.iconPath + "ownShip.svg"
            
#         elif self.affiliation == preferences.AFFILIATION_Unknown:
#             self.iconPath = str(preferences.ICON_PATH) + os.sep + 'mil2525' + os.sep
#             if self.classification == enums.FUNCTION_MERCHANT or \
#                self.classification == enums.FUNCTION_MERCHANT_B or \
#                self.classification == enums.FUNCTION_MERCHANT_C:
#                 self.iconPath = self.iconPath + "SUSPXM------.svg"
#             elif self.classification == enums.FUNCTION_WARSHIP:
#                 self.iconPath = self.iconPath + "SUSPCL------.svg"
#             elif self.classification == enums.FUNCTION_FISHING:
#                 self.iconPath = self.iconPath + "SUSPXF------.svg"
#             elif self.classification == enums.FUNCTION_SUBMARINE:
#                 self.iconPath = self.iconPath + "SUUPSNA-----.svg"
#                     
#         elif self.affiliation == preferences.AFFILIATION_Friendly:
#             self.iconPath = str(preferences.ICON_PATH) + os.sep + 'mil2525' + os.sep
#             if self.classification == enums.FUNCTION_MERCHANT or \
#                self.classification == enums.FUNCTION_MERCHANT_B or \
#                self.classification == enums.FUNCTION_MERCHANT_C:
#                 self.iconPath = self.iconPath + "SFSPXM------.svg"
#             elif self.classification == enums.FUNCTION_WARSHIP:
#                 self.iconPath = self.iconPath + "SFSPCL------.svg"
#             elif self.classification == enums.FUNCTION_FISHING:
#                 self.iconPath = self.iconPath + "SFSPXF------.svg"
#             elif self.classification == enums.FUNCTION_SUBMARINE:
#                 self.iconPath = self.iconPath + "SFUPSNA-----.svg"
#                                     
#         elif self.affiliation == preferences.AFFILIATION_Neutral:
#             self.iconPath = str(preferences.ICON_PATH) + os.sep + 'mil2525' + os.sep
#             if self.classification == enums.FUNCTION_MERCHANT or \
#                self.classification == enums.FUNCTION_MERCHANT_B or \
#                self.classification == enums.FUNCTION_MERCHANT_C:
#                 self.iconPath = self.iconPath + "SNSPXM------.svg"
#             elif self.classification == enums.FUNCTION_WARSHIP:
#                 self.iconPath = self.iconPath + "SNSPCL------.svg"
#             elif self.classification == enums.FUNCTION_FISHING:
#                 self.iconPath = self.iconPath + "SNSPXF------.svg"
#             elif self.classification == enums.FUNCTION_SUBMARINE:
#                 self.iconPath = self.iconPath + "SNUPSNA-----.svg"
#                                     
#         elif self.affiliation == preferences.AFFILIATION_Hostile:
#             self.iconPath = str(preferences.ICON_PATH) + os.sep + 'mil2525' + os.sep
#             if self.classification == enums.FUNCTION_MERCHANT or \
#                self.classification == enums.FUNCTION_MERCHANT_B or \
#                self.classification == enums.FUNCTION_MERCHANT_C:
#                 self.iconPath = self.iconPath + "SHSPXM------.svg"
#             elif self.classification == enums.FUNCTION_WARSHIP:
#                 self.iconPath = self.iconPath + "SHSPCL------.svg"
#             elif self.classification == enums.FUNCTION_FISHING:
#                 self.iconPath = self.iconPath + "SHSPXF------.svg"                    
#             elif self.classification == enums.FUNCTION_SUBMARINE:
#                 self.iconPath = self.iconPath + "SHUPSNA-----.svg"                

        return self.iconPath       