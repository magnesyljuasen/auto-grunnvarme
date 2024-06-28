import streamlit as st
import pandas as pd
from src.scripts.scripts import Building, EnergyDemand, GeoEnergy, SolarPanels, HeatPump, DistrictHeating, OperationCosts, GreenEnergyFund

st.write("PROFet for ett bygg med **standard** temperaturserie")
st.code("""
from src.scripts import Building, EnergyDemand
building_instance = Building()
building_instance.profet_building_standard = ["Lite energieffektivt"]
building_instance.profet_building_type = ["Kontor"]
building_instance.area = [2000]
energydemand_instance = EnergyDemand(building_instance)
energydemand_instance.profet_calculation()
c1, c2, c3 = st.columns(3)
with c1:
    st.area_chart(building_instance.dict_energy['spaceheating_array'], height=200)
with c2:
    st.area_chart(building_instance.dict_energy['dhw_array'], height=200)
with c3:
    st.area_chart(building_instance.dict_energy['electric_array'], height=200)
st.dataframe(data = building_instance.dict_energy, height=200, use_container_width=True)
""")
if st.button("Kjør kode", key="0"):
    building_instance = Building()
    building_instance.profet_building_standard = ["Lite energieffektivt"]
    building_instance.profet_building_type = ["Kontor"]
    building_instance.area = [2000]
    energydemand_instance = EnergyDemand(building_instance)
    energydemand_instance.profet_calculation()
    c1, c2, c3 = st.columns(3)
    with c1:
        st.area_chart(building_instance.dict_energy['spaceheating_array'], height=200)
    with c2:
        st.area_chart(building_instance.dict_energy['dhw_array'], height=200)
    with c3:
        st.area_chart(building_instance.dict_energy['electric_array'], height=200)
    st.dataframe(data = building_instance.dict_energy, height=200, use_container_width=True)

st.markdown("---")

st.write("PROFet for **kombinasjonsbygg** med **standard** temperaturserie")
st.code("""
from src.scripts import Building, EnergyDemand
building_instance = Building()
building_instance.profet_building_standard = ["Veldig energieffektivt", "Middels energieffektivt"]
building_instance.profet_building_type = ["Kontor", "Leilighet"]
building_instance.area = [2000, 5000]
energydemand_instance = EnergyDemand(building_instance)
energydemand_instance.profet_calculation()
c1, c2, c3 = st.columns(3)
with c1:
    st.area_chart(building_instance.dict_energy['spaceheating_array'], height=200)
with c2:
    st.area_chart(building_instance.dict_energy['dhw_array'], height=200)
with c3:
    st.area_chart(building_instance.dict_energy['electric_array'], height=200)
st.dataframe(data = building_instance.dict_energy, height=200, use_container_width=True)
""")
if st.button("Kjør kode", key="1"):
    building_instance = Building()
    building_instance.profet_building_standard = ["Veldig energieffektivt", "Middels energieffektivt"]
    building_instance.profet_building_type = ["Kontor", "Leilighet"]
    building_instance.area = [2000, 5000]
    energydemand_instance = EnergyDemand(building_instance)
    energydemand_instance.profet_calculation()
    c1, c2, c3 = st.columns(3)
    with c1:
        st.area_chart(building_instance.dict_energy['spaceheating_array'], height=200)
    with c2:
        st.area_chart(building_instance.dict_energy['dhw_array'], height=200)
    with c3:
        st.area_chart(building_instance.dict_energy['electric_array'], height=200)
    st.dataframe(data = building_instance.dict_energy, height=200, use_container_width=True)

st.markdown("---")

st.write("PROFet for **kombinasjonsbygg** med **egendefinert** temperaturserie")
st.code("""
import pandas as pd        
from src.scripts import Building, EnergyDemand
building_instance = Building()
building_instance.profet_building_standard = ["Veldig energieffektivt", "Middels energieffektivt"]
building_instance.profet_building_type = ["Kontor", "Leilighet"]
building_instance.area = [2000, 5000]
df = pd.read_csv('src/testdata/temperatures_dummy.csv', sep=',', index_col=0)
temperature_array = df['2021-2022'].to_list()
building_instance.temperature_array = temperature_array
energydemand_instance = EnergyDemand(building_instance)
energydemand_instance.profet_calculation()
c1, c2, c3 = st.columns(3)
with c1:
    st.area_chart(building_instance.dict_energy['spaceheating_array'], height=200)
with c2:
    st.area_chart(building_instance.dict_energy['dhw_array'], height=200)
with c3:
    st.area_chart(building_instance.dict_energy['electric_array'], height=200)
st.dataframe(data = building_instance.dict_energy, height=200, use_container_width=True)
""")
if st.button("Kjør kode", key="2"):
    building_instance = Building()
    building_instance.profet_building_standard = ["Veldig energieffektivt", "Middels energieffektivt"]
    building_instance.profet_building_type = ["Kontor", "Leilighet"]
    building_instance.area = [2000, 5000]
    df = pd.read_csv('src/testdata/temperatures_dummy.csv', sep=',', index_col=0)
    temperature_array = df['2021-2022'].to_list()
    building_instance.outdoor_temperature_array = temperature_array
    energydemand_instance = EnergyDemand(building_instance)
    energydemand_instance.profet_calculation()
    c1, c2, c3 = st.columns(3)
    with c1:
        st.area_chart(building_instance.dict_energy['spaceheating_array'], height=200)
    with c2:
        st.area_chart(building_instance.dict_energy['dhw_array'], height=200)
    with c3:
        st.area_chart(building_instance.dict_energy['electric_array'], height=200)
    st.dataframe(data = building_instance.dict_energy, height=200, use_container_width=True)