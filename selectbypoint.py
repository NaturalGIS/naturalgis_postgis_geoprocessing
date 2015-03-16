# -*- coding: utf-8 -*-

"""
***************************************************************************
    selectbypoint.py
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

class selectbypoint(OgrAlgorithm):

    INPUT_LAYER_A = 'INPUT_LAYER_A'
    INPUT_LAYER_B = 'INPUT_LAYER_B'
    FIELDS_B = 'FIELDS_B'
    TABLE = 'TABLE'
    SCHEMA = 'SCHEMA'
    SINGLE = 'SINGLE' 
    BUFFER = 'BUFFER' 
    KEEP = 'KEEP' 
    OPTIONS = 'OPTIONS'
    OUTPUT = 'OUTPUT'
    
    def getIcon(self):
        return  QIcon(os.path.dirname(__file__) + '/icons/postgis.png')

    def defineCharacteristics(self):
        self.name = 'Select by points (select by location)'
        self.group = 'Vector geoprocessing'

        self.addParameter(ParameterVector(self.INPUT_LAYER_A, 'Point layer used for the selection',
                          [ParameterVector.VECTOR_TYPE_POINT], False))
        self.addParameter(ParameterVector(self.INPUT_LAYER_B, 'Select features from',
                          [ParameterVector.VECTOR_TYPE_ANY], False))
        self.addParameter(ParameterString(self.FIELDS_B, 'Attributes to keep (comma separated list). Aliasing permitted.',
                          '', optional=False))
        self.addParameter(ParameterString(self.BUFFER, 'Buffer distance for points selection layer.',
                          '0', optional=False))
        self.addParameter(ParameterBoolean(self.SINGLE,
                          'Force output as singlepart', True))
        self.addParameter(ParameterBoolean(self.KEEP,
                          'Select also features just touching the selection layer (used when buffering or selecting polygons)', False))
        self.addParameter(ParameterString(self.SCHEMA, 'Output schema',
                          'public', optional=False))
        self.addParameter(ParameterString(self.TABLE, 'Output table name',
                          'select', optional=False))
        self.addParameter(ParameterString(self.OPTIONS, 'Additional creation options (see ogr2ogr manual)',
                          '', optional=True))
        self.addOutput(OutputHTML(self.OUTPUT, 'Output log'))
        
    def processAlgorithm(self, progress):
        inLayerA = self.getParameterValue(self.INPUT_LAYER_A)
        ogrLayerA = self.ogrConnectionString(inLayerA)[1:-1]
        layernameA = self.ogrLayerName(inLayerA)
        inLayerB = self.getParameterValue(self.INPUT_LAYER_B)
        ogrLayerB = self.ogrConnectionString(inLayerB)[1:-1]
        layernameB = self.ogrLayerName(inLayerB)
        fieldsB = unicode(self.getParameterValue(self.FIELDS_B))
        dsUriA = QgsDataSourceURI(self.getParameterValue(self.INPUT_LAYER_A))
        geomColumnA = dsUriA.geometryColumn()
        dsUriB = QgsDataSourceURI(self.getParameterValue(self.INPUT_LAYER_B))
        geomColumnB = dsUriB.geometryColumn()
        layerB = dataobjects.getObjectFromUri(self.getParameterValue(self.INPUT_LAYER_B))
        geomTypeB = layerB.geometryType()
        wkbTypeB = layerB.wkbType()
        sridB = layerB.crs().postgisSrid()
        schema = unicode(self.getParameterValue(self.SCHEMA))
        table = unicode(self.getParameterValue(self.TABLE))
        single = self.getParameterValue(self.SINGLE)
        keep = self.getParameterValue(self.KEEP)
        bufferdist = self.getParameterValue(self.BUFFER)
        
        if len(fieldsB) > 0:
           fieldstringB = "," + fieldsB
        else:
           fieldstringB = ""          

        if geomTypeB == 0:
           type = "POINT"
        elif geomTypeB == 1:
           type = "LINESTRING"
        else:
           type = "POLYGON"

        if single:
           multistring = "-nlt " + type
           caststring = type
           st_function = "ST_Dump"
           castgeom = ".geom"
        else:
           multistring = "-nlt MULTI" + type
           caststring = "MULTI" + type
           st_function = "ST_Multi"
           castgeom = ""           
           
        if geomTypeB == 0:        
           if bufferdist == '0' or bufferdist == '':
              sqlstring = "-sql \"SELECT (" + st_function + "(g2." + geomColumnB + "))" + castgeom + "::geometry(" + caststring + "," + str(sridB) + ") AS geom" + fieldstringB + " FROM " + layernameA + " AS g1, " + layernameB + " AS g2 WHERE ST_Intersects(g2." + geomColumnB + ",g1." + geomColumnA + ") is true\" -nln " + table + " -lco SCHEMA=" + schema + " -lco FID=gid " + multistring + " -lco GEOMETRY_NAME=geom --config PG_USE_COPY YES"
           else:
              if keep:
                 sqlstring = "-sql \"SELECT (" + st_function + "(g2." + geomColumnB + "))" + castgeom + "::geometry(" + caststring + "," + str(sridB) + ") AS geom" + fieldstringB + " FROM " + layernameA + " AS g1, " + layernameB + " AS g2 WHERE (ST_Intersects(ST_Buffer(g1." + geomColumnA + "," + bufferdist + "),g2." + geomColumnB + ")) is true OR (ST_Touches(ST_Buffer(g1." + geomColumnA + "," + bufferdist + "),g2." + geomColumnB + ")) is true\" -nln " + table + " -lco SCHEMA=" + schema + " -lco FID=gid " + multistring + " -lco GEOMETRY_NAME=geom --config PG_USE_COPY YES"
              else:
                 sqlstring = "-sql \"SELECT (" + st_function + "(g2." + geomColumnB + "))" + castgeom + "::geometry(" + caststring + "," + str(sridB) + ") AS geom" + fieldstringB + " FROM " + layernameA + " AS g1, " + layernameB + " AS g2 WHERE (ST_Intersects(ST_Buffer(g1." + geomColumnA + "," + bufferdist + "),g2." + geomColumnB + ")) is true AND (ST_Touches(ST_Buffer(g1." + geomColumnA + "," + bufferdist + "),g2." + geomColumnB + ")) is false\" -nln " + table + " -lco SCHEMA=" + schema + " -lco FID=gid " + multistring + " -lco GEOMETRY_NAME=geom --config PG_USE_COPY YES"
        elif geomTypeB == 1:
           if bufferdist == '0' or bufferdist == '':
              sqlstring = "-sql \"SELECT (" + st_function + "(g2." + geomColumnB + "))" + castgeom + "::geometry(" + caststring + "," + str(sridB) + ") AS geom" + fieldstringB + " FROM " + layernameA + " AS g1, " + layernameB + " AS g2 WHERE ST_Intersects(g2." + geomColumnB + ",g1." + geomColumnA + ") is true\" -nln " + table + " -lco SCHEMA=" + schema + " -lco FID=gid " + multistring + " -lco GEOMETRY_NAME=geom --config PG_USE_COPY YES"
           else:
              if keep:
                 sqlstring = "-sql \"SELECT (" + st_function + "(g2." + geomColumnB + "))" + castgeom + "::geometry(" + caststring + "," + str(sridB) + ") AS geom" + fieldstringB + " FROM " + layernameA + " AS g1, " + layernameB + " AS g2 WHERE (ST_Intersects(ST_Buffer(g1." + geomColumnA + "," + bufferdist + "),g2." + geomColumnB + ")) is true OR (ST_Touches(ST_Buffer(g1." + geomColumnA + "," + bufferdist + "),g2." + geomColumnB + ")) is true\" -nln " + table + " -lco SCHEMA=" + schema + " -lco FID=gid " + multistring + " -lco GEOMETRY_NAME=geom --config PG_USE_COPY YES"
              else:
                 sqlstring = "-sql \"SELECT (" + st_function + "(g2." + geomColumnB + "))" + castgeom + "::geometry(" + caststring + "," + str(sridB) + ") AS geom" + fieldstringB + " FROM " + layernameA + " AS g1, " + layernameB + " AS g2 WHERE (ST_Intersects(ST_Buffer(g1." + geomColumnA + "," + bufferdist + "),g2." + geomColumnB + ")) is true AND (ST_Touches(ST_Buffer(g1." + geomColumnA + "," + bufferdist + "),g2." + geomColumnB + ")) is false\" -nln " + table + " -lco SCHEMA=" + schema + " -lco FID=gid " + multistring + " -lco GEOMETRY_NAME=geom --config PG_USE_COPY YES"
        else:
           if bufferdist == '0' or bufferdist == '':
              if keep:
                 sqlstring = "-sql \"SELECT (" + st_function + "(g2." + geomColumnB + "))" + castgeom + "::geometry(" + caststring + "," + str(sridB) + ") AS geom" + fieldstringB + " FROM " + layernameA + " AS g1, " + layernameB + " AS g2 WHERE ST_Intersects(g2." + geomColumnB + ",g1." + geomColumnA + ") is true\" -nln " + table + " -lco SCHEMA=" + schema + " -lco FID=gid " + multistring + " -lco GEOMETRY_NAME=geom --config PG_USE_COPY YES"
              else:
                 sqlstring = "-sql \"SELECT (" + st_function + "(g2." + geomColumnB + "))" + castgeom + "::geometry(" + caststring + "," + str(sridB) + ") AS geom" + fieldstringB + " FROM " + layernameA + " AS g1, " + layernameB + " AS g2 WHERE ST_Within(g1." + geomColumnA + ",g2." + geomColumnB + ") is true\" -nln " + table + " -lco SCHEMA=" + schema + " -lco FID=gid " + multistring + " -lco GEOMETRY_NAME=geom --config PG_USE_COPY YES"
           else: 
              if keep:
                 sqlstring = "-sql \"SELECT (" + st_function + "(g2." + geomColumnB + "))" + castgeom + "::geometry(" + caststring + "," + str(sridB) + ") AS geom" + fieldstringB + " FROM " + layernameA + " AS g1, " + layernameB + " AS g2 WHERE (ST_Intersects(ST_Buffer(g1." + geomColumnA + "," + bufferdist + "),g2." + geomColumnB + ")) is true OR ST_Contains(g2." + geomColumnB+ ",ST_Buffer(g1." + geomColumnA + "," + bufferdist + ")) is true\" -nln " + table + " -lco SCHEMA=" + schema + " -lco FID=gid " + multistring + " -lco GEOMETRY_NAME=geom --config PG_USE_COPY YES"
              else:
                 sqlstring = "-sql \"SELECT (" + st_function + "(g2." + geomColumnB + "))" + castgeom + "::geometry(" + caststring + "," + str(sridB) + ") AS geom" + fieldstringB + " FROM " + layernameA + " AS g1, " + layernameB + " AS g2 WHERE (ST_Contains(ST_Buffer(g1." + geomColumnA + "," + bufferdist + "),g2." + geomColumnB + ")) is true OR ST_Overlaps(ST_Buffer(g1." + geomColumnA + "," + bufferdist + "),g2." + geomColumnB + ") is true OR ST_Contains(g2." + geomColumnB+ ",ST_Buffer(g1." + geomColumnA + "," + bufferdist + ")) is true\" -nln " + table + " -lco SCHEMA=" + schema + " -lco FID=gid " + multistring + " -lco GEOMETRY_NAME=geom --config PG_USE_COPY YES"

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
        print geomTypeB
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