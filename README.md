PostGIS geoprocessing tools for the QGIS processing toolbox
--------------------------------------

![](/icons/naturalgis.png)

Developed by/for NaturalGIS 

web: http://www.naturalgis.pt/ 

email: giovanni.manghi@naturalgis.pt

This tools are meant to allow users do Spatial Analysis leveraging on the power of PostGIS (http://postgis.net/) spatial functions/operators without needing Knowledge of Spatial SQL.

The plugin needs QGIS 3.4 to work.

Main contributors:

- Alexander Bruy: developer of the QGIS/GDAL-OGR Processing based tools that gave the idea for this plugin, porting of the code to the QGIS 3 API
- Giovanni Manghi (giovanni.manghi@naturalgis.pt)

Supported operations:

- Select by (select by location)

- Sample polygons with points

- Distance matrix

- Buffer (fixed distance)

- Buffer (variable distance)

- Clip points, lines and polygons

- Closest point

- Dissolve polygons

- Extract invald polygons (ST_IsValid)

- Fix invalid polygons (ST_MakeValid)

- Fix invalid polygons (ST_Buffer)

- Minimum distance

- Polygon difference (non symmetrical)

Notes:

- This tools are meant to be used only with PostGIS layers, and as output they will create new PostGIS layer, meaning that the user needs permissions to write in the Database where the inputs layers come from.

- As expected when working directly inside a PostGIS database, the tools that need two inputs layers this must be in the same CRS/SRID.

Known issues:

- At the moment there is no way to add the outputs directly in the QGIS project after the geoprocessing operation ends.
