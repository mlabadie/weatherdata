# -*- python -*-
# -*- coding:utf-8 -*-
#
#       Copyright 2020 INRAE-CIRAD
#       Distributed under the Cecill-C License.
#       See https://cecill.info/licences/Licence_CeCILL-C_V1-en.html
#
# ==============================================================================

from agroservices import IPM
import pandas
import datetime

ipm = IPM()
ressource_ids = {'Met Norway Locationforecast': 'yr',
                 'Finnish Meteorological Institute measured data': 'fmi',
                 'FMI weather forecasts': 'fmi_forecasts',
                 'Landbruksmeteorologisk tjeneste': 'lmt',
                 'MeteoBot API': 'metobot',
                 'Fruitweb': 'fw',
                 'Metos':'metos'}

weather_adapter = {'fmi': ipm.get_weatheradapter_fmi,
                   'yr': ipm.get_weatheradapter_yr,
                   'lmt':'',
                   'meteobot':'',
                   'fw':'',
                   'metos':''
                    }

class WeatherDataSource(object):

    def __init__(self, name):
        self.id = ressource_ids[name]
        self.name = name
        self.ipm = IPM()
        self.ws = weather_adapter[ressource_ids.get(name)]

    def get_station_ids(self):
        rep = self.ipm.get_weatherdatasource()  

        values = {item['name']:item['spatial']['geoJSON']for item in rep}

        station_ids = dict()
        coord = dict()

        for names in values:
            if 'features' in values[names]:
                station_ids[names]=[values[names]['features'][item]['properties'] for item in range(len(values[names]['features']))]
                coord[names]=[values[names]['features'][item]['geometry'] for item in range(len(values[names]['features']))]
            else:
                station_ids[names]= 'no stations for this ressources'
                coord[names]= 'no stations for this ressources'

        df_station_ids = pandas.DataFrame(station_ids[self.name])
        df_coord = pandas.DataFrame(coord[self.name])
        df = [df_station_ids,df_coord]
        data = pandas.concat(df,axis=1)
        data = data[["name","id","coordinates"]]
        return data

    def list_available_parameters(self):
        """
        Get list of available parameters for ressource

        Parameters:
        -----------

        Returns:
        --------
            a dictionnary containing common and optional parameters
        """
        rep = self.ipm.get_weatherdatasource()

        values = {item['name']:item['parameters']for item in rep}
         
        if self.name in values:
           parameters = values[self.name]

        return parameters
        
         
    def get_data(self,parameters, station_id, daterange):
        """
        Get weather data from weatherdataressource

        Parameters:
        -----------
            parameters: list of parameters of weatherdata 
            station_id: (int) station id of weather station 
            daterange:  a pandas.date_range(start date, end date, freq='H', timezone(tz))
                        https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.date_range.html
        
        Returns:
        --------
            return a dataframe 
        """
        timeStart = daterange[0].strftime('%Y-%m-%dT%H:%M:%S')
        timeEnd = daterange[-1].strftime('%Y-%m-%dT%H:%M:%S')
        if daterange.tz._tzname == 'UTC':
            timeStart +='Z'
            timeEnd += 'Z'
        else:
            decstr = daterange[0].strftime('%z')
            decstr = decstr[:-2] + ':' + decstr[-2:]
            timeStart += decstr
            timeEnd += decstr
        
        interval = pandas.Timedelta(daterange.freq).seconds

        response=self.ws(
            weatherStationId=station_id, 
            timeStart=timeStart, 
            timeEnd=timeEnd, 
            interval=interval, 
            parameters=parameters
            )

        data = {str(var): vals for var, vals in zip(response['weatherParameters'], zip(*response['locationWeatherData'][0]['data']))}
        df = pandas.DataFrame(data)
        df.index = daterange
        # TODO : get all what is needed for intantiating a WeatherData object (meta, units, ...) and retrun it
        return df
    
# TODO : this class should inheritate from a more generic Wheather DataHub
class WeatherDataHub(object):
    """
    """

    def __init__(self):
        self.ws = IPM()

    def list_ressources(self):
        """
        get list of ressource available in IPM services

        Parameters:
        -----------

        Returns:
        ---------
            dictionnary with name and description of available weatherdatasource on IPM service
        """
        rep = self.ws.get_weatherdatasource()
        return {item['name']:item['description'] for item in rep}

    def get_ressource(self, name):
        rep = self.ws.get_weatherdatasource()
        keys = [item['name'] for item in rep]
        if name in keys:
            return WeatherDataSource(name)
        else:
            raise NotImplementedError()

rep = ipm.get_weatherdatasource()  

values = {item['name']:item['spatial']['geoJSON']for item in rep}

station_ids = dict()
coord = dict()
for names in values:
    if 'features' in values[names]:
        station_ids[names]=[values[names]['features'][item]['properties'] for item in range(len(values[names]['features']))]
        coord[names]=[values[names]['features'][item]['geometry'] for item in range(len(values[names]['features']))]

    else:
        station_ids[names]= 'no stations for this ressources'
        coord[names]= 'no stations for this ressources'