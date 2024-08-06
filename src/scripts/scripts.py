from typing import Union
from shapely.geometry import Polygon, Point
import numpy as np
import pandas as pd
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient
import numpy_financial as npf
from sklearn.linear_model import LinearRegression
from GHEtool import Borefield, GroundConstantTemperature, HourlyGeothermalLoad, HourlyGeothermalLoadMultiYear
from src.scripts.utilities import linear_interpolation, linear_regression, coverage_calculation
import pygfunction as gt
import datetime
import plotly.graph_objects as go
##
import streamlit as st
##

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
        self.outdoor_temperature_array = []
        self.dict_energy = {}
        self.dict_operation_costs = {}

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
        self.building_instance.dict_energy['dhw_array'] = np.array(array)

    def set_spaceheating_array(self, array):
        self.building_instance.dict_energy['spaceheating_array'] = np.array(array)

    def set_electric_array(self, array):
        self.building_instance.dict_energy['electric_array'] = np.array(array)

    def profet_calculation(self, spaceheating_sum = None, dhw_sum = None, electric_sum = None):
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
            temperature_array = self.building_instance.outdoor_temperature_array

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
        
        if spaceheating_sum != None:
            spaceheating_factor = spaceheating_sum/np.sum(spaceheating_array)
            spaceheating_array = spaceheating_array * spaceheating_factor
        if dhw_sum != None:
            dhw_factor = dhw_sum/np.sum(dhw_array)
            dhw_array = dhw_array * dhw_factor
        if electric_sum != None:
            electric_factor = electric_sum/np.sum(electric_array)
            electric_array = electric_array * electric_factor

        self.set_dhw_array(dhw_array)
        self.set_spaceheating_array(spaceheating_array)
        self.set_electric_array(electric_array)

    def calcluate_flow_temperature(self, OUTDOOR_TEMPERATURE_AT_MIN_FLOW_TEMPERATURE = 15, OUTDOOR_TEMPERATURE_AT_MAX_FLOW_TEMPERATURE = -15, FLOW_TEMPERATURE_MIN = 35, FLOW_TEMPERATURE_MAX = 45):
        self.OUTDOOR_TEMPERATURE_AT_MIN_FLOW_TEMPERATURE, self.OUTDOOR_TEMPERATURE_AT_MAX_FLOW_TEMPERATURE = OUTDOOR_TEMPERATURE_AT_MIN_FLOW_TEMPERATURE, OUTDOOR_TEMPERATURE_AT_MAX_FLOW_TEMPERATURE
        self.FLOW_TEMPERATURE_MIN, self.FLOW_TEMPERATURE_MAX = FLOW_TEMPERATURE_MIN, FLOW_TEMPERATURE_MAX
        self.flow_temperature_array = self._calculate_flow_temperature()
        self.building_instance.flow_temperature_array = self.flow_temperature_array
        self.building_instance.FLOW_TEMPERATURE_MIN, self.building_instance.FLOW_TEMPERATURE_MAX = self.FLOW_TEMPERATURE_MIN, self.FLOW_TEMPERATURE_MAX
        self.building_instance.OUTDOOR_TEMPERATURE_AT_MIN_FLOW_TEMPERATURE, self.building_instance.OUTDOOR_TEMPERATURE_AT_MAX_FLOW_TEMPERATURE = self.OUTDOOR_TEMPERATURE_AT_MIN_FLOW_TEMPERATURE, self.OUTDOOR_TEMPERATURE_AT_MAX_FLOW_TEMPERATURE
        
    def _calculate_flow_temperature(self):
        outdoor_temperature_array = self.building_instance.outdoor_temperature_array
        flow_temperature = np.zeros(8760)
        for i in range(0, len(flow_temperature)):
            if outdoor_temperature_array[i] < self.OUTDOOR_TEMPERATURE_AT_MAX_FLOW_TEMPERATURE:
                flow_temperature[i] = self.FLOW_TEMPERATURE_MAX
            elif outdoor_temperature_array[i] > self.OUTDOOR_TEMPERATURE_AT_MIN_FLOW_TEMPERATURE:
                flow_temperature[i] = self.FLOW_TEMPERATURE_MIN
            else:
                flow_temperature[i] = linear_interpolation(outdoor_temperature_array[i], self.OUTDOOR_TEMPERATURE_AT_MAX_FLOW_TEMPERATURE, self.OUTDOOR_TEMPERATURE_AT_MIN_FLOW_TEMPERATURE, self.FLOW_TEMPERATURE_MAX, self.FLOW_TEMPERATURE_MIN)
        return flow_temperature

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

        self.building_instance.dict_energy['geoenergy_production_array'] = -self.heatpump_array
        self.building_instance.dict_energy['geoenergy_consumption_compressor_array'] = self.compressor_array
        self.building_instance.dict_energy['geoenergy_consumption_peak_array'] = self.peak_array  

    def calculate_heat_pump_size(self):
        heat_pump_size = round(np.max(self.heatpump_array))
        self.heat_pump_size = heat_pump_size
        self.building_instance.geoenergy_heat_pump_size = heat_pump_size
    
    def simple_sizing_of_boreholes(self):
        borehole_meters = round(np.sum(self.from_wells_array)/80)
        self.borehole_meters = borehole_meters
        self.building_instance.geoenergy_borehole_meters = borehole_meters
    
    def _calculate_cop(self, source_temperature, SLOPE_FLOW_TEMPERATURE_MIN, SLOPE_FLOW_TEMPERATURE_MAX, INTERSECT_FLOW_TEMPERATURE_MIN, INTERSECT_FLOW_TEMPERATURE_MAX, flow_temperature_array, FLOW_TEMPERATURE_MAX, FLOW_TEMPERATURE_MIN, COP_YEAR):
        cop_array = np.zeros(8760)
        for i in range(0, len(cop_array)):
            if flow_temperature_array[i] == FLOW_TEMPERATURE_MAX:
                cop_array[i] = SLOPE_FLOW_TEMPERATURE_MAX * source_temperature[i + (COP_YEAR-1)*8760] + INTERSECT_FLOW_TEMPERATURE_MAX
            elif flow_temperature_array[i] == FLOW_TEMPERATURE_MIN:
                cop_array[i] = SLOPE_FLOW_TEMPERATURE_MIN * source_temperature[i+ (COP_YEAR-1)*8760] + INTERSECT_FLOW_TEMPERATURE_MIN
            else:
                slope_interpolated = linear_interpolation(flow_temperature_array[i], FLOW_TEMPERATURE_MAX, FLOW_TEMPERATURE_MIN, SLOPE_FLOW_TEMPERATURE_MAX, SLOPE_FLOW_TEMPERATURE_MIN)
                intercept_interpolated = linear_interpolation(flow_temperature_array[i], FLOW_TEMPERATURE_MAX, FLOW_TEMPERATURE_MIN, INTERSECT_FLOW_TEMPERATURE_MAX, INTERSECT_FLOW_TEMPERATURE_MIN)
                cop_interpolated = slope_interpolated * source_temperature[i + (COP_YEAR-1)*8760] + intercept_interpolated
                cop_array[i] = cop_interpolated
        return cop_array
    
    def set_simulation_parameters(self):
        self.TECHNICAL_SHEET_FLUID_TEMPERATURE_MIN = np.array([-5, -2, 0, 2, 5, 10, 15])
        self.TECHNICAL_SHEET_COP_MIN = np.array([3.68, 4.03, 4.23, 4.41, 4.56, 5.04, 5.42]) - 0
        self.TECHNICAL_SHEET_FLUID_TEMPERATURE_MAX = np.array([-2, 0, 2, 5, 10, 15])
        self.TECHNICAL_SHEET_COP_MAX = np.array([3.3, 3.47, 3.61, 3.77, 4.11, 4.4]) - 0

        self.SIMULATION_PERIOD = 25
        self.THERMAL_CONDUCTIVITY = 3.0
        self.UNDISTRUBED_GROUND_TEMPERATURE = 8
        self.BOREHOLE_EQUIVALENT_RESISTANCE = 0.12
        self.MAX_ALLOWED_FLUID_TEMPERATURE = 16
        self.MIN_ALLOWED_FLUID_TEMPERATURE = 0
        self.DISTANCE_BETWEEN_WELLS = 15
        self.TARGET_DEPTH = 300

    def advanced_sizing_of_boreholes(self, variable_cop_sizing = True):
        self.slope_flow_temperature_min, self.intersect_flow_temperature_min = linear_regression(self.TECHNICAL_SHEET_FLUID_TEMPERATURE_MIN, self.TECHNICAL_SHEET_COP_MIN)
        self.slope_flow_temperature_max, self.intersect_flow_temperature_max = linear_regression(self.TECHNICAL_SHEET_FLUID_TEMPERATURE_MAX, self.TECHNICAL_SHEET_COP_MAX)   
             
        borefield = Borefield()
        ground_data = GroundConstantTemperature(k_s=self.THERMAL_CONDUCTIVITY, T_g=self.UNDISTRUBED_GROUND_TEMPERATURE, volumetric_heat_capacity=2.4*10**6)
        borefield.set_ground_parameters(data = ground_data)
        borefield.set_Rb(Rb = self.BOREHOLE_EQUIVALENT_RESISTANCE)
        borefield.set_max_avg_fluid_temperature(self.MAX_ALLOWED_FLUID_TEMPERATURE)  # maximum temperature
        borefield.set_min_avg_fluid_temperature(self.MIN_ALLOWED_FLUID_TEMPERATURE)  # minimum temperature

        NUMBER_OF_ITERATIONS = 10
        cop_array = np.full(8760, 3.5)
        number_of_wells_x = 1
        number_of_wells_y = 1
        distance_between_wells_x = self.DISTANCE_BETWEEN_WELLS
        distance_between_wells_y = self.DISTANCE_BETWEEN_WELLS
        borehole_length = 250
        depth = 250
        for i in range(0, NUMBER_OF_ITERATIONS):
            from_wells_array = self.heatpump_array - self.heatpump_array/cop_array
            field = gt.boreholes.rectangle_field(
                N_1=number_of_wells_x,
                N_2=number_of_wells_y,
                B_1=distance_between_wells_x,
                B_2=distance_between_wells_y,
                H=borehole_length,
                D=10, # borehole buried depth
                r_b=0.114, # borehole radius
                tilt=0 # tilt
                )
            load = HourlyGeothermalLoad(heating_load=from_wells_array, simulation_period=self.SIMULATION_PERIOD)
            borefield.set_load(load = load)
            borefield.set_borefield(borefield = field)
            borefield.calculation_setup(use_constant_Rb=True) # constant Rb*
            previous_depth = depth
            depth = round(borefield.size(L4_sizing=True))

            if variable_cop_sizing == True:
                source_temperature = borefield.results.peak_heating
                cop_array = self._calculate_cop(
                    source_temperature=source_temperature,
                    SLOPE_FLOW_TEMPERATURE_MIN=self.slope_flow_temperature_min,
                    SLOPE_FLOW_TEMPERATURE_MAX=self.slope_flow_temperature_max,
                    INTERSECT_FLOW_TEMPERATURE_MIN=self.intersect_flow_temperature_min,
                    INTERSECT_FLOW_TEMPERATURE_MAX=self.intersect_flow_temperature_max,
                    flow_temperature_array=self.building_instance.flow_temperature_array,
                    FLOW_TEMPERATURE_MAX=self.building_instance.FLOW_TEMPERATURE_MAX,
                    FLOW_TEMPERATURE_MIN=self.building_instance.FLOW_TEMPERATURE_MIN,
                    COP_YEAR = round(self.SIMULATION_PERIOD / 2) # velger år for COP som år 25 / 2 = 12
                    )
            
            if depth > self.TARGET_DEPTH:
                number_of_wells_x = number_of_wells_x + 1 # øke med en brønn
            
            if depth == previous_depth:
                break
        
        self.field = gt.boreholes.visualize_field(field)
        self.fluid_temperature = borefield.results.peak_heating
        self.cop_array = cop_array
        self.from_wells_array = from_wells_array
        self.flow_temperature_array = self.building_instance.flow_temperature_array
        self.compressor_array = self.heatpump_array - self.from_wells_array
        self.number_of_boreholes = borefield.number_of_boreholes
        self.depth_per_borehole = depth
        self.borehole_meters = self.number_of_boreholes * self.depth_per_borehole
        self.building_instance.geoenergy_borehole_meters = self.borehole_meters  

    def calculate_investment_costs(self):
        self.investment_cost_borehole = round(20000 + self.borehole_meters * 437.5) # brønn + graving
        self.investment_cost_heat_pump = round(214000 + self.heat_pump_size * 2200) # varmepumpe
        self.building_instance.geoenergy_investment_cost_borehole = self.investment_cost_borehole
        self.building_instance.geoenergy_investment_cost_heat_pump = self.investment_cost_heat_pump
        

################
        
class SolarPanels:
    def __init__(self, building_instance):
        self.building_instance = building_instance

    def set_solar_array(self, array):
        self.solar_array = np.array(array)
        self.building_instance.dict_energy['solar_production_array'] = -self.solar_array

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

    def set_base_parameters(self, spaceheating_cop=3.5, spaceheating_coverage=95, dhw_cop=2.5, dhw_coverage=70):
        self.spaceheating_cop = spaceheating_cop
        self.spaceheating_coverage = spaceheating_coverage
        self.dhw_cop = dhw_cop
        self.dhw_coverage = dhw_coverage

    def set_demand(self, spaceheating_demand, dhw_demand):
        self.spaceheating_demand = spaceheating_demand
        self.dhw_demand = dhw_demand
        
    def set_simulation_parameters(self):
        self.TECHNICAL_SHEET_FLUID_TEMPERATURE_MIN = np.array([-20, -15, -10, -7, 2, 7, 10, 18])
        self.TECHNICAL_SHEET_COP_MIN = np.array([2.16, 2.48, 2.83, 3.06, 3.79, 4.13, 4.6, 5.31]) - 0
        self.TECHNICAL_SHEET_FLUID_TEMPERATURE_MAX = np.array([-20, -15, -10, -7, 2, 7, 10, 18])
        self.TECHNICAL_SHEET_COP_MAX = np.array([1.8, 2.06, 2.36, 2.56, 3.04, 3.33, 3.66, 4.17]) - 0

        self.P_3031_35 = np.array([
            [0.48, 0.76, 1,], #1.25],
            [0.24, 0.38, 0.5,], #0.62],
            [0.12, 0.19, 0.25,]# 0.31]
            ])
        self.COP_3031_35 = np.array([
            [0.5, 0.69, 0.99,], #1.19],
            [0.51, 0.73, 1,], #1.24],
            [0.45, 0.65, 0.93,] #1.13]
            ])
        
        self.COP_NOMINAL = 4.8

    def _calculate_cop(self, source_temperature, SLOPE_FLOW_TEMPERATURE_MIN, SLOPE_FLOW_TEMPERATURE_MAX, INTERSECT_FLOW_TEMPERATURE_MIN, INTERSECT_FLOW_TEMPERATURE_MAX, flow_temperature_array, FLOW_TEMPERATURE_MAX, FLOW_TEMPERATURE_MIN):
        cop_array = np.zeros(8760)
        for i in range(0, len(cop_array)):
            if flow_temperature_array[i] == FLOW_TEMPERATURE_MAX:
                cop_array[i] = SLOPE_FLOW_TEMPERATURE_MAX * source_temperature[i] + INTERSECT_FLOW_TEMPERATURE_MAX
            elif flow_temperature_array[i] == FLOW_TEMPERATURE_MIN:
                cop_array[i] = SLOPE_FLOW_TEMPERATURE_MIN * source_temperature[i] + INTERSECT_FLOW_TEMPERATURE_MIN
            else:
                slope_interpolated = linear_interpolation(flow_temperature_array[i], FLOW_TEMPERATURE_MAX, FLOW_TEMPERATURE_MIN, SLOPE_FLOW_TEMPERATURE_MAX, SLOPE_FLOW_TEMPERATURE_MIN)
                intercept_interpolated = linear_interpolation(flow_temperature_array[i], FLOW_TEMPERATURE_MAX, FLOW_TEMPERATURE_MIN, INTERSECT_FLOW_TEMPERATURE_MAX, INTERSECT_FLOW_TEMPERATURE_MIN)
                cop_interpolated = slope_interpolated * source_temperature[i] + intercept_interpolated
                cop_array[i] = cop_interpolated
        return cop_array
    
    def nspek_heatpump_calculation(self, P_NOMINAL, power_reduction = 0, cop_reduction = 0):
        outdoor_temperature_array = self.building_instance.outdoor_temperature_array
        heating_demand_array = self.spaceheating_demand + self.dhw_demand
        COP_NOMINAL = self.COP_NOMINAL  # Nominell COP
        temperature_datapoints = [-15, 2, 7,] #15] # SN- NSPEK 3031:2023 - tabell K.13
        P_3031_35 = self.P_3031_35
        COP_3031_35 = self.COP_3031_35
        
        P_3031_list = []
        COP_3031_list = []
        for i in range(0, len(temperature_datapoints)):
            P_3031_list.append(np.polyfit(x = temperature_datapoints, y = P_3031_35[i], deg = 1))
            COP_3031_list.append(np.polyfit(x = temperature_datapoints, y = COP_3031_35[i], deg = 1))

        P_HP_DICT = []
        COP_HP_DICT = []
        INTERPOLATE_HP_DICT = []
        for index, outdoor_temperature in enumerate(outdoor_temperature_array):
            p_hp_list = np.array([np.polyval(P_3031_list[0], outdoor_temperature), np.polyval(P_3031_list[1], outdoor_temperature), np.polyval(P_3031_list[2], outdoor_temperature)])
            cop_hp_list = np.array([np.polyval(COP_3031_list[0], outdoor_temperature), np.polyval(COP_3031_list[1], outdoor_temperature), np.polyval(COP_3031_list[2], outdoor_temperature)]) * COP_NOMINAL
            interpolate_hp_list = np.polyfit(x = p_hp_list, y = cop_hp_list, deg = 0)[0]
            #--
            P_HP_DICT.append(p_hp_list)
            COP_HP_DICT.append(cop_hp_list)
            INTERPOLATE_HP_DICT.append(interpolate_hp_list)
        #--
        heatpump = np.zeros(8760)
        cop = np.zeros(8760)
        P_NOMINAL = P_NOMINAL
        #P_NOMINAL = np.max(heating_demand_array) * 0.5 # 50% effektdekningsgrad
    #    if P_NOMINAL > 10: # ikke større varmepumpe enn 10 kW?
    #        P_NOMINAL = 10
        for i, outdoor_temperature in enumerate(outdoor_temperature_array):
            effekt = heating_demand_array[i]
            if outdoor_temperature < -15:
                cop[i] = 1
                heatpump[i] = 0
            else:
                varmepumpe_effekt_verdi = effekt
                p_hp_list = P_HP_DICT[i] * P_NOMINAL
                cop_hp_list = COP_HP_DICT[i]
                if effekt >= p_hp_list[0]:
                    varmepumpe_effekt_verdi = p_hp_list[0] - (p_hp_list[0]*power_reduction/100)
                    if outdoor_temperature > -2 and outdoor_temperature < 7:
                        cop_verdi = cop_hp_list[0] - (cop_hp_list[0]*cop_reduction/100)
                    else:
                        cop_verdi = cop_hp_list[0]
                elif effekt <= p_hp_list[2]:
                    if outdoor_temperature > -2 and outdoor_temperature < 7:
                        cop_verdi = cop_hp_list[2] - (cop_hp_list[2]*cop_reduction/100)
                    else:
                        cop_verdi = cop_hp_list[2]
                else:
                    if outdoor_temperature > -2 and outdoor_temperature < 7:
                        cop_verdi = INTERPOLATE_HP_DICT[i] - (INTERPOLATE_HP_DICT[i] * cop_reduction/100)
                    else:
                        cop_verdi = INTERPOLATE_HP_DICT[i]
                heatpump[i] = varmepumpe_effekt_verdi
                cop[i] = cop_verdi
        self.heatpump_array = heatpump
        self.from_air_array = self.heatpump_array - self.heatpump_array / np.array(cop_verdi)
        self.compressor_array = self.heatpump_array - self.from_air_array
        self.peak_array = heating_demand_array - self.heatpump_array
        self.cop_array = cop

        self.building_instance.dict_energy['heatpump_production_array'] = -self.heatpump_array
        self.building_instance.dict_energy['heatpump_consumption_compressor_array'] = self.compressor_array
        self.building_instance.dict_energy['heatpump_consumption_peak_array'] = self.peak_array  
    
    def advanced_sizing_of_heat_pump(self):
        spaceheating_heatpump, spaceheating_peak = coverage_calculation(coverage_percentage=self.spaceheating_coverage, array=self.spaceheating_demand)
        dhw_heatpump, dhw_peak = coverage_calculation(coverage_percentage=self.dhw_coverage, array=self.dhw_demand)
        self.heatpump_array = spaceheating_heatpump + dhw_heatpump
        self.peak_array = spaceheating_peak + dhw_peak

        slope_flow_temperature_min, intersect_flow_temperature_min = linear_regression(self.TECHNICAL_SHEET_FLUID_TEMPERATURE_MIN, self.TECHNICAL_SHEET_COP_MIN)
        slope_flow_temperature_max, intersect_flow_temperature_max = linear_regression(self.TECHNICAL_SHEET_FLUID_TEMPERATURE_MAX, self.TECHNICAL_SHEET_COP_MAX)

        source_temperature = self.building_instance.outdoor_temperature_array     
        self.cop_array = self._calculate_cop(
            source_temperature=source_temperature,
            SLOPE_FLOW_TEMPERATURE_MIN=slope_flow_temperature_min,
            SLOPE_FLOW_TEMPERATURE_MAX=slope_flow_temperature_max,
            INTERSECT_FLOW_TEMPERATURE_MIN=intersect_flow_temperature_min,
            INTERSECT_FLOW_TEMPERATURE_MAX=intersect_flow_temperature_max,
            flow_temperature_array=self.building_instance.flow_temperature_array,
            FLOW_TEMPERATURE_MAX=self.building_instance.FLOW_TEMPERATURE_MAX,
            FLOW_TEMPERATURE_MIN=self.building_instance.FLOW_TEMPERATURE_MIN,
            )
        self.from_air_array = self.heatpump_array - self.heatpump_array/self.cop_array
        self.compressor_array = self.heatpump_array - self.from_air_array

        self.building_instance.dict_energy['heatpump_production_array'] = -self.heatpump_array
        self.building_instance.dict_energy['heatpump_consumption_compressor_array'] = self.compressor_array
        self.building_instance.dict_energy['heatpump_consumption_peak_array'] = self.peak_array  
        
        
        # bør turtemperatur regnes ut for seg i en egen klasse?
        # husk forskjell i COP-data fra denne og grunnvarme
        
        # turtemperatur fra utetemperatur
        # regne ut COP ut ifra turtemperatur og kildetemperatur (utetemperatur)
        # få ut serier
################
        
class OperationCosts:
    def __init__(self, building_instance):
        self.building_instance = building_instance

    def set_spotprice_array(self, year, region, surcharge=0):
        df = pd.read_csv(filepath_or_buffer=f'src/data/spotprices_{year}.csv', sep=';', index_col=0)
        self.spotprice_array = np.array(list(df[region])) + surcharge

    def set_network_tarrifs(self):
        pass

    def set_network_energy_component(self):
        hours_in_year = pd.date_range(start='2023-01-01 00:00:00', end='2023-12-31 23:00:00', freq='h')
        network_energy_array = np.zeros(8760)
        for i in range(0, len(network_energy_array)):
            element = hours_in_year[i]
            hour = element.hour
            month = element.month
            weekday = element.dayofweek
            if (0 <= hour < 6) or (22 <= hour <= 23) or (weekday in [5,6]): # night
                if (month in [1, 2, 3]): # jan - mar
                    energy_component = 32.09
                else: # apr - dec
                    energy_component = 40.75
            else: # day
                if (month in [1, 2, 3]): # jan - mar
                    energy_component = 39.59
                else:
                    energy_component = 48.25 # apr - dec
            energy_component = energy_component/100
            network_energy_array[i] = energy_component
        self.network_energy_array = network_energy_array
    
    def _network_capacity_component(self, demand_array):
        previous_index = 0
        daymax = 0
        daymax_list = []
        series_list = []
        cost_per_hour = 0
        for index, value in enumerate(demand_array):
            if value > daymax:
                daymax = value
            if index % 24 == 23:
                daymax_list.append(daymax)
                daymax = 0
            if index in [744, 1416, 2160, 2880, 3624, 4344, 5088, 5832, 6552, 7296, 8016, 8759]:
                daymax_list = np.sort(daymax_list)[::-1]
                average_max_value = np.mean(daymax_list[0:3])
                if 0 < average_max_value <= 2:
                    cost = 120
                elif 2 < average_max_value <= 5:
                    cost = 190
                elif 5 < average_max_value <= 10:
                    cost = 305
                elif 10 < average_max_value <= 15:
                    cost = 420
                elif 15 < average_max_value <= 20:
                    cost = 535
                elif 20 < average_max_value <= 25:
                    cost = 650
                elif 25 < average_max_value <= 50:
                    cost = 1225
                elif 50 < average_max_value <= 75:
                    cost = 1800
                elif 75 < average_max_value <= 100:
                    cost = 2375
                elif average_max_value > 100:
                    cost = 4750
                else:
                    cost = 0
                cost_per_hour = cost/(index-previous_index)
                daymax_list = []
                previous_index = index
            series_list.append(cost_per_hour)
        return series_list

    def set_network_tariffs(self):
        # utbedre
        pass     

    def calculate_operation_costs(self, array):
        spotcosts_array = self.spotprice_array * array # spotpris
        network_energycosts_array = self.network_energy_array * array # energiledd
        network_capacitycosts_array = self._network_capacity_component(array) # kapasitetsledd
        return spotcosts_array + network_energycosts_array + network_capacitycosts_array

    def get_operation_costs(self):
        dict_operation_costs = {}
        for key, array in self.building_instance.dict_energy.items():
            dict_operation_costs[key] = self.calculate_operation_costs(array)
        self.building_instance.dict_operation_costs = dict_operation_costs

################
    
class GreenEnergyFund:
    def __init__(self, building_instance):
        self.building_instance = building_instance

    def set_economic_parameters(self, investering_borehole=0, investering_øvrig=9012000, inflation=2.00, renteswap=2.25, rentemarginal=1.50, belåning=30.00, ekonomisk_livslengd=15, management_fee_percentage=1.00, bolagsskatt=22.00, driftskostnad_per_år=50000):
        self.INVESTERING_BOREHOLE = investering_borehole
        self.INVESTERING_ØVIRG = investering_øvrig
        self.INFLATION = inflation
        self.RENTESWAP = renteswap 
        self.RENTEMARGINAL = rentemarginal 
        self.BELÅNING = belåning
        self.EKONOMISK_LIVSLENGD = ekonomisk_livslengd
        self.MANAGEMENT_FEE_PERCENTAGE = management_fee_percentage
        self.BOLAGSSKATT = bolagsskatt
        self.DRIFTSKOSTNAD_PER_ÅR = driftskostnad_per_år

        self.INVESTERING = self.INVESTERING_BOREHOLE + self.INVESTERING_ØVIRG
        self.RENTEKOSTNAD = self.RENTESWAP + self.RENTEMARGINAL
        self.EGENKAPTIAL = self.INVESTERING * (1 - self.BELÅNING/100)
        self.LÅN = self.INVESTERING - self.EGENKAPTIAL

    def set_energy_parameters(self, produced_heat=900000, produced_heat_value=1173724, consumed_electricity_cost=254500):
        self.produced_heat = produced_heat
        self.produced_heat_value = produced_heat_value
        self.consumed_electricity_cost = consumed_electricity_cost

    def calculation_15_year(self, leasingavgift_år_1, amortering_lån_år=15):
        # konstanter
        MANAGEMENT_FEE = -self.INVESTERING * self.MANAGEMENT_FEE_PERCENTAGE/100
        AVSKRIVNING = -self.INVESTERING / self.EKONOMISK_LIVSLENGD
        if amortering_lån_år > 0:
            AMORTERING = -self.LÅN / amortering_lån_år
        else:
            AMORTERING = 0
        MANAGEMENT_FEE_array = [round(MANAGEMENT_FEE)] * 15
        AVSKRIVNING_ARRAY = [round(AVSKRIVNING)] * 15
        AMORTERING_ARRAY = [round(AMORTERING)] * 15
        # iterasjon
        avgift_array = []
        driftskostnad_array = []
        EBIT_array = []
        rentekostnad_array = []
        EBT_array = []
        bolagsskatt_array = []
        gevinst_etter_skatt_array = []
        kassaflode_innan_driftskostnader_array = []
        cash_flow_array = []
        for year in range(0, 15):
            if year == 0:
                avgift = leasingavgift_år_1
                driftskostnad = self.DRIFTSKOSTNAD_PER_ÅR
                rentekostnad = self.LÅN * self.RENTEKOSTNAD/100
            else:
                avgift = (1 + self.INFLATION/100) * avgift
                driftskostnad = (1 + self.INFLATION/100) * driftskostnad
                rentekostnad = (self.LÅN + AMORTERING * year) * self.RENTEKOSTNAD/100
            EBIT = avgift - driftskostnad + MANAGEMENT_FEE + AVSKRIVNING
            EBT = EBIT - rentekostnad
            bolagsskatt = EBT * self.BOLAGSSKATT/100
#            if bolagsskatt < 0:
#                bolagsskatt = 0
            gevinst_etter_skatt = EBT - bolagsskatt
            kassaflode_innan_driftskostnader = driftskostnad - AVSKRIVNING + gevinst_etter_skatt
            kassaflode_sum = kassaflode_innan_driftskostnader + AMORTERING

            avgift_array.append(round(avgift))
            driftskostnad_array.append(round(-driftskostnad))
            EBIT_array.append(round(EBIT))
            rentekostnad_array.append(round(-rentekostnad))
            EBT_array.append(round(EBT))
            bolagsskatt_array.append(round(-bolagsskatt))
            gevinst_etter_skatt_array.append(round(gevinst_etter_skatt))
            kassaflode_innan_driftskostnader_array.append(round(kassaflode_innan_driftskostnader))
            cash_flow_array.append(round(kassaflode_sum))

        cash_flow_array.insert(0, -round(self.EGENKAPTIAL))
        avgift_array.insert(0, 0)
        driftskostnad_array.insert(0, 0)
        EBIT_array.insert(0, 0)
        rentekostnad_array.insert(0, 0)
        EBT_array.insert(0, 0)
        bolagsskatt_array.insert(0, 0)
        gevinst_etter_skatt_array.insert(0, 0)
        MANAGEMENT_FEE_array.insert(0, 0)
        AVSKRIVNING_ARRAY.insert(0, 0)
        AMORTERING_ARRAY.insert(0, 0)
        self.df_profit_and_loss_15 = pd.DataFrame({
            'Avgift' : avgift_array,
            'Management fee' : MANAGEMENT_FEE_array,
            'Driftskostnader' : driftskostnad_array,
            'Avskrivning' : AVSKRIVNING_ARRAY,
            'EBIT' : EBIT_array,
            'Rentekostnad' : rentekostnad_array,
            'EBT' : EBT_array,
            'Bolagsskatt' : bolagsskatt_array,
            'Gevinst etter skatt' : gevinst_etter_skatt_array
        }).transpose()

        self.irr_value_15 = npf.irr(cash_flow_array)

################
class Visualization:
    def __init__(self):
        pass

    def plot_hourly_series(
        self,
        *args,
        colors=("#1d3c34", "#4d4b32", "#4d4b32"),
        xlabel=None,
        ylabel=None,
        ymin=None,
        ymax=None,
        height=200,
        showlegend=True,
        linemode=False,
        xtick_datemode=True,
        yticksuffix=' kW',
        unit='kW',
        export_name = None
    ):
        if unit == 'kW':
            unit_sum = 'kWh/år'
        elif unit == 'kr':
            unit_sum = 'kr/år'
        elif unit == '°C':
            unit_sum = '°C'
        elif unit == '-':
            unit_sum = '-'
            
        num_series = len(args) // 2
        colors = colors[:num_series]  # Ensure colors match the number of series
        y_arrays = [arg for arg in args[::2]]
        if xtick_datemode:
            start = datetime.datetime(2023, 1, 1, 0)  # Start from January 1, 2023, 00:00
            end = datetime.datetime(2023, 12, 31, 23)  # End on December 31, 2023, 23:00
            hours = int((end - start).total_seconds() / 3600) + 1
            x_arr = np.array([start + datetime.timedelta(hours=i) for i in range(hours)])
            ticksuffix = None
        else:
            x_arr = np.arange(0, 8760, 1)
            start = 0
            end = 8760
            ticksuffix = ' t'
        fig = go.Figure()
        if linemode == False:
            stackgroup='one'
            fill='tonexty'
            width=0
            barmode='stack'
        else:
            stackgroup, fill, width, barmode = None, None, 1, None
        for i in range(num_series):
            fig.add_trace(
                go.Scatter(
                    x=x_arr,
                    y=y_arrays[i],
                    stackgroup=stackgroup,
                    fill=fill,
                    line=dict(width=width, color=colors[i]),
                    name=f"{args[i*2+1]}:<br>{round(np.sum(y_arrays[i])):,} {unit_sum} | {round(np.max(y_arrays[i])):,} {unit}".replace(",", " ").replace(".", ",")
                    )
                )
        fig.update_layout(
            legend=dict(yanchor="top", y=0.98, xanchor="left", x=0.01, bgcolor="rgba(0,0,0,0)", font=dict(size=16), orientation="h"),
            height=height,
            xaxis_title=xlabel, 
            yaxis_title=ylabel,
            barmode=barmode, 
            margin=dict(l=20, r=20, t=20, b=20, pad=0),
            showlegend=showlegend,
            xaxis=dict(tickfont=dict(size=16), gridwidth=0.1),
            yaxis=dict(tickfont=dict(size=16), gridwidth=0.1),
        )
        fig.update_xaxes(
            ticksuffix=ticksuffix,
            tickformat="%d.%m",
            range=[start, end],
            mirror=True,
            ticks="outside",
            showline=True,
            #linecolor="black",
            #gridcolor="lightgrey",
        )
        fig.update_yaxes(
            ticksuffix=yticksuffix,
            range=[ymin, ymax],
            mirror=True,
            ticks="outside",
            showline=True,
            #linecolor="black",
            #gridcolor="lightgrey",
        )
        if export_name != None:
            fig.write_image(f"src/plots/{export_name}.svg")
        return fig
