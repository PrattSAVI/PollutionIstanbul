#%% IMPORT

import cdsapi
import netCDF4
import xarray as xr
import pandas as pd
import datetime as dt

#%% Setup variables for Query

#Data is only available starting from yesterday.
#today = (dt.datetime.now()-dt.timedelta(days=1)).strftime( '%Y-%m-%d' )
today = dt.datetime.now().strftime( '%Y-%m-%d' )
yesterday = (dt.datetime.now()-dt.timedelta(days=1)).strftime( '%Y-%m-%d' )
dates = yesterday + '/' + today #From yesterday to today, how to get fro tomorrow.

dates
#%% Query API , Convert to dictionary. Saves NetCDF file locally and accesses it again. 
#https://ads.atmosphere.copernicus.eu/cdsapp#!/dataset/cams-europe-air-quality-forecasts?tab=form

c = cdsapi.Client()
file_path = r'C:\Users\csucuogl\Desktop\WORK\MISC_TEST\Istanbul_AirQuality\test.nc' #Saving Locally For Now

c.retrieve(
    'cams-europe-air-quality-forecasts',
    {
        'variable': [
            'carbon_monoxide', 'nitrogen_dioxide',
            'particulate_matter_2.5um', 'pm2.5_anthropogenic_fossil_fuel_carbon',
        ],
        'model': 'ensemble',
        'level': '0',
        'date': dates ,
        'type': 'forecast', #How does 'forecast' work, there is one forcast per day.
        'time': '00:00',
        'leadtime_hour': '7',
        'area': [ 41.59, 28.15 , 40.54 , 30.34 ],
        'format': 'netcdf',
    }, file_path )

ds_disk = xr.open_dataset( file_path )
dd = ds_disk.to_dict() #Convert to dict to convert to pandas

#%% Convert 4D data to long Pandas List.
# Continue using dfo as long list dataframe
dfo = pd.DataFrame(columns = ['lat','lon','ind','time','values']) #Empty long list
for ind in dd['data_vars'].keys(): #For each Indicator
    for i in range( len( dd['data_vars'][ind]['data'] ) ): #for each time

        df = pd.DataFrame.from_dict( dd['data_vars'][ind]['data'][i][0] ) #NetCDF dict to table.
        df.index = dd['coords']['latitude']['data']
        df.columns = dd['coords']['longitude']['data']
        
        df = df.stack().reset_index() #Table to long list
        df.columns = ['lat','lon','values']
        toto = str( dd['coords']['time']['data'][i] ).split(':')[0]
        df['time'] = toto
        df['ind'] = ind
        
        dfo = dfo.append( df )

print( dfo['time'].unique().tolist() )
print( dfo['ind'].unique().tolist() )
dfo[ dfo['ind']=='pm2p5_conc']['values'].hist()

# %% Export Data to CSV fro further Processing 
# Increase Resolution using INverse Weighted Average of a Grid

import geopandas as gpd
import numpy as np 

grid = gpd.read_file( r"C:\Users\csucuogl\Desktop\WORK\MISC_TEST\Istanbul_AirQuality\Grid_64_Larger.shp" )
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

df_all = gpd.GeoDataFrame()
for ind in dfo['ind'].unique():
    for time in dfo['time'].unique():
        dft = dfo[ (dfo.ind == ind) & (dfo.time == time) ]
        gdf = gpd.GeoDataFrame(dft, geometry=gpd.points_from_xy(dft.lon, dft.lat))

        wa = []
        for i1,r1 in centers.iteritems():
            dist = []
            for i2,r2 in gdf.iterrows(): #Calculate the distanve of ech grid center to each measuement point
                t = haversine( (r1.x,r1.y) , (r2.geometry.x,r2.geometry.y) )
                dist.append( [t , r2['values']] )

            temp = pd.DataFrame( data = dist , columns = ['dist','value'])
            temp = temp[ temp['dist'] != 0 ] #Not itself
            temp = temp.sort_values(by='dist',ascending=True)[:19] #Closest 32
            temp['inv_dist'] = 1/temp['dist']

            weighted_avg = np.average(temp['value'].tolist(), weights=temp['inv_dist'].tolist() )
            wa.append( weighted_avg )

        cents = gpd.GeoDataFrame( data = wa , geometry = grid.geometry , columns = ['values'] )
        cents.crs = {'init' :'epsg:4326'}
        cents['id'] = [i for i in range(len(cents)) ]
        cents['time'] = time
        cents['ind'] = ind
        
        df_all = df_all.append( cents )
        print( time , ind )


#%% Save file. Commit and Push to Github Manually. 
# WGS84 hexagon geometry
df_all.to_file(r'C:\Users\csucuogl\Documents\GitHub\PollutionIstanbul\data\IstanbulPollution_all.geojson',driver="GeoJSON")



# %%
