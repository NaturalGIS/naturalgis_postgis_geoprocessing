# -*- coding: utf-8 -*-

"""
***************************************************************************
    dissolve.py
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
                       QgsDataSourceUri
                      )
from processing.algs.gdal.GdalUtils import GdalUtils

pluginPath = os.path.dirname(__file__)


class dissolve(QgsProcessingAlgorithm):

    OUTPUT_LAYER = 'OUTPUT_LAYER'
    INPUT_LAYER = 'INPUT_LAYER'
    FIELD = 'FIELD'
    DISSOLVEALL = 'DISSOLVEALL'
    SINGLE = 'SINGLE'
    COUNT = 'COUNT'
    STATS = 'STATS'
    STATSATT = 'STATSATT'
    AREA = 'AREA'
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
        return 'dissolvepolygons'

    def displayName(self):
        return 'Dissolve polygons'

    def group(self):
        return 'Vector geoprocessing'

    def groupId(self):
        return 'vectorgeoprocessing'

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT_LAYER,
                                                            'Input layer',
                                                            [QgsProcessing.TypeVectorPolygon]))
        self.addParameter(QgsProcessingParameterBoolean(self.DISSOLVEALL,
                                                        'Dissolve all',
                                                        False))
        self.addParameter(QgsProcessingParameterField(self.FIELD,
                                                      'Dissolve field. Ignored if "Dissolve all" is selected.',
                                                      None,
                                                      self.INPUT_LAYER))
        self.addParameter(QgsProcessingParameterBoolean(self.SINGLE,
                                                        'Force output as singlepart',
                                                        False))
        self.addParameter(QgsProcessingParameterBoolean(self.COUNT,
                                                        'Count dissolved features',
                                                        False))
        self.addParameter(QgsProcessingParameterBoolean(self.AREA,
                                                        'Compute area and perimeter of dissolved features',
                                                        False))
        self.addParameter(QgsProcessingParameterBoolean(self.STATS,
                                                        'Compute min/max/sum/mean for the following numeric attribute',
                                                        False))
        self.addParameter(QgsProcessingParameterField(self.STATSATT,
                                                      'Numeric attribute to compute dissolved features stats',
                                                      None,
                                                      self.INPUT_LAYER,
                                                      QgsProcessingParameterField.Numeric))
        self.addParameter(QgsProcessingParameterString(self.SCHEMA,
                                                       'Output schema',
                                                       'public'))
        self.addParameter(QgsProcessingParameterString(self.TABLE,
                                                       'Output table name',
                                                       'dissolved'))
        self.addParameter(QgsProcessingParameterString(self.OPTIONS,
                                                       'Additional creation options (see ogr2ogr manual)',
                                                       '',
                                                       optional=True))

    def processAlgorithm(self, parameters, context, feedback):
        inLayerA = self.parameterAsVectorLayer(parameters, self.INPUT_LAYER_A, context)
        ogrLayerA = GdalUtils.ogrConnectionStringFromLayer(inLayerA)[1:-1]
        layernameA = GdalUtils.ogrLayerName(inLayerA.dataProvider().dataSourceUri())

        uri = QgsDataSourceUri(inLayer.source())
        geomColumn = uri.geometryColumn()
        srid = inLayer.crs().postgisSrid()

        field = self.parameterAsString(parameters, self.FIELD, context)
        statsatt = self.parameterAsString(parameters, self.STATSATT, context)

        stats = self.parameterAsBool(parameters, self.STATS, context)
        area = self.parameterAsBool(parameters, self.AREA, context)
        single = self.parameterAsBool(parameters, self.SINGLE, context)
        count = self.parameterAsBool(parameters, self.COUNT, context)
        dissolveall = self.parameterAsBool(parameters, self.DISSOLVEALL, context)

        schema = self.parameterAsString(parameters, self.SCHEMA, context)
        table = self.parameterAsString(parameters, self.TABLE, context)
        options = self.parameterAsString(parameters, self.OPTIONS, context)

        if single:
           layertype = "POLYGON"
        else:
           layertype = "MULTIPOLYGON"

        if dissolveall:
           fieldstring = ""
        else:
           fieldstring = "," + field

        if single:
           layertype = "POLYGON"
        else:
           layertype = "MULTIPOLYGON"

        if dissolveall:
           fieldstring = ""
        else:
           fieldstring = "," + field

        if single:
            querystart = '-sql "SELECT (ST_Dump(ST_Union(' + geomColumn + '))).geom::geometry(POLYGON,' + str(srid) + ')' + fieldstring
        else:
            querystart = '-sql "SELECT (ST_Multi(ST_Union(' + geomColumn + ')))::geometry(MULTIPOLYGON,' + str(srid) + ')' + fieldstring

        if dissolveall:
            queryend = ' FROM ' + layername + '"' + " -nln " + schema + "." + table + " -nlt " + layertype + " -lco FID=gid -lco GEOMETRY_NAME=geom --config PG_USE_COPY YES"
        else:
            queryend = ' FROM ' + layername + ' GROUP BY ' + field + '"' + " -nln " + schema + "." + table + " -nlt " + layertype + " -lco FID=gid -lco GEOMETRY_NAME=geom --config PG_USE_COPY YES"

        if count:
           querycount = ", COUNT(" + geomColumn + ") AS count"
        else:
           querycount = ""

        if stats:
           querystats = ", SUM(" + statsatt + ") AS sum_dissolved, MIN(" + statsatt + ") AS min_dissolved, MAX(" + statsatt + ") AS max_dissolved, AVG(" + statsatt + ") AS avg_dissolved"
        else:
           querystats = ""

        if area:
           queryarea = ", SUM(ST_area(" + geomColumn + ")) AS area_dissolved, ST_perimeter(ST_union(" + geomColumn + ")) AS perimeter_dissolved"
        else:
           queryarea = ""

        query = querystart + querystats + queryarea + querycount + queryend
        arguments = []
        arguments.append('-f')
        arguments.append('PostgreSQL')
        arguments.append(ogrLayer)
        arguments.append(ogrLayer)
        arguments.append(query)
        arguments.append('-overwrite')

        if len(options) > 0:
            arguments.append(options)

        commands = ['ogr2ogr', GdalUtils.escapeAndJoin(arguments)]
        GdalUtils.runGdal(commands, feedback)

        return {}
