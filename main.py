# -*- coding: utf-8 -*-
"""
Created on Wed Dec  7 23:29:59 2022

@author: Sandeep Allampalli
"""
import numpy as np
import scipy
import wradlib as wrl
import xarray as xr
import rioxarray 
import geopandas as gpd
import cartopy
import cartopy.crs as ccrs
import shapely
from shapely.geometry import mapping
import matplotlib.pyplot as plt
import os
import sys
import tarfile

print(sys.path)
os.getcwd()
filepath = "C:/Users/v-sandeepa/Desktop/Personal/Thesis/"        # Directory folder path(replace it with your own directory path).
os.chdir(filepath)

# Define the directory where the archives are located
tar_dir = filepath + "Raw Data/"                                 # Sub folder created in the directory where the downloaded raw data was saved.
dest_dir = filepath + "Extracted Data/"                          # Subfolder where the extracted data was saved.

# Loop through all files in the directory                       #---------------------------------------------------------------------------------------
for filename in os.listdir(tar_dir):
    # Check if the file is a .tar.gz archive
    if filename.endswith('.tar.gz'):
        # Open the archive
        tar = tarfile.open(os.path.join(tar_dir, filename))     # this piece of code extracts the raw data files to the extracted data folder   
        
        # Extract all files to a directory
        tar.extractall(path=dest_dir)
        
        # Close the archive
        tar.close()                                             #---------------------------------------------------------------------------------------



dict(xarray=xr.__version__, rioxarray=rioxarray.__version__, geopandas=gpd.__version__, cartopy=cartopy.__version__, 
     shapely=shapely.__version__, wradlib=wrl.__version__)

# binary data files downloaded from https://opendata.dwd.de/climate_environment/CDC/grids_germany/hourly/radolan/historical/bin/
# load radolan raster data
fname = "Extracted Data/raa01-rw_10000-*-dwd---bin.gz"
rad = xr.open_mfdataset(fname, engine="radolan")
rad.RW.encoding["_FillValue"] = 65536             # fix encoding _FillValue
# rad

#rad.to_netcdf("D:/Sandeep/Thesis/Data/rad_2006.nc", mode="w")
#rad_2006 = xr.open_dataset("D:/Sandeep/Thesis/Data/rad_2006.nc", chunks={"time":1})

#setup projection
proj_radolan = ccrs.Stereographic(
    true_scale_latitude=60.0, central_latitude=90.0, central_longitude=10.0
)

rad.rio.set_spatial_dims(x_dim="x", y_dim="y", inplace=True)
rad.rio.write_crs(proj_radolan, inplace=True)

#Load German federal states shapefile
germany = gpd.read_file(filepath + "VG2500_LAN.shp")
germany.crs
germany.crs = "EPSG:3857"


#Extract Brandenburg
brandenburg = germany.loc[[11], "geometry"]
brandenburg.plot()
brandenburg = brandenburg.set_crs(germany.crs)


#Clip using rioxarray clip_box
bounds = brandenburg.to_crs(proj_radolan).bounds.iloc[0]

bounds.minx = rad.x.min().values
bounds.miny = rad.y.min().values
bounds.maxx = rad.x.max().values
bounds.maxy = rad.y.max().values

clip_box = rad.rio.clip_box(bounds.minx, bounds.miny, bounds.maxx, bounds.maxy)
# clip_box

fig = plt.figure(figsize=(12, 6))
ax = fig.add_subplot(projection=ccrs.PlateCarree())
clip_box.RW[0].plot(ax=ax, transform=proj_radolan)
ax.gridlines(draw_labels=True, x_inline=False, y_inline=False)


bounds_brandenburg = brandenburg.to_crs(proj_radolan).bounds.iloc[0]
bounds_brandenburg['minx'] = rad.x.min().values
bounds_brandenburg['miny'] = rad.y.min().values
bounds_brandenburg['maxx'] = rad.x.max().values
bounds_brandenburg['maxy'] = rad.y.max().values

clip_shape = rad.rio.clip_box(bounds_brandenburg.minx, bounds_brandenburg.miny, bounds_brandenburg.maxx, bounds_brandenburg.maxy)

#clip using rioxarray with shape
clip_shape = rad.rio.clip(brandenburg.geometry.apply(mapping), brandenburg.crs, drop=True)
# clip_shape

fig = plt.figure(figsize=(12, 6))
ax = fig.add_subplot(projection=ccrs.PlateCarree())
clip_shape.RW[0].plot(ax=ax, transform=proj_radolan)
ax.gridlines(draw_labels=True, x_inline=False, y_inline=False)

#------------------------------------------------------------------------------
#Next steps
#------------------------------------------------------------------------------

#Resample the data by daily, monthly, quarterly and yearly values.

#Do the analysis.

#Plot the data.

#Look for precipitation types(light or heavy rain)
pr_types = wrl.classify.pr_types
for k,v in pr_types.items():
    print(str(k) + "-".join(v))

#Compare with an other year to see the changes.


import matplotlib.pyplot as plt

# Set the time step index to plot
timestep_idx = 0

# Extract the data for the given time step
data = clip_box.RW.isel(time=timestep_idx)

# Plot the data
fig = plt.figure(figsize=(10, 10))
ax = fig.add_subplot(1, 1, 1, projection=proj_radolan)
ax.set_extent(bounds.to_list())
ax.add_feature(cartopy.feature.BORDERS, linestyle="-", alpha=.5)
ax.add_feature(cartopy.feature.COASTLINE, linestyle="-", alpha=.5)
ax.add_feature(cartopy.feature.LAKES, alpha=0.95)
ax.add_feature(cartopy.feature.RIVERS, alpha=0.95)
data.plot(ax=ax, transform=proj_radolan)
plt.show()


