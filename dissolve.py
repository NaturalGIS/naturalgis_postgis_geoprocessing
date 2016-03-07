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

class dissolve(GeoAlgorithm):

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
    OUTPUT = 'OUTPUT'
    
    def getIcon(self):
        return  QIcon(os.path.dirname(__file__) + '/icons/postgis.png')

    def defineCharacteristics(self):
        self.name = 'Dissolve polygons'
        self.group = 'Vector geoprocessing'

        self.addParameter(ParameterVector(self.INPUT_LAYER,
            self.tr('Input layer'), [ParameterVector.VECTOR_TYPE_POLYGON], False))
        self.addParameter(ParameterBoolean(self.DISSOLVEALL,
            self.tr('Dissolve all'), False))
        self.addParameter(ParameterTableField(self.FIELD,
            self.tr('Dissolve field. Ignored if "Dissolve all" is selected.'), self.INPUT_LAYER))
        self.addParameter(ParameterBoolean(self.SINGLE,
            self.tr('Force output as singlepart'), False))
        self.addParameter(ParameterBoolean(self.COUNT,
            self.tr('Count dissolved features'), False))
        self.addParameter(ParameterBoolean(self.AREA,
            self.tr('Compute area and perimeter of dissolved features'), False))
        self.addParameter(ParameterBoolean(self.STATS,
            self.tr('Compute min/max/sum/mean for the following numeric attribute'), False))
        self.addParameter(ParameterTableField(self.STATSATT,
            self.tr('Numeric attribute to compute dissolved features stats'), self.INPUT_LAYER))
        self.addParameter(ParameterString(self.SCHEMA, 'Output schema',
                          'public', optional=False))
        self.addParameter(ParameterString(self.TABLE, 'Output table name',
                          'dissolved', optional=False))
        self.addParameter(ParameterString(self.OPTIONS, 'Additional creation options (see ogr2ogr manual)',
                          '', optional=True))
        self.addOutput(OutputHTML(self.OUTPUT, 'Output log'))
        
    def processAlgorithm(self, progress):
        inLayer = self.getParameterValue(self.INPUT_LAYER)
        ogrLayer = ogrConnectionString(inLayer)[1:-1]
        layername = ogrLayerName(inLayer)
        dsUri = QgsDataSourceURI(self.getParameterValue(self.INPUT_LAYER))
        geomColumn = dsUri.geometryColumn()
        layer = dataobjects.getObjectFromUri(self.getParameterValue(self.INPUT_LAYER))
        geomType = layer.geometryType()
        wkbType = layer.wkbType()
        srid = layer.crs().postgisSrid()
        field = unicode(self.getParameterValue(self.FIELD))
        statsatt = unicode(self.getParameterValue(self.STATSATT))
        stats = self.getParameterValue(self.STATS)
        area = self.getParameterValue(self.AREA)
        single = self.getParameterValue(self.SINGLE)
        count = self.getParameterValue(self.COUNT)
        schema = unicode(self.getParameterValue(self.SCHEMA))
        table = unicode(self.getParameterValue(self.TABLE))
        dissolveall = self.getParameterValue(self.DISSOLVEALL)
        options = unicode(self.getParameterValue(self.OPTIONS))

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

        #if fields:
        #   queryfields = ",*"
        #else:
        #   queryfields = "," + field
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
        query = querystart + querystats + queryarea + querycount +  queryend
        #query = querystart + queryfields + querycount + querystats + queryarea + queryend
        arguments = []
        arguments.append('-f')
        arguments.append('PostgreSQL')
        arguments.append(ogrLayer)
        arguments.append(ogrLayer)
        arguments.append(query)
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