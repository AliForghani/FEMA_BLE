## FEMA_BLE
A program to make shapefile and plot streamlines and cross sections of FEMA_BLE HEC-RAS models

## Background
Base Level Engineering (BLE) is an efficient modeling and mapping approach that provides credible flood hazard data, especially for areas where no flood hazard data exists. The Federal Emergency Management Agency (FEMA) develops BLE datasets for different parts of the US (on HUC8 level). Each BLE dataset consists of: 
- Thousands of 1-D HEC-RAS models
- A gdb file containing flood depth grids and the study area domain vector file

This repository provides tools to read HEC-RAS geometry text files and create shapefiles of streamlines and cross sections. The HEC-RAS models do not provide information on the projection of the coordinates used in geometry file. Instead, the gdb file needs to be processed to obtain projected coordinate system.

## Data

For illustration, we use the BLE dataset dowloaded from [FEMA](https://webapps.usgs.gov/infrm/estBFE/) for Lower Colorado-Cummins (HUC8 12090301) close to Austin, Texas, with ~2400 HEC-RAS models. We download two zip files of "12090301_Models.zip" and "12090301_SpatialData.zip" and unzip them inside a "Data" folder created inside this cloned repository. 

<img src="https://github.com/AliForghani/FEMA_BLE/assets/22843733/42d511ed-c05d-4a30-b16e-23bc9333d63e" alt="Image" width="50%">

Unzipping the "12090301_Models.zip" provides a "Model" folder containing HEC-RAS models and unzipping the "12090301_SpatialData.zip" will provide a gdb file inside "Spatial" folder:

![image](https://github.com/AliForghani/FEMA_BLE/assets/22843733/158b0015-e63a-4f7e-903b-d28a0039ed04)

![image](https://github.com/AliForghani/FEMA_BLE/assets/22843733/b6100884-cb01-4c11-b65d-afaccaa234fc)

We define below paths for data processing in next section. 
```python
RAS_models_path = r"../Data/Model"
Spatial_gdb_path= r"../Data/Spatial/BLE_LowColoradoCummins.gdb"
```

## Data Processing

First, we import the required packages including BLE class from BLE_Processor module:


```python
from BLE_Processor import BLE
import numpy as np
import geopandas as gpd
import glob
import os
import fnmatch
import matplotlib.pyplot as plt
import contextily as ctx
from shapely.geometry import Point
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
```
Create an object of the class BLE to access the package methods
```python
ble = BLE()
```

For the users having arcpy license, EPSG code (coordinate system) of the study area can be read using 'get_epsg()' method of BLE class. Without an arcpy license, gdb file should be opened by QGIS and EPSG code (2277) can be derived from raster files (shown in green box). The other contents of the gdb (Feature Datasets and tables) only provide the geographic coordinate system and not a projected coordinate system as used for streamline and cross section coordinates in geometry files. At this time, we could not find any open-source python package that can read raster files inside an ESRI gdb file to obtain EPSG. 


<img src="https://github.com/AliForghani/FEMA_BLE/assets/22843733/bd48edcf-8983-44b5-9d3c-fa5d17554230" alt="Image" width="50%">

```python
#if you have arcpy license, get EPSG code as below
EPSG= ble.get_epsg(Spatial_gdb_path)
print(EPSG)
2277

#if you do not have arcpy license, use QGIS to get EPSG and then assign EPSG manually
EPSG=2277 
```

Before processing all ~2400 HEC-RAS models, it is a good idea to process a single HEC-RAS model geometry file and plot cross sections and streamlines. We can use "read_geometry()" method of BLE class to make GeoDataFrame 
objects for cross sections and streamline of the provided geometry file. The EPSG code derived from previous section is an input argument for the "read_geometry()" method.


```python
geometry_path=r"../Data\Model\Piney Creek-Colorado River\BURLSON CREEK\BURLSON CREEK.g01"
river_gdf,Xsection_gdf= ble.read_geometry(geometry_path,EPSG)

#above GeoDataFrames can be saves as a shapefile. Also, we can them
ax=plt.subplot(1,1,1)
Xsection_gdf.plot(ax=ax, color='red')
river_gdf.plot(ax=ax, color='blue')
plt.axis('off')
```
![image](https://github.com/AliForghani/FEMA_BLE/assets/22843733/2bbf4536-c880-4b79-84bb-f6b8e5204120)

Now, we can process all ~2400 HEC-RAS models
```python
#geometry text files have extension of '.g01'
pattern = "*.g01"

#first get all files 
all_files = glob.glob(os.path.join(RAS_models_path, '**/*'), recursive=True)

#then only select geometry files
Geo_files= fnmatch.filter(all_files, pattern)
```
Make a shapefile for models streamlines inside below directory following the same directory tree as the models directory
```python
parent_output_dir= r"../Data\River_SHP"
for geo_file_id, geo_file in enumerate(Geo_files,1):
    print("working on %d/%d"%(geo_file_id, len(Geo_files)))
    
    # call the read_geometry method to make GeoDataFrame for streamlines (and Xsections) of each HEC-RAS model
    this_file_river_gdf,this_file_xsec_gdf=ble.read_geometry(geo_file,EPSG)
    
    #make the name of shp file the same as geometry (**.g files)
    shp_name=os.path.basename(geo_file)[0:-3]+'shp'
    
    #build the directory to save shp file...it should folow the directory tree of HEC-RAS models
    #first split the path of the *.g01 file
    folders, filename=os.path.split(geo_file)
    folders_splitted=folders.split(os.sep)
    
    #find the index of the parent "Model" directory containing all HEC-RAS models
    parent_index=0
    for folder_index, folder in enumerate(folders_splitted):
        if folder == 'Model':
            parent_index = folder_index
    
    #build the relative path for each shp file
    relative_path=folders_splitted[parent_index+1:]  
    
    #also add the requested parent output directory into the beginning of the above relatrive path
    output_dir=os.path.join(parent_output_dir,*relative_path)

    #now create the directory before saving the shp file into it
    os.makedirs(output_dir, exist_ok=True)

    #save shp files
    this_file_river_gdf.to_file(os.path.join(output_dir,shp_name))
```

~2400 shapefiles of streamlines of all ~2400 HEC-RAS models have been created! Also, make a GeoDataFrame object for the domain of study area (HUC8) from gdb file using "read_domain()" method of the BLE class:
```python
domain_gdf=ble.read_domain( Spatial_gdb_path, EPSG)
domain_gdf
```
![image](https://github.com/AliForghani/FEMA_BLE/assets/22843733/92f9e3c5-34c7-49ec-8df1-a4a6b5d32840)

find the streamlines that are not completely inside the domain (likely due to a mistake in the creation of geometry file)
```python
#a function to return True if some part of streamlines is outside  domain
def is_river_outside_domain(line, polygon):
    line_coords = line.coords
    for coord in line_coords:
        point = Point(coord)
        if not polygon.contains(point):
            return True
    return False

#read all shapefiles
parent_output_dir= r"../Data\River_SHP"
pattern = "*.shp"
all_files = glob.glob(os.path.join(parent_output_dir, '**/*'), recursive=True)
shp_files = fnmatch.filter(all_files, pattern)

shps_out_of_domain = []
domain_polygon=domain_gdf.loc[0,'geometry']
for shp_id, shp_name in enumerate(shp_files, 1):
    print("working on %d (%d)" % (shp_id, len(shp_files)))
    river_gdf = gpd.read_file(shp_name)
    river_lines=river_gdf.loc[0,"geometry"]
    
    if is_river_outside_domain(river_lines,domain_polygon ):
        shps_out_of_domain.append(shp_name)
```
![image](https://github.com/AliForghani/FEMA_BLE/assets/22843733/1cb702ec-ee91-47d2-99c2-e77c27cc62b5)

There are 12 shp files that are out of the domain. Plotting these 12 shp can reveal if they are completely out of domain or just overlaping the domain boundary:  
```python
#plot the shapefiles that were found to be outside domain
AllRiv_outside = gpd.GeoDataFrame()
for shp_name in shps_out_of_domain:
    river_gdf = gpd.read_file(shp_name)
    AllRiv_outside=AllRiv_outside.append(river_gdf)

ax = plt.subplot(1, 1, 1)
domain_gdf.boundary.plot(ax=ax, color='red')
AllRiv_outside.plot(ax=ax, color='blue')
plt.axis('off')
```
<img ![image](https://github.com/AliForghani/FEMA_BLE/assets/22843733/960f3994-de1e-40e2-98f1-9b913334523f) width="50%">

Above plot shows that one shp file ('../River_SHP\Rabbs Creek-Colorado River\RABBS 0421\RABBS 0421.shp') has major error and needs to be excluded from the final plot.
```python
#now plot all streamlines with the HUC8 domain in a single plot
AllRiv = gpd.GeoDataFrame(crs="EPSG:%d"%EPSG)
for shp_name in shp_files:
    if os.path.basename(shp_name) != 'RABBS 0421.shp':
        river_gdf = gpd.read_file(shp_name)
        AllRiv=AllRiv.append(river_gdf)

ax = plt.subplot(1, 1, 1)
domain_gdf.boundary.plot(ax=ax, color='red')
AllRiv.plot(ax=ax, color='blue')
ax.set_title("Streamlines in Lower Colorado-Cummins (HUC8 12090301)")
ctx.add_basemap(ax, crs=AllRiv.crs.to_string(), source=ctx.providers.Stamen.TonerLabels, zoom=9)
ctx.add_basemap(ax, crs=AllRiv.crs.to_string(), source=ctx.providers.Stamen.Watercolor)
plt.axis('off')
```
![image](https://github.com/AliForghani/FEMA_BLE/assets/22843733/76e60b95-c652-4e56-b086-a51c232f4c01)

