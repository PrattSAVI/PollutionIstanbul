#%% IMPORT

import cdsapi
import netCDF4

c = cdsapi.Client()

file_path = r'C:\Users\csucuogl\Desktop\WORK\MISC_TEST\Istanbul_AirQuality\test.nc'

c.retrieve(
    'cams-europe-air-quality-forecasts',
    {
        'variable': 'particulate_matter_2.5um',
        'model': 'ensemble',
        'level': '0',
        'date': '2020-09-16/2020-09-18',
        'type': 'analysis',
        'time': [
            '15:00', '16:00', '17:00',
            '18:00', '19:00', '20:00',
            '21:00', '22:00', '23:00',
        ],
        'leadtime_hour': '0',
        'area': [
            41.48, 28.17, 40.67,
            29.85,
        ],
        'format': 'netcdf',
    }, file_path )


#%% OPEN in Python

import xarray as xr
import pandas as pd

ds_disk = xr.open_dataset( file_path)

dd = ds_disk.to_dict()

#%%

#For first time entry
dfo = pd.DataFrame(columns = ['lat','lon','time','values'])
for i in range( len( dd['data_vars']['pm2p5_conc']['data'] ) ): #for each time

    df = pd.DataFrame.from_dict( dd['data_vars']['pm2p5_conc']['data'][i][0] )
    df.index = dd['coords']['latitude']['data']
    df.columns = dd['coords']['longitude']['data']
    
    df = df.stack().reset_index()
    df.columns = ['lat','lon','values']
    df['time'] = dd['coords']['time']['data'][i]
    
    dfo = dfo.append( df )
