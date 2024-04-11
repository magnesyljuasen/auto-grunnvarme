import streamlit as st
import pandas as pd
from src.scripts import Building, EnergyDemand, GeoEnergy, SolarPanels, HeatPump, DistrictHeating, OperationCosts, GreenEnergyFund

st.write("Integrert serviettkalkyle")
st.code("""
with st.form('Beregning'):
    c1, c2, c3 = st.columns(3)
    with c1:
        BEBYGDAREAL = st.number_input('Bebygd areal', value=100)
        BYGNINGSAREAL = st.number_input('Bygningsareal', value=5000)
    with c2:
        ROMOPPVARMING_COP = st.number_input('Romoppvarming COP', value=3.5)
        ROMOPPVARMING_DEKNINGSGRAD = st.number_input('Romoppvarming dekningsgrad', value=90)
        TAPPEVANN_COP = st.number_input('Tappevann COP', value=2.5)
        TAPPEVANN_DEKNINGSGRAD = st.number_input('Tappevannn dekningsgrad', value=70)
    with c3:
        SPOT_YEAR = st.selectbox('Spotprisår', options=[2021, 2022, 2023])
        SPOT_REGION = st.selectbox('Spotprisregion', options=['NO1', 'NO2', 'NO3', 'NO4', 'NO5'])
        SPOT_PAASLAG = st.number_input('Spotpris-påslag', value=0)
    submitted = st.form_submit_button("Start kalkyle")

if submitted:
    df = pd.read_csv('src/testdata/solar_dummy.csv', sep=';')
    solar_array = df['Småhus'] * BEBYGDAREAL

    building_instance = Building()
    building_instance.profet_building_standard = ["Lite energieffektivt"]
    building_instance.profet_building_type = ["Skole"]
    building_instance.area = [BYGNINGSAREAL]
    energydemand_instance = EnergyDemand(building_instance)
    energydemand_instance.profet_calculation()
    geoenergy_instance = GeoEnergy(building_instance)
    geoenergy_instance.set_base_parameters(spaceheating_cop=ROMOPPVARMING_COP, spaceheating_coverage=ROMOPPVARMING_DEKNINGSGRAD, dhw_cop=TAPPEVANN_COP, dhw_coverage=TAPPEVANN_DEKNINGSGRAD)
    geoenergy_instance.set_demand(spaceheating_demand=building_instance.dict_energy['spaceheating_array'], dhw_demand=building_instance.dict_energy['dhw_array'])
    geoenergy_instance.simple_coverage_cop_calculation()
    geoenergy_instance.calculate_heat_pump_size()
    geoenergy_instance.simple_sizing_of_boreholes()
    geoenergy_instance.calculate_investment_costs()
    solar_instance = SolarPanels(building_instance)
    solar_instance.set_solar_array(array = solar_array)
    operation_costs_instance = OperationCosts(building_instance)
    operation_costs_instance.set_spotprice_array(year=SPOT_YEAR, region=SPOT_REGION, surcharge=SPOT_PAASLAG)
    operation_costs_instance.set_network_tariffs()
    operation_costs_instance.set_network_energy_component()
    operation_costs_instance.get_operation_costs()
    green_energy_fund_instance = GreenEnergyFund(building_instance)
    green_energy_fund_instance.set_economic_parameters(
        investering_borehole=geoenergy_instance.investment_cost_borehole, 
        investering_øvrig=geoenergy_instance.investment_cost_heat_pump,
        driftskostnad_per_år=building_instance.dict_operation_costs['geoenergy_consumption_compressor_array'].sum())
    green_energy_fund_instance.set_energy_parameters(
        produced_heat=building_instance.dict_energy['geoenergy_production_array'].sum(),
        produced_heat_value=building_instance.dict_operation_costs['geoenergy_production_array'].sum(),
        consumed_electricity_cost=building_instance.dict_operation_costs['geoenergy_consumption_compressor_array'].sum()
    )
    green_energy_fund_instance.calculation_15_year(leasingavgift_år_1=round(green_energy_fund_instance.INVESTERING*0.102), amortering_lån_år=15)

    st.write(f"IRR: **{round(green_energy_fund_instance.irr_value_15*100, 3)} %**")
    st.dataframe(data = green_energy_fund_instance.df_profit_and_loss_15, use_container_width=True)
    st.write(f"Data som lagres på bygningsobjektet:")
    st.write(vars(building_instance))
""")

with st.form('Beregning'):
    c1, c2, c3 = st.columns(3)
    with c1:
        BYGNINGSTYPE = st.selectbox('Bygningstype', options=['Skole', 'Hus', 'Leilighet', 'Kontor'])
        BYGNINGSSTANDARD = st.selectbox('Bygningsstandard', options=['Veldig energieffektivt', 'Middels energieffektivt', 'Lite energieffektivt'])
        BEBYGDAREAL = st.number_input('Bebygd areal', value=100)
        BYGNINGSAREAL = st.number_input('Bygningsareal', value=5000)
    with c2:
        ROMOPPVARMING_COP = st.number_input('Romoppvarming COP', value=3.5)
        ROMOPPVARMING_DEKNINGSGRAD = st.number_input('Romoppvarming dekningsgrad', value=90)
        TAPPEVANN_COP = st.number_input('Tappevann COP', value=2.5)
        TAPPEVANN_DEKNINGSGRAD = st.number_input('Tappevannn dekningsgrad', value=70)
    with c3:
        SPOT_YEAR = st.selectbox('Spotprisår', options=[2021, 2022, 2023])
        SPOT_REGION = st.selectbox('Spotprisregion', options=['NO1', 'NO2', 'NO3', 'NO4', 'NO5'])
        SPOT_PAASLAG = st.number_input('Spotpris-påslag', value=0)
    submitted = st.form_submit_button("Start kalkyle")

if submitted:
    df = pd.read_csv('src/testdata/solar_dummy.csv', sep=';')
    solar_array = df['Småhus'] * BEBYGDAREAL

    building_instance = Building()
    building_instance.profet_building_standard = [BYGNINGSSTANDARD]
    building_instance.profet_building_type = [BYGNINGSTYPE]
    building_instance.area = [BYGNINGSAREAL]
    energydemand_instance = EnergyDemand(building_instance)
    energydemand_instance.profet_calculation()
    geoenergy_instance = GeoEnergy(building_instance)
    geoenergy_instance.set_base_parameters(spaceheating_cop=ROMOPPVARMING_COP, spaceheating_coverage=ROMOPPVARMING_DEKNINGSGRAD, dhw_cop=TAPPEVANN_COP, dhw_coverage=TAPPEVANN_DEKNINGSGRAD)
    geoenergy_instance.set_demand(spaceheating_demand=building_instance.dict_energy['spaceheating_array'], dhw_demand=building_instance.dict_energy['dhw_array'])
    geoenergy_instance.simple_coverage_cop_calculation()
    geoenergy_instance.calculate_heat_pump_size()
    geoenergy_instance.simple_sizing_of_boreholes()
    geoenergy_instance.calculate_investment_costs()
    solar_instance = SolarPanels(building_instance)
    solar_instance.set_solar_array(array = solar_array)
    operation_costs_instance = OperationCosts(building_instance)
    operation_costs_instance.set_spotprice_array(year=SPOT_YEAR, region=SPOT_REGION, surcharge=SPOT_PAASLAG)
    operation_costs_instance.set_network_tariffs()
    operation_costs_instance.set_network_energy_component()
    operation_costs_instance.get_operation_costs()
    green_energy_fund_instance = GreenEnergyFund(building_instance)
    green_energy_fund_instance.set_economic_parameters(
        investering_borehole=geoenergy_instance.investment_cost_borehole, 
        investering_øvrig=geoenergy_instance.investment_cost_heat_pump,
        driftskostnad_per_år=building_instance.dict_operation_costs['geoenergy_consumption_compressor_array'].sum())
    green_energy_fund_instance.set_energy_parameters(
        produced_heat=building_instance.dict_energy['geoenergy_production_array'].sum(),
        produced_heat_value=building_instance.dict_operation_costs['geoenergy_production_array'].sum(),
        consumed_electricity_cost=building_instance.dict_operation_costs['geoenergy_consumption_compressor_array'].sum()
    )
    green_energy_fund_instance.calculation_15_year(leasingavgift_år_1=round(green_energy_fund_instance.INVESTERING*0.102), amortering_lån_år=15)

    st.write(f""" 
             Det er registrert en {BYGNINGSTYPE.lower()} med 
             bygningsareal {BYGNINGSAREAL} og kategorisert 
             som {BYGNINGSSTANDARD.lower()}. Med PROFet gir dette
             et romoppvarmingsbehov på {round(building_instance.dict_energy['spaceheating_array'].sum())} kWh/år
             med en maksimal effekt på {round(building_instance.dict_energy['spaceheating_array'].max())} kW.
             Tappevannsbehovet blir {round(building_instance.dict_energy['dhw_array'].sum())} kWh/år
             med en maksimal effekt på {round(building_instance.dict_energy['dhw_array'].max())} kW. 
             Det elspesifikke behovet er på {round(building_instance.dict_energy['electric_array'].sum())} kWh/år
             med en maksimal effekt på {round(building_instance.dict_energy['electric_array'].max())} kW. 
    """)
    st.write(f""" 
             Med grunnvarme til romoppvarming (COP = {ROMOPPVARMING_COP} 
             og {ROMOPPVARMING_DEKNINGSGRAD} % energidekningsgrad) og tappevann 
             (COP = {TAPPEVANN_COP} og {TAPPEVANN_DEKNINGSGRAD} % energidekningsgrad), trengs 
             det ca. {building_instance.geoenergy_borehole_meters} m brønn og en varmepumpe
             på {building_instance.geoenergy_heat_pump_size} kW. 
    """)
    st.write(f"""
             Verdien på levert varme fra brønn er 
             {abs(round((building_instance.dict_operation_costs['geoenergy_production_array'] - building_instance.dict_operation_costs['geoenergy_consumption_compressor_array']).sum()))} kr/år.
             """)
    st.write(f"IRR: **{round(green_energy_fund_instance.irr_value_15*100, 3)} %**")
    st.dataframe(data = green_energy_fund_instance.df_profit_and_loss_15, use_container_width=True)
    st.write(f"Data som lagres på bygningsobjektet:")
    st.write(vars(building_instance))
