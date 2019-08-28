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

from qgis.PyQt.QtGui import QIcon

from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterField,
                       QgsProcessingParameterString,
                       QgsProcessingParameterVectorLayer,
                       QgsDataSourceUri,
                       QgsWkbTypes
                      )
from processing.algs.gdal.GdalUtils import GdalUtils

pluginPath = os.path.dirname(__file__)


class extractinvalid(QgsProcessingAlgorithm):

    INPUT_LAYER = 'INPUT_LAYER'
    FIELDS = 'FIELDS'
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
        return 'extractinvalidpolygonsstisvalid'

    def displayName(self):
        return 'Extract invalid polygons (ST_IsValid)'

    def group(self):
        return 'Vector geoprocessing'

    def groupId(self):
        return 'vectorgeoprocessing'

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT_LAYER,
                                                            'Input layer',
                                                            [QgsProcessing.TypeVectorPolygon]))
        self.addParameter(QgsProcessingParameterField(self.FIELDS,
                                                      'Attributes to keep',
                                                      None,
                                                      self.INPUT_LAYER,
                                                      allowMultiple=True))
        self.addParameter(QgsProcessingParameterString(self.SCHEMA,
                                                       'Output schema',
                                                       'public'))
        self.addParameter(QgsProcessingParameterString(self.TABLE,
                                                       'Output table name',
                                                       'invalid_polygons'))
        self.addParameter(QgsProcessingParameterString(self.OPTIONS,
                                                       'Additional creation options (see ogr2ogr manual)',
                                                       '',
                                                       optional=True))

    def processAlgorithm(self, parameters, context, feedback):
        inLayerA = self.parameterAsVectorLayer(parameters, self.INPUT_LAYER_A, context)
        ogrLayerA = GdalUtils.ogrConnectionStringFromLayer(inLayerA)[1:-1]
        layernameA = GdalUtils.ogrLayerName(inLayerA.dataProvider().dataSourceUri())

        fields = self.parameterAsFields(parameters, self.FIELDS, context)

        uri = QgsDataSourceUri(inLayer.source())
        geomColumn = uri.geometryColumn()
        wkbType = layer.wkbType()
        srid = layer.crs().postgisSrid()

        schema = self.parameterAsString(parameters, self.SCHEMA, context)
        table = self.parameterAsString(parameters, self.TABLE, context)
        options = self.parameterAsString(parameters, self.OPTIONS, context)

        if len(fields) > 0:
           fieldstring = "," + ",".join(fields)
        else:
           fieldstring = ""

        if wkbType == QgsWkbTypes.Polygon:
           layertype = "POLYGON"
           sqlstring = "-sql \"SELECT (ST_Dump(g1." + geomColumn + ")).geom::geometry(" + layertype + "," + str(srid) + ") AS geom, ST_IsValidReason(" + geomColumn + ") AS invalid_reason" + fieldstring + " FROM " + layername + " AS g1 WHERE NOT ST_IsValid(" + geomColumn + ")\" -nlt " + layertype + " -nln " + schema + "." + table + " -lco FID=gid -lco GEOMETRY_NAME=geom --config PG_USE_COPY YES"
        else:
            layertype = "MULTIPOLYGON"
            sqlstring = "-sql \"SELECT (g1." + geomColumn + ")::geometry(" + layertype + "," + str(srid) + ") AS geom, ST_IsValidReason(" + geomColumn + ") AS invalid_reason" + fieldstring + " FROM " + layername + " AS g1 WHERE NOT ST_IsValid(" + geomColumn + ")\" -nlt " + layertype + " -nln " + schema + "." + table + " -lco FID=gid -lco GEOMETRY_NAME=geom --config PG_USE_COPY YES"

        arguments = []
        arguments.append('-f')
        arguments.append('PostgreSQL')
        arguments.append(ogrLayer)
        arguments.append(ogrLayer)
        arguments.append(sqlstring)
        arguments.append('-overwrite')

        if len(options) > 0:
            arguments.append(options)

        commands = ['ogr2ogr', GdalUtils.escapeAndJoin(arguments)]
        GdalUtils.runGdal(commands, feedback)

        return {}
