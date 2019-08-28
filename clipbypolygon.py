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

from qgis.PyQt.QtGui import QIcon

from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterField,
                       QgsProcessingParameterString,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterVectorLayer,
                       QgsDataSourceUri,
                       QgsWkbTypes
                      )
from processing.algs.gdal import GdalUtils

pluginPath = os.path.dirname(__file__)


class clipbypolygon(QgsProcessingAlgorithm):

    INPUT_LAYER_A = 'INPUT_LAYER_A'
    INPUT_LAYER_B = 'INPUT_LAYER_B'
    FIELDS_A = 'FIELDS_A'
    FIELDS_B = 'FIELDS_B'
    TABLE = 'TABLE'
    SCHEMA = 'SCHEMA'
    SINGLE = 'SINGLE'
    KEEP = 'KEEP'
    OPTIONS = 'OPTIONS'

    def __init__(self):
        super().__init__()

    def createInstance(self):
        return type(self)()

    def icon(self):
        return QIcon(os.path.join(pluginPath, 'icons', 'postgis.png'))

    def name(self):
        return 'clipwithpolygonintersection'

    def displayName(self):
        return 'Clip with polygons (Intersection)'

    def group(self):
        return 'Vector geoprocessing'

    def groupId(self):
        return 'vectorgeoprocessing'

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT_LAYER_A,
                                                            'Clip polygon layer',
                                                            [QgsProcessing.TypeVectorPolygon]))
        self.addParameter(QgsProcessingParameterField(self.FIELDS_A,
                                                      'Attributes to keep',
                                                      None,
                                                      self.INPUT_LAYER_A,
                                                      allowMultiple=True))
        self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT_LAYER_B,
                                                            'Layer to be clipped',
                                                            [QgsProcessing.TypeVectorAnyGeometry]))
        self.addParameter(QgsProcessingParameterField(self.FIELDS_B,
                                                      'Attributes to keep',
                                                      None,
                                                      self.INPUT_LAYER_B,
                                                      allowMultiple=True))
        self.addParameter(QgsProcessingParameterBoolean(self.SINGLE,
                                                        'Force output as singlepart',
                                                        True))
        self.addParameter(QgsProcessingParameterBoolean(self.KEEP,
                                                        'Keep points and lines on borders of clip polygons (not used when clipping polygons)',
                                                        True))
        self.addParameter(QgsProcessingParameterString(self.SCHEMA,
                                                       'Output schema',
                                                       'public'))
        self.addParameter(QgsProcessingParameterString(self.TABLE,
                                                       'Output table name',
                                                       'clip'))
        self.addParameter(QgsProcessingParameterString(self.OPTIONS,
                                                       'Additional creation options (see ogr2ogr manual)',
                                                       '',
                                                       optional=True))

    def processAlgorithm(self, parameters, context, feedback):
        inLayerA = self.parameterAsVectorLayer(parameters, self.INPUT_LAYER_A, context)
        ogrLayerA = GdalUtils.ogrConnectionStringFromLayer(inLayerA)[1:-1]
        layernameA = GdalUtils.ogrLayerName(inLayerA.dataProvider().dataSourceUri())

        inLayerB = self.parameterAsVectorLayer(parameters, self.INPUT_LAYER_B, context)
        ogrLayerB = GdalUtils.ogrConnectionStringFromLayer(inLayerB)[1:-1]
        layernameB = GdalUtils.ogrLayerName(inLayerB.dataProvider().dataSourceUri())

        fieldsA = self.parameterAsFields(parameters, self.FIELDS_A, context)
        fieldsB = self.parameterAsFields(parameters, self.FIELDS_B, context)

        uri = QgsDataSourceUri(inLayerA.source())
        geomColumnA = uri.geometryColumn()
        uir = QgsDataSourceUri(inLayerB.source())
        geomColumnB = uri.geometryColumn()

        geomTypeB = inLayerB.geometryType()
        sridB = inLayerB.crs().postgisSrid()

        single = self.parameterAsBool(parameters, self.SINGLE, context)
        keep = self.parameterAsBool(parameters, self.KEEP, context)

        schema = self.parameterAsString(parameters, self.SCHEMA, context)
        table = self.parameterAsString(parameters, self.TABLE, context)
        options = self.parameterAsString(parameters, self.OPTIONS, context)

        if len(fieldsB) > 0:
           fieldstringB = ', '.join(["g2.{}".format(f) for f in fieldsB])
           fieldstringB = ", " + fieldstringB
        else:
           fieldstringB = ""

        if len(fieldsA) > 0:
           fieldstringA = ', '.join(["g1.{}".format(f) for f in fieldsA])
           fieldstringA = ", " + fieldstringA
        else:
           fieldstringA = ""

        if geomTypeB == QgsWkbTypes.PointGeometry:
           type = "POINT"
        elif geomTypeB == QgsWkbTypes.LineGeometry:
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

        if geomTypeB == QgsWkbTypes.PointGeometry:
           if keep:
              sqlstring = "-sql \"SELECT (" + st_function + "(g2." + geomColumnB + "))" + castgeom + "::geometry(" + caststring + "," + str(sridB) + ") AS geom" + fieldstringA + fieldstringB + " FROM " + layernameA + " AS g1, " + layernameB + " AS g2 WHERE ST_Intersects(g1." + geomColumnA + ",g2." + geomColumnB + ") is true\" -nln " + schema + "." + table + " -lco FID=gid " + multistring + " -lco GEOMETRY_NAME=geom --config PG_USE_COPY YES"
           else:
              sqlstring = "-sql \"WITH temp_table AS (SELECT ST_Union(" + geomColumnA + ") AS geom FROM " + layernameA + ") SELECT (" + st_function + "(g2." + geomColumnB + "))" + castgeom + "::geometry(" + caststring + "," + str(sridB) + ") AS geom" + fieldstringA + fieldstringB + " FROM temp_table AS g1, " + layernameB + " AS g2 WHERE ST_Contains(g1." + geomColumnA + ",g2." + geomColumnB + ") is true\" -nln " + schema + "." + table + " -lco FID=gid " + multistring + " -lco GEOMETRY_NAME=geom --config PG_USE_COPY YES -a_srs EPSG:" + str(sridB) + ""
        elif geomTypeB == QgsWkbTypes.LineGeometry:
           if keep:
              sqlstring = "-sql \"SELECT (" + st_function + "(ST_CollectionExtract(ST_Intersection(g1." + geomColumnA + ",g2." + geomColumnB + "),2)))" + castgeom + "::geometry(" + caststring + "," + str(sridB) + ") AS geom" + fieldstringA + fieldstringB + " FROM " + layernameA + " AS g1, " + layernameB + " AS g2 WHERE ST_Intersects(g1." + geomColumnA + ",g2." + geomColumnB + ") is true\" -nln " + schema + "." + table + " -lco FID=gid " + multistring + " -lco GEOMETRY_NAME=geom --config PG_USE_COPY YES"
           else:
              sqlstring = "-sql \"SELECT (" + st_function + "(ST_Intersection(g1." + geomColumnA + ",g2." + geomColumnB + ")))" + castgeom + "::geometry(" + caststring + "," + str(sridB) + ") AS geom" + fieldstringA + fieldstringB + " FROM " + layernameA + " AS g1, " + layernameB + " AS g2 WHERE ST_Intersects(g1." + geomColumnA + ",g2." + geomColumnB + ") is true AND ST_Touches(g1." + geomColumnA + ",g2." + geomColumnB + ") is false\" -nln " + schema + "." + table + " -lco FID=gid " + multistring + " -lco GEOMETRY_NAME=geom --config PG_USE_COPY YES"
        else:
             sqlstring = "-sql \"SELECT (" + st_function + "(ST_Intersection(g1." + geomColumnA + ",g2." + geomColumnB + ")))" + castgeom + "::geometry(" + caststring + "," + str(sridB) + ") AS geom" + fieldstringA + fieldstringB + " FROM " + layernameA + " AS g1, " + layernameB + " AS g2 WHERE ST_Contains(g1." + geomColumnA + ",g2." + geomColumnB + ") is true OR ST_Overlaps(g1." + geomColumnA + ",g2." + geomColumnB + ") is true OR ST_Contains(g2." + geomColumnB + ",g1." + geomColumnA + ") is true\" -nln " + schema + "." + table + " -lco FID=gid " + multistring + " -lco GEOMETRY_NAME=geom --config PG_USE_COPY YES"

        arguments = []
        arguments.append('-f')
        arguments.append('PostgreSQL')
        arguments.append(ogrLayerA)
        arguments.append(ogrLayerA)
        arguments.append(sqlstring)
        arguments.append('-overwrite')

        if len(options) > 0:
            arguments.append(options)

        commands = ['ogr2ogr', GdalUtils.escapeAndJoin(arguments)]
        GdalUtils.runGdal(commands, feedback)

        return {}
