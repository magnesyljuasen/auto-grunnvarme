import streamlit as st
import pandas as pd
import numpy as np
from src.scripts.scripts import Building, EnergyDemand, GeoEnergy, SolarPanels, HeatPump, DistrictHeating, OperationCosts, GreenEnergyFund, Visualization

st.set_page_config(layout='wide')


st.write("Sjøsiden Hovde - Utregninger")

def calculation(TEMPERATUR, BYGNINGSSTANDARD, BYGNINGSTYPE, BYGNINGSAREAL, ROMOPPVARMING_COP, ROMOPPVARMING_DEKNINGSGRAD, TAPPEVANN_COP, TAPPEVANN_DEKNINGSGRAD, SPOT_YEAR, SPOT_REGION, SPOT_PAASLAG, power_reduction, cop_reduction, MULTIPLIER = 1):
    df = pd.read_excel('src/testdata/Beregninger - Sjøsiden Hovde.xlsx', sheet_name='Utetemperatur')
    outdoor_temperature_array = list(df[TEMPERATUR])
    # Geoenergy
    building_instance = Building()
    building_instance.profet_building_standard = [BYGNINGSSTANDARD]
    building_instance.profet_building_type = [BYGNINGSTYPE]
    building_instance.area = [BYGNINGSAREAL]
    building_instance.outdoor_temperature_array = outdoor_temperature_array 
    energydemand_instance = EnergyDemand(building_instance)
    energydemand_instance.profet_calculation(spaceheating_sum=128167 * MULTIPLIER, dhw_sum=42722 * MULTIPLIER)
    energydemand_instance.calcluate_flow_temperature()
    geoenergy_instance = GeoEnergy(building_instance)
    geoenergy_instance.set_base_parameters(spaceheating_cop=ROMOPPVARMING_COP, spaceheating_coverage=ROMOPPVARMING_DEKNINGSGRAD, dhw_cop=TAPPEVANN_COP, dhw_coverage=TAPPEVANN_DEKNINGSGRAD)
    geoenergy_instance.set_demand(spaceheating_demand=building_instance.dict_energy['spaceheating_array'], dhw_demand=building_instance.dict_energy['dhw_array'])
    geoenergy_instance.set_demand(spaceheating_demand=building_instance.dict_energy['spaceheating_array'] + building_instance.dict_energy['dhw_array'], dhw_demand=np.zeros(8760))
    geoenergy_instance.simple_coverage_cop_calculation()
    geoenergy_instance.calculate_heat_pump_size()
    geoenergy_instance.set_simulation_parameters()
    geoenergy_instance.advanced_sizing_of_boreholes(variable_cop_sizing=True)
    #geoenergy_instance.simple_sizing_of_boreholes()
    geoenergy_instance.calculate_investment_costs()
    #--
    heatpump_instance = HeatPump(building_instance)
    heatpump_instance.set_base_parameters(spaceheating_cop=ROMOPPVARMING_COP, spaceheating_coverage=ROMOPPVARMING_DEKNINGSGRAD, dhw_cop=TAPPEVANN_COP, dhw_coverage=TAPPEVANN_DEKNINGSGRAD)
    heatpump_instance.set_demand(spaceheating_demand=building_instance.dict_energy['spaceheating_array'], dhw_demand=building_instance.dict_energy['dhw_array'])
    heatpump_instance.set_simulation_parameters()
    heatpump_instance.nspek_heatpump_calculation(P_NOMINAL=32 * MULTIPLIER, power_reduction=power_reduction, cop_reduction=cop_reduction)
    #heatpump_instance.advanced_sizing_of_heat_pump()
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
        height=400,
        ylabel='Effekt (kW)',
        yticksuffix=None,
        colors=("#367061", "#8ec9b9")
    )
    figure_geoenergy = visualization_instance.plot_hourly_series(
        geoenergy_instance.compressor_array,
        'Strøm til varmepumpe',
        geoenergy_instance.from_wells_array,
        'Levert fra brønner',
        geoenergy_instance.peak_array,
        'Spisslast',
        ylabel='Effekt (kW)',
        yticksuffix=None,
        height=500,
        colors=("#1d3c34", "#48a23f", "#FFC358")
    )
    figure_heatpump = visualization_instance.plot_hourly_series(
        heatpump_instance.compressor_array,
        'Strøm til varmepumpe',
        heatpump_instance.from_air_array,
        'Levert fra luft',
        heatpump_instance.peak_array,
        'Spisslast',
        ylabel='Effekt (kW)',
        yticksuffix=None,
        height=500,
        colors=("#1d3c34", "#48a23f", "#FFC358")
    )
    ymax_costs = np.max(building_instance.dict_operation_costs['dhw_array'] + building_instance.dict_operation_costs['spaceheating_array'])
    figure_cost_direct_electric_heating = visualization_instance.plot_hourly_series(
        building_instance.dict_operation_costs['dhw_array'],
        'Strøm til tappevann',
        building_instance.dict_operation_costs['spaceheating_array'],
        'Strøm til romoppvarming',
        unit='kr',
        ylabel='Kostnad (kr)',
        yticksuffix=None,
        ymin=0,
        ymax=ymax_costs,
        height=250,
        colors=("#367061", "#8ec9b9"),
        export_name='Grunnvarme'
    )
    figure_cost_geoenergy = visualization_instance.plot_hourly_series(
        building_instance.dict_operation_costs['geoenergy_consumption_compressor_array'],
        'Strøm til varmepumpe',
        building_instance.dict_operation_costs['geoenergy_consumption_peak_array'],
        'Strøm til spisslast',
        unit='kr',
        ylabel='Kostnad (kr)',
        yticksuffix=None,
        ymin=0,
        ymax=ymax_costs,
        height=250,
        colors=("#367061", "#8ec9b9")
    )
    figure_cost_heatpump = visualization_instance.plot_hourly_series(
        building_instance.dict_operation_costs['heatpump_consumption_compressor_array'],
        'Strøm til varmepumpe',
        building_instance.dict_operation_costs['heatpump_consumption_peak_array'],
        'Strøm til spisslast',
        unit='kr',
        ylabel='Kostnad (kr)',
        yticksuffix=None,
        ymin=0,
        ymax=ymax_costs,
        height=250,
        colors=("#367061", "#8ec9b9")
    )
    figure_flow_temperature = visualization_instance.plot_hourly_series(
        geoenergy_instance.flow_temperature_array,
        'Turtemperatur, varmesystem',
        unit='°C',
        linemode=True,
        ymin=30,
        ymax=50,
        ylabel='Temperatur (°C)',
        showlegend=False,
        yticksuffix=None,
        height=250,
        colors=("#367061", "#8ec9b9")
    )
    #st.write(np.mean(building_instance.outdoor_temperature_array), np.max(building_instance.outdoor_temperature_array), np.min(building_instance.outdoor_temperature_array))
    figure_outdoor_temperature = visualization_instance.plot_hourly_series(
        building_instance.outdoor_temperature_array,
        'Utetemperatur',
        unit='°C',
        linemode=True,
        ymin=-20,
        ymax=30,
        ylabel='Utetemperatur (°C)',
        showlegend=False,
        yticksuffix=None,
        height=250,
        colors=("#367061", "#8ec9b9")
    )
    figure_well_temperature = visualization_instance.plot_hourly_series(
        geoenergy_instance.fluid_temperature[8760*12:8760*13],
        'Brønntemperatur, år 12 - 13',
        unit='°C',
        linemode=True,
        ylabel='Brønntemperatur, år 12 - 13 (°C)',
        showlegend=False,
        yticksuffix=None,
        height=250,
        colors=("#367061", "#8ec9b9")
    )
    figure_cop_geoenergy = visualization_instance.plot_hourly_series(
        geoenergy_instance.cop_array,
        'COP',
        unit='-',
        linemode=True,
        ylabel='COP',
        showlegend=False,
        yticksuffix=None,
        ymin=0,
        ymax=5,
        height=250,
        colors=("#367061", "#8ec9b9")
    )
    figure_cop_heatpump = visualization_instance.plot_hourly_series(
        heatpump_instance.cop_array,
        'COP',
        unit='-',
        linemode=True,
        ylabel='COP',
        ymin=0,
        ymax=5,
        showlegend=False,
        yticksuffix=None,
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
    pd.DataFrame({'Til EED' : -geoenergy_instance.from_wells_array*1000}).to_csv('til_eed.csv')
    pd.DataFrame({
        'Romoppvarming_sum' : [int(building_instance.dict_energy['spaceheating_array'].sum())],
        'Tappevann_sum' : [int(building_instance.dict_energy['dhw_array'].sum())],
        'DirekteElektrisk_sum' : [int((building_instance.dict_energy['dhw_array'] + building_instance.dict_energy['spaceheating_array']).sum())],
        'Levert_fra_luft_sum' : [int(heatpump_instance.from_air_array.sum())],
        'Kompressor_luft_sum' : [int(heatpump_instance.compressor_array.sum())],
        'Spisslast_luft_sum' : [int(heatpump_instance.peak_array.sum())],
        'Strøm_luft_sum' : [int((heatpump_instance.peak_array + heatpump_instance.compressor_array).sum())],
        'Levert_fra_brønn_sum' : [int(geoenergy_instance.from_wells_array.sum())],
        'Kompressor_grunnvarme_sum' : [int(geoenergy_instance.compressor_array.sum())],
        'Strøm_grunnvarme_sum' : [int((geoenergy_instance.peak_array + geoenergy_instance.compressor_array).sum())],
        'Spisslast_grunnvarme_sum' : [int(geoenergy_instance.peak_array.sum())],
        'Romoppvarming_maks' : [int(building_instance.dict_energy['spaceheating_array'].max())],
        'Tappevann_maks' : [int(building_instance.dict_energy['dhw_array'].max())],
        'DirekteElektrisk_maks' : [int((building_instance.dict_energy['dhw_array'] + building_instance.dict_energy['spaceheating_array']).max())],
        'Levert_fra_luft_maks' : [int(heatpump_instance.from_air_array.max())],
        'Kompressor_luft_maks' : [int(heatpump_instance.compressor_array.max())],
        'Strøm_luft_maks' : [int((heatpump_instance.peak_array + heatpump_instance.compressor_array).max())],
        'Spisslast_luft_maks' : [int(heatpump_instance.peak_array.max())],
        'Levert_fra_brønn_maks' : [int(geoenergy_instance.from_wells_array.max())],
        'Kompressor_grunnvarme_maks' : [int(geoenergy_instance.compressor_array.max())],
        'Strøm_grunnvarme_maks' : [int((geoenergy_instance.peak_array + geoenergy_instance.compressor_array).max())],
        'Spisslast_grunnvarme_maks' : [int(geoenergy_instance.peak_array.max())]
         }).T.to_csv(f'data_{selected_byggetrinn}.csv')
    #--
    pd.DataFrame({
        'Romoppvarming' : (building_instance.dict_energy['spaceheating_array']),
        'Tappevann' : (building_instance.dict_energy['dhw_array']),
        'DirekteElektrisk' : ((building_instance.dict_energy['dhw_array'] + building_instance.dict_energy['spaceheating_array'])),
        'Levert_fra_luft' : (heatpump_instance.from_air_array),
        'Kompressor_luft' : (heatpump_instance.compressor_array),
        'Spisslast_luft' : (heatpump_instance.peak_array),
        'Strøm_luft' : ((heatpump_instance.peak_array + heatpump_instance.compressor_array)),
        'Levert_fra_brønn' : (geoenergy_instance.from_wells_array),
        'Kompressor_grunnvarme' : (geoenergy_instance.compressor_array),
        'Strøm_grunnvarme' : ((geoenergy_instance.peak_array + geoenergy_instance.compressor_array)),
        'Spisslast_grunnvarme' : (geoenergy_instance.peak_array),
         }).to_csv(f'timeserier_{selected_byggetrinn}.csv')
    st.plotly_chart(figure_geoenergy, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': False})
    with st.expander("Detaljerte figurer", expanded=False):
        st.plotly_chart(figure_flow_temperature, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': False})
        st.plotly_chart(figure_outdoor_temperature, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': False})
        st.plotly_chart(figure_well_temperature, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': False})
        #st.pyplot(geoenergy_instance.field, use_container_width=True)
        st.caption("COP")
        st.plotly_chart(figure_cop_geoenergy, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': False})
        st.metric('SCOP', value = round(np.sum(geoenergy_instance.heatpump_array)/np.sum(geoenergy_instance.compressor_array),1))
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
    st.write('**Bergvarme**')
    st.plotly_chart(figure_cost_geoenergy, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': False})
    geoenergy_operation_costs_per_year = round(np.sum(building_instance.dict_operation_costs['geoenergy_consumption_compressor_array'] + building_instance.dict_operation_costs['geoenergy_consumption_peak_array']))
    st.metric(f'Driftskostnad for **bergvarme**', value = f'{geoenergy_operation_costs_per_year:,} kr/år'.replace(',', ' '))
    #    st.subheader('Serviettkalkyle')
#    st.write(f"IRR: **{round(green_energy_fund_instance.irr_value_15*100, 3)} %**")
#    st.dataframe(data = green_energy_fund_instance.df_profit_and_loss_15, use_container_width=True)
    st.markdown('---')
    st.header('3) Luft-vann-varmepumpe')
    st.subheader('Energiflyt')
    st.plotly_chart(figure_heatpump, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': False})
    with st.expander("Detaljerte figurer", expanded=False):
        st.caption("COP")
        st.plotly_chart(figure_cop_heatpump, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': False})
        st.metric('SCOP', value = round(np.sum(heatpump_instance.heatpump_array)/np.sum(heatpump_instance.compressor_array),1))
    st.subheader('Investering')
    st.write('...')
    st.subheader('Driftskostnader')
    st.write('**Luft-vann-varmepumpe**')
    st.plotly_chart(figure_cost_heatpump, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': False})
    geoenergy_operation_costs_per_year = round(np.sum(building_instance.dict_operation_costs['heatpump_consumption_compressor_array'] + building_instance.dict_operation_costs['heatpump_consumption_peak_array']))
    st.metric(f'Driftskostnad for **luft-vann-varmepumpe**', value = f'{geoenergy_operation_costs_per_year:,} kr/år'.replace(',', ' '))
    st.header('4) Direkte elektrisk oppvarming')
    st.subheader('Driftskostnader')
    st.plotly_chart(figure_cost_direct_electric_heating, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': False})
    electric_operation_costs_per_year = round(np.sum(building_instance.dict_operation_costs['spaceheating_array'] + building_instance.dict_operation_costs['dhw_array']))
    st.metric(f'Driftskostnad for **direkte elektrisk oppvarming**', value = f'{electric_operation_costs_per_year:,} kr/år'.replace(',', ' '))

    

    st.markdown("---")
    st.header('5) Oppsummering')
    with st.expander("Variabler"):
        st.write(vars(building_instance))
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric('Strøm for **direkte elektrisk oppvarming**', value = f'{dhw_energy_per_year + spaceheating_energy_per_year:,} kWh/år'.replace(',', ' '))
    with c2:
        geoenergy_operation_costs_per_year = round(np.sum(building_instance.dict_energy['heatpump_consumption_compressor_array'] + building_instance.dict_energy['heatpump_consumption_peak_array']))
        st.metric(f'Strøm for **luft-vann-varmepumpe**', value = f'{geoenergy_operation_costs_per_year:,} kWh'.replace(',', ' '))
    with c3:
        geoenergy_operation_costs_per_year = round(np.sum(building_instance.dict_energy['geoenergy_consumption_compressor_array'] + building_instance.dict_energy['geoenergy_consumption_peak_array']))
        st.metric(f'Strøm for **bergvarme**', value = f'{geoenergy_operation_costs_per_year:,} kWh'.replace(',', ' '))    
    #--
    with c1:
        electric_operation_costs_per_year = round(np.sum(building_instance.dict_operation_costs['spaceheating_array'] + building_instance.dict_operation_costs['dhw_array']))
        st.metric(f'Driftskostnad for **direkte elektrisk oppvarming**', value = f'{electric_operation_costs_per_year:,} kr/år'.replace(',', ' '))
    with c2:
        geoenergy_operation_costs_per_year = round(np.sum(building_instance.dict_operation_costs['heatpump_consumption_compressor_array'] + building_instance.dict_operation_costs['heatpump_consumption_peak_array']))
        st.metric(f'Driftskostnad for **luft-vann-varmepumpe**', value = f'{geoenergy_operation_costs_per_year:,} kr/år'.replace(',', ' '))
    with c3:
        geoenergy_operation_costs_per_year = round(np.sum(building_instance.dict_operation_costs['geoenergy_consumption_compressor_array'] + building_instance.dict_operation_costs['geoenergy_consumption_peak_array']))
        st.metric(f'Driftskostnad for **bergvarme**', value = f'{geoenergy_operation_costs_per_year:,} kr/år'.replace(',', ' '))
    #--
selected_byggetrinn = st.radio('Velg byggetrinn', options=['Byggetrinn 2', 'Byggetrinn 1 + 2'])
if selected_byggetrinn == 'Byggetrinn 2':
    MULTIPLIER = 1
    BYGNINGSAREAL = 2321 * MULTIPLIER
else:
    MULTIPLIER = 2
    BYGNINGSAREAL = 2321 * MULTIPLIER
BYGNINGSTYPE = 'Leilighet'
ROMOPPVARMING_COP = 3.5
ROMOPPVARMING_DEKNINGSGRAD = 98.8
TAPPEVANN_COP = 2.5
TAPPEVANN_DEKNINGSGRAD = 90
BYGNINGSSTANDARD = 'Middels energieffektivt'
TEMPERATUR = st.selectbox('Temperaturår', options=['ØRLANDET', 'TRONDHEIM', '2022-2023', '2021-2022', '2020-2021', '2019-2020'])
SPOT_YEAR = st.selectbox('Spotprisår', options=[2023, 2022, 2021, 2020])
SPOT_REGION = 'NO3'
SPOT_PAASLAG = 0

power_reduction = st.number_input('Prosentvis reduksjon i effekt', value = 0, min_value=0, max_value=100)
cop_reduction = st.number_input('Prosentvis reduksjon i COP', value = 0, min_value=0, max_value=100)


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
            SPOT_PAASLAG,
            power_reduction,
            cop_reduction,
            MULTIPLIER
            )

    
    