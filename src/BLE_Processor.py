import pandas as pd
import flopy
import numpy as np
import geopandas as gpd
from shapely.geometry import Point, LineString
from pathlib import Path
import os
import glob
from pyproj import CRS



class BLE (object):

    def get_epsg(self,gdb_path):
        '''
        This method needs arcpy license
        input is the path to the FEMA gdb file accompanied with HEC-RAS models
        output is the EPSG code, or appropriate warning messages if no unique EPSG was derived from gdb
        '''
        import arcpy

        # set workspace
        arcpy.env.workspace = gdb_path

        # list all rasters available in the gdb file
        rasters = arcpy.ListRasters()
        if len(rasters) == 0 :
            print("Error: There is no raster file in the given gdb file")
            return None

        # read all raster files and records their EPSG code
        EPSG_codes = []
        for raster_name in rasters:
            raster = arcpy.Raster(raster_name)
            sr = raster.spatialReference
            epsg_code = sr.factoryCode
            EPSG_codes.append(epsg_code)

        # count the number of unique EPSGs
        unique_count = len(set(EPSG_codes))

        if unique_count == 1:
            return EPSG_codes[0]
        elif unique_count == 0:
            print("Warning: Rasters spatial references do not have corresponding EPSG codes.")
        elif unique_count > 1 :
            print("Warning! There are multiple EPSG codes for the rasters in the provided gdb file")
            return set(EPSG_codes)

    def river_centerline_shp(self,geo_file_path,ReachInfoDF):
        '''
        inputs are 1) path to the HEC-RAS geometry text file, 2) A Pandas DataFrame with reach info
        output is a GeoDataFrame of the streamlines of the HEC-RAS model
        '''
        AllReachesPoints_gpd_list=[] 
        for i, row in ReachInfoDF.iterrows():
            reachname, reachstart, reachend = row["river, reach"], row['StartlineNo'], row['EndlineNo']
            with open(geo_file_path) as TXTFile:
                for linenumer, line in enumerate(TXTFile):
                    if linenumer >= reachstart and linenumer < reachend:
                        if line.startswith('River Reach'):
                            rivername, reachname = line.split('=')[-1].split(",")
                            Count=int(TXTFile.readline().split('=')[-1])
                            ThisXs = flopy.utils.Util2d.load_txt((Count, 2), TXTFile, np.float64, "(10F16.0)")
                            geometry = [Point(xy) for xy in zip(ThisXs[:, 0], ThisXs[:, 1])]

                            ThisReach_Points = gpd.GeoDataFrame(geometry=geometry)
                            ThisReach_Points["river_reach"] = "%s,%s"%(rivername,reachname)

                    elif linenumer >= reachend:
                        break

            AllReachesPoints_gpd_list.append(ThisReach_Points)
        AllReachesPoints=pd.concat(AllReachesPoints_gpd_list)
        AllReachesLines = AllReachesPoints.groupby(['river_reach'],as_index=False)['geometry'].apply(lambda x: LineString(x.tolist()))
        AllReachesLines['river']=AllReachesLines.apply(lambda row: row.river_reach.split(',')[0], axis=1)
        AllReachesLines['reach'] = AllReachesLines.apply(lambda row: row.river_reach.split(',')[1], axis=1)
        AllReachesLines.drop(columns=["river_reach"], inplace=True)
        return AllReachesLines

    def xsec_shp(self,geo_file_path,ReachInfoDF):
        '''
        inputs are 1) path to the HEC-RAS geometry text file, 2) A Pandas DataFrame with reach info
        output is a GeoDataFrame of the cross sections of the HEC-RAS model
        '''
        AllXsPoints_gpd_list = []
        for i, row in ReachInfoDF.iterrows():
            reachname, reachstart, reachend = row["river, reach"], row['StartlineNo'], row['EndlineNo']
            ThisReach_Points_gpd_list=[]
            with open(geo_file_path) as TXTFile:
                for linenumer, line in enumerate(TXTFile):
                    if linenumer >= reachstart and linenumer < reachend:
                        if line.startswith('Type RM Length L Ch R'):
                            stn = line.split('=')[-1].split(",")[1]
                            #it is possible to have description or other info for the Xsection, so move on until Xs GIS
                            while 1:
                                CountLine=TXTFile.readline()
                                if CountLine.startswith("XS GIS Cut Line"):
                                    break

                            Count = int(CountLine.split('=')[-1])
                            ThisXs = flopy.utils.Util2d.load_txt((Count, 2), TXTFile, np.float64, "(10F16.0)")
                            geometry = [Point(xy) for xy in zip(ThisXs[:, 0], ThisXs[:, 1])]

                            ThisXsectionPoints = gpd.GeoDataFrame(geometry=geometry)
                            ThisXsectionPoints['Xsectionid'] = "%s,%s" % (reachname, stn)
                            ThisReach_Points_gpd_list.append(ThisXsectionPoints)

                    elif linenumer >= reachend:
                        break

            ThisReach_Points=pd.concat(ThisReach_Points_gpd_list)
            AllXsPoints_gpd_list.append(ThisReach_Points)
        AllXsPoints=pd.concat(AllXsPoints_gpd_list)
        AllXsLines = AllXsPoints.groupby(['Xsectionid'],as_index=False)['geometry'].apply(lambda x: LineString(x.tolist()))
        AllXsLines['river']=AllXsLines.apply(lambda row: row.Xsectionid.split(',')[0], axis=1)
        AllXsLines['reach'] = AllXsLines.apply(lambda row: row.Xsectionid.split(',')[1], axis=1)
        AllXsLines['stn'] = AllXsLines.apply(lambda row: row.Xsectionid.split(',')[2], axis=1)
        AllXsLines.drop(columns=["Xsectionid"], inplace=True)
        return AllXsLines


    def read_geometry(self,geo_file_path, EPSG):
        '''
        - the input is the path to HEC-RAS geometry text file
        - returns two GeoDataFrames for HEC-RAS model's 1) the streamline  2) cross sections
        '''

        #find lines of reach definition
        ReachInfo=[]
        ReachNum=0
        with open(geo_file_path) as TXTFile:
            for lineid, line in enumerate(TXTFile):
                if line.startswith('River Reach'):
                    ReachNum += 1
                    ReachString = line.split('=')[-1][0:-2]
                    ReachInfo.append([ReachNum,ReachString,lineid])
                else:
                    continue
        ReachInfoDF=pd.DataFrame(ReachInfo, columns=["id","river, reach", 'StartlineNo'])
        ReachInfoDF['EndlineNo']=ReachInfoDF['StartlineNo'].shift(-1)
        ReachInfoDF.iloc[-1,-1]=np.inf

        river_gdf=self.river_centerline_shp(geo_file_path,ReachInfoDF)
        xsec_gdf=self.xsec_shp(geo_file_path,ReachInfoDF)

        #assign crs
        river_gdf.crs = EPSG
        xsec_gdf.crs = EPSG

        return river_gdf,xsec_gdf


    def read_domain(self,gdb_path, EPSG, driver='FileGDB', layer='S_HUC_Ar'):
        '''
        Required inputs are path to the gdb file and EPSG code. Optionally driver and layer name can be adjusted
        '''
        domain_gdf = gpd.read_file(gdb_path, driver=driver, layer=layer)

        #the domain already has EPSG 4269 crs, reproject it to the given EPSG
        target_crs = CRS.from_epsg(EPSG)
        domain_gdf.to_crs(target_crs, inplace=True)

        return domain_gdf







