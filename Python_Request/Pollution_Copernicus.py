#%% IMPORT

import cdsapi
import netCDF4
import xarray as xr
import pandas as pd
import datetime as dt
#%% Setup variables for Query

times = [str(i).zfill(2) + ':00' for i in range(0,24)] #Each hour from 00 to 23

today = dt.datetime.now().strftime( '%Y-%m-%d' )
yesterday = (dt.datetime.now()-dt.timedelta(days=1)).strftime( '%Y-%m-%d' )
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
        'type': 'forecast',
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
dfo = pd.DataFrame(columns = ['lat','lon','time','values'])
for i in range( len( dd['data_vars']['pm2p5_conc']['data'] ) ): #for each time

    df = pd.DataFrame.from_dict( dd['data_vars']['pm2p5_conc']['data'][i][0] )
    df.index = dd['coords']['latitude']['data']
    df.columns = dd['coords']['longitude']['data']
    
    df = df.stack().reset_index()
    df.columns = ['lat','lon','values']
    print( dd['coords']['time']['data'][i] )
    df['time'] = dd['coords']['time']['data'][i]
    
    dfo = dfo.append( df )

# %%
