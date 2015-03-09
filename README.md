PostGIS geoprocessing tools for the QGIS processing toolbox
--------------------------------------

![](/icons/naturalgis.png)

Developed by NaturalGIS 

web: http://www.naturalgis.pt/ 

email: giovanni.manghi@naturalgis.pt

This tools are meant to allow users do Spatial Analysis leveraging on the power of PostGIS (http://postgis.net/) spatial functions/operators, but without needing the Knowledge of Spatial SQL.

The plugin needs QGIS 2.8 to work.

This tools will benefit from a few improvements will be made to the QGIS Processing toolbox, that at this time are missing.

Supported operations:

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

- As expected when working directly inside a PostGIS database, in tools that need two inputs layers this mus me in the same CRS/SRID.

Known issues:

- At the moment there is no way to add the outputs directly in the QGIS project after the geoprocessing operation ends.

- Processing misses an option to allow choose multiple columns/attributes for a certain inuput layer, this would be useful for certain operations.

