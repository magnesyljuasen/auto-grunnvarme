from typing import Union
from shapely.geometry import Polygon, Point
import numpy as np
import pandas as pd
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient

def coverage_calculation(coverage_percentage, array):
    if coverage_percentage == 100:
        return array, np.zeros(8760)
    elif coverage_percentage == 0:
        return np.zeros(8760), array
    array_sorted = np.sort(array)
    timeserie_sum = np.sum(array)
    timeserie_N = len(array)
    startpunkt = timeserie_N // 2
    i = 0
    avvik = 0.0001
    pm = 2 + avvik
    while abs(pm - 1) > avvik:
        cutoff = array_sorted[startpunkt]
        array_tmp = np.where(array > cutoff, cutoff, array)
        beregnet_dekningsgrad = (np.sum(array_tmp) / timeserie_sum) * 100
        pm = beregnet_dekningsgrad / coverage_percentage
        gammelt_startpunkt = startpunkt
        if pm < 1:
            startpunkt = startpunkt + timeserie_N // 2 ** (i + 2) - 1
        else:
            startpunkt = startpunkt - timeserie_N // 2 ** (i + 2) - 1
        if startpunkt == gammelt_startpunkt:
            break
        i += 1
        if i > 13:
            break
    return array_tmp, array - array_tmp

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

    def find_energy_arrays(self):
        numpy_arrays = {}
        for attr_name, value in self.__dict__.items():
            if isinstance(value, np.ndarray) and len(value) == 8760:
                numpy_arrays[attr_name] = value
        return numpy_arrays

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
        self.building_instance.dhw_array = np.array(array)

    def set_spaceheating_array(self, array):
        self.building_instance.spaceheating_array = np.array(array)

    def set_electric_array(self, array):
        self.building_instance.electric_array = np.array(array)

    def profet_calculation(self):
        def get_secret(filename):
            with open(filename) as file:
                secret = file.readline()
            return secret
        dhw_array = np.zeros(8760)
        spaceheating_array = np.zeros(8760)
        electric_array = np.zeros(8760)
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
                dhw_array = dhw_array + df['DHW'].to_numpy()
                spaceheating_array = spaceheating_array + df['SpaceHeating'].to_numpy()
                electric_array = electric_array + df['Electric'].to_numpy()
            else:
                raise TypeError("PROFet virker ikke")
        
        self.set_dhw_array(dhw_array)
        self.set_spaceheating_array(spaceheating_array)
        self.set_electric_array(electric_array)


################
        
class GeoEnergy:
    def __init__(self, building_instance):
        self.building_instance = building_instance
        self.spaceheating_cop = float
        self.spaceheating_coverage = float
        self.dhw_cop = float
        self.dhw_coverage = float

    def set_base_parameters(self, spaceheating_cop=3.5, spaceheating_coverage=95, dhw_cop=2.5, dhw_coverage=70):
        self.spaceheating_cop = spaceheating_cop
        self.spaceheating_coverage = spaceheating_coverage
        self.dhw_cop = dhw_cop
        self.dhw_coverage = dhw_coverage

    def set_demand(self, spaceheating_demand, dhw_demand, cooling_demand=np.zeros(8760)):
        self.spaceheating_demand = spaceheating_demand
        self.dhw_demand = dhw_demand
        self.cooling_demand = cooling_demand

    def simple_coverage_cop_calculation(self):
        spaceheating_heatpump, spaceheating_peak = coverage_calculation(coverage_percentage=self.spaceheating_coverage, array=self.spaceheating_demand)
        spaceheating_from_wells = spaceheating_heatpump - spaceheating_heatpump / self.spaceheating_cop
        spaceheating_compressor = spaceheating_heatpump - spaceheating_from_wells

        dhw_heatpump, dhw_peak = coverage_calculation(coverage_percentage=self.dhw_coverage, array=self.dhw_demand)
        dhw_from_wells = dhw_heatpump - dhw_heatpump / self.dhw_cop
        dhw_compressor = dhw_heatpump - dhw_from_wells

        self.heatpump_array = spaceheating_heatpump + dhw_heatpump
        self.from_wells_array = spaceheating_from_wells + dhw_from_wells
        self.compressor_array = spaceheating_compressor + dhw_compressor
        self.peak_array = spaceheating_peak + dhw_peak

        self.building_instance.geoenergy_production_array = -self.heatpump_array
        self.building_instance.geoenergy_consumption_array = self.compressor_array + self.peak_array

        

################
        
class SolarPanels:
    def __init__(self, building_instance):
        self.building_instance = building_instance

    def set_solar_array(self, array):
        self.solar_array = np.array(array)
        self.building_instance.solar_production_array = -self.solar_array

    def solar_calculation(self):
        pass 

################

class DistrictHeating:
    def __init__(self, building_instance):
        self.building_instance = building_instance

################
        
class HeatPump:
    def __init__(self, building_instance):
        self.building_instance = building_instance

################
        
class Costs:
    def __init__(self, building_instance):
        self.building_instance = building_instance
        self.energy_dict = self.building_instance.find_energy_arrays()

    def set_base_parameters(self):
        pass 

    



