import numpy as np
from scripts import Building, EnergyDemand, GeoEnergy, SolarPanels, HeatPump, DistrictHeating

# instansiering av klassene
building_instance = Building()
energydemand_instance = EnergyDemand(building_instance)
geoenergy_instance = GeoEnergy(building_instance)
solar_instance = SolarPanels(building_instance)
heatpump_instance = HeatPump(building_instance)
districtheating_instance = DistrictHeating(building_instance)
print(building_instance, energydemand_instance, geoenergy_instance, solar_instance, heatpump_instance, districtheating_instance)

# sette nye parametere til Building
building_instance = Building()
energydemand_instance = EnergyDemand(building_instance)
energydemand_instance.set_spaceheating_array(array=[1,2,3,4,5])
energydemand_instance.set_dhw_array(array=np.zeros(8760))
energydemand_instance.set_electric_array(array=[10,9,95,4,3,2])
print(building_instance.spaceheating_array)
print(building_instance.dhw_array)
print(building_instance.electric_array)

# bruk PROFet til å sette energibehov
building_instance = Building()
building_instance.profet_building_standard = ["Lite energieffektivt", "Lite energieffektivt"]
building_instance.profet_building_type = ["Leilighet", "Hus"]
building_instance.area = [5000,3000]
energydemand_instance = EnergyDemand(building_instance)
energydemand_instance.profet_calculation()
print(building_instance.spaceheating_array)
print(building_instance.dhw_array)
print(building_instance.electric_array)




