import streamlit as st
import pandas as pd
import numpy as np
from src.scripts.scripts import Building, EnergyDemand, GeoEnergy, SolarPanels, HeatPump, DistrictHeating, OperationCosts, GreenEnergyFund, Visualization

st.set_page_config(layout='wide')

def economic_comparison(df):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.write('Bergvarme')
        st.metric(label='LCOE', value=df['LCOE grunnvarme'][0])
        st.metric(label='Totalkostnad', value=df['Totalkostnad grunnvarme'][0])
    with c2:
        st.write('Luft-vann')
        st.metric(label='LCOE', value=df['LCOE luft-vann'][0])
        st.metric(label='Totalkostnad', value=df['Totalkostnad luft-vann'][0])
    with c3:
        st.write('Luft-luft')
        st.metric(label='LCOE', value=df['LCOE luft-luft'][0])
        st.metric(label='Totalkostnad', value=df['Totalkostnad luft-luft'][0])
    with c4:
        st.write('Direkte elektrisk')
        st.metric(label='LCOE', value=df['LCOE_direkte_el'][0])
        st.metric(label='Totalkostnad', value=df['Totalkostnad direkte elektrisk'][0])

    compared_data = {
        "luft-vann": df['Totalkostnad luft-vann'][0] - df['Totalkostnad grunnvarme'][0],
        "luft-luft": df['Totalkostnad luft-luft'][0] - df['Totalkostnad grunnvarme'][0],
        "direkte elektrisk": df['Totalkostnad direkte elektrisk'][0] - df['Totalkostnad grunnvarme'][0],
    }

    min_string = min(compared_data, key=compared_data.get)
    min_number = compared_data[min_string]
    st.info(f"Bergvarme vs. {min_string}. **Mulig erstatning: {min_number} kr.**")
        

def economic_calculation(result_map, PERCENTAGE_INCREASE=1.00, DISKONTERINGSRENTE=4, YEARS=40):
    produced_energy_list = np.zeros(YEARS)
    investment_geoenergy_list = np.zeros(YEARS)
    investment_air_water_list = np.zeros(YEARS)
    investment_air_air_list = np.zeros(YEARS)

    energy_cost_geoenergy_list = np.zeros(YEARS)
    energy_cost_air_water_list = np.zeros(YEARS)
    energy_cost_air_air_list = np.zeros(YEARS)

    cost_direct_el_list = np.zeros(YEARS) 
    cost_geoenergy_list = np.zeros(YEARS)
    cost_air_water_list = np.zeros(YEARS)
    cost_air_air_list = np.zeros(YEARS)

    diskonteringsrente_list = np.zeros(YEARS)
    year_list = np.zeros(YEARS)
    for i in range(0, YEARS):
        year_list[i] = i
        if i != 0:
            produced_energy_list[i] = result_map['Strøm direkte elektrisk']
            energy_cost_geoenergy_list[i] = result_map['Kostnad grunnvarme'] * PERCENTAGE_INCREASE**i
            energy_cost_air_water_list[i] = result_map[f'Kostnad luft-vann-varmepumpe'] * PERCENTAGE_INCREASE**i
            energy_cost_air_air_list[i] = result_map[f'Kostnad luft-luft-varmepumpe'] * PERCENTAGE_INCREASE**i
            cost_direct_el_list[i] = result_map['Kostnad direkte elektrisk'] * PERCENTAGE_INCREASE**i

        if i == 0:
            investment_geoenergy_list[i] = result_map['Investering bergvarme-VP'] + result_map['Investering bergvarme brønner'] + result_map['Vannbåren varme']
            investment_air_water_list[i] = result_map[f'Investering luft-vann-VP'] + result_map['Vannbåren varme']
            investment_air_air_list[i] = result_map[f'Investering luft-luft-VP']

        if i == 15 or i == 30 or i == 45 or i == 60:
            investment_air_water_list[i] = result_map[f'Investering luft-vann-VP']

        if i == 10 or i == 20 or i == 30 or i == 40 or i == 50 or i == 60:
            investment_air_air_list[i] = result_map[f'Investering luft-luft-VP']

        if i == 20 or i == 40 or i == 60:
            investment_geoenergy_list[i] = result_map['Investering bergvarme-VP']

        cost_geoenergy_list = investment_geoenergy_list + energy_cost_geoenergy_list
        cost_air_water_list = investment_air_water_list + energy_cost_air_water_list
        cost_air_air_list = investment_air_air_list + energy_cost_air_air_list
        
        if i >= 1:
            diskonteringsrente = 1 / (1 + (DISKONTERINGSRENTE/100))**i
        else:
            diskonteringsrente = 1
        diskonteringsrente_list[i] = diskonteringsrente

    cost_geoenergy_diskontert_list = cost_geoenergy_list * diskonteringsrente_list
    cost_air_water_diskontert_list = cost_air_water_list * diskonteringsrente_list    
    cost_air_air_diskontert_list = cost_air_air_list * diskonteringsrente_list
    cost_direct_el_diskontert_list = cost_direct_el_list * diskonteringsrente_list
    produced_energy_diskontert_list = produced_energy_list * diskonteringsrente_list

    geoenergy_LCOE = round((cost_geoenergy_diskontert_list.sum()/produced_energy_diskontert_list.sum()),2)
    air_water_LCOE = round((cost_air_water_diskontert_list.sum()/produced_energy_diskontert_list.sum()),2)
    air_air_LCOE = round((cost_air_air_diskontert_list.sum()/produced_energy_diskontert_list.sum()),2)
    direct_el_LCOE = round((cost_direct_el_diskontert_list.sum()/produced_energy_diskontert_list.sum()),2)
    
    geoenergy_total_cost = int(cost_geoenergy_diskontert_list.sum())
    air_water_total_cost = int(cost_air_water_diskontert_list.sum())
    air_air_total_cost = int(cost_air_air_diskontert_list.sum())
    direct_el_total_cost = int(cost_direct_el_diskontert_list.sum())

    df = pd.DataFrame({
        'År' : year_list,
        'Produsert energi' : produced_energy_list,
        'Investering grunnvarme' : investment_geoenergy_list,
        'Investering luft-vann-VP' : investment_air_water_list,
        'Investering luft-luft-VP' : investment_air_air_list,
        'Diskonteringsrente' : diskonteringsrente_list,
        'Energikostnad grunnvarme' : energy_cost_geoenergy_list,
        'Energikostnad luft-vann-VP' : energy_cost_air_water_list,
        'Energikostnad luft-luft-VP' : energy_cost_air_air_list,
        'Energikostnad direkte elektrisk' : cost_direct_el_list,
        'Kostnad grunnvarme' : cost_geoenergy_list,
        'Kostnad luft-vann-VP' : cost_air_water_list,
        'Kostnad luft-luft-VP' : cost_air_air_list,
        'Kostnad direkte elektrisk' : cost_direct_el_diskontert_list,
        'Kostnad grunnvarme (diskontert)' : cost_geoenergy_diskontert_list,
        'Kostnad luft-vann-VP (diskontert)' : cost_air_water_diskontert_list,
        'Kostnad luft-luft-VP (diskontert)' : cost_air_air_diskontert_list,
        'Kostnad direkte elektrisk (diskontert)' : cost_direct_el_diskontert_list,
        'LCOE grunnvarme' : geoenergy_LCOE,
        'LCOE luft-vann' : air_water_LCOE,
        'LCOE luft-luft' : air_air_LCOE,
        'LCOE_direkte_el' : direct_el_LCOE,
        'Totalkostnad grunnvarme' : geoenergy_total_cost,
        'Totalkostnad luft-vann' : air_water_total_cost,
        'Totalkostnad luft-luft' : air_air_total_cost,
        'Totalkostnad direkte elektrisk' : direct_el_total_cost
    })
    df = df.set_index('År')
    return df

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
    P_NOMINAL_REDUCED = st.number_input('Reduser varmepumpestørrelse', value=0.23, step=0.1, key='luft-luft')

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

def calculate_geoenergy(building_instance, energydemand_instance, outdoor_temperature, building_standard, building_type, building_area):
    SPACEHEATING_COP = 3.5
    SPACEHEATING_COVERAGE = 100
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

    return building_instance, geoenergy_instance

def display_air_air_results(building_instance, air_air_instance):
    with st.popover('Data', use_container_width=True):
        st.write(vars(air_air_instance))

    c1, c2 = st.columns(2)
    with c1:
        st.metric('Varmepumpestørrelse (kW)', np.max(air_air_instance.heatpump_array))
    with c2:
        st.metric('SCOP', round((np.sum(air_air_instance.heatpump_array)/np.sum(air_air_instance.compressor_array)),2))
    with c1:
        st.metric('Energidekningsgrad (%)', round((np.sum(air_air_instance.heatpump_array)/np.sum(building_instance.dict_energy['dhw_array'] + building_instance.dict_energy['spaceheating_array']))*100))

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
  
    electric_array = air_water_instance.compressor_array + air_water_instance.peak_array
    thermal_array = air_water_instance.from_air_array
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
        st.metric('Varmepumpestørrelse (kW)', np.max(air_water_instance.heatpump_array))
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

def calculate_operation_costs(building_instance, SPOT_YEAR):
    SPOT_REGION = 'NO1'
    SPOT_EXTRA = 0.0

    operation_costs_instance = OperationCosts(building_instance)
    operation_costs_instance.set_spotprice_array(year=SPOT_YEAR, region=SPOT_REGION, surcharge=SPOT_EXTRA)
    operation_costs_instance.set_network_tariffs()
    operation_costs_instance.set_network_energy_component()
    operation_costs_instance.get_operation_costs()

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

def display_energy_effect(building_instance):
    visualization_instance = Visualization()
    figure_demands = visualization_instance.plot_hourly_series(
        building_instance.dict_energy['dhw_array'],
        'Tappevannsbehov',
        building_instance.dict_energy['spaceheating_array'],
        'Romoppvarmingsbehov',
        building_instance.dict_energy['electric_array'],
        'Elspesifikt behov',
        height=400,
        ylabel='Effekt (kW)',
        yticksuffix=None,
        colors=("#367061", "#8ec9b9", "#C98E9E")
    )
    st.plotly_chart(figure_demands, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': False})
    st.metric('Totalt (kWh)', int(np.sum(building_instance.dict_energy['dhw_array'] + building_instance.dict_energy['spaceheating_array'] + building_instance.dict_energy['electric_array'])))
    st.metric('Oppvarming (kWh)', int(np.sum(building_instance.dict_energy['dhw_array'] + building_instance.dict_energy['spaceheating_array'])))



if __name__ == "__main__":
    BUILDING_STANDARD = 'Lite energieffektivt'
    BUILDING_TYPE = 'Hus'
    BUILDING_AREA = st.number_input(label = 'Areal', value=291, step=10)
    WATERBORNE_HEATING_COST = st.number_input(label='Vannbåren varme (kr)', value=20000 + 815 * BUILDING_AREA)
    c1, c2 = st.columns(2)
    with c1:
        SPOT_YEAR = st.number_input(label='Spotprisår', value=2023)
        FLAT_EL_PRICE = st.number_input(label='Flat strømpris?', value=0)
    with c2:
        DISKONTERINGSRENTE = st.number_input('Diskonteringsrente', value=4.0, step=0.1)
        YEARS = st.number_input('Levetid', value=40, step=1)
        PERCENTAGE_INCREASE = (st.number_input('Prosentvis økning i strømpris (%)', value = 2, min_value=0, max_value=10))/100 + 1

    with st.expander('Spotpris'):
        operation_costs_instance_plot = OperationCosts(Building())
        operation_costs_instance_plot.set_spotprice_array(year=SPOT_YEAR, region='NO1', surcharge=0)

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



    cooling_array = get_cooling_array()
    outdoor_temperature = get_outdoor_temperature()
    
    with st.expander('Energibehov'):
        building_instance = Building()
        building_instance.profet_building_standard = [BUILDING_STANDARD]
        building_instance.profet_building_type = [BUILDING_TYPE]
        building_instance.area = [BUILDING_AREA]
        building_instance.outdoor_temperature_array = outdoor_temperature

        energydemand_instance = EnergyDemand(building_instance)
        energydemand_instance.profet_calculation()
        energydemand_instance.calcluate_flow_temperature()
        display_energy_effect(building_instance=building_instance)

    with st.expander('Bergvarme'):
        building_instance_geoenergy, geoenergy_instance = calculate_geoenergy(
            building_instance=building_instance,
            energydemand_instance=energydemand_instance,
            outdoor_temperature=outdoor_temperature,
            building_standard=BUILDING_STANDARD,
            building_type=BUILDING_TYPE,
            building_area=BUILDING_AREA
            )
        electric_array_geoenergy, thermal_array_geoenergy = display_geoenergy_results(building_instance_geoenergy, geoenergy_instance)
        air_water_operation_costs = calculate_operation_costs(building_instance_geoenergy, SPOT_YEAR)
        cost_array_geoenergy = air_water_operation_costs['geoenergy_consumption_array']
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
        air_water_operation_costs = calculate_operation_costs(building_instance_air_water, SPOT_YEAR)
        cost_array_air_water = air_water_operation_costs['heatpump_consumption_array']
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
        air_air_operation_costs = calculate_operation_costs(building_instance_air_air, SPOT_YEAR)
        cost_array_air_air = air_air_operation_costs['heatpump_consumption_array']
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
        direct_operation_costs = calculate_operation_costs(building_instance_direct, SPOT_YEAR)
        cost_array_direct = direct_operation_costs['heating_array']
        if FLAT_EL_PRICE > 0:
            cost_array_direct = electric_direct * FLAT_EL_PRICE
        display_operation_costs(cost_array_direct)

    with st.expander('Økonomi', expanded=True):
        result_map = {
            'Investering bergvarme-VP' : geoenergy_instance.investment_cost_heat_pump,
            'Investering luft-vann-VP' : (geoenergy_instance.investment_cost_heat_pump + geoenergy_instance.investment_cost_borehole) * 0.76,
            'Investering luft-luft-VP' : 30000,
            'Investering bergvarme brønner' : geoenergy_instance.investment_cost_borehole,
            'Strøm direkte elektrisk' : electric_direct.sum(),
            'Strøm luft-vann-varmepumpe' : electric_array_air_water.sum(),
            'Strøm luft-luft-varmepumpe' : electric_array_air_air.sum(),
            'Strøm grunnvarme' : electric_array_geoenergy.sum(),
            'Kostnad direkte elektrisk' : cost_array_direct.sum(),
            'Kostnad luft-vann-varmepumpe' : cost_array_air_water.sum(),
            'Kostnad luft-luft-varmepumpe' : cost_array_air_air.sum(),
            'Kostnad grunnvarme' : cost_array_geoenergy.sum(),
            'Vannbåren varme' : WATERBORNE_HEATING_COST
        }
        df_final = economic_calculation(result_map=result_map, DISKONTERINGSRENTE=DISKONTERINGSRENTE, YEARS=YEARS, PERCENTAGE_INCREASE=PERCENTAGE_INCREASE)
        st.write(df_final)
        economic_comparison(df_final)

