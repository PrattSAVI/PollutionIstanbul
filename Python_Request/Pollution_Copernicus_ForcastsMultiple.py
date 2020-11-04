#%% IMPORT

import cdsapi
import netCDF4
import xarray as xr
import pandas as pd
import datetime as dt

#Setup variables for Query
#Data is only available starting from yesterday.
#today = (dt.datetime.now()-dt.timedelta(days=1)).strftime( '%Y-%m-%d' )
today = (dt.datetime.now()-dt.timedelta(days=1)).strftime( '%Y-%m-%d' )
yesterday = (dt.datetime.now()-dt.timedelta(days=2)).strftime( '%Y-%m-%d' )
dates = yesterday + '/' + today #From yesterday to today, how to get fro tomorrow.
times = [ str(i).zfill(2) + ":00" for i in range(0,24,2)] #Times

dates

#%% Query API , Convert to dictionary. Saves NetCDF file locally and accesses it again. 
#https://ads.atmosphere.copernicus.eu/cdsapp#!/dataset/cams-europe-air-quality-forecasts?tab=form

c = cdsapi.Client()
file_path = r'C:\Users\csucuogl\Desktop\WORK\MISC_TEST\Istanbul_AirQuality\test_12.nc' #Saving Locally For Now

c.retrieve(
    'cams-europe-air-quality-forecasts',
    {
        'variable': [
            'carbon_monoxide', 'nitrogen_dioxide', 'particulate_matter_2.5um'
        ],
        'model': 'ensemble',
        'level': '0',
        'date': dates ,
        'type': 'analysis', #How does 'forecast' work, there is one forcast per day.
        'time': times ,
        'leadtime_hour': '0',
        'area': [ 41.59, 28.15 , 40.54 , 30.34 ],
        'format': 'netcdf',
    }, file_path )

ds_disk = xr.open_dataset( file_path )
dd = ds_disk.to_dict() #Convert to dict to convert to pandas

#%% Convert 4D data to long Pandas List.
# Continue using dfo as long list dataframe
import matplotlib.pyplot as plt
import seaborn as sns

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

dfo.sample( 5 )


#%% Correct time

dfo['day'] = [r.split(',')[0] if ',' in r else None for i,r in dfo['time'].iteritems() ]
dfo['day'] = dfo['day'].fillna( '0 day' )

dfo['hour'] = [r.split(',')[1] if ',' in r else r for i,r in dfo['time'].iteritems() ]
dfo = dfo.drop('time' , axis = 1)

dfo = dfo[['lat','lon','ind','day','values']].groupby( ['lat','lon','ind','day'] ).max().reset_index()

dfo.sample(5)


# %% Export Data to CSV fro further Processing 
# Increase Resolution using INverse Weighted Average of a Grid

import geopandas as gpd
import numpy as np 

grid = gpd.read_file( r"C:\Users\csucuogl\Desktop\WORK\MISC_TEST\Istanbul_AirQuality\Grid_64_Larger.shp" )
c1 = [(r.x,r.y) for i,r in grid.centroid.iteritems()]
dfo['values'] = dfo['values'].round( 3 ) 

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

def make_long( dfo , grid , c1 ): # Intrepolate and make a long list
    df_all = gpd.GeoDataFrame() #Empty Dataframe

    for ind in dfo['ind'].unique():
        for time in dfo['day'].unique():
            print( time , ind )
            dft = dfo[ (dfo.ind == ind) & (dfo.day == time) ][['lat','lon','values']]
            df_list = dft.set_index('values').to_records().tolist()

            wa = []
            for x,y in c1:
                dist = [ ( haversine( (x,y) , (lon,lat) ) , value ) for value,lat,lon in df_list] #Calculate the distanve of ech grid center to each measuement point
                   
                temp = pd.DataFrame( data = dist , columns = ['dist','value'])
                temp = temp[ temp['dist'] != 0 ].sort_values(by='dist',ascending=True)[:16] #Closest 16 and not itself
                temp['inv_dist'] = 1/temp['dist']

                weighted_avg = np.average(temp['value'].tolist(), weights=temp['inv_dist'].tolist() )
                wa.append( weighted_avg )

            cents = gpd.GeoDataFrame( data = wa , geometry = grid.geometry , columns = ['values'] )
            cents.crs = {'init' :'epsg:4326'}
            cents['id'] = [i for i in range(len(cents)) ]
            cents['time'] = time
            cents['ind'] = ind
            
            df_all = df_all.append( cents )

    return df_all

df_all = make_long( dfo , grid , c1 )
print( 'Processing Complete, Mapping ->')

df_all[ df_all.ind == 'co_conc'].plot( column = 'values' , legend = True , cmap='OrRd')

#%%

dft = dfo[ (dfo.ind == 'co_conc') & (dfo.day == '0 day') ][['lat','lon','values']]
dft.set_index('values').to_records().tolist()
        
#%% Save file. Commit and Push to Github Manually. 
# WGS84 hexagon geometry
df_all.to_file(r'C:\Users\csucuogl\Documents\GitHub\PollutionIstanbul\data\IstanbulPollution_all.geojson',driver="GeoJSON")

