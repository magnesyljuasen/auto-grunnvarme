import streamlit as st
import pandas as pd
from src.scripts.scripts import Building, EnergyDemand, GeoEnergy, SolarPanels, HeatPump, DistrictHeating, OperationCosts, GreenEnergyFund

st.write("Energibehov fra fil. Grunnvarme dekker romoppvarming og tappevann. Vi legger også til solproduksjon.")
st.code("""
df = pd.read_csv('src/testdata/solar_dummy.csv', sep=';')
solar_array = df['Småhus'] * 100
df = pd.read_csv('src/testdata/energy_demand_dummy.csv', sep=',', index_col=0)
spaceheating_array = df['SpaceHeating'].to_list()
dhw_array = df['DHW'].to_list()
building_instance = Building()
energydemand_instance = EnergyDemand(building_instance)
energydemand_instance.set_spaceheating_array(array = spaceheating_array)
energydemand_instance.set_dhw_array(array = dhw_array)
geoenergy_instance = GeoEnergy(building_instance)
geoenergy_instance.set_base_parameters(spaceheating_cop=3.5, spaceheating_coverage=90, dhw_cop=2.5, dhw_coverage=70)
geoenergy_instance.set_demand(spaceheating_demand=building_instance.dict_energy['spaceheating_array'], dhw_demand=building_instance.dict_energy['dhw_array'])
geoenergy_instance.simple_coverage_cop_calculation()
solar_instance = SolarPanels(building_instance)
solar_instance.set_solar_array(array = solar_array)
geoenergy_instance.calculate_heat_pump_size()
geoenergy_instance.simple_sizing_of_boreholes()
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.caption("Levert fra varmepumpe")
    st.area_chart(-building_instance.dict_energy['geoenergy_production_array'], height=200)
with c2:
    st.caption("Kompressor varmepumpe")
    st.area_chart(building_instance.dict_energy['geoenergy_consumption_compressor_array'], height=200)
with c3:
    st.caption("Spisslast")
    st.area_chart(building_instance.dict_energy['geoenergy_consumption_peak_array'], height=200)
with c4:
    st.caption("Strøm fra solceller")
    st.area_chart(-building_instance.dict_energy['solar_production_array'], height=200)
st.dataframe(data = building_instance.dict_energy, height=200, use_container_width=True)
""")
if st.button("Kjør kode", key="0"):
    df = pd.read_csv('src/testdata/solar_dummy.csv', sep=';')
    solar_array = df['Småhus'] * 100
    df = pd.read_csv('src/testdata/energy_demand_dummy.csv', sep=',', index_col=0)
    spaceheating_array = df['SpaceHeating'].to_list()
    dhw_array = df['DHW'].to_list()
    building_instance = Building()
    energydemand_instance = EnergyDemand(building_instance)
    energydemand_instance.set_spaceheating_array(array = spaceheating_array)
    energydemand_instance.set_dhw_array(array = dhw_array)
    geoenergy_instance = GeoEnergy(building_instance)
    geoenergy_instance.set_base_parameters(spaceheating_cop=3.5, spaceheating_coverage=90, dhw_cop=2.5, dhw_coverage=70)
    geoenergy_instance.set_demand(spaceheating_demand=building_instance.dict_energy['spaceheating_array'], dhw_demand=building_instance.dict_energy['dhw_array'])
    geoenergy_instance.simple_coverage_cop_calculation()
    solar_instance = SolarPanels(building_instance)
    solar_instance.set_solar_array(array = solar_array)
    geoenergy_instance.calculate_heat_pump_size()
    geoenergy_instance.simple_sizing_of_boreholes()
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.caption("Levert fra varmepumpe")
        st.area_chart(-building_instance.dict_energy['geoenergy_production_array'], height=200)
    with c2:
        st.caption("Kompressor varmepumpe")
        st.area_chart(building_instance.dict_energy['geoenergy_consumption_compressor_array'], height=200)
    with c3:
        st.caption("Spisslast")
        st.area_chart(building_instance.dict_energy['geoenergy_consumption_peak_array'], height=200)
    with c4:
        st.caption("Strøm fra solceller")
        st.area_chart(-building_instance.dict_energy['solar_production_array'], height=200)
    st.dataframe(data = building_instance.dict_energy, height=200, use_container_width=True)
