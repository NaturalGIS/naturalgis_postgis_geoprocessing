# -*- coding: utf-8 -*-

"""
***************************************************************************
    distance.py
    ---------------------
    Date                 : August 2019
    Copyright            : (C) 2019 by Giovanni Manghi
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

__author__ = 'Alexander Bruy and Giovanni Manghi'
__date__ = 'August 2019'
__copyright__ = '(C) 2019, Giovanni Manghi'

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
                       QgsDataSourceUri
                      )
from processing.algs.gdal.GdalUtils import GdalUtils

pluginPath = os.path.dirname(__file__)


class distance(QgsProcessingAlgorithm):

    OUTPUT_LAYER = 'OUTPUT_LAYER'
    INPUT_LAYER_A = 'INPUT_LAYER_A'
    INPUT_LAYER_B = 'INPUT_LAYER_B'
    FIELD_A = 'FIELD_A'
    FIELD_B = 'FIELD_B'
    MULTI = 'MULTI'
    TABLE = 'TABLE'
    SCHEMA = 'SCHEMA'
    OPTIONS = 'OPTIONS'

    def __init__(self):
        super().__init__()

    def createInstance(self):
        return type(self)()

    def icon(self):
        return QIcon(os.path.join(pluginPath, 'icons', 'postgis.png'))

    def name(self):
        return 'minimumdistance'

    def displayName(self):
        return 'Minimum distance'

    def group(self):
        return 'Vector geoprocessing'

    def groupId(self):
        return 'vectorgeoprocessing'

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT_LAYER_A,
                                                            '"FROM" layer',
                                                            [QgsProcessing.TypeVectorAnyGeometry]))
        self.addParameter(QgsProcessingParameterField(self.FIELD_A,
                                                      '"FROM" layer ID',
                                                      None,
                                                      self.INPUT_LAYER_A))
        self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT_LAYER_B,
                                                            '"TO" layer',
                                                            [QgsProcessing.TypeVectorAnyGeometry]))
        self.addParameter(QgsProcessingParameterField(self.FIELD_B,
                                                      '"TO" layer layer ID',
                                                      None,
                                                      self.INPUT_LAYER_B))
        self.addParameter(QgsProcessingParameterBoolean(self.MULTI,
                                                        'Consider "TO" layer as one unique feature',
                                                        True))
        self.addParameter(QgsProcessingParameterString(self.SCHEMA,
                                                       'Output schema',
                                                       'public'))
        self.addParameter(QgsProcessingParameterString(self.TABLE,
                                                       'Output table name',
                                                       'distance_analysis'))
        self.addParameter(QgsProcessingParameterString(self.OPTIONS,
                                                       'Additional creation options (see ogr2ogr manual)',
                                                       '',
                                                       optional=True))

    def processAlgorithm(self, parameters, context, feedback):
        inLayerA = self.parameterAsVectorLayer(parameters, self.INPUT_LAYER_A, context)
        ogrLayerA = GdalUtils.ogrConnectionStringFromLayer(inLayerA)
        layernameA = GdalUtils.ogrLayerName(inLayerA.dataProvider().dataSourceUri())

        inLayerB = self.parameterAsVectorLayer(parameters, self.INPUT_LAYER_B, context)
        ogrLayerB = GdalUtils.ogrConnectionStringFromLayer(inLayerB)
        layernameB = GdalUtils.ogrLayerName(inLayerB.dataProvider().dataSourceUri())

        fieldA = self.parameterAsString(parameters, self.FIELD_A, context)
        fieldB = self.parameterAsString(parameters, self.FIELD_B, context)

        uri = QgsDataSourceUri(inLayerA.source())
        geomColumnA = uri.geometryColumn()
        uri = QgsDataSourceUri(inLayerB.source())
        geomColumnB = uri.geometryColumn()

        multi = self.parameterAsBool(parameters, self.MULTI, context)

        schema = self.parameterAsString(parameters, self.SCHEMA, context)
        table = self.parameterAsString(parameters, self.TABLE, context)
        options = self.parameterAsString(parameters, self.OPTIONS, context)

        if multi:
           sqlstring = "-sql \"WITH temp_table AS (SELECT ST_Union(" + geomColumnB + ") AS geom FROM " + layernameB + ") SELECT ST_ShortestLine(g1." + geomColumnA + ",g2.geom) AS geom, ST_Distance(g1." + geomColumnA + ",g2.geom) AS distance, g1." + fieldA + " AS id_from FROM " + layernameA + " AS g1, temp_table AS g2\" -nln " + schema + "." + table + " -lco FID=gid -lco GEOMETRY_NAME=geom -nlt LINESTRING --config PG_USE_COPY YES -a_srs EPSG:" + str(sridA) + ""
        else:
           sqlstring = "-sql \"SELECT ST_ShortestLine(g1." + geomColumnA + ",g2." + geomColumnB + ") AS geom, ST_Distance(g1." + geomColumnA + ",g2." + geomColumnB + ") AS distance, g1." + fieldA + " AS id_from, g2." + fieldB + " AS id_to FROM " + layernameA + " AS g1, " + layernameB + " AS g2\" -nln " + schema + "." + table + " -lco FID=gid -lco GEOMETRY_NAME=geom -nlt LINESTRING --config PG_USE_COPY YES"

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
