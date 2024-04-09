from typing import Union
from shapely.geometry import Polygon, Point
import numpy as np
import pandas as pd
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient
################

class Building:
    def __init__(self):
        self.geometry = Union[Polygon, Point]
        self.name = str
        self.address = str
        self.built_year = int
        self.area = [] # list of areas, for combination_buildings
        self.floor_area = int
        self.roof_angle = int
        self.roof_surfaces = []
        self.roof_areas = []
        self.roof_orientations = []
        self.profet_building_standard = [] # list of strings, for combination-buildings
        self.profet_building_type = [] # list of strings, , for combination-buildings
        self.temperature_array = []

################

class EnergyDemand:
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
        self.building_instance = building_instance

    def set_dhw_array(self, array):
        self.building_instance.dhw_array = array

    def set_spaceheating_array(self, array):
        self.building_instance.spaceheating_array = array

    def set_electric_array(self, array):
        self.building_instance.electric_array = array

    def profet_calculation(self):
        def get_secret(filename):
            with open(filename) as file:
                secret = file.readline()
            return secret
        for i in range(0, len(self.building_instance.profet_building_standard)):
            building_standard = self.building_instance.profet_building_standard[i]
            building_type = self.building_instance.profet_building_type[i]
            building_area = self.building_instance.area[i]
            temperature_array = self.building_instance.temperature_array

            oauth = OAuth2Session(client=BackendApplicationClient(client_id="profet_2024"))
            predict = OAuth2Session(
                token=oauth.fetch_token(
                    token_url="https://identity.byggforsk.no/connect/token",
                    client_id="profet_2024",
                    client_secret=get_secret("src/config/profet_secret.txt"),
                )
            )
            selected_standard = self.BUILDING_STANDARDS[building_standard]
            if selected_standard == "Reg":
                regular_area, efficient_area, veryefficient_area = building_area, 0, 0
            if selected_standard == "Eff-E":
                regular_area, efficient_area, veryefficient_area = 0, building_area, 0
            if selected_standard == "Vef":
                regular_area, efficient_area, veryefficient_area = 0, 0, building_area
            # --
            if len(temperature_array) == 0:
                request_data = {
                    "StartDate": "2023-01-01", 
                    "Areas": {f"{self.BUILDING_TYPES[building_type]}": {"Reg": regular_area, "Eff-E": efficient_area, "Eff-N": 0, "Vef": veryefficient_area}},
                    "RetInd": False,  # Boolean, if True, individual profiles for each category and efficiency level are returned
                    "Country": "Norway"}
            else:
                request_data = {
                "StartDate": "2023-01-01", 
                "Areas": {f"{self.BUILDING_TYPES[building_type]}": {"Reg": regular_area, "Eff-E": efficient_area, "Eff-N": 0, "Vef": veryefficient_area}},
                "RetInd": False,  # Boolean, if True, individual profiles for each category and efficiency level are returned
                "Country": "Norway",  # Optional, possiblity to get automatic holiday flags from the python holiday library.
                "TimeSeries": {"Tout": temperature_array}}
                
            r = predict.post(
                "https://flexibilitysuite.byggforsk.no/api/Profet", json=request_data
            )
            if r.status_code == 200:
                df = pd.DataFrame.from_dict(r.json())
                dhw_array = df['DHW'].to_numpy()
                spaceheating_array = df['SpaceHeating'].to_numpy()
                electric_array = df['Electric'].to_numpy()
            else:
                raise TypeError("PROFet virker ikke")
        
        self.set_dhw_array(dhw_array)
        self.set_spaceheating_array(spaceheating_array)
        self.set_electric_array(electric_array)


################
        
class GeoEnergy:
    def __init__(self, building_instance):
        self.building_instance = building_instance

################
        
class SolarPanels:
    def __init__(self, building_instance):
        self.building_instance = building_instance

################

class DistrictHeating:
    def __init__(self, building_instance):
        self.building_instance = building_instance

################
        
class HeatPump:
    def __init__(self, building_instance):
        self.building_instance = building_instance


    



