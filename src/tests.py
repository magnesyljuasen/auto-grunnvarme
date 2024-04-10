import numpy as np
import pandas as pd
from scripts import Building, EnergyDemand, GeoEnergy, SolarPanels, HeatPump, DistrictHeating

def energy_demand_tests():
    # instansiering av klassene
    print("---")
    building_instance = Building()
    energydemand_instance = EnergyDemand(building_instance)
    geoenergy_instance = GeoEnergy(building_instance)
    solar_instance = SolarPanels(building_instance)
    heatpump_instance = HeatPump(building_instance)
    districtheating_instance = DistrictHeating(building_instance)
    print(building_instance, energydemand_instance, geoenergy_instance, solar_instance, heatpump_instance, districtheating_instance)

    # sette nye parametere til Building
    print("---")
    building_instance = Building()
    energydemand_instance = EnergyDemand(building_instance)
    energydemand_instance.set_spaceheating_array(array=[1,2,3,4,5])
    energydemand_instance.set_dhw_array(array=np.zeros(8760))
    energydemand_instance.set_electric_array(array=[10,9,95,4,3,2])
    print(building_instance.spaceheating_array)
    print(building_instance.dhw_array)
    print(building_instance.electric_array)

    # bruk PROFet til å sette energibehov med default temperatur på kombinasjonsbygg
    print("---")
    building_instance = Building()
    building_instance.profet_building_standard = ["Lite energieffektivt", "Veldig energieffektivt"]
    building_instance.profet_building_type = ["Leilighet", "Hus"]
    building_instance.area = [5000, 3000]
    energydemand_instance = EnergyDemand(building_instance)
    energydemand_instance.profet_calculation()
    print(np.sum(building_instance.spaceheating_array))
    print(np.sum(building_instance.dhw_array))
    print(np.sum(building_instance.electric_array))

    # bruk PROFet til å sette energibehov med egen temperatur på kombinasjonsbygg
    print("---")
    building_instance = Building()
    building_instance.profet_building_standard = ["Lite energieffektivt", "Veldig energieffektivt"]
    building_instance.profet_building_type = ["Leilighet", "Hus"]
    building_instance.area = [5000, 3000]
    df = pd.read_csv('src/testdata/temperatures_dummy.csv', sep=',', index_col=0)
    temperature_array = df['2021-2022'].to_list()
    building_instance.temperature_array = temperature_array
    energydemand_instance = EnergyDemand(building_instance)
    energydemand_instance.profet_calculation()
    print(np.sum(building_instance.spaceheating_array))
    print(np.sum(building_instance.dhw_array))
    print(np.sum(building_instance.electric_array))

    # hent inn energibehov fra fil
    print("---")
    df = pd.read_csv('src/testdata/energy_demand_dummy.csv', sep=',', index_col=0)
    space_heating_array = df['SpaceHeating'].to_list()
    dhw_array = df['DHW'].to_list()
    electric_array = df['Electric'].to_list()
    building_instance = Building()
    energydemand_instance = EnergyDemand(building_instance)
    energydemand_instance.set_spaceheating_array(array = space_heating_array)
    energydemand_instance.set_dhw_array(array = dhw_array)
    energydemand_instance.set_electric_array(array = electric_array)
    print(np.sum(building_instance.spaceheating_array))
    print(np.sum(building_instance.dhw_array))
    print(np.sum(building_instance.electric_array))

def geoenergy_tests():
    # energibehov fra fil -> grunnvarme dekker romoppvarming og tappevann
    print("---")
    df = pd.read_csv('src/testdata/energy_demand_dummy.csv', sep=',', index_col=0)
    spaceheating_array = df['SpaceHeating'].to_list()
    dhw_array = df['DHW'].to_list()
    building_instance = Building()
    energydemand_instance = EnergyDemand(building_instance)
    energydemand_instance.set_spaceheating_array(array = spaceheating_array)
    energydemand_instance.set_dhw_array(array = dhw_array)
    geoenergy_instance = GeoEnergy(building_instance)
    geoenergy_instance.set_base_parameters(spaceheating_cop=3.5, spaceheating_coverage=90, dhw_cop=2, dhw_coverage=80)
    geoenergy_instance.set_demand(spaceheating_demand=building_instance.spaceheating_array, dhw_demand=building_instance.dhw_array)
    geoenergy_instance.simple_coverage_cop_calculation()
    print(np.sum(building_instance.spaceheating_array + building_instance.dhw_array))
    print(np.sum(building_instance.geoenergy_production_array))
    print(np.sum(building_instance.geoenergy_consumption_array))
    print(building_instance.find_energy_arrays())

    

if __name__ == "__main__":
    #energy_demand_tests()
    geoenergy_tests()