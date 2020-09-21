#%% IMPORT

import cdsapi
import netCDF4
import xarray as xr
import pandas as pd
import datetime as dt
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

#%%

dft = dfo[ dfo.time == 0 ]
dft


# %% Plotting - Remove this section

import folium

dfo['values'] = dfo['values'].astype(float)
dfo['values'] = dfo['values'].round( 3 )

m = folium.Map(
    location=[ dfo['lat'].mean() , dfo['lon'].mean() ],
    tiles='Stamen Toner',
    zoom_start=9
)


for i,r in dfo[ dfo.time == 0 ].iterrows(): 
    folium.Circle(
        radius=r['values'] * 200,
        location=[ r['lat'], r['lon'] ],
        color='crimson',
        tooltip = r['values'],
        fill=False,
    ).add_to(m)

m
# %%
