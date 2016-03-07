# -*- coding: utf-8 -*-

"""
***************************************************************************
    difference.py
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

from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.algs.gdal.GdalUtils import GdalUtils
from processing.tools.vector import ogrConnectionString, ogrLayerName

class difference(GeoAlgorithm):

    INPUT_LAYER_A = 'INPUT_LAYER_A'
    INPUT_LAYER_B = 'INPUT_LAYER_B'
    FIELDS_A = 'FIELDS_A'
    TABLE = 'TABLE'
    SCHEMA = 'SCHEMA'
    SINGLE = 'SINGLE'    
    OPTIONS = 'OPTIONS'
    OUTPUT = 'OUTPUT'
    
    def getIcon(self):
        return  QIcon(os.path.dirname(__file__) + '/icons/postgis.png')

    def defineCharacteristics(self):
        self.name = 'Polygon difference (non symmetrical)'
        self.group = 'Vector geoprocessing'

        self.addParameter(ParameterVector(self.INPUT_LAYER_A, 'Input layer',
                          [ParameterVector.VECTOR_TYPE_POLYGON], False))
        self.addParameter(ParameterString(self.FIELDS_A, 'Attributes to keep (comma separated list). Aliasing permitted.',
                          '', optional=False))
        self.addParameter(ParameterVector(self.INPUT_LAYER_B, 'Layer to be subtracted',
                          [ParameterVector.VECTOR_TYPE_POLYGON], False))
        self.addParameter(ParameterString(self.SCHEMA, 'Output schema',
                          'public', optional=False))
        self.addParameter(ParameterString(self.TABLE, 'Output table name',
                          'difference', optional=False))
        self.addParameter(ParameterBoolean(self.SINGLE,
                          'Force output as singlepart', False))
        self.addParameter(ParameterString(self.OPTIONS, 'Additional creation options (see ogr2ogr manual)',
                          '', optional=True))
        self.addOutput(OutputHTML(self.OUTPUT, 'Output log'))
        
    def processAlgorithm(self, progress):
        inLayerA = self.getParameterValue(self.INPUT_LAYER_A)
        ogrLayerA = ogrConnectionString(inLayerA)[1:-1]
        layernameA = ogrLayerName(inLayerA)
        inLayerB = self.getParameterValue(self.INPUT_LAYER_B)
        ogrLayerB = ogrConnectionString(inLayerB)[1:-1]
        layernameB = ogrLayerName(inLayerB)
        fieldsA = unicode(self.getParameterValue(self.FIELDS_A))
        dsUriA = QgsDataSourceURI(self.getParameterValue(self.INPUT_LAYER_A))
        geomColumnA = dsUriA.geometryColumn()
        dsUriB = QgsDataSourceURI(self.getParameterValue(self.INPUT_LAYER_B))
        geomColumnB = dsUriB.geometryColumn()
        schema = unicode(self.getParameterValue(self.SCHEMA))
        table = unicode(self.getParameterValue(self.TABLE))
        single = self.getParameterValue(self.SINGLE)
        if len(fieldsA) > 0:
           fieldstring = fieldsA.replace(",", ", g1.")
           fieldstring = ", g1." + fieldstring               
        else:
           fieldstring = ""        

        if single:
           sqlstring = "-sql \"SELECT (ST_Dump(ST_Difference(g1." + geomColumnA + ",ST_Union(g2." + geomColumnB + ")))).geom::geometry(Polygon) AS geom" + fieldstring + " FROM " + layernameA + " AS g1, " + layernameB + " AS g2 GROUP BY g1." + geomColumnA + fieldstring + "\""" -nln " + schema + "." + table + " -lco FID=gid -nlt POLYGON -lco GEOMETRY_NAME=geom --config PG_USE_COPY YES"
        else:
           sqlstring = "-sql \"SELECT (ST_Multi(ST_CollectionExtract(ST_Difference(g1." + geomColumnA + ",ST_Union(g2." + geomColumnB + ")),3)))::geometry(MultiPolygon) AS geom" + fieldstring + " FROM " + layernameA + " AS g1, " + layernameB + " AS g2 GROUP BY g1." + geomColumnA + fieldstring + "\""" -nln " + schema + "." + table + " -lco FID=gid -nlt MULTIPOLYGON -lco GEOMETRY_NAME=geom --config PG_USE_COPY YES"

        options = unicode(self.getParameterValue(self.OPTIONS))

        arguments = []
        arguments.append('-f')
        arguments.append('PostgreSQL')
        arguments.append(ogrLayerA)
        arguments.append(ogrLayerA)
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