from typing import Union
from shapely.geometry import Polygon, Point
import numpy as np
import pandas as pd
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient
import numpy_financial as npf

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
        self.dict_energy = {}

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
