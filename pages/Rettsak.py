import streamlit as st
import pandas as pd
import numpy as np
from src.scripts.scripts import Building, EnergyDemand, GeoEnergy, SolarPanels, HeatPump, DistrictHeating, OperationCosts, GreenEnergyFund, Visualization

st.set_page_config(layout='wide')


st.write("Rettsak - Utregninger")

st.info('Totalt behov (inkl. elspesifikt) bør være ca. likt det som er i excel-arket (dersom det ikke er eksisterende tiltak)')
st.info('Avriming mellom -2 og +7 grader eller -5 og +5 grader (har mye å si for SCOP)?')
st.warning('Hvordan løser vi luft-luft? Det kommer for bra ut her. Bør justere for planløsning? Hva er reinvesteringsintervall og hvor mye er investering på?')

def calculation(factor_air_water, factor_air_air, NAME, WATERBORNE_HEAT_ON, TEMPERATUR, BYGNINGSSTANDARD, BYGNINGSTYPE, BYGNINGSAREAL, ROMOPPVARMING_COP, ROMOPPVARMING_DEKNINGSGRAD, TAPPEVANN_COP, TAPPEVANN_DEKNINGSGRAD, SPOT_YEAR, SPOT_REGION, SPOT_PAASLAG, power_reduction, cop_reduction, MULTIPLIER = 1):
    df = pd.read_excel('src/testdata/Beregninger - Sjøsiden Hovde.xlsx', sheet_name='Utetemperatur')
    cooling_array = pd.read_excel('src/testdata/cooling_sheet.xlsx')['Hus_Oslo'].to_numpy()
    outdoor_temperature_array = list(df[TEMPERATUR])
    # Geoenergy
    building_instance = Building()
    building_instance.profet_building_standard = [BYGNINGSSTANDARD]
    building_instance.profet_building_type = [BYGNINGSTYPE]
    building_instance.area = [BYGNINGSAREAL]
    building_instance.outdoor_temperature_array = outdoor_temperature_array 
    energydemand_instance = EnergyDemand(building_instance)
    energydemand_instance.profet_calculation()
    energydemand_instance.calcluate_flow_temperature()
    geoenergy_instance = GeoEnergy(building_instance)
    geoenergy_instance.set_base_parameters(spaceheating_cop=ROMOPPVARMING_COP, spaceheating_coverage=100, dhw_cop=TAPPEVANN_COP, dhw_coverage=TAPPEVANN_DEKNINGSGRAD)
    geoenergy_instance.set_demand(spaceheating_demand=building_instance.dict_energy['spaceheating_array'], dhw_demand=building_instance.dict_energy['dhw_array'])
    geoenergy_instance.simple_coverage_cop_calculation()
    geoenergy_instance.calculate_heat_pump_size()
    geoenergy_instance.set_simulation_parameters()
    geoenergy_instance.advanced_sizing_of_boreholes(variable_cop_sizing=True)
    #geoenergy_instance.simple_sizing_of_boreholes()
    geoenergy_instance.calculate_investment_costs()
    P_NOMINAL = geoenergy_instance.heat_pump_size
    cooling_demand = BYGNINGSAREAL * cooling_array
    if WATERBORNE_HEAT_ON:
        waterborne_heat_cost = 20000 + 815 * BYGNINGSAREAL
    else:
        waterborne_heat_cost = 0
    #--
    if heatpump_type == 'Luft-vann':
        heatpump_instance = HeatPump(building_instance)
        heatpump_instance.set_base_parameters(spaceheating_cop=ROMOPPVARMING_COP, spaceheating_coverage=100, dhw_cop=TAPPEVANN_COP, dhw_coverage=TAPPEVANN_DEKNINGSGRAD)
        heatpump_instance.set_demand(spaceheating_demand=building_instance.dict_energy['spaceheating_array'], dhw_demand=building_instance.dict_energy['dhw_array'])
        heatpump_instance.set_simulation_parameters()
        heatpump_instance.nspek_heatpump_calculation(P_NOMINAL=P_NOMINAL * factor_air_water * MULTIPLIER, power_reduction=power_reduction, cop_reduction=cop_reduction, coverage=100)
        #heatpump_instance.advanced_sizing_of_heat_pump()
        st.write(f'Luft-vann varmepumpe {P_NOMINAL * factor_air_water} kW')
    elif heatpump_type == 'Luft-luft':
        heatpump_instance = HeatPump(building_instance)
        #heatpump_instance.set_base_parameters(spaceheating_cop=ROMOPPVARMING_COP, spaceheating_coverage=ROMOPPVARMING_DEKNINGSGRAD, dhw_cop=TAPPEVANN_COP, dhw_coverage=TAPPEVANN_DEKNINGSGRAD)
        heatpump_instance.set_demand(spaceheating_demand=building_instance.dict_energy['spaceheating_array'], dhw_demand=np.zeros(8760))
        heatpump_instance.set_simulation_parameters()
        heatpump_instance.P_3031_35 = np.array([
            [0.46, 0.72, 1],
            [0.23, 0.36, 0.5],
            [0.09, 0.14, 0.2]
            ])

        heatpump_instance.COP_3031_35 = np.array([
            [0.44, 0.53, 0.64],
            [0.61, 0.82, 0.9],
            [0.55, 0.68, 0.82]
            ])
        
        heatpump_instance.nspek_heatpump_calculation(P_NOMINAL=P_NOMINAL * factor_air_air * MULTIPLIER, power_reduction=power_reduction, cop_reduction=cop_reduction, coverage=100)
        #heatpump_instance.advanced_sizing_of_heat_pump()
        st.write(f'Luft-luft varmepumpe {P_NOMINAL * factor_air_air} kW')

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
        cooling_demand,
        'Kjølebehov',
        height=400,
        ylabel='Effekt (kW)',
        yticksuffix=None,
        colors=("#367061", "#8ec9b9", "#C98E9E")
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

    figure_spotprice = visualization_instance.plot_hourly_series(
        operation_costs_instance.spotprice_array,
        'Spotpris',
        unit='-',
        linemode=False,
        ylabel='Spotpris (kr)',
        ymin=0,
        ymax=10,
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
    total_effect_per_year = round(np.max(building_instance.dict_energy['spaceheating_array'] + building_instance.dict_energy['dhw_array'] + building_instance.dict_energy['electric_array']))
    total_energy_per_year = round(np.sum(building_instance.dict_energy['spaceheating_array'] + building_instance.dict_energy['dhw_array'] + building_instance.dict_energy['electric_array']))
    st.metric('Energi til **alle formål (inkl. elspesifikt)**', value = f'{total_energy_per_year:,} kWh/år'.replace(',', ' '))
    st.metric('Maksimal effekt til **alle formål (inkl. elspesifikt)**', value = f'{total_effect_per_year:,} kW'.replace(',', ' '))
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
    st.metric('Energidekningsgrad [%]', value=round((geoenergy_instance.heatpump_array.sum() / (building_instance.dict_energy['spaceheating_array'] + building_instance.dict_energy['dhw_array']).sum())*100))
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
        st.metric(f'**Investeringskostnad for bergvarme**', value = f'{building_instance.geoenergy_investment_cost_borehole + building_instance.geoenergy_investment_cost_heat_pump:,} kr'.replace(',', ' '))
        st.metric(f'**Vannbåren varme**', value = f'{waterborne_heat_cost:,} kr'.replace(',', ' '))
        
    with c2:
        st.metric('Antall brønner', value = f'{geoenergy_instance.number_of_boreholes} brønner á {geoenergy_instance.depth_per_borehole} m')
        st.metric('Investeringskostnad for **brønner**', value = f'{building_instance.geoenergy_investment_cost_borehole:,} kr'.replace(',', ' '))
        st.metric('kWh/m', value = f'{int(geoenergy_instance.from_wells_array.sum() / (geoenergy_instance.number_of_boreholes * geoenergy_instance.depth_per_borehole))} kWh/m')
    st.subheader('Spotpris')
    st.plotly_chart(figure_spotprice, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': False})
    st.subheader(f'**Gjennomsnittlig spotpris: {round(operation_costs_instance.spotprice_array.mean(),2)} kr/kWh**')
    st.subheader('Driftskostnader')
    st.write('**Bergvarme**')
    st.plotly_chart(figure_cost_geoenergy, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': False})
    geoenergy_operation_costs_per_year = round(np.sum(building_instance.dict_operation_costs['geoenergy_consumption_compressor_array'] + building_instance.dict_operation_costs['geoenergy_consumption_peak_array']))
    st.metric(f'Driftskostnad for **bergvarme**', value = f'{geoenergy_operation_costs_per_year:,} kr/år'.replace(',', ' '))
    #    st.subheader('Serviettkalkyle')
#    st.write(f"IRR: **{round(green_energy_fund_instance.irr_value_15*100, 3)} %**")
#    st.dataframe(data = green_energy_fund_instance.df_profit_and_loss_15, use_container_width=True)
    st.markdown('---')
    st.header(f'3) {heatpump_type}-varmepumpe')
    st.subheader('Energiflyt')
    st.plotly_chart(figure_heatpump, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': False})
    st.metric('Energidekningsgrad [%]', value=round((heatpump_instance.heatpump_array.sum() / (building_instance.dict_energy['spaceheating_array'] + building_instance.dict_energy['dhw_array']).sum())*100))
    
    with st.expander("Detaljerte figurer", expanded=False):
        st.caption("COP")
        st.plotly_chart(figure_cop_heatpump, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': False})
        st.metric('SCOP', value = round(np.sum(heatpump_instance.heatpump_array)/np.sum(heatpump_instance.compressor_array),1))
    st.subheader('Investering')
    st.write('...')
    st.subheader('Driftskostnader')
    st.write(f'**{heatpump_type}-varmepumpe**')
    st.plotly_chart(figure_cost_heatpump, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': False})
    geoenergy_operation_costs_per_year = round(np.sum(building_instance.dict_operation_costs['heatpump_consumption_compressor_array'] + building_instance.dict_operation_costs['heatpump_consumption_peak_array']))
    st.metric(f'Driftskostnad for **{heatpump_type.lower()}-varmepumpe**', value = f'{geoenergy_operation_costs_per_year:,} kr/år'.replace(',', ' '))
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
        kWh_air_water = round(np.sum(building_instance.dict_energy['heatpump_consumption_compressor_array'] + building_instance.dict_energy['heatpump_consumption_peak_array']))
        st.metric(f'Strøm for **{heatpump_type.lower()}-varmepumpe**', value = f'{kWh_air_water:,} kWh'.replace(',', ' '))
    with c3:
        kWh_geoenergy = round(np.sum(building_instance.dict_energy['geoenergy_consumption_compressor_array'] + building_instance.dict_energy['geoenergy_consumption_peak_array']))
        st.metric(f'Strøm for **bergvarme**', value = f'{kWh_geoenergy:,} kWh'.replace(',', ' '))    
    #--
    with c1:
        cost_el = round(np.sum(building_instance.dict_operation_costs['spaceheating_array'] + building_instance.dict_operation_costs['dhw_array']))
        st.metric(f'Driftskostnad for **direkte elektrisk oppvarming**', value = f'{electric_operation_costs_per_year:,} kr/år'.replace(',', ' '))
    with c2:
        cost_air_water = round(np.sum(building_instance.dict_operation_costs['heatpump_consumption_compressor_array'] + building_instance.dict_operation_costs['heatpump_consumption_peak_array']))
        st.metric(f'Driftskostnad for **{heatpump_type.lower()}-varmepumpe**', value = f'{cost_air_water:,} kr/år'.replace(',', ' '))
    with c3:
        cost_geoenergy = round(np.sum(building_instance.dict_operation_costs['geoenergy_consumption_compressor_array'] + building_instance.dict_operation_costs['geoenergy_consumption_peak_array']))
        st.metric(f'Driftskostnad for **bergvarme**', value = f'{cost_geoenergy:,} kr/år'.replace(',', ' '))
    #--
    

    df2 = pd.DataFrame({
        'Utetemperatur (grader)' : building_instance.outdoor_temperature_array,
        'Turtemperatur, varmesystem (grader)' : geoenergy_instance.flow_temperature_array,
        'Tappevannsbehov (kWh)' : building_instance.dict_energy['dhw_array'],
        'Romoppvarmingsbehov (kWh)' : building_instance.dict_energy['spaceheating_array'],
        'Kjølebehov (kWh)' : cooling_demand,
        'Grunnvarme, kompressor (kWh)' : geoenergy_instance.compressor_array,
        'Grunnvarme, fra brønner (kWh)' : geoenergy_instance.from_wells_array,
        'Grunnvarme, spisslast (kWh)' : geoenergy_instance.peak_array,
        'Grunnvarme, COP' : geoenergy_instance.cop_array,
        f'{heatpump_type}, kompressor (kWh)' : heatpump_instance.compressor_array,
        f'{heatpump_type}, fra luft (kWh)' : heatpump_instance.from_air_array,
        f'{heatpump_type}, spisslast (kWh)' : heatpump_instance.peak_array,
        f'{heatpump_type}, COP' : heatpump_instance.cop_array,
        'Direkte elektrisk, strømkostnad (kr)' : building_instance.dict_operation_costs['dhw_array'] + building_instance.dict_operation_costs['spaceheating_array'],
        'Grunnvarme, strømkostnad (kr)' : building_instance.dict_operation_costs['geoenergy_consumption_compressor_array'] + building_instance.dict_operation_costs['geoenergy_consumption_peak_array'],
        f'{heatpump_type}, strømkostnad (kr)' : building_instance.dict_operation_costs['heatpump_consumption_compressor_array'] + building_instance.dict_operation_costs['heatpump_consumption_peak_array'],
        'Brønntemperatur år 12 - 13 (grader)' : geoenergy_instance.fluid_temperature[8760*12:8760*13],
        'Spotpris (kr)' : operation_costs_instance.spotprice_array
    })
    st.write(df2)
    df2.to_csv(f'rettsak/{NAME}_timeserier.csv')
    if heatpump_type == 'Luft-vann':
        investment_cost_heatpump = (building_instance.geoenergy_investment_cost_heat_pump + building_instance.geoenergy_investment_cost_borehole)*0.76
    else:
        #st.write(P_NOMINAL * factor_air_air)
        #investment_cost_heatpump = (building_instance.geoenergy_investment_cost_heat_pump + building_instance.geoenergy_investment_cost_borehole)*0.3
        investment_cost_heatpump = 30000
    return {
        'Investering bergvarme-VP' : building_instance.geoenergy_investment_cost_heat_pump,
        f'Investering {heatpump_type.lower()}-VP' : investment_cost_heatpump,
        'Investering bergvarme brønner' : building_instance.geoenergy_investment_cost_borehole,
        'Strøm direkte elektrisk' : dhw_energy_per_year + spaceheating_energy_per_year,
        f'Strøm {heatpump_type.lower()}-varmepumpe' : kWh_air_water,
        'Strøm grunnvarme' : kWh_geoenergy,
        'Kostnad direkte elektrisk' : cost_el,
        f'Kostnad {heatpump_type.lower()}-varmepumpe' : cost_air_water,
        'Kostnad grunnvarme' : cost_geoenergy,
        'Vannbåren varme' : waterborne_heat_cost
    }

selected_byggetrinn = 'Rettsak'
MULTIPLIER = 1
NAME = st.text_input('Skriv inn adresse')
BYGNINGSAREAL = st.number_input('Areal', value=200)
#P_NOMINAL = st.number_input('Nominell P', value=10)
YEARS = 40
DISKONTERINGSRENTE = 4
BYGNINGSTYPE = 'Hus'
ROMOPPVARMING_COP = 3.5
ROMOPPVARMING_DEKNINGSGRAD = 100
TAPPEVANN_COP = 2.5
TAPPEVANN_DEKNINGSGRAD = 100
BYGNINGSSTANDARD = 'Lite energieffektivt'
TEMPERATUR = st.selectbox('Temperaturår', options=['Blindern', 'Oslo', 'ØRLANDET', 'TRONDHEIM', '2022-2023', '2021-2022', '2020-2021', '2019-2020'])
SPOT_YEAR = st.selectbox('Spotprisår', options=[2023, 2022, 2021, 2020])
SPOT_REGION = 'NO1'
SPOT_PAASLAG = 0

factor_air_water = st.number_input('Luft-vann (reduksjon i P_nominal)', value=0.7)
factor_air_air = st.number_input('Luft-luft (reduksjon i P_nominal)', value=0.3)
power_reduction = st.number_input('Prosentvis reduksjon i effekt', value = 20, min_value=0, max_value=100)
cop_reduction = st.number_input('Prosentvis reduksjon i COP', value = 20, min_value=0, max_value=100)
WATERBORNE_HEAT_ON = st.toggle('Vannbåren varme?', value=True)
heatpump_type = st.selectbox('Varmepumpe', options=['Luft-vann', 'Luft-luft'])

if st.button('Start beregning'):
    with st.spinner('Beregner...'):
        result_map = calculation(
            factor_air_water,
            factor_air_air,
            NAME,
            WATERBORNE_HEAT_ON,
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
        st.write(result_map)
        st.markdown('---')
        produced_energy_list = np.zeros(YEARS)
        investment_geoenergy_list = np.zeros(YEARS)
        investment_air_water_list = np.zeros(YEARS)
        energy_cost_geoenergy_list = np.zeros(YEARS)
        energy_cost_air_water_list = np.zeros(YEARS)
        cost_direct_el_list = np.zeros(YEARS) 
        cost_geoenergy_list = np.zeros(YEARS)
        cost_air_water_list = np.zeros(YEARS)
        diskonteringsrente_list = np.zeros(YEARS)
        year_list = np.zeros(YEARS)
        for i in range(0, YEARS):
            year_list[i] = i
            if i != 0:
                produced_energy_list[i] = result_map['Strøm direkte elektrisk']
                energy_cost_geoenergy_list[i] = result_map['Kostnad grunnvarme']
                energy_cost_air_water_list[i] = result_map[f'Kostnad {heatpump_type.lower()}-varmepumpe']
                cost_direct_el_list[i] = result_map['Kostnad direkte elektrisk']

            if i == 0:
                investment_geoenergy_list[i] = result_map['Investering bergvarme-VP'] + result_map['Investering bergvarme brønner'] + result_map['Vannbåren varme']
                investment_air_water_list[i] = result_map[f'Investering {heatpump_type.lower()}-VP'] + result_map['Vannbåren varme']
            if heatpump_type == 'Luft-vann':
                if i == 15 or i == 30 or i == 45 or i == 60:
                    investment_air_water_list[i] = result_map[f'Investering {heatpump_type.lower()}-VP']
            elif heatpump_type == 'Luft-luft':
                if i == 10 or i == 20 or i == 30 or i == 40 or i == 50 or i == 60:
                    investment_air_water_list[i] = result_map[f'Investering {heatpump_type.lower()}-VP']
            if i == 20 or i == 40 or i == 60:
                investment_geoenergy_list[i] = result_map['Investering bergvarme-VP']

            cost_geoenergy_list = investment_geoenergy_list + energy_cost_geoenergy_list
            cost_air_water_list = investment_air_water_list + energy_cost_air_water_list
            
            if i >= 1:
                diskonteringsrente = 1 / (1 + (DISKONTERINGSRENTE/100))**i
            else:
                diskonteringsrente = 1
            diskonteringsrente_list[i] = diskonteringsrente
    


        cost_geoenergy_diskontert_list = cost_geoenergy_list * diskonteringsrente_list
        cost_air_water_diskontert_list = cost_air_water_list * diskonteringsrente_list    
        cost_direct_el_diskontert_list = cost_direct_el_list * diskonteringsrente_list
        
        produced_energy_diskontert_list = produced_energy_list * diskonteringsrente_list


        LCOE_geoenergy = round((cost_geoenergy_diskontert_list.sum()/produced_energy_diskontert_list.sum()),2)
        st.write(f'LCOE grunnvarme: **{LCOE_geoenergy} kr/kWh**')

        LCOE_air_water = round((cost_air_water_diskontert_list.sum()/produced_energy_diskontert_list.sum()),2)
        st.write(f'LCOE {heatpump_type.lower()}: **{LCOE_air_water} kr/kWh**')

        LCOE_direct_el = round((cost_direct_el_diskontert_list.sum()/produced_energy_diskontert_list.sum()),2)
        st.write(f'LCOE direkte elektrisk: **{LCOE_direct_el} kr/kWh**')

        st.write(f'Kostnad grunnvarme: **{int(round((cost_geoenergy_diskontert_list.sum()))):,}** kr'.replace(',', ' '))

        st.write(f'Kostnad {heatpump_type.lower()}: **{int(round((cost_air_water_diskontert_list.sum()))):,}** kr'.replace(',', ' '))

        st.write(f'Kostnad direkte elektrisk: **{int(round((cost_direct_el_diskontert_list.sum()))):,}** kr'.replace(',', ' '))

        st.subheader(f'Differanse etter {YEARS} år (grunnvarme. vs {heatpump_type.lower()}): **{int(round((cost_air_water_diskontert_list.sum()))) - int(round((cost_geoenergy_diskontert_list.sum()))):,}** kr'.replace(',', ' '))

        st.subheader(f'Differanse etter {YEARS} år (grunnvarme. vs direkte elektrisk): **{int(round((cost_direct_el_diskontert_list.sum()))) - int(round((cost_geoenergy_diskontert_list.sum()))):,}** kr'.replace(',', ' '))

        df = pd.DataFrame({
            'År' : year_list,
            'Produsert energi' : produced_energy_list,
            'Investering grunnvarme' : investment_geoenergy_list,
            f'Investering {heatpump_type.lower()}' : investment_air_water_list,
            'Diskonteringsrente' : diskonteringsrente_list,
            'Energikostnad grunnvarme' : energy_cost_geoenergy_list,
            f'Energikostnad {heatpump_type.lower()}' : energy_cost_air_water_list,
            'Energikostnad direkte elektrisk' : cost_direct_el_list,
            'Kostnad grunnvarme' : cost_geoenergy_list,
            f'Kostnad {heatpump_type.lower()}' : cost_air_water_list,
            'Kostnad direkte elektrisk' : cost_direct_el_diskontert_list,
            'Kostnad grunnvarme (diskontert)' : cost_geoenergy_diskontert_list,
            f'Kostnad {heatpump_type.lower()} (diskontert)' : cost_air_water_diskontert_list,
            'Kostnad direkte elektrisk (diskontert)' : cost_direct_el_diskontert_list,
            'LCOE grunnvarme' : LCOE_geoenergy,
            f'LCOE {heatpump_type.lower()}' : LCOE_air_water,
            'LCOE_direkte_el' : LCOE_direct_el,
            f'Grunnvarme vs. {heatpump_type.lower()} ({YEARS} år)' : int(round((cost_air_water_diskontert_list.sum()))) - int(round((cost_geoenergy_diskontert_list.sum()))),
            f'Grunnvarme vs. direkte elektrisk ({YEARS} år)' : int(round((cost_direct_el_diskontert_list.sum()))) - int(round((cost_geoenergy_diskontert_list.sum())))
        })
        df = df.set_index('År')
        st.write(df)
        df.to_csv(f'rettsak/{NAME}_kostnader.csv')



            


    
    