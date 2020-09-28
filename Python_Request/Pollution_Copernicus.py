#%% IMPORT

import cdsapi
import netCDF4
import xarray as xr
import pandas as pd
import datetime as dt
import folium
#%% Setup variables for Query

times = [str(i).zfill(2) + ':00' for i in range(0,24)] #Each hour from 00 to 23

#Data is only available starting from yesterday.
today = (dt.datetime.now()-dt.timedelta(days=1)).strftime( '%Y-%m-%d' )
yesterday = (dt.datetime.now()-dt.timedelta(days=2)).strftime( '%Y-%m-%d' )
dates = yesterday + '/' + today #From yesterday to today, how to get fro tomorrow.

#%% Query API

c = cdsapi.Client()
file_path = r'C:\Users\csucuogl\Desktop\WORK\MISC_TEST\Istanbul_AirQuality\test.nc' #Saving Locally For Now

c.retrieve(
    'cams-europe-air-quality-forecasts',
    {
        'variable': 'particulate_matter_2.5um',
        'model': 'ensemble',
        'level': '0',
        'date': dates ,
        'type': 'analysis', #How does 'forecast' work, there is one forcast per day.
        'time': times ,
        'leadtime_hour': '0',
        'area': [
            41.48, 28.17, 40.67,
            29.85,
        ],
        'format': 'netcdf',
    }, file_path )

ds_disk = xr.open_dataset( file_path )
dd = ds_disk.to_dict() #Convert to dict to convert to pandas

#%% Convert 4D data to long Pandas List.
dfo = pd.DataFrame(columns = ['lat','lon','time','values']) #Empty long list
for i in range( len( dd['data_vars']['pm2p5_conc']['data'] ) ): #for each time

    df = pd.DataFrame.from_dict( dd['data_vars']['pm2p5_conc']['data'][i][0] ) #NetCDF dict to table.
    df.index = dd['coords']['latitude']['data']
    df.columns = dd['coords']['longitude']['data']
    
    df = df.stack().reset_index() #Table to long list
    df.columns = ['lat','lon','values']
    toto = str( dd['coords']['time']['data'][i] ).split(':')[0]
    df['time'] = int(toto)
    
    dfo = dfo.append( df )

#%% For a single Time

dft = dfo[ dfo.time == 0 ]
dft

# %% Export Data to CSV fro further Processing ( Delete )
# Can I increase the reolution of the grid. 

import geopandas as gpd

gdf = gpd.GeoDataFrame(
    dft, geometry=gpd.points_from_xy(dft.lon, dft.lat))


# %% Increase Resolution using INverse Weighted Average of a Grid

import numpy as np 

grid = gpd.read_file( r"C:\Users\csucuogl\Desktop\WORK\MISC_TEST\Istanbul_AirQuality\Grid_64.shp" )
centers = grid.centroid

def haversine(coord1, coord2): #Calculate Distance in Meters
    import math
    lon1, lat1 = coord1
    lon2, lat2 = coord2
    R = 6371000  # radius of Earth in meters
    phi_1 = math.radians(lat1)
    phi_2 = math.radians(lat2)

    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi_1) * math.cos(phi_2) * math.sin(delta_lambda / 2.0) ** 2

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    meters = R * c  # output distance in meters
    meters = round(meters)
    return meters

wa = []
for i1,r1 in centers.iteritems():
    dist = []
    for i2,r2 in gdf.iterrows(): #Calculate the distanve of ech grid center to each measuement point
        t = haversine( (r1.x,r1.y) , (r2.geometry.x,r2.geometry.y) )
        dist.append( [t , r2['values']] )

    temp = pd.DataFrame( data = dist , columns = ['dist','value'])
    temp = temp[ temp['dist'] != 0 ] #Not itself
    temp = temp.sort_values(by='dist',ascending=True)[:32] #Closest 32
    temp['inv_dist'] = 1/temp['dist']

    weighted_avg = np.average(temp['value'].tolist(), weights=temp['inv_dist'].tolist() )
    wa.append( weighted_avg )

cents = gpd.GeoDataFrame( data = wa , geometry = grid.geometry , columns = ['values'] )
cents['id'] = [i for i in range(len(cents)) ]
cents.crs = {'init' :'epsg:4326'}
cents.head(4)

#%%

cents.to_file(r'C:\Users\csucuogl\Documents\GitHub\PollutionIstanbul\data\IstanbulPollution.geojson',driver="GeoJSON")
# %%
cents.head(4)

# %%
cents['values'].max() , cents['values'].min()
# %%
