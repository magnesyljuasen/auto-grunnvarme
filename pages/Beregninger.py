import streamlit as st
import pandas as pd
import numpy as np
from src.scripts.scripts import Building, EnergyDemand, GeoEnergy, SolarPanels, HeatPump, DistrictHeating, OperationCosts, GreenEnergyFund, Visualization

st.set_page_config(layout='wide')

def economic_comparison(df):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.write('Bergvarme')
        st.metric(label='LCOE (kr/kWh)', value=df['LCOE grunnvarme'][0])
        st.metric(label='Totalkostnad (kr)', value=f"{df['Totalkostnad grunnvarme'][0]:,}".replace(',', ' '))
        st.metric(label='Total inntekt (kr)', value=f"{int(df['Verdi grunnvarme (diskontert)'].sum()):,}".replace(',', ' '))
        st.metric(label='Nåverdi (kr)', value=f"{df['Nåverdi grunnvarme'][0]:,}".replace(',', ' '))
    with c2:
        st.write('Luft-vann')
        st.metric(label='LCOE (kr/kWh)', value=df['LCOE luft-vann'][0])
        st.metric(label='Totalkostnad (kr)', value=f"{df['Totalkostnad luft-vann'][0]:,}".replace(',', ' '))
        st.metric(label='Total inntekt (kr)', value=f"{int(df['Verdi luft-vann-VP (diskontert)'].sum()):,}".replace(',', ' '))
        st.metric(label='Nåverdi (kr)', value=f"{df['Nåverdi luft-vann'][0]:,}".replace(',', ' '))
    with c3:
        st.write('Luft-luft')
        st.metric(label='LCOE (kr/kWh)', value=df['LCOE luft-luft'][0])
        st.metric(label='Totalkostnad (kr)', value=f"{df['Totalkostnad luft-luft'][0]:,}".replace(',', ' '))
        st.metric(label='Total inntekt (kr)', value=f"{int(df['Verdi luft-luft-VP (diskontert)'].sum()):,}".replace(',', ' '))
        st.metric(label='Nåverdi (kr)', value=f"{df['Nåverdi luft-luft'][0]:,}".replace(',', ' '))
    with c4:
        st.write('Direkte elektrisk')
        st.metric(label='LCOE (kr/kWh)', value=df['LCOE_direkte_el'][0])
        st.metric(label='Totalkostnad (kr)', value=f"{df['Totalkostnad direkte elektrisk'][0]:,}".replace(',', ' '))
        st.metric(label='Total inntekt (kr)', value=f"{int(df['Verdi direkte elektrisk (diskontert)'].sum()):,}".replace(',', ' '))
        st.metric(label='Nåverdi (kr)', value=f"{df['Nåverdi direkte elektrisk'][0]:,}".replace(',', ' '))

    #compared_data = {
    #    "luft-vann": df['Totalkostnad luft-vann'][0] - df['Totalkostnad grunnvarme'][0],
    #    "luft-luft": df['Totalkostnad luft-luft'][0] - df['Totalkostnad grunnvarme'][0],
    #    "direkte elektrisk": df['Totalkostnad direkte elektrisk'][0] - df['Totalkostnad grunnvarme'][0],
    #}

    #min_string = min(compared_data, key=compared_data.get)
    #min_number = compared_data[min_string]
    #st.info(f"Bergvarme vs. {min_string}. **Mulig erstatning: {min_number} kr.**")
        

def economic_calculation(result_map, PERCENTAGE_INCREASE=1.00, DISKONTERINGSRENTE=4, YEARS=40, COVERED_BY_ENOVA=0):
    produced_energy_list = np.zeros(YEARS)
    investment_geoenergy_list = np.zeros(YEARS)
    investment_air_water_list = np.zeros(YEARS)
    investment_air_air_list = np.zeros(YEARS)
    investment_direct_list = np.zeros(YEARS)

    energy_cost_geoenergy_list = np.zeros(YEARS)
    energy_cost_air_water_list = np.zeros(YEARS)
    energy_cost_air_air_list = np.zeros(YEARS)
    energy_cost_direct_list = np.zeros(YEARS)

    cost_geoenergy_list = np.zeros(YEARS)
    cost_air_water_list = np.zeros(YEARS)
    cost_air_air_list = np.zeros(YEARS)
    cost_direct_list = np.zeros(YEARS)

    value_geoenergy_list = np.zeros(YEARS)
    value_air_water_list = np.zeros(YEARS)
    value_air_air_list = np.zeros(YEARS)
    value_direct_list = np.zeros(YEARS) 

    diskonteringsrente_list = np.zeros(YEARS)
    year_list = np.zeros(YEARS)
    for i in range(0, YEARS):
        year_list[i] = i
        if i == 1:
            produced_energy_list[i] = result_map['Strøm direkte elektrisk']
            energy_cost_geoenergy_list[i] = result_map['Kostnad grunnvarme (strømstøtte)'] * PERCENTAGE_INCREASE**i
            energy_cost_air_water_list[i] = result_map[f'Kostnad luft-vann-varmepumpe (strømstøtte)'] * PERCENTAGE_INCREASE**i
            energy_cost_air_air_list[i] = result_map[f'Kostnad luft-luft-varmepumpe (strømstøtte)'] * PERCENTAGE_INCREASE**i
            energy_cost_direct_list[i] = result_map['Kostnad direkte elektrisk (strømstøtte)'] * PERCENTAGE_INCREASE**i

            value_geoenergy_list[i] = result_map['Verdi grunnvarme'] * PERCENTAGE_INCREASE**i
            value_air_water_list[i] = result_map['Verdi luft-vann-varmepumpe'] * PERCENTAGE_INCREASE**i
            value_air_air_list[i] = result_map['Verdi luft-luft-varmepumpe'] * PERCENTAGE_INCREASE**i
            value_direct_list[i] = result_map['Verdi direkte elektrisk'] * PERCENTAGE_INCREASE**i

        if i != 0 and i != 1:
            produced_energy_list[i] = result_map['Strøm direkte elektrisk']
            energy_cost_geoenergy_list[i] = result_map['Kostnad grunnvarme'] * PERCENTAGE_INCREASE**i
            energy_cost_air_water_list[i] = result_map[f'Kostnad luft-vann-varmepumpe'] * PERCENTAGE_INCREASE**i
            energy_cost_air_air_list[i] = result_map[f'Kostnad luft-luft-varmepumpe'] * PERCENTAGE_INCREASE**i
            energy_cost_direct_list[i] = result_map['Kostnad direkte elektrisk'] * PERCENTAGE_INCREASE**i

            value_geoenergy_list[i] = result_map['Verdi grunnvarme'] * PERCENTAGE_INCREASE**i
            value_air_water_list[i] = result_map['Verdi luft-vann-varmepumpe'] * PERCENTAGE_INCREASE**i
            value_air_air_list[i] = result_map['Verdi luft-luft-varmepumpe'] * PERCENTAGE_INCREASE**i
            value_direct_list[i] = result_map['Verdi direkte elektrisk'] * PERCENTAGE_INCREASE**i

        if i == 0:
            if WITHOUT_WELL == True:
                investment_geoenergy_list[i] = 15000
            else:
                investment_geoenergy_list[i] = (result_map['Investering bergvarme-VP'] + result_map['Investering bergvarme brønner'] + result_map['Vannbåren varme']) - COVERED_BY_ENOVA
            if COVERED_BY_ENOVA == 15000 or COVERED_BY_ENOVA == 40000:
                air_water_stotte = 15000
            else:
                air_water_stotte = 0
            investment_air_water_list[i] = result_map[f'Investering luft-vann-VP'] + result_map['Vannbåren varme'] - air_water_stotte
            investment_air_air_list[i] = result_map[f'Investering luft-luft-VP'] + result_map['Kostnad direkte elektrisk']*0.4
            investment_direct_list[i] = result_map['Investering direkte elektrisk']

        if i == 15 or i == 30 or i == 45 or i == 60:
            investment_air_water_list[i] = result_map[f'Investering luft-vann-VP'] * 0.6

        if i == 12 or i == 24 or i == 36 or i == 48 or i == 60:
            investment_air_air_list[i] = result_map[f'Investering luft-luft-VP']

        if i == 20 or i == 40 or i == 60:
            #investment_geoenergy_list[i] = result_map['Investering bergvarme-VP'] * 0.6
            investment_direct_list[i] = result_map['Investering direkte elektrisk'] 
            investment_air_air_list[i] = result_map[f'Investering luft-luft-VP'] *0.5

        # GARTNERVEIEN
        if i == 6 or i == 26 or i == 46 or i == 66:
            investment_geoenergy_list[i] = result_map['Investering bergvarme-VP'] * 0.6

        # SKOGVEIEN
        #if i == 7 or i == 27 or i == 47 or i == 67:
        #    investment_geoenergy_list[i] = result_map['Investering bergvarme-VP'] * 0.6

        cost_geoenergy_list = investment_geoenergy_list + energy_cost_geoenergy_list
        cost_air_water_list = investment_air_water_list + energy_cost_air_water_list
        cost_air_air_list = investment_air_air_list + energy_cost_air_air_list
        cost_direct_list = investment_direct_list + energy_cost_direct_list
        
        if i >= 1:
            diskonteringsrente = 1 / (1 + (DISKONTERINGSRENTE/100))**i
        else:
            diskonteringsrente = 1
        diskonteringsrente_list[i] = diskonteringsrente

    cost_geoenergy_diskontert_list = cost_geoenergy_list * diskonteringsrente_list
    cost_air_water_diskontert_list = cost_air_water_list * diskonteringsrente_list    
    cost_air_air_diskontert_list = cost_air_air_list * diskonteringsrente_list
    cost_direct_el_diskontert_list = cost_direct_list * diskonteringsrente_list
    produced_energy_diskontert_list = produced_energy_list * diskonteringsrente_list

    value_geoenergy_diskontert_list = value_geoenergy_list * diskonteringsrente_list
    value_air_water_diskontert_list = value_air_water_list * diskonteringsrente_list
    value_air_air_diskontert_list = value_air_air_list * diskonteringsrente_list
    value_direct_diskontert_list = value_direct_list * diskonteringsrente_list

    geoenergy_LCOE = round((cost_geoenergy_diskontert_list.sum()/produced_energy_diskontert_list.sum()),2)
    air_water_LCOE = round((cost_air_water_diskontert_list.sum()/produced_energy_diskontert_list.sum()),2)
    air_air_LCOE = round((cost_air_air_diskontert_list.sum()/produced_energy_diskontert_list.sum()),2)
    direct_el_LCOE = round((cost_direct_el_diskontert_list.sum()/produced_energy_diskontert_list.sum()),2)

    geoenergy_total_cost = int(cost_geoenergy_diskontert_list.sum())
    air_water_total_cost = int(cost_air_water_diskontert_list.sum())
    air_air_total_cost = int(cost_air_air_diskontert_list.sum())
    direct_el_total_cost = int(cost_direct_el_diskontert_list.sum())

    geoenergy_nnv = int(-(cost_geoenergy_diskontert_list.sum()) + cost_direct_el_diskontert_list.sum())
    air_water_nnv = int(-(cost_air_water_diskontert_list.sum()) + cost_direct_el_diskontert_list.sum())
    air_air_nnv = int(-(cost_air_air_diskontert_list.sum()) + cost_direct_el_diskontert_list.sum())
    direct_nnv = int(-(cost_direct_el_diskontert_list.sum()) + cost_direct_el_diskontert_list.sum())

    c1, c2 = st.columns(2)
    with c1:
        df_costs_geoenergy = pd.DataFrame({
            'Kostnader, grunnvarme' : -cost_geoenergy_diskontert_list,
            'Inntekter, grunnvarme' : cost_direct_el_diskontert_list
        })
        st.bar_chart(df_costs_geoenergy)
        df_costs_air_air = pd.DataFrame({
            'Kostnader, luft-luft' : -cost_air_air_diskontert_list,
            'Inntekter, luft-luft' : cost_direct_el_diskontert_list
        })
        st.bar_chart(df_costs_air_air)
    with c2:
        df_costs_air_water = pd.DataFrame({
            'Kostnader, luft-vann' : -cost_air_water_diskontert_list,
            'Inntekter, luft-vann' : cost_direct_el_diskontert_list
        })
        st.bar_chart(df_costs_air_water)
        df_direct_electric = pd.DataFrame({
            'Kostnader, direkte elektrisk' : -cost_direct_el_diskontert_list,
            'Inntekter, direkte elektrisk' : cost_direct_el_diskontert_list
        })
        st.bar_chart(df_direct_electric)
    df = pd.DataFrame({
        'År' : year_list,
        'Produsert energi' : produced_energy_list,
        'Investering grunnvarme' : investment_geoenergy_list,
        'Investering luft-vann-VP' : investment_air_water_list,
        'Investering luft-luft-VP' : investment_air_air_list,
        'Investering direkte elektrisk' : investment_direct_list,
        'Diskonteringsrente' : diskonteringsrente_list,
        'Energikostnad grunnvarme' : energy_cost_geoenergy_list,
        'Energikostnad luft-vann-VP' : energy_cost_air_water_list,
        'Energikostnad luft-luft-VP' : energy_cost_air_air_list,
        'Energikostnad direkte elektrisk' : cost_direct_list,
        'Kostnad grunnvarme' : cost_geoenergy_list,
        'Kostnad luft-vann-VP' : cost_air_water_list,
        'Kostnad luft-luft-VP' : cost_air_air_list,
        'Kostnad direkte elektrisk' : cost_direct_list,
        'Kostnad grunnvarme (diskontert)' : cost_geoenergy_diskontert_list,
        'Kostnad luft-vann-VP (diskontert)' : cost_air_water_diskontert_list,
        'Kostnad luft-luft-VP (diskontert)' : cost_air_air_diskontert_list,
        'Kostnad direkte elektrisk (diskontert)' : cost_direct_el_diskontert_list,
        'Verdi grunnvarme (diskontert)' : value_geoenergy_diskontert_list,
        'Verdi luft-vann-VP (diskontert)' : value_air_water_diskontert_list,
        'Verdi luft-luft-VP (diskontert)' : value_air_air_diskontert_list,
        'Verdi direkte elektrisk (diskontert)' : value_direct_diskontert_list,
        'LCOE grunnvarme' : geoenergy_LCOE,
        'LCOE luft-vann' : air_water_LCOE,
        'LCOE luft-luft' : air_air_LCOE,
        'LCOE_direkte_el' : direct_el_LCOE,
        'Totalkostnad grunnvarme' : geoenergy_total_cost,
        'Totalkostnad luft-vann' : air_water_total_cost,
        'Totalkostnad luft-luft' : air_air_total_cost,
        'Totalkostnad direkte elektrisk' : direct_el_total_cost,
        'Nåverdi grunnvarme' : geoenergy_nnv,
        'Nåverdi luft-vann' : air_water_nnv,
        'Nåverdi luft-luft' : air_air_nnv,
        'Nåverdi direkte elektrisk' : direct_nnv,
    })
    df = df.set_index('År')
    st.line_chart(energy_cost_geoenergy_list[1:len(energy_cost_geoenergy_list)])
    start_cost = energy_cost_geoenergy_list[1]
    end_cost = energy_cost_geoenergy_list[len(energy_cost_geoenergy_list)-1]
    st.write(f'Økning i driftskostnader (eksempel; bergvarme): {int(((end_cost-start_cost)/start_cost)*100)} %')

    st.write(f'**Gjennomsnittlig strømpris, start (eksempel; bergvarme): {round(start_cost/np.sum(electric_array_geoenergy),2)} kr/kWh**')
    st.write(f'**Gjennomsnittlig strømpris, slutt (eksempel; bergvarme): {round(end_cost/np.sum(electric_array_geoenergy),2)} kr/kWh**')
    
    return df, air_water_stotte

def get_cooling_array():
    cooling_array = pd.read_excel('src/testdata/cooling_sheet.xlsx')['Hus_Oslo'].to_numpy()
    return cooling_array

def get_outdoor_temperature(station = 'Blindern'):
    outdoor_temperature = pd.read_excel('src/testdata/Beregninger - Sjøsiden Hovde.xlsx', sheet_name='Utetemperatur')[station]
    return list(outdoor_temperature)

def calculate_electric(building_instance, energydemand_instance, outdoor_temperature, building_standard, building_type, building_area):

    return building_instance

def calculate_air_air(building_instance, energydemand_instance, outdoor_temperature, building_standard, building_type, building_area):
    SPACEHEATING_COP = 3.5
    SPACEHEATING_COVERAGE = 100
    DHW_COP = 2.5
    DHW_COVERAGE = 100
    
    POWER_REDUCTION = 20
    COP_REDUCTION = 20
    COVERAGE = 100
    P_NOMINAL_REDUCED = st.number_input('Reduser varmepumpestørrelse', value=0.41, step=0.1, key='luft-luft')

    heatpump_instance = HeatPump(building_instance)
    heatpump_instance.set_base_parameters(spaceheating_cop=SPACEHEATING_COP, spaceheating_coverage=SPACEHEATING_COVERAGE, dhw_cop=DHW_COP, dhw_coverage=DHW_COVERAGE)
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
    heatpump_instance.nspek_heatpump_calculation(P_NOMINAL=np.max(heatpump_instance.spaceheating_demand + heatpump_instance.dhw_demand) * P_NOMINAL_REDUCED, power_reduction=POWER_REDUCTION, cop_reduction=COP_REDUCTION, coverage=COVERAGE)

    return building_instance, heatpump_instance

def calculate_air_water(building_instance, energydemand_instance, outdoor_temperature, building_standard, building_type, building_area):
    SPACEHEATING_COP = 3.5
    SPACEHEATING_COVERAGE = 100
    DHW_COP = 2.5
    DHW_COVERAGE = 100
    
    POWER_REDUCTION = 20
    COP_REDUCTION = 20
    COVERAGE = 100
    P_NOMINAL_REDUCED = st.number_input('Reduser varmepumpestørrelse', value=0.65, step=0.1)

    heatpump_instance = HeatPump(building_instance)
    heatpump_instance.set_base_parameters(spaceheating_cop=SPACEHEATING_COP, spaceheating_coverage=SPACEHEATING_COVERAGE, dhw_cop=DHW_COP, dhw_coverage=DHW_COVERAGE)
    heatpump_instance.set_demand(spaceheating_demand=building_instance.dict_energy['spaceheating_array'], dhw_demand=building_instance.dict_energy['dhw_array'])
    heatpump_instance.set_simulation_parameters()
    heatpump_instance.nspek_heatpump_calculation(P_NOMINAL=np.max(heatpump_instance.spaceheating_demand + heatpump_instance.dhw_demand) * P_NOMINAL_REDUCED, power_reduction=POWER_REDUCTION, cop_reduction=COP_REDUCTION, coverage=COVERAGE)

    return building_instance, heatpump_instance

def calculate_geoenergy(building_instance, energydemand_instance, outdoor_temperature, building_standard, building_type, building_area, without_well=False):
    SPACEHEATING_COP = 3.5
    SPACEHEATING_COVERAGE = 99
    DHW_COP = 2.5
    DHW_COVERAGE = 100
    
    geoenergy_instance = GeoEnergy(building_instance)
    geoenergy_instance.set_base_parameters(spaceheating_cop=SPACEHEATING_COP, spaceheating_coverage=SPACEHEATING_COVERAGE, dhw_cop=DHW_COP, dhw_coverage=DHW_COVERAGE)
    geoenergy_instance.set_demand(spaceheating_demand=building_instance.dict_energy['spaceheating_array'], dhw_demand=building_instance.dict_energy['dhw_array'])
    geoenergy_instance.simple_coverage_cop_calculation()
    geoenergy_instance.calculate_heat_pump_size()
    geoenergy_instance.set_simulation_parameters()
    geoenergy_instance.advanced_sizing_of_boreholes(variable_cop_sizing=True)
    geoenergy_instance.calculate_investment_costs()

    #if without_well == True:
    #    building_instance.geoenergy_investment_cost_borehole = 0
    #    building_instance.geoenergy_investment_cost_heat_pump = 0
    #    geoenergy_instance.investment_cost_borehole = 0
    #    geoenergy_instance.investment_cost_heat_pump = 0
        
    
    return building_instance, geoenergy_instance

def display_air_air_results(building_instance, air_air_instance):
    with st.popover('Data', use_container_width=True):
        st.write(vars(air_air_instance))

    c1, c2 = st.columns(2)
    with c1:
        st.metric('Varmepumpestørrelse (kW)', int(np.max(air_air_instance.heatpump_array)))
    with c2:
        st.metric('SCOP', round((np.sum(air_air_instance.heatpump_array)/np.sum(air_air_instance.compressor_array)),2))
    with c1:
        st.metric('Energidekningsgrad totalt (%)', round((np.sum(air_air_instance.heatpump_array)/np.sum(building_instance.dict_energy['dhw_array'] + building_instance.dict_energy['spaceheating_array']))*100))
        st.metric('Energidekningsgrad romoppvarming (%)', round((np.sum(air_air_instance.heatpump_array)/np.sum(building_instance.dict_energy['spaceheating_array']))*100))

    visualization_instance = Visualization()
    figure_air_air = visualization_instance.plot_hourly_series(
        air_air_instance.compressor_array,
        'Strøm til varmepumpe',
        air_air_instance.from_air_array,
        'Levert fra luft',
        air_air_instance.peak_array,
        'Spisslast',
        ylabel='Effekt (kW)',
        yticksuffix=None,
        height=250,
        colors=("#1d3c34", "#48a23f", "#FFC358")
    )

    figure_cop_air_air = visualization_instance.plot_hourly_series(
        air_air_instance.cop_array,
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

    st.plotly_chart(figure_air_air, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': False})
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(figure_cop_air_air, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': False})
  
    electric_array = air_air_instance.compressor_array + air_air_instance.peak_array
    thermal_array = air_air_instance.from_air_array
    return electric_array, thermal_array

def display_electric_results(building_instance):
    with st.popover('Data', use_container_width=True):
        st.write(vars(building_instance))

    visualization_instance = Visualization()
    figure_electric = visualization_instance.plot_hourly_series(
        building_instance.dict_energy['heating_array'],
        'Strøm',
        ylabel='Effekt (kW)',
        yticksuffix=None,
        height=250,
        colors=("#1d3c34", "#48a23f", "#FFC358")
    )

    st.plotly_chart(figure_electric, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': False})
  
    electric_array = building_instance.dict_energy['heating_array']
    thermal_array = np.zeros(8760)
    return electric_array, thermal_array

def display_air_water_results(building_instance, air_water_instance):
    with st.popover('Data', use_container_width=True):
        st.write(vars(air_water_instance))

    c1, c2 = st.columns(2)
    with c1:
        st.metric('Varmepumpestørrelse (kW)', int(np.max(air_water_instance.heatpump_array)))
    with c2:
        st.metric('SCOP', round((np.sum(air_water_instance.heatpump_array)/np.sum(air_water_instance.compressor_array)),2))
    with c1:
        st.metric('Energidekningsgrad (%)', round((np.sum(air_water_instance.heatpump_array)/np.sum(building_instance.dict_energy['dhw_array'] + building_instance.dict_energy['spaceheating_array']))*100))

    visualization_instance = Visualization()
    figure_air_water = visualization_instance.plot_hourly_series(
        air_water_instance.compressor_array,
        'Strøm til varmepumpe',
        air_water_instance.from_air_array,
        'Levert fra luft',
        air_water_instance.peak_array,
        'Spisslast',
        ylabel='Effekt (kW)',
        yticksuffix=None,
        height=250,
        colors=("#1d3c34", "#48a23f", "#FFC358")
    )

    figure_cop_air_water = visualization_instance.plot_hourly_series(
        air_water_instance.cop_array,
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

    st.plotly_chart(figure_air_water, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': False})
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(figure_cop_air_water, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': False})
  
    electric_array = air_water_instance.compressor_array + air_water_instance.peak_array
    thermal_array = air_water_instance.from_air_array
    return electric_array, thermal_array

def display_geoenergy_results(building_instance, geoenergy_instance):
    with st.popover('Data', use_container_width=True):
        st.write(vars(geoenergy_instance))

    c1, c2 = st.columns(2)
    with c1:
        st.metric('Varmepumpestørrelse (kW)', building_instance.geoenergy_heat_pump_size)
    with c2:
        st.metric('Brønndybde (m)', f'{geoenergy_instance.number_of_boreholes} brønn a {geoenergy_instance.depth_per_borehole} m')
    with c1:
        st.metric('Investeringskostnad, brønn (kr)', building_instance.geoenergy_investment_cost_borehole)
    with c2:
        st.metric('Investeringskostnad, varmepumpe (kr)', building_instance.geoenergy_investment_cost_heat_pump)
    with c1:
        st.metric('SCOP', round((np.sum(geoenergy_instance.heatpump_array)/np.sum(geoenergy_instance.compressor_array)),2))
    with c2:
        st.metric('Energidekningsgrad (%)', round((np.sum(geoenergy_instance.heatpump_array)/np.sum(building_instance.dict_energy['dhw_array'] + building_instance.dict_energy['spaceheating_array']))*100))

    visualization_instance = Visualization()
    figure_geoenergy = visualization_instance.plot_hourly_series(
        geoenergy_instance.compressor_array,
        'Strøm til varmepumpe',
        geoenergy_instance.from_wells_array,
        'Levert fra brønner',
        geoenergy_instance.peak_array,
        'Spisslast',
        ylabel='Effekt (kW)',
        yticksuffix=None,
        height=250,
        colors=("#1d3c34", "#48a23f", "#FFC358")
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

    st.plotly_chart(figure_geoenergy, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': False})
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(figure_cop_geoenergy, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': False})
    with c2:
        st.plotly_chart(figure_well_temperature, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': False})

    electric_array = geoenergy_instance.compressor_array + geoenergy_instance.peak_array
    thermal_array = geoenergy_instance.from_wells_array
    return electric_array, thermal_array

def calculate_operation_costs_2(array, SPOT_YEAR, NETTLEIE = 'Variabel', with_stromstotte = False):
    SPOT_REGION = 'NO1'
    SPOT_EXTRA = 0.05

    operation_costs_instance = OperationCosts(building_instance)
    operation_costs_instance.set_spotprice_array(year=SPOT_YEAR, region=SPOT_REGION, surcharge=SPOT_EXTRA)
    if with_stromstotte == True:
        spot_array = operation_costs_instance.spotprice_array
        threshold = 0.9125
        new_spot_array = []
        for i in range(0, len(spot_array)):
            if spot_array[i] > threshold:
                difference = spot_array[i] - threshold
                difference_covered = difference * 0.9
            else:
                difference_covered = 0
            new_spot_array.append(spot_array[i] - difference_covered)
        
        operation_costs_instance.spotprice_array = new_spot_array
        figure_new_spotprice = Visualization().plot_hourly_series(
            new_spot_array,
            'Spotpris',
            ylabel='kr/kWh',
            showlegend=False,
            ymin=0,
            ymax=6,
            linemode=True,
            yticksuffix=None,
            height=250,
            colors=("#1d3c34", "#48a23f", "#FFC358")
        )
        st.plotly_chart(figure_new_spotprice, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': False})

    operation_costs_instance.set_network_tariffs()
    operation_costs_instance.set_network_energy_component()

    if NETTLEIE == 'Variabel':
        cost_array = operation_costs_instance.calculate_operation_costs(array)
    else:
        cost_array = operation_costs_instance.calculate_operation_costs_fast_nettleie(array)

    return cost_array

def calculate_operation_costs(building_instance, SPOT_YEAR, TYPE='Kostnad'):
    SPOT_REGION = 'NO1'
    SPOT_EXTRA = 0.05
    operation_costs_instance = OperationCosts(building_instance)
    operation_costs_instance.set_spotprice_array(year=SPOT_YEAR, region=SPOT_REGION, surcharge=SPOT_EXTRA)
    operation_costs_instance.set_network_tariffs()
    operation_costs_instance.set_network_energy_component()
    operation_costs_instance.get_operation_costs(nettleie=False)

    return operation_costs_instance.building_instance.dict_operation_costs

def display_operation_costs(array, ymax=50):
    visualization_instance = Visualization()
    figure_costs = visualization_instance.plot_hourly_series(
        array,
        'Strøm',
        unit='kr',
        ylabel='Kostnad (kr)',
        yticksuffix=None,
        ymin=0,
        ymax=ymax,
        height=250,
        colors=("#367061", "#8ec9b9"),
        export_name='Grunnvarme'
    )
    st.plotly_chart(figure_costs, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': False})
    c1, c2 = st.columns(2)
    with c1:
        st.metric('Kostnad for strøm (kr)', int(np.sum(array)))

def display_energy_effect(building_instance, cooling_array):
    visualization_instance = Visualization()
    figure_demands = visualization_instance.plot_hourly_series(
        building_instance.dict_energy['dhw_array'],
        'Tappevannsbehov',
        building_instance.dict_energy['spaceheating_array'],
        'Romoppvarmingsbehov',
        building_instance.dict_energy['electric_array'],
        'Elspesifikt behov',
        cooling_array,
        'Kjølebehov',
        height=400,
        ylabel='Effekt (kW)',
        yticksuffix=None,
        colors=("#367061", "#8ec9b9", "#C98E9E", "#8ebcc9")
    )
    st.plotly_chart(figure_demands, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': False})
    st.metric('Totalt (kWh)', int(np.sum(building_instance.dict_energy['dhw_array'] + building_instance.dict_energy['spaceheating_array'] + building_instance.dict_energy['electric_array'])))
    st.metric('Oppvarming (kWh)', int(np.sum(building_instance.dict_energy['dhw_array'] + building_instance.dict_energy['spaceheating_array'])))



if __name__ == "__main__":
    st.title('Demo av beregninger for ulike energiforsyningsløsninger')
    with st.expander('Videreutvikling'):
        st.info('1) Tilpasse energibehov. Til målte data om det finnes | Hvis ikke; bruke areal og bygningsår.')
        st.info('2) Velge dekningsgrader. Forslag (bergvarme = 100%, luft-vann = 85 %, luft-luft = 35%)')
        st.info('3) Velge strømpris. Forslag (spotpris fra 2023 m/ nettleie også en økning som tilsvarer NVE sin 40% økning i strømpris mot 2051(?))')
        st.info('4) Andre betraktninger; hva velger vi av levetid og diskonteringsrente?')

    
    c1, c2 = st.columns(2)
    with c1:
        BUILDING_STANDARD = st.selectbox('Bygningsstandard', ['Lite energieffektivt', 'Middels energieffektivt'])
    with c2:
        BUILDING_TYPE = 'Hus'
        BUILDING_AREA = st.number_input(label = 'Areal (m2)', value=200, step=10)
    with c1:    
        WATERBORNE_COST = 20000 + 815 * BUILDING_AREA
        WATERBORNE_COST = 566 * BUILDING_AREA
        WATERBORNE_HEATING_COST = st.number_input(label='Vannbåren varme (kr)', value=WATERBORNE_COST)
    with c2:
        NETTLEIE_MODUS = st.selectbox('Nettleie', ['Variabel', 'Fast'])
    c1, c2, c3 = st.columns(3)
    with c1:
        ENOVA_STOTTE = st.checkbox(label='Med Enova-støtte?',value=True)
    with c2:
        WITHOUT_WELL = st.checkbox('Fjern investeringskostnad for bergvarme?', value=False)
    with c3:
        WITH_STROMSTOTTE = st.checkbox('Med strømstøtte?', value=False)
    
    c1, c2 = st.columns(2)
    with c1:
        SPOT_YEAR = st.number_input(label='Spotprisår', value=2023)
        DISKONTERINGSRENTE = st.number_input('Diskonteringsrente', value=4.0, step=0.1)
    with c2:
        YEARS = st.number_input('Levetid', value=60, step=1)
        PERCENTAGE_INCREASE = (st.number_input('Prosentvis økning i strømpris per år (%)', value = 0.0, min_value=0.0, max_value=10.0))/100 + 1

    with st.expander('Flat strømpris?'):
        FLAT_EL_PRICE = st.number_input(label='Flat strømpris?', value=0)

    with st.expander('Spotpris'):
        operation_costs_instance_plot = OperationCosts(Building())
        surcharge = 0.05
        operation_costs_instance_plot.set_spotprice_array(year=SPOT_YEAR, region='NO1', surcharge=surcharge)
        operation_costs_instance_plot.set_network_tariffs()
        st.info(f'Påslag spotpris: {surcharge*100} øre/kWh')
        
        figure_spotprice = Visualization().plot_hourly_series(
            operation_costs_instance_plot.spotprice_array,
            'Spotpris',
            ylabel='kr/kWh',
            showlegend=False,
            ymin=0,
            ymax=6,
            linemode=True,
            yticksuffix=None,
            height=250,
            colors=("#1d3c34", "#48a23f", "#FFC358")
        )
        st.plotly_chart(figure_spotprice, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': False})
        st.metric('Gjennomsnittlig spotpris (kr/kWh)', round(operation_costs_instance_plot.spotprice_array.mean(),2))
        st.metric('Gjennomsnittlig strømpris (inkl. nettleie + påslag) (kr/kWh)', round(((operation_costs_instance_plot.spotprice_array + operation_costs_instance_plot.NETTLEIE).mean()),2))


    cooling_array = get_cooling_array()
    cooling_array = cooling_array * BUILDING_AREA
    outdoor_temperature = get_outdoor_temperature()
    if st.button('Start beregning', use_container_width=True):
        
        with st.expander('Energibehov'):
            building_instance = Building()
            building_instance.profet_building_standard = [BUILDING_STANDARD]
            building_instance.profet_building_type = [BUILDING_TYPE]
            building_instance.area = [BUILDING_AREA]
            building_instance.outdoor_temperature_array = outdoor_temperature

            energydemand_instance = EnergyDemand(building_instance)
            energydemand_instance.profet_calculation()
            energydemand_instance.calcluate_flow_temperature()
            display_energy_effect(building_instance=building_instance, cooling_array=cooling_array)

        with st.expander('Bergvarme'):
            building_instance_geoenergy, geoenergy_instance = calculate_geoenergy(
                building_instance=building_instance,
                energydemand_instance=energydemand_instance,
                outdoor_temperature=outdoor_temperature,
                building_standard=BUILDING_STANDARD,
                building_type=BUILDING_TYPE,
                building_area=BUILDING_AREA,
                without_well=WITHOUT_WELL,
                )
            electric_array_geoenergy, thermal_array_geoenergy = display_geoenergy_results(building_instance_geoenergy, geoenergy_instance)
            #geoenergy_operation_costs = calculate_operation_costs(building_instance_geoenergy, SPOT_YEAR)
            #cost_array_geoenergy = geoenergy_operation_costs['geoenergy_consumption_array']
            cost_array_geoenergy = calculate_operation_costs_2(array=electric_array_geoenergy, SPOT_YEAR=SPOT_YEAR, NETTLEIE=NETTLEIE_MODUS, with_stromstotte=WITH_STROMSTOTTE)
            cost_array_geoenergy_STROMSTOTTE = calculate_operation_costs_2(array=electric_array_geoenergy, SPOT_YEAR=SPOT_YEAR, NETTLEIE=NETTLEIE_MODUS, with_stromstotte=True)
            value_array_geoenergy = calculate_operation_costs_2(array=(thermal_array_geoenergy+electric_array_geoenergy), SPOT_YEAR=SPOT_YEAR, NETTLEIE=NETTLEIE_MODUS, with_stromstotte=WITH_STROMSTOTTE)
            #st.metric(label='Beregnet strømpris (kr/kWh)', value=round(np.mean(np.sum(cost_array_geoenergy)/np.sum(electric_array_geoenergy)),2))
            
            if FLAT_EL_PRICE > 0:
                cost_array_geoenergy = electric_array_geoenergy * FLAT_EL_PRICE
            display_operation_costs(cost_array_geoenergy)

        with st.expander('Luft-vann'):
            building_instance_air_water, air_water_instance = calculate_air_water(
                building_instance=building_instance,
                energydemand_instance=energydemand_instance,
                outdoor_temperature=outdoor_temperature,
                building_standard=BUILDING_STANDARD,
                building_type=BUILDING_TYPE,
                building_area=BUILDING_AREA
                )
            electric_array_air_water, thermal_array_air_water = display_air_water_results(building_instance_air_water, air_water_instance)
            #air_water_operation_costs = calculate_operation_costs(building_instance_air_water, SPOT_YEAR)
            #cost_array_air_water = air_water_operation_costs['heatpump_consumption_array']
            cost_array_air_water = calculate_operation_costs_2(array=electric_array_air_water, SPOT_YEAR=SPOT_YEAR, NETTLEIE=NETTLEIE_MODUS, with_stromstotte=WITH_STROMSTOTTE)
            cost_array_air_water_STROMSTOTTE = calculate_operation_costs_2(array=electric_array_air_water, SPOT_YEAR=SPOT_YEAR, NETTLEIE=NETTLEIE_MODUS, with_stromstotte=True)
            value_array_air_water = calculate_operation_costs_2(array=(thermal_array_air_water+electric_array_air_water), SPOT_YEAR=SPOT_YEAR, NETTLEIE=NETTLEIE_MODUS, with_stromstotte=WITH_STROMSTOTTE)
            #st.metric(label='Beregnet strømpris (kr/kWh)', value=round(np.mean(np.sum(cost_array_air_water)/np.sum(electric_array_air_water)),2))
            if FLAT_EL_PRICE > 0:
                cost_array_air_water = electric_array_air_water * FLAT_EL_PRICE
            display_operation_costs(cost_array_air_water)

        with st.expander('Luft-luft'):
            building_instance_air_air, air_air_instance = calculate_air_air(
                building_instance=building_instance,
                energydemand_instance=energydemand_instance,
                outdoor_temperature=outdoor_temperature,
                building_standard=BUILDING_STANDARD,
                building_type=BUILDING_TYPE,
                building_area=BUILDING_AREA
                )
            electric_array_air_air, thermal_array_air_air = display_air_air_results(building_instance_air_air, air_air_instance)
            #air_air_operation_costs = calculate_operation_costs(building_instance_air_air, SPOT_YEAR)
            #cost_array_air_air = air_air_operation_costs['heatpump_consumption_array']
            cost_array_air_air = calculate_operation_costs_2(array=electric_array_air_air, SPOT_YEAR=SPOT_YEAR, NETTLEIE=NETTLEIE_MODUS, with_stromstotte=WITH_STROMSTOTTE)
            cost_array_air_air_STROMSTOTTE = calculate_operation_costs_2(array=electric_array_air_air, SPOT_YEAR=SPOT_YEAR, NETTLEIE=NETTLEIE_MODUS, with_stromstotte=True)
            value_array_air_air = calculate_operation_costs_2(array=(thermal_array_air_air+electric_array_air_air), SPOT_YEAR=SPOT_YEAR, NETTLEIE=NETTLEIE_MODUS, with_stromstotte=WITH_STROMSTOTTE)
            #st.metric(label='Beregnet strømpris (kr/kWh)', value=round(np.mean(np.sum(cost_array_air_air)/np.sum(electric_array_air_air)),2))
            if FLAT_EL_PRICE > 0:
                cost_array_air_air = electric_array_air_air * FLAT_EL_PRICE
            display_operation_costs(cost_array_air_air)

        with st.expander('Direkte elektrisk oppvarming'):
            building_instance_direct = calculate_electric(
                building_instance=building_instance,
                energydemand_instance=energydemand_instance,
                outdoor_temperature=outdoor_temperature,
                building_standard=BUILDING_STANDARD,
                building_type=BUILDING_TYPE,
                building_area=BUILDING_AREA
                )
            electric_direct, thermal_direct = display_electric_results(building_instance_direct)
            #direct_operation_costs = calculate_operation_costs(building_instance_direct, SPOT_YEAR)
            #cost_array_direct = direct_operation_costs['heating_array']
            cost_array_direct = calculate_operation_costs_2(array=electric_direct, SPOT_YEAR=SPOT_YEAR, NETTLEIE=NETTLEIE_MODUS, with_stromstotte=WITH_STROMSTOTTE)
            cost_array_direct_STROMSTOTTE = calculate_operation_costs_2(array=electric_direct, SPOT_YEAR=SPOT_YEAR, NETTLEIE=NETTLEIE_MODUS, with_stromstotte=True)
            value_array_direct = calculate_operation_costs_2(array=(thermal_direct+electric_direct), SPOT_YEAR=SPOT_YEAR, NETTLEIE=NETTLEIE_MODUS, with_stromstotte=WITH_STROMSTOTTE)
            #st.metric(label='Beregnet strømpris (kr/kWh)', value=round(np.mean(np.sum(cost_array_direct)/np.sum(electric_direct)),2))
            if FLAT_EL_PRICE > 0:
                cost_array_direct = electric_direct * FLAT_EL_PRICE
            display_operation_costs(cost_array_direct)

        with st.expander('Økonomi', expanded=True):
            COVERED_BY_ENOVA = 0
            if (ENOVA_STOTTE == True) and (WATERBORNE_HEATING_COST > 0):
                COVERED_BY_ENOVA = 40000
            elif (ENOVA_STOTTE == True) and (WATERBORNE_HEATING_COST == 0):
                COVERED_BY_ENOVA = 15000
            elif (ENOVA_STOTTE == False):
                COVERED_BY_ENOVA = 0

            result_map = {
                'Investering bergvarme-VP' : int(geoenergy_instance.investment_cost_heat_pump),
                'Investering luft-vann-VP' : int((geoenergy_instance.investment_cost_heat_pump + geoenergy_instance.investment_cost_borehole) * 0.76),
                'Investering luft-luft-VP' : int(30000),
                'Investering direkte elektrisk' : int(150*BUILDING_AREA),
                'Investering bergvarme brønner' : int(geoenergy_instance.investment_cost_borehole),
                'Strøm direkte elektrisk' : int(electric_direct.sum()),
                'Strøm luft-vann-varmepumpe' : int(electric_array_air_water.sum()),
                'Strøm luft-luft-varmepumpe' : int(electric_array_air_air.sum()),
                'Strøm grunnvarme' : int(electric_array_geoenergy.sum()),
                'Kostnad direkte elektrisk' : int(cost_array_direct.sum()),
                'Kostnad luft-vann-varmepumpe' : int(cost_array_air_water.sum()),
                'Kostnad luft-luft-varmepumpe' : int(cost_array_air_air.sum()),
                'Kostnad grunnvarme' : int(cost_array_geoenergy.sum()),
                'Kostnad direkte elektrisk (strømstøtte)' : int(cost_array_direct_STROMSTOTTE.sum()),
                'Kostnad luft-vann-varmepumpe (strømstøtte)' : int(cost_array_air_water_STROMSTOTTE.sum()),
                'Kostnad luft-luft-varmepumpe (strømstøtte)' : int(cost_array_air_air_STROMSTOTTE.sum()),
                'Kostnad grunnvarme (strømstøtte)' : int(cost_array_geoenergy_STROMSTOTTE.sum()),
                'Verdi direkte elektrisk' : int(value_array_direct.sum()),
                'Verdi luft-vann-varmepumpe' : int(value_array_air_water.sum()),
                'Verdi luft-luft-varmepumpe' : int(value_array_geoenergy.sum()), # NBNB
                'Verdi grunnvarme' : int(value_array_geoenergy.sum()),
                'Vannbåren varme' : int(WATERBORNE_HEATING_COST)
            }
            #st.write(result_map)
            df_final, air_water_stotte = economic_calculation(result_map=result_map, DISKONTERINGSRENTE=DISKONTERINGSRENTE, YEARS=YEARS, PERCENTAGE_INCREASE=PERCENTAGE_INCREASE, COVERED_BY_ENOVA = COVERED_BY_ENOVA)
            st.dataframe(df_final, use_container_width=200)
            economic_comparison(df_final)
            
            df_to_excel = pd.DataFrame({
                'Oppvarmingsbehov' : [int(df_final['Produsert energi'][2])],
                'Strømforbruk, bergvarme (kWh/år)' : [result_map['Strøm grunnvarme']],
                'Strømforbuk, luft-vann (kWh/år)' : [result_map['Strøm luft-vann-varmepumpe']],
                'Strømforbruk, luft-luft (kWh/år)' : [result_map['Strøm luft-luft-varmepumpe']],
                'Strømforbruk, direkte elektrisk (kWh/år)' : [result_map['Strøm direkte elektrisk']],
                'Driftskostnad, bergvarme (kr/år)' : [int(result_map['Kostnad grunnvarme'])],
                'Driftskostnad, luft-vann (kr/år)' : [int(result_map['Kostnad luft-vann-varmepumpe'])],
                'Driftskostnad, luft-luft (kr/år)' : [int(result_map['Kostnad luft-luft-varmepumpe'])],
                'Driftskostnad, direkte elektrisk (kr/år)' : [int(result_map['Kostnad direkte elektrisk'])],
                'Investeringskostnad, bergvarme (kr)' : [int(df_final['Investering grunnvarme'][0]-WATERBORNE_HEATING_COST-COVERED_BY_ENOVA)],
                'Investeringskostnad, luft-vann (kr)' : [int(df_final['Investering luft-vann-VP'][0]-WATERBORNE_HEATING_COST-air_water_stotte)],
                'Investeringskostnad, luft-luft (kr)' : [int(df_final['Investering luft-luft-VP'][0])],
                'Investeringskostnad, direkte elektrisk (kr)' : [int(df_final['Investering direkte elektrisk'][0])],
                'Investeringskostnad, vannbåren varme (kr)' : [int(WATERBORNE_HEATING_COST)],
                'Nåverdi, bergvarme (kr)' : [int(df_final['Nåverdi grunnvarme'][0])],
                'Nåverdi, luft-vann (kr)' : [int(df_final['Nåverdi luft-vann'][0])],
                'Nåverdi, luft-luft (kr)' : [int(df_final['Nåverdi luft-luft'][0])],
                'Nåverdi, direkte elektrisk (kr)' : [int(df_final['Nåverdi direkte elektrisk'][0])],
                
            })
            df_to_excel = df_to_excel.astype(int)
            st.dataframe(df_to_excel, use_container_width=200)


    # 10000 for væske vann
    # 10000 for vannbåren varme
    # 5000 for akkumulatortank
    # 15000 for alt 