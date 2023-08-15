# FEMA_BLE
A program to make shapefile and plot streamlines of FEMA_BLE HEC-RAS models

# Background
Base Level Engineering (BLE) is an efficient modeling and mapping approach that provides credible flood hazard data, especially for areas where no flood hazard data exists. The Federal Emergency Management Agency (FEMA) develops BLE datasets for different parts of the US (on HUC8 level). Each BLE dataset consists of: 
- Thousands of 1-D HEC-RAS models
- A gdb file containing flood depth grids and the study area domain vector file

This repo provides tools to read HEC-RAS geometry text files and create shapefiles of streamlines and cross sections. However, the HEC-RAS models do not provide information on the projection of the coordintaes. This repo shows a method to derive the projection using arcpy package. 

# Data

To illustrate, we use the BLE dataset dowloaded from [FEMA](https://webapps.usgs.gov/infrm/estBFE/) for Lower Colorado-Cummins (HUC8 12090301) close to Austin, Texas, with ~2400 HEC-RAS models. We download two zip files of "12090301_Models.zip" and "12090301_SpatialData.zip" and will work with them. 
![image](https://github.com/AliForghani/FEMA_BLE/assets/22843733/42d511ed-c05d-4a30-b16e-23bc9333d63e)

Unzipping the "12090301_Models.zip" provides a "Model" folder containing HEC-RAS models and unzipping the "12090301_SpatialData.zip" will provide a gdb file inside "Spatial" folder:

![image](https://github.com/AliForghani/FEMA_BLE/assets/22843733/158b0015-e63a-4f7e-903b-d28a0039ed04)

![image](https://github.com/AliForghani/FEMA_BLE/assets/22843733/b6100884-cb01-4c11-b65d-afaccaa234fc)

We define below paths for data processing. 
```python
RAS_models_path = r"../Data/Model"
Spatial_gdb_path= r"../Data/Spatial/BLE_LowColoradoCummins.gdb"
```

# Data Processing

First, we import the required packages including BLE class from BLE_Processor


```python
from BLE_Processor import BLE
import numpy as np
import geopandas as gpd
import glob
import os
import fnmatch
import matplotlib.pyplot as plt
from shapely.geometry import Point
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
```
Create an object of the class BLE to access the package methods
```python
ble = BLE()
```

Before processing all ~2400 HEC-RAS models, we can process a single HEC-RAS model geometry file and plot cross sections and streamlines. For the users having arcpy license, EPSG code (coordinate system) of the study area 
can be read using 'get_epsg()' method as shown below
```python
#if you have arcpy license, get EPSG code as below
EPSG= ble.get_epsg(Spatial_gdb_path)
print(EPSG)
2277

#if you do not have arcpy license, use QGIS to get EPSG and then assign EPSG manually
EPSG=2277 
```
Without an arcpy license, gdb file should be opened by QGIS and EPSG code (2277) can be derived from raster files (shown in green box). The other contents of the gdb (Feature Datasets and tables) only provide the geographic coordinate system and not a projected coordinate system as used for streamline and cross section coordinates in geometry files. 
![image](https://github.com/AliForghani/FEMA_BLE/assets/22843733/bd48edcf-8983-44b5-9d3c-fa5d17554230)


```python
geometry_path= r"../Data/Model/Piney Creek-Colorado River/BURLSON CREEK/BURLSON CREEK.g01"
```
