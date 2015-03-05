# -*- coding: utf-8 -*-

"""
***************************************************************************
    extractinvalid.py
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

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *

from processing.core.parameters import ParameterVector
from processing.core.parameters import ParameterString
from processing.core.parameters import ParameterNumber
from processing.core.parameters import ParameterBoolean
from processing.core.parameters import ParameterTableField
from processing.core.outputs import OutputVector
from processing.core.outputs import OutputHTML

from processing.tools.system import *
from processing.tools import dataobjects

from processing.algs.gdal.OgrAlgorithm import OgrAlgorithm
from processing.algs.gdal.GdalUtils import GdalUtils

class extractinvalid(OgrAlgorithm):

    INPUT_LAYER = 'INPUT_LAYER'
    FIELDS = 'FIELDS'    
    TABLE = 'TABLE'
    SCHEMA = 'SCHEMA'
    OPTIONS = 'OPTIONS'
    OUTPUT = 'OUTPUT'
    
    def getIcon(self):
        return  QIcon(os.path.dirname(__file__) + '/icons/postgis.png')

    def defineCharacteristics(self):
        self.name = 'Extract invalid polygons (ST_IsValid)'
        self.group = 'Vector geoprocessing'

        self.addParameter(ParameterVector(self.INPUT_LAYER, 'Input layer',
                          [ParameterVector.VECTOR_TYPE_POLYGON], False))
        self.addParameter(ParameterString(self.FIELDS, 'Attributes to keep (comma separated list). Aliasing permitted.',
                          '', optional=False))
        self.addParameter(ParameterString(self.SCHEMA, 'Output schema',
                          'public', optional=False))
        self.addParameter(ParameterString(self.TABLE, 'Output table name',
                          'invalid_polygons', optional=False))
        self.addParameter(ParameterString(self.OPTIONS, 'Additional creation options (see ogr2ogr manual)',
                          '', optional=True))
        self.addOutput(OutputHTML(self.OUTPUT, 'Output log'))
        
    def processAlgorithm(self, progress):
        inLayer = self.getParameterValue(self.INPUT_LAYER)
        ogrLayer = self.ogrConnectionString(inLayer)[1:-1]
        layername = self.ogrLayerName(inLayer)
        fields = unicode(self.getParameterValue(self.FIELDS))
        dsUri = QgsDataSourceURI(self.getParameterValue(self.INPUT_LAYER))
        geomColumn = dsUri.geometryColumn()
        layer = dataobjects.getObjectFromUri(self.getParameterValue(self.INPUT_LAYER))
        geomType = layer.geometryType()
        wkbType = layer.wkbType()
        srid = layer.crs().postgisSrid()
        schema = unicode(self.getParameterValue(self.SCHEMA))
        table = unicode(self.getParameterValue(self.TABLE))
        if len(fields) > 0:
           fieldstring = "," + fields
        else:
           fieldstring = ""

        if wkbType == 3:
           layertype = "POLYGON"              
           sqlstring = "-sql \"SELECT (ST_Dump(g1." + geomColumn + ")).geom::geometry(" + layertype + "," + str(srid) + ") AS geom, ST_IsValidReason(" + geomColumn + ") AS invalid_reason" + fieldstring + " FROM " + layername + " AS g1 WHERE NOT ST_IsValid(" + geomColumn + ")\" -nlt " + layertype + " -nln " + table + " -lco SCHEMA=" + schema + " -lco FID=gid -lco GEOMETRY_NAME=geom --config PG_USE_COPY YES"
        else:
            layertype = "MULTIPOLYGON"            
            sqlstring = "-sql \"SELECT (g1." + geomColumn + ")::geometry(" + layertype + "," + str(srid) + ") AS geom, ST_IsValidReason(" + geomColumn + ") AS invalid_reason" + fieldstring + " FROM " + layername + " AS g1 WHERE NOT ST_IsValid(" + geomColumn + ")\" -nlt " + layertype + " -nln " + table + " -lco SCHEMA=" + schema + " -lco FID=gid -lco GEOMETRY_NAME=geom --config PG_USE_COPY YES"

        options = unicode(self.getParameterValue(self.OPTIONS))

        arguments = []
        arguments.append('-f')
        arguments.append('PostgreSQL')
        arguments.append(ogrLayer)
        arguments.append(ogrLayer)
        arguments.append(sqlstring)
        arguments.append('-overwrite')
                
        if len(options) > 0:
            arguments.append(options)
        commands = []
        if isWindows():
            commands = ['cmd.exe', '/C ', 'ogr2ogr.exe',
                        GdalUtils.escapeAndJoin(arguments)]
        else:
            commands = ['ogr2ogr', GdalUtils.escapeAndJoin(arguments)]

        GdalUtils.runGdal(commands, progress)

        output = self.getOutputValue(self.OUTPUT)
        f = open(output, 'w')
        f.write('<pre>')
        for s in GdalUtils.getConsoleOutput()[1:]:
            f.write(unicode(s))
        f.write('</pre>')
        f.close()          