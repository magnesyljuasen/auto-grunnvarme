import streamlit as st
import pandas as pd
import numpy as np
from src.scripts import Building, EnergyDemand, GeoEnergy, SolarPanels, HeatPump, DistrictHeating, OperationCosts, GreenEnergyFund, Visualization

st.set_page_config(layout='wide')

st.write("Sjøsiden Hovde - Utregninger")

def calculation(TEMPERATUR, BYGNINGSSTANDARD, BYGNINGSTYPE, BYGNINGSAREAL, ROMOPPVARMING_COP, ROMOPPVARMING_DEKNINGSGRAD, TAPPEVANN_COP, TAPPEVANN_DEKNINGSGRAD, SPOT_YEAR, SPOT_REGION, SPOT_PAASLAG ):
    df = pd.read_excel('src/testdata/Beregninger - Sjøsiden Hovde.xlsx', sheet_name='Utetemperatur')
    temperature_array = df[TEMPERATUR].tolist()
    # Geoenergy
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
    geoenergy_instance.calculate_investment_costs()
    #--
    heatpump_instance = HeatPump(building_instance)
    heatpump_instance.advanced_sizing_of_heat_pump()
    #--
    operation_costs_instance = OperationCosts(building_instance)
    operation_costs_instance.set_spotprice_array(year=SPOT_YEAR, region=SPOT_REGION, surcharge=SPOT_PAASLAG)
    operation_costs_instance.set_network_tariffs()
    operation_costs_instance.set_network_energy_component()
    operation_costs_instance.get_operation_costs()
    green_energy_fund_instance = GreenEnergyFund(building_instance)
    green_energy_fund_instance.set_economic_parameters(
        investering_borehole=geoenergy_instance.investment_cost_borehole, 
        investering_øvrig=geoenergy_instance.investment_cost_heat_pump,
        driftskostnad_per_år=(building_instance.dict_operation_costs['geoenergy_consumption_compressor_array'] + building_instance.dict_operation_costs['geoenergy_consumption_peak_array']).sum())
    green_energy_fund_instance.set_energy_parameters(
        produced_heat=building_instance.dict_energy['geoenergy_production_array'].sum(),
        produced_heat_value=building_instance.dict_operation_costs['geoenergy_production_array'].sum(),
        consumed_electricity_cost=(building_instance.dict_operation_costs['geoenergy_consumption_compressor_array']  + building_instance.dict_operation_costs['geoenergy_consumption_peak_array']).sum()
    )
    green_energy_fund_instance.calculation_15_year(leasingavgift_år_1=round(green_energy_fund_instance.INVESTERING*0.102), amortering_lån_år=15)
    
    #-- results
    visualization_instance = Visualization()
    figure_demands = visualization_instance.plot_hourly_series(
        building_instance.dict_energy['dhw_array'],
        'Tappevannsbehov',
        building_instance.dict_energy['spaceheating_array'],
        'Romoppvarmingsbehov',
#        building_instance.dict_energy['electric_array'],
#        'Elspesifkt behov',
        height=250,
        colors=("#367061", "#8ec9b9")
    )
    figure_thermal = visualization_instance.plot_hourly_series(
        geoenergy_instance.compressor_array,
        'Strøm til varmepumpe',
        geoenergy_instance.from_wells_array,
        'Levert fra brønner',
        geoenergy_instance.peak_array,
        'Spisslast',
        height=250,
        colors=("#1d3c34", "#48a23f", "#FFC358")
    )
    ymax_costs = np.max(building_instance.dict_operation_costs['dhw_array'] + building_instance.dict_operation_costs['spaceheating_array'])
    figure_cost_direct_electric_heating = visualization_instance.plot_hourly_series(
        building_instance.dict_operation_costs['dhw_array'],
        'Strøm til tappevann',
        building_instance.dict_operation_costs['spaceheating_array'],
        'Strøm til romoppvarming',
        unit='kr',
        yticksuffix=' kr',
        ymin=0,
        ymax=ymax_costs,
        height=250,
        colors=("#367061", "#8ec9b9")
    )
    figure_cost_geoenergy = visualization_instance.plot_hourly_series(
        building_instance.dict_operation_costs['geoenergy_consumption_compressor_array'],
        'Strøm til varmepumpe',
        building_instance.dict_operation_costs['geoenergy_consumption_peak_array'],
        'Strøm til spisslast',
        unit='kr',
        yticksuffix=' kr',
        ymin=0,
        ymax=ymax_costs,
        height=250,
        colors=("#367061", "#8ec9b9")
    )
    st.header('1) Energibehov')
    st.plotly_chart(figure_demands, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': False})    
    c1, c2, c3 = st.columns(3)
    with c1:
        spaceheating_energy_per_year = round(np.sum(building_instance.dict_energy['spaceheating_array']))
        spaceheating_effect_per_year = round(np.max(building_instance.dict_energy['spaceheating_array']))
        st.metric('Energi til romoppvarming', value = f'{spaceheating_energy_per_year:,} kWh/år'.replace(',', ' '))
        st.metric('Maksimal effekt til romoppvarming', value = f'{spaceheating_effect_per_year:,} kW'.replace(',', ' '))
    with c2:
        dhw_energy_per_year = round(np.sum(building_instance.dict_energy['dhw_array']))
        dhw_effect_per_year = round(np.max(building_instance.dict_energy['dhw_array']))
        st.metric('Energi til tappevann', value = f'{dhw_energy_per_year:,} kWh/år'.replace(',', ' '))
        st.metric('Maksimal effekt til tappevann', value = f'{dhw_effect_per_year:,} kW'.replace(',', ' '))
    with c3:
        total_effect_per_year = round(np.max(building_instance.dict_energy['spaceheating_array'] + building_instance.dict_energy['dhw_array']))
        dhw_energy_per_year = round(np.sum(building_instance.dict_energy['dhw_array']))
        dhw_effect_per_year = round(np.max(building_instance.dict_energy['dhw_array']))
        st.metric('Energi til **oppvarmingsformål**', value = f'{dhw_energy_per_year + spaceheating_energy_per_year:,} kWh/år'.replace(',', ' '))
        st.metric('Maksimal effekt til **oppvarmingsformål**', value = f'{total_effect_per_year:,} kW'.replace(',', ' '))
    st.markdown('---')
    st.header('2) Bergvarme')
    st.subheader('Energiflyt')
    st.plotly_chart(figure_thermal, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': False})
    with st.expander("Detaljerte figurer", expanded=False):
        st.caption("Turtemperatur, varmesystem")
        st.line_chart(geoenergy_instance.flow_temperature_array, height=150)
        st.caption("Utetemperatur")
        st.line_chart(building_instance.temperature_array, height=150)
        st.caption("Brønntemperatur, år 12-13")
        st.line_chart(geoenergy_instance.fluid_temperature[8760*12:8760*13], height=150)
        st.caption("COP")
        st.line_chart(geoenergy_instance.cop_array, height=150)
    st.subheader('Investering')
    c1, c2 = st.columns(2)
    with c1:
        st.metric('Varmepumpestørrelse', value = f'{building_instance.geoenergy_heat_pump_size} kW')
        st.metric('Investeringskostnad for **bergvarmepumpe**', value = f'{building_instance.geoenergy_investment_cost_heat_pump:,} kr'.replace(',', ' '))
    with c2:
        st.metric('Antall brønner', value = f'{geoenergy_instance.number_of_boreholes} brønner á {geoenergy_instance.depth_per_borehole} m')
        st.metric('Investeringskostnad for **brønner**', value = f'{building_instance.geoenergy_investment_cost_borehole:,} kr'.replace(',', ' '))
    st.metric(f'**Investeringskostnad for bergvarme**', value = f'{building_instance.geoenergy_investment_cost_borehole + building_instance.geoenergy_investment_cost_heat_pump:,} kr'.replace(',', ' '))
    st.subheader('Driftskostnader')
    c1, c2 = st.columns(2)
    with c1:
        st.write('**Bergvarme**')
        st.plotly_chart(figure_cost_geoenergy, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': False})
        geoenergy_operation_costs_per_year = round(np.sum(building_instance.dict_operation_costs['geoenergy_consumption_compressor_array'] + building_instance.dict_operation_costs['geoenergy_consumption_peak_array']))
        st.metric(f'Driftskostnad for **bergvarme**', value = f'{geoenergy_operation_costs_per_year:,} kr/år'.replace(',', ' '))
    with c2:
        st.write('**Elektrisk oppvarming**')
        st.plotly_chart(figure_cost_direct_electric_heating, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': False})
        geoenergy_operation_costs_per_year = round(np.sum(building_instance.dict_operation_costs['spaceheating_array'] + building_instance.dict_operation_costs['dhw_array']))
        st.metric(f'Driftskostnad for **direkte elektrisk oppvarming**', value = f'{geoenergy_operation_costs_per_year:,} kr/år'.replace(',', ' '))
    st.subheader('Serviettkalkyle')
    st.write(f"IRR: **{round(green_energy_fund_instance.irr_value_15*100, 3)} %**")
    st.dataframe(data = green_energy_fund_instance.df_profit_and_loss_15, use_container_width=True)
    st.markdown('---')
    st.header('3) Væske-vann-varmepumpe')

        
selected_byggetrinn = st.radio('Velg byggetrinn', options=['Byggetrinn 2', 'Byggetrinn 1 + 2'])
if selected_byggetrinn == 'Byggetrinn 2':
    BYGNINGSAREAL = 2321
else:
    BYGNINGSAREAL = 2321 * 2
BYGNINGSTYPE = 'Leilighet'
ROMOPPVARMING_COP = 3.5
ROMOPPVARMING_DEKNINGSGRAD = 95
TAPPEVANN_COP = 3.5
TAPPEVANN_DEKNINGSGRAD = 90
BYGNINGSSTANDARD = st.selectbox('Bygningsstandard', options=['Veldig energieffektivt', 'Middels energieffektivt'])
TEMPERATUR = st.selectbox('Temperaturår', options=['2022-2023', '2021-2022', '2020-2021', '2019-2020'])
SPOT_YEAR = st.selectbox('Spotprisår', options=[2021, 2022, 2023])
SPOT_REGION = 'NO3'
SPOT_PAASLAG = 0

if st.button('Start beregning'):
    with st.spinner('Beregner...'):
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

    
    