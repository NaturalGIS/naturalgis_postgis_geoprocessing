# -*- coding: utf-8 -*-

"""
***************************************************************************
    clipbypolygon.py
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

class clipbypolygon(OgrAlgorithm):

    INPUT_LAYER_A = 'INPUT_LAYER_A'
    INPUT_LAYER_B = 'INPUT_LAYER_B'
    FIELDS_A = 'FIELDS_A'
    FIELDS_B = 'FIELDS_B'
    TABLE = 'TABLE'
    SCHEMA = 'SCHEMA'
    SINGLE = 'SINGLE' 
    KEEP = 'KEEP' 
    OPTIONS = 'OPTIONS'
    OUTPUT = 'OUTPUT'
    
    def getIcon(self):
        return  QIcon(os.path.dirname(__file__) + '/icons/postgis.png')

    def defineCharacteristics(self):
        self.name = 'Clip with polygons (Intersection)'
        self.group = 'Vector geoprocessing'

        self.addParameter(ParameterVector(self.INPUT_LAYER_A, 'Clip polygon layer',
                          [ParameterVector.VECTOR_TYPE_POLYGON], False))
        self.addParameter(ParameterString(self.FIELDS_A, 'Attributes to keep (comma separated list). Aliasing permitted.',
                          '', optional=False))
        self.addParameter(ParameterVector(self.INPUT_LAYER_B, 'Layer to be clipped',
                          [ParameterVector.VECTOR_TYPE_ANY], False))
        self.addParameter(ParameterString(self.FIELDS_B, 'Attributes to keep (comma separated list). Aliasing permitted.',
                          '', optional=False))
        self.addParameter(ParameterBoolean(self.SINGLE,
                          'Force output as singlepart', True))
        self.addParameter(ParameterBoolean(self.KEEP,
                          'Keep points and lines on borders of clip polygons (not used when clipping polygons)', True))
        self.addParameter(ParameterString(self.SCHEMA, 'Output schema',
                          'public', optional=False))
        self.addParameter(ParameterString(self.TABLE, 'Output table name',
                          'clip', optional=False))
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
        fieldsA = unicode(self.getParameterValue(self.FIELDS_A))
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
        if len(fieldsB) > 0:
           fieldstringB = "," + fieldsB
        else:
           fieldstringB = ""        

        if len(fieldsA) > 0:
           fieldstringA = "," + fieldsA
        else:
           fieldstringA = ""   

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
           if keep:
              sqlstring = "-sql \"SELECT (" + st_function + "(g2." + geomColumnB + "))" + castgeom + "::geometry(" + caststring + "," + str(sridB) + ") AS geom" + fieldstringA + fieldstringB + " FROM " + layernameA + " AS g1, " + layernameB + " AS g2 WHERE ST_Intersects(g1." + geomColumnA + ",g2." + geomColumnB + ") is true\" -nln " + schema + "." + table + " -lco FID=gid " + multistring + " -lco GEOMETRY_NAME=geom --config PG_USE_COPY YES"
           else:
              sqlstring = "-sql \"WITH temp_table AS (SELECT ST_Union(" + geomColumnA + ") AS geom FROM " + layernameA + ") SELECT (" + st_function + "(g2." + geomColumnB + "))" + castgeom + "::geometry(" + caststring + "," + str(sridB) + ") AS geom" + fieldstringB + " FROM temp_table AS g1, " + layernameB + " AS g2 WHERE ST_Contains(g1." + geomColumnA + ",g2." + geomColumnB + ") is true\" -nln " + schema + "." + table + " -lco FID=gid " + multistring + " -lco GEOMETRY_NAME=geom --config PG_USE_COPY YES -a_srs EPSG:" + str(sridB) + ""
        elif geomTypeB == 1:
           if keep:
              sqlstring = "-sql \"SELECT (" + st_function + "(ST_CollectionExtract(ST_Intersection(g1." + geomColumnA + ",g2." + geomColumnB + "),2)))" + castgeom + "::geometry(" + caststring + "," + str(sridB) + ") AS geom" + fieldstringA + fieldstringB + " FROM " + layernameA + " AS g1, " + layernameB + " AS g2 WHERE ST_Intersects(g1." + geomColumnA + ",g2." + geomColumnB + ") is true\" -nln " + schema + "." + table + " -lco FID=gid " + multistring + " -lco GEOMETRY_NAME=geom --config PG_USE_COPY YES"
           else:
              sqlstring = "-sql \"SELECT (" + st_function + "(ST_Intersection(g1." + geomColumnA + ",g2." + geomColumnB + ")))" + castgeom + "::geometry(" + caststring + "," + str(sridB) + ") AS geom" + fieldstringA + fieldstringB + " FROM " + layernameA + " AS g1, " + layernameB + " AS g2 WHERE ST_Intersects(g1." + geomColumnA + ",g2." + geomColumnB + ") is true AND ST_Touches(g1." + geomColumnA + ",g2." + geomColumnB + ") is false\" -nln " + schema + "." + table + " -lco FID=gid " + multistring + " -lco GEOMETRY_NAME=geom --config PG_USE_COPY YES"
        else:
             sqlstring = "-sql \"SELECT (" + st_function + "(ST_Intersection(g1." + geomColumnA + ",g2." + geomColumnB + ")))" + castgeom + "::geometry(" + caststring + "," + str(sridB) + ") AS geom" + fieldstringA + fieldstringB + " FROM " + layernameA + " AS g1, " + layernameB + " AS g2 WHERE ST_Contains(g1." + geomColumnA + ",g2." + geomColumnB + ") is true OR ST_Overlaps(g1." + geomColumnA + ",g2." + geomColumnB + ") is true OR ST_Contains(g2." + geomColumnB + ",g1." + geomColumnA + ") is true\" -nln " + schema + "." + table + " -lco FID=gid " + multistring + " -lco GEOMETRY_NAME=geom --config PG_USE_COPY YES"

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