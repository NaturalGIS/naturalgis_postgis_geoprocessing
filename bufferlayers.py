# -*- coding: utf-8 -*-

"""
***************************************************************************
    bufferlayers.py
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
from processing.tools import vector

from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.algs.gdal.GdalUtils import GdalUtils
from processing.tools.vector import ogrConnectionString, ogrLayerName

class bufferlayers(GeoAlgorithm):

    OUTPUT_LAYER = 'OUTPUT_LAYER'
    INPUT_LAYER = 'INPUT_LAYER'
    GEOMETRY = 'GEOMETRY'
    DISTANCE = 'DISTANCE'
    DISSOLVEALL = 'DISSOLVEALL'
    FIELDS = 'FIELDS'
    DISSFIELD = 'DISSFIELD'
    SINGLE = 'SINGLE'
    TABLE = 'TABLE'
    SCHEMA = 'SCHEMA'
    OPTIONS = 'OPTIONS'
    OUTPUT = 'OUTPUT'
    
    def getIcon(self):
        return  QIcon(os.path.dirname(__file__) + '/icons/postgis.png')

    def defineCharacteristics(self):
        self.name = 'Buffer (fixed distance)'
        self.group = 'Vector geoprocessing'

        self.addParameter(ParameterVector(self.INPUT_LAYER,
            self.tr('Input layer'), [ParameterVector.VECTOR_TYPE_ANY], False))
        self.addParameter(ParameterString(self.FIELDS, 'Attributes to keep (comma separated list). Aliasing permitted. Ignored if dissolving outputs.',
                          '', optional=False))
        self.addParameter(ParameterString(self.DISTANCE,
            self.tr('Buffer distance'), '1000', optional=False))
        self.addParameter(ParameterBoolean(self.DISSOLVEALL,
            self.tr('Dissolve all'), False))
        self.addParameter(ParameterTableField(self.DISSFIELD,
            self.tr('Dissolve by attribute (ignored if "Dissolve all" is selected)'), self.INPUT_LAYER, optional=True))
        self.addParameter(ParameterBoolean(self.SINGLE,
            self.tr('Force output as singlepart'), False))
        self.addParameter(ParameterString(self.SCHEMA, 'Output schema',
                          'public', optional=False))
        self.addParameter(ParameterString(self.TABLE, 'Output table name',
                          'buffer', optional=False))
        self.addParameter(ParameterString(self.OPTIONS,
            self.tr('Additional creation options (see ogr2ogr manual)'),
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
        fields = unicode(self.getParameterValue(self.FIELDS))
        dissfield = unicode(self.getParameterValue(self.DISSFIELD))
        schema = unicode(self.getParameterValue(self.SCHEMA))
        table = unicode(self.getParameterValue(self.TABLE))
        options = unicode(self.getParameterValue(self.OPTIONS))
        distance = unicode(self.getParameterValue(self.DISTANCE))
        dissolveall = self.getParameterValue(self.DISSOLVEALL)
        single = self.getParameterValue(self.SINGLE)

        if len(fields) > 0:
           fieldstring = fields + ","
        else:
           fieldstring = ""

        if dissolveall:
             if single:
                query = '-sql "SELECT (ST_Dump(ST_Multi(ST_Union(ST_Buffer(' + geomColumn + ',' + distance + '))))).geom::geometry(POLYGON,' + str(srid) + ') AS geom FROM ' + layername + '" -nln ' + schema + '.' + table + ' -nlt POLYGON -lco FID=gid -lco GEOMETRY_NAME=geom --config PG_USE_COPY YES'
             else:
                query = '-sql "SELECT (ST_Multi(ST_Union(ST_Buffer(' + geomColumn + ',' + distance + '))))::geometry(MULTIPOLYGON,' + str(srid) + ') AS geom FROM ' + layername + '" -nln ' + schema + '.' + table + ' -nlt MULTIPOLYGON -lco FID=gid -lco GEOMETRY_NAME=geom --config PG_USE_COPY YES'
        else:
           if dissfield != 'None':
             if single:
                query = '-sql "SELECT ' + dissfield + ',(ST_Dump(ST_Union(ST_Buffer(' + geomColumn + ',' + distance + ')))).geom::geometry(POLYGON,' + str(srid) + ') AS geom FROM ' + layername + ' GROUP BY ' + dissfield + '" -nln ' + schema + '.' + table + ' -nlt POLYGON -lco FID=gid -lco GEOMETRY_NAME=geom --config PG_USE_COPY YES'       
             else:
                query = '-sql "SELECT ' + dissfield + ',(ST_Multi(ST_Union(ST_Buffer(' + geomColumn + ',' + distance + '))))::geometry(MULTIPOLYGON,' + str(srid) + ') AS geom FROM ' + layername + ' GROUP BY ' + dissfield + '" -nln ' + schema + '.' + table + ' -nlt MULTIPOLYGON -lco FID=gid -lco GEOMETRY_NAME=geom --config PG_USE_COPY YES'
           else:
             if single:
                query = '-sql "SELECT ' + fieldstring + '(ST_Dump(ST_Multi(ST_Buffer(' + geomColumn + ',' + distance + ')))).geom::geometry(POLYGON,' + str(srid) + ') AS geom FROM ' + layername + '" -nln ' + schema + '.' + table + ' -nlt POLYGON -lco FID=gid -lco GEOMETRY_NAME=geom --config PG_USE_COPY YES'
             else:
                query = '-sql "SELECT ' + fieldstring + '(ST_Multi(ST_Buffer(' + geomColumn + ',' + distance + ')))::geometry(MULTIPOLYGON,' + str(srid) + ') AS geom FROM ' + layername + '" -nln ' + schema + '.' + table + ' -nlt MULTIPOLYGON -lco FID=gid -lco GEOMETRY_NAME=geom --config PG_USE_COPY YES'

        print dissfield 
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