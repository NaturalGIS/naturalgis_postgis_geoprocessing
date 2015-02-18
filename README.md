PostGIS geoprocessing tools for the QGIS processing toolbox
--------------------------------------

![](/icons/naturalgis.png)

Developed by NaturalGIS 

web: http://www.naturalgis.pt/ 

email: giovanni.manghi@naturalgis.pt

This tools are meant to allow users do Spatial Analysis leveraging on the power of PostGIS (http://postgis.net/) spatial functions/operators, but without needing the Knowledge of Spatial SQL.

The plugin needs QGIS 2.8 to work.

This tools will benefit from a few improvements will be made to the QGIS Processing toolbox, that at this time are missing.

Notes:

- This tools are meant to be used only with PostGIS layers, and as output they will create new PostGIS layer, meaning that the user needs permissions to write in the Database where the inputs layers come from.

Known issues:

- At the moment there is no way to add the outputs directly in the QGIS project after the geoprocessing operation ends

- Processing misses an option to allow choose multiple columns/attributes for a certain inuput layer, this would be useful for certain operations