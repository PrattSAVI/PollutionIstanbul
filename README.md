## Visualizing Pollution in Istanbul
WebApp visualizing the pollution data received from CAMS European air quality forecasts.

* Here is the main page for the data : <a href = 'https://ads.atmosphere.copernicus.eu/cdsapp#!/home'>ADS</a>  
* The dowload and API source is here: <a href = 'https://ads.atmosphere.copernicus.eu/cdsapp#!/dataset/cams-europe-air-quality-forecasts?tab=form'>Air Quality Forecasts</a>  

Data is retrieved with a Python application and NetCDF data is converted to a pandas long list. Resolution of the point data is not great. I have created a **Inverse Distance Weigthed (IDW)** average for each hexagon. It is a little slow. 

App uses Mapbox GL for visualization.    
App can be viewed [here](https://prattsavi.github.io/PollutionIstanbul/).

This max pm2.5 levels measured throughout the day in Istanbul. <br>
<img src='https://raw.githubusercontent.com/PrattSAVI/PollutionIstanbul/master/img/Cover.JPG'>
