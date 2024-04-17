import streamlit as st
import pandas as pd
import numpy as np
from src.scripts import Building, EnergyDemand, GeoEnergy, SolarPanels, HeatPump, DistrictHeating, OperationCosts, GreenEnergyFund

st.write("Sjøsiden Hovde - Utregninger")

def calculation(TEMPERATUR, BYGNINGSSTANDARD, BYGNINGSTYPE, BYGNINGSAREAL, ROMOPPVARMING_COP, ROMOPPVARMING_DEKNINGSGRAD, TAPPEVANN_COP, TAPPEVANN_DEKNINGSGRAD, SPOT_YEAR, SPOT_REGION, SPOT_PAASLAG ):
    df = pd.read_excel('src/testdata/Beregninger - Sjøsiden Hovde.xlsx', sheet_name='Utetemperatur')
    temperature_array = df[TEMPERATUR].tolist()
    
    building_instance = Building()
    building_instance.profet_building_standard = [BYGNINGSSTANDARD]
    building_instance.profet_building_type = [BYGNINGSTYPE]
    building_instance.area = [BYGNINGSAREAL]
    building_instance.temperature_array = temperature_array
    energydemand_instance = EnergyDemand(building_instance)
    energydemand_instance.profet_calculation()
    geoenergy_instance = GeoEnergy(building_instance)
    geoenergy_instance.set_base_parameters(spaceheating_cop=ROMOPPVARMING_COP, spaceheating_coverage=ROMOPPVARMING_DEKNINGSGRAD, dhw_cop=TAPPEVANN_COP, dhw_coverage=TAPPEVANN_DEKNINGSGRAD)
    geoenergy_instance.set_demand(spaceheating_demand=building_instance.dict_energy['spaceheating_array'], dhw_demand=building_instance.dict_energy['dhw_array'])
    geoenergy_instance.simple_coverage_cop_calculation()
    geoenergy_instance.calculate_heat_pump_size()
    geoenergy_instance.set_simulation_parameters()
    geoenergy_instance.advanced_sizing_of_boreholes()

    st.caption("Turtemperatur, varmesystem")
    st.line_chart(geoenergy_instance.flow_temperature_array, height=150)
    st.caption("Utetemperatur")
    st.line_chart(building_instance.temperature_array, height=150)
    st.caption("Brønntemperatur, år 12-13")
    st.line_chart(geoenergy_instance.fluid_temperature[8760*12:8760*13], height=150)
    st.caption("COP")
    st.line_chart(geoenergy_instance.cop_array, height=150)
    st.caption(f'''Hentes fra brønnene; Energi: {round(np.sum(geoenergy_instance.from_wells_array)):,} kWh/år | Effekt: {round(np.max(geoenergy_instance.from_wells_array)):,} kW'''.replace(',', ' ')) 
    st.line_chart(geoenergy_instance.from_wells_array, height=150)
    st.caption(f'''Strøm til varmepumpe; Energi: {round(np.sum(geoenergy_instance.compressor_array)):,} kWh/år | Effekt: {round(np.max(geoenergy_instance.compressor_array)):,} kW'''.replace(',', ' ')) 
    st.line_chart(geoenergy_instance.compressor_array, height=150)
    
#    geoenergy_instance.simple_sizing_of_boreholes()
#    geoenergy_instance.calculate_investment_costs()
#    operation_costs_instance = OperationCosts(building_instance)
#    operation_costs_instance.set_spotprice_array(year=SPOT_YEAR, region=SPOT_REGION, surcharge=SPOT_PAASLAG)
#    operation_costs_instance.set_network_tariffs()
#    operation_costs_instance.set_network_energy_component()
#    operation_costs_instance.get_operation_costs()
#    green_energy_fund_instance = GreenEnergyFund(building_instance)
#    green_energy_fund_instance.set_economic_parameters(
#        investering_borehole=geoenergy_instance.investment_cost_borehole, 
#        investering_øvrig=geoenergy_instance.investment_cost_heat_pump,
#        driftskostnad_per_år=building_instance.dict_operation_costs['geoenergy_consumption_compressor_array'].sum())
#    green_energy_fund_instance.set_energy_parameters(
#        produced_heat=building_instance.dict_energy['geoenergy_production_array'].sum(),
#        produced_heat_value=building_instance.dict_operation_costs['geoenergy_production_array'].sum(),
#        consumed_electricity_cost=building_instance.dict_operation_costs['geoenergy_consumption_compressor_array'].sum()
#    )
#    green_energy_fund_instance.calculation_15_year(leasingavgift_år_1=round(green_energy_fund_instance.INVESTERING*0.102), amortering_lån_år=15)
    #-- results
    #st.write(vars(building_instance))
#    st.subheader('Energibehov')
#    st.caption('Romoppvarming')
#    st.write(f''' Energi: {round(np.sum(building_instance.dict_energy['spaceheating_array'])):,} kWh/år | Effekt: {round(np.max(building_instance.dict_energy['spaceheating_array'])):,} kW'''.replace(',', ' ')) 
#    st.area_chart(data = building_instance.dict_energy['spaceheating_array'], height=200, use_container_width=True)

#    st.caption('Tappevann')
#    st.write(f''' Energi: {round(np.sum(building_instance.dict_energy['dhw_array'])):,} kWh/år | Effekt: {round(np.max(building_instance.dict_energy['dhw_array'])):,} kW'''.replace(',', ' ')) 
#    st.area_chart(data = building_instance.dict_energy['dhw_array'], height=200, use_container_width=True)

#    st.caption('Romoppvarming + tappevann')
#    st.write(f''' Energi: {round(np.sum(building_instance.dict_energy['dhw_array'] + building_instance.dict_energy['spaceheating_array'])):,} kWh/år | Effekt: {round(np.max(building_instance.dict_energy['dhw_array'] + building_instance.dict_energy['spaceheating_array'])):,} kW'''.replace(',', ' ')) 
#    st.area_chart(data = building_instance.dict_energy['dhw_array'] + building_instance.dict_energy['spaceheating_array'], height=200, use_container_width=True)
#    st.markdown('---')

#    st.subheader('Grunnvarme')
#    st.caption('Levert fra varmepumpe')
#    st.write(f''' Energi: {round(-np.sum(building_instance.dict_energy['geoenergy_production_array'])):,} kWh/år | Effekt: {round(-np.max(building_instance.dict_energy['geoenergy_production_array'])):,} kW'''.replace(',', ' ')) 
#    st.area_chart(data = -building_instance.dict_energy['geoenergy_production_array'], height=200, use_container_width=True)

#    st.caption('Strøm til varmepumpe')
#    st.write(f''' Energi: {round(np.sum(building_instance.dict_energy['geoenergy_consumption_compressor_array'])):,} kWh/år | Effekt: {round(np.max(building_instance.dict_energy['geoenergy_consumption_compressor_array'])):,} kW'''.replace(',', ' ')) 
#    st.area_chart(data = building_instance.dict_energy['geoenergy_consumption_compressor_array'], height=200, use_container_width=True)
    
#    st.caption('Spisslast')
#    st.write(f''' Energi: {round(np.sum(building_instance.dict_energy['geoenergy_consumption_peak_array'])):,} kWh/år | Effekt: {round(np.max(building_instance.dict_energy['geoenergy_consumption_peak_array'])):,} kW'''.replace(',', ' ')) 
#    st.area_chart(data = building_instance.dict_energy['geoenergy_consumption_peak_array'], height=200, use_container_width=True)



tab1, tab2 = st.tabs(['Byggetrinn 2', 'Byggetrinn 1 + 2'])
with tab1:
    BYGNINGSTYPE = 'Leilighet'
    BYGNINGSAREAL = 2321
    BYGNINGSSTANDARD = st.selectbox('Bygningsstandard', options=['Veldig energieffektivt', 'Middels energieffektivt', 'Lite energieffektivt'])
    TEMPERATUR = st.selectbox('Temperaturår', options=['2022-2023', '2021-2022', '2020-2021', '2019-2020'])
    ROMOPPVARMING_COP = 3.5
    ROMOPPVARMING_DEKNINGSGRAD = 95
    TAPPEVANN_COP = 3.5
    TAPPEVANN_DEKNINGSGRAD = 90
    SPOT_YEAR = st.selectbox('Spotprisår', options=[2021, 2022, 2023])
    SPOT_REGION = 'NO3'
    SPOT_PAASLAG = 0

    calculation(
        TEMPERATUR,
        BYGNINGSSTANDARD,
        BYGNINGSTYPE, 
        BYGNINGSAREAL, 
        ROMOPPVARMING_COP,
        ROMOPPVARMING_DEKNINGSGRAD,
        TAPPEVANN_COP,
        TAPPEVANN_DEKNINGSGRAD,
        SPOT_YEAR,
        SPOT_REGION,
        SPOT_PAASLAG
        )
    
    