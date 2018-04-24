# -*- coding: utf-8 -*-

"""
***************************************************************************
    OgrGeoProcessingProvider.py
    ---------------------
    Date                 : January 2015
    Copyright            : (C) 2015 by Giovanni Manghi
    Email                : giovanni dot manghi at naturalgis dot pt
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

__author__ = 'Giovanni Manghi'
__date__ = 'January 2015'
__copyright__ = '(C) 2015, Giovanni Manghi'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os

from qgis.PyQt.QtGui import QIcon

from qgis.core import QgsProcessingProvider

from processing.core.ProcessingConfig import ProcessingConfig, Setting

from postgis_geoprocessing.distance import distance
from postgis_geoprocessing.clipbypolygon import clipbypolygon
from postgis_geoprocessing.makevalid import makevalid
from postgis_geoprocessing.difference import difference
from postgis_geoprocessing.dissolve import dissolve
from postgis_geoprocessing.extractinvalid import extractinvalid
from postgis_geoprocessing.bufferlayers import bufferlayers
from postgis_geoprocessing.makevalidbufferzero import makevalidbufferzero
from postgis_geoprocessing.bufferlayersvariable import bufferlayersvariable
from postgis_geoprocessing.closestpoint import closestpoint
from postgis_geoprocessing.distancematrix import distancematrix
from postgis_geoprocessing.selectbypolygon import selectbypolygon
from postgis_geoprocessing.selectbypoint import selectbypoint
#from postgis_geoprocessing.selectbyline import selectbyline
#from postgis_geoprocessing.samplewithpoints import samplewithpoints

OGR_GEOPROCESSING_ACTIVE = 'OGR_GEOPROCESSING_ACTIVE'

pluginPath = os.path.dirname(__file__)


class OgrGeoprocessingProvider(QgsProcessingProvider):

    def __init__(self):
        super().__init__()
        self.algs = []

    def id(self):
        return 'postgisgeoprocessing'

    def name(self):
        return 'PostGIS Geoprocessing tools'

    def icon(self):
        return QIcon(os.path.join(pluginPath, 'icons', 'naturalgis_32.png'))

    def load(self):
        ProcessingConfig.settingIcons[self.name()] = self.icon()
        ProcessingConfig.addSetting(Setting(self.name(),
                                            OGR_GEOPROCESSING_ACTIVE,
                                            'Activate',
                                            True))
        ProcessingConfig.readSettings()
        self.refreshAlgorithms()
        return True

    def unload(self):
        ProcessingConfig.removeSetting(OGR_GEOPROCESSING_ACTIVE)

    def isActive(self):
        return ProcessingConfig.getSetting(OGR_GEOPROCESSING_ACTIVE)

    def setActive(self, active):
        ProcessingConfig.setSettingValue(OGR_GEOPROCESSING_ACTIVE, active)

    def supportsNonFileBasedOutput(self):
        return True

    def getAlgs(self):
        algs = [distance(),
                clipbypolygon(),
                makevalid(),
                difference(),
                dissolve(),
                extractinvalid(),
                bufferlayers(),
                makevalidbufferzero(),
                bufferlayersvariable(),
                closestpoint(),
                distancematrix(),
                selectbypolygon(),
                selectbypoint(),
                #selectbyline(),
                #samplewithpoints()
               ]

        return algs

    def loadAlgorithms(self):
        self.algs = self.getAlgs()
        for a in self.algs:
            self.addAlgorithm(a)
