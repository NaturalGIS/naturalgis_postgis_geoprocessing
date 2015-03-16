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

from PyQt4.QtGui import *

from processing.core.AlgorithmProvider import AlgorithmProvider
from processing.core.ProcessingConfig import Setting, ProcessingConfig
from processing.tools import system

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
from postgis_geoprocessing.selectbyline import selectbyline

class OgrGeoprocessingProvider(AlgorithmProvider):

    def __init__(self):
        AlgorithmProvider.__init__(self)

        self.activate = False

        self.alglist = [distance(),clipbypolygon(),makevalid(),difference(),dissolve(),extractinvalid(),
                        bufferlayers(),makevalidbufferzero(),bufferlayersvariable(),closestpoint(),distancematrix(),
                        selectbypolygon(),selectbypoint(),selectbyline()]
        for alg in self.alglist:
            alg.provider = self

    def initializeSettings(self):
        AlgorithmProvider.initializeSettings(self)

    def unload(self):
        AlgorithmProvider.unload(self)

    def getName(self):
        return 'PostGIS Geoprocessing tools'

    def getDescription(self):
        return 'PostGIS Geoprocessing tools'

    def getIcon(self):
        return QIcon(os.path.dirname(__file__) + '/icons/naturalgis_32.png')

    def _loadAlgorithms(self):
        self.algs = self.alglist
