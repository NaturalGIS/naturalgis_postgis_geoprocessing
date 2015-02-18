Vector geoprocessing tools for the QGIS processing toolbox, based on ogr2ogr, Spatialite and PostGIS
--------------------------------------

Experimental plugin for the QGIS Processing toolbox.

This tools are meant to allow users do Spatial Analysis leveraging on the power of PostGIS (http://postgis.net/) and Spatialite (http://www.gaia-gis.it/gaia-sins/) spatial functions/operators, but without needing the Knowledge of Spatial SQL.

The real hero is anyway the command line tool ogr2ogr (http://www.gdal.org/ogr2ogr.html) that is used to run the spatial queries.

The plugin needs QGIS master (2.7) to work and it will stop to be experimental only when a few improvements will be added to the QGIS Processing toolbox, that at this time are missing.

Notes:

- The tools in the "Geoprocessing" group can accept as input the following (tested) formats: Shapefiles, Spatialite and PostGIS. This tool will output a Shapefile as a result, but in future outputting to Spatialite could be added.

- The tools in the "PostGIS Geoprocessing" group are meant to work only with PostGIS layers (but at this stage the tools will show also other type of layers as possible inputs) and output also will be created directly inside a PostGIS database (the same where the inputs come from, so writing permissions are needed).

Known issues:

- input layers must have an explicit geometry column. At the moment supported formats are shapefiles (with a geometry column named "geometry"), Spatialite and PostGIS.

- in some case it is asked to specify the name of the geometry column, in the future this could be avoided when processing will support a way to list just the input data layers belonging to supported formats

- when tools are run and something goes wrong there are cases that in the "log" tab of the tool does not show anything that can warn the user (but useful info can be found inside the processing history, in the "info" section)

- in case of tools of the "PostGIS Geoprocessing" group at the moment there is no way to add directly in QGIS the result of the operation

- Processing misses an option to allow choose multiple columns/attributes for a certain inuput layer, this would be useful for certain operations

- the toos in the "Geoprocessing" group can at the moment only do operations involving 1 input layer: in Processing must be implemented a mechanism to transform 2 or more input layers into 1 virtual vector layer (.vrt)