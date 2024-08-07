from typing import Union, List
from shapely.geometry import Polygon, Point
import numpy as np
import pandas as pd
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient
import numpy_financial as npf
from sklearn.linear_model import LinearRegression
from GHEtool import Borefield, GroundConstantTemperature, HourlyGeothermalLoad, HourlyGeothermalLoadMultiYear
from utilities import linear_interpolation, linear_regression, coverage_calculation
import pygfunction as gt
import datetime
import plotly.graph_objects as go
from dataclasses import dataclass

@dataclass
class Building:
    name: str = None
    geometry: Union[Polygon, Point] = None
    address_name: str = None
    latitude: float = None 
    longitude: float = None
    year: int = None
    area: List = None
    floor_area: int = None
    roof_angle: int = None
    roof_surfaces: List = None
    roof_areas: List = None
    roof_orientations: List = None
    profet_building_standard: List = None
    profet_building_type: List = None
    outdoor_temperature_array: List = None


class Energyanalysis:
    BUILDING_STANDARDS = {
        "Lite energieffektivt": "Reg", 
        "Middels energieffektivt": "Eff-E", 
        "Veldig energieffektivt": "Vef"
        }
    BUILDING_TYPES = {
        "Hus": "Hou",
        "Leilighet": "Apt",
        "Kontor": "Off",
        "Butikk": "Shp",
        "Hotell": "Htl",
        "Barnehage": "Kdg",
        "Skole": "Sch",
        "Universitet": "Uni",
        "Kultur": "CuS",
        "Sykehjem": "Nsh",
        "Sykehus": "Other",
        "Andre": "Other"
        }
    
    def __init__(self, building_instance):
        self.building = building_instance




building_object = Building(
    name = 'halla', 
    area=[50, 100], 
    address_name='bajasvegen'
    )

energy = Energyanalysis(building_instance=building_object)
print(energy.building.area)