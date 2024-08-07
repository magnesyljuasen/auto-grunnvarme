import streamlit as st
import pandas as pd
import numpy as np
from src.scripts.scripts import Building, EnergyDemand, GeoEnergy, SolarPanels, HeatPump, DistrictHeating, OperationCosts, GreenEnergyFund, Visualization

st.set_page_config(layout='wide')

def get_cooling_array():
    cooling_array = pd.read_excel('src/testdata/cooling_sheet.xlsx')['Hus_Oslo'].to_numpy()
    return cooling_array

def get_outdoor_temperature(station = 'Blindern'):
    outdoor_temperature = pd.read_excel('src/testdata/Beregninger - Sjøsiden Hovde.xlsx', sheet_name='Utetemperatur')[station]
    return list(outdoor_temperature)

def calculate_air_water(outdoor_temperature, building_standard, building_type, building_area):
    SPACEHEATING_COP = 3.5
    SPACEHEATING_COVERAGE = 100
    DHW_COP = 2.5
    DHW_COVERAGE = 100
    
    POWER_REDUCTION = 20
    COP_REDUCTION = 20
    COVERAGE = 100

    building_instance = Building()
    building_instance.profet_building_standard = [building_standard]
    building_instance.profet_building_type = [building_type]
    building_instance.area = [building_area]
    building_instance.outdoor_temperature_array = outdoor_temperature

    energydemand_instance = EnergyDemand(building_instance)
    energydemand_instance.profet_calculation()
    energydemand_instance.calcluate_flow_temperature()

    heatpump_instance = HeatPump(building_instance)
    heatpump_instance.set_base_parameters(spaceheating_cop=SPACEHEATING_COP, spaceheating_coverage=SPACEHEATING_COVERAGE, dhw_cop=DHW_COP, dhw_coverage=DHW_COVERAGE)
    heatpump_instance.set_demand(spaceheating_demand=building_instance.dict_energy['spaceheating_array'], dhw_demand=building_instance.dict_energy['dhw_array'])
    heatpump_instance.set_simulation_parameters()
    heatpump_instance.nspek_heatpump_calculation(P_NOMINAL=np.max(heatpump_instance.spaceheating_demand), power_reduction=POWER_REDUCTION, cop_reduction=COP_REDUCTION, coverage=COVERAGE)

    return building_instance, heatpump_instance

def calculate_geoenergy(outdoor_temperature, building_standard, building_type, building_area):
    SPACEHEATING_COP = 3.5
    SPACEHEATING_COVERAGE = 100
    DHW_COP = 2.5
    DHW_COVERAGE = 100

    building_instance = Building()
    building_instance.profet_building_standard = [building_standard]
    building_instance.profet_building_type = [building_type]
    building_instance.area = [building_area]
    building_instance.outdoor_temperature_array = outdoor_temperature
    
    energydemand_instance = EnergyDemand(building_instance)
    energydemand_instance.profet_calculation()
    energydemand_instance.calcluate_flow_temperature()
    
    geoenergy_instance = GeoEnergy(building_instance)
    geoenergy_instance.set_base_parameters(spaceheating_cop=SPACEHEATING_COP, spaceheating_coverage=SPACEHEATING_COVERAGE, dhw_cop=DHW_COP, dhw_coverage=DHW_COVERAGE)
    geoenergy_instance.set_demand(spaceheating_demand=building_instance.dict_energy['spaceheating_array'], dhw_demand=building_instance.dict_energy['dhw_array'])
    geoenergy_instance.simple_coverage_cop_calculation()
    geoenergy_instance.calculate_heat_pump_size()
    geoenergy_instance.set_simulation_parameters()
    geoenergy_instance.advanced_sizing_of_boreholes(variable_cop_sizing=True)
    geoenergy_instance.calculate_investment_costs()

    return building_instance, geoenergy_instance

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

    figure_cop_geoenergy = visualization_instance.plot_hourly_series(
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
        st.plotly_chart(figure_cop_geoenergy, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': False})
  
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

if __name__ == "__main__":
    BUILDING_STANDARD = 'Lite energieffektivt'
    BUILDING_TYPE = 'Hus'
    BUILDING_AREA = 150

    cooling_array = get_cooling_array()
    outdoor_temperature = get_outdoor_temperature()
    
    with st.expander('Bergvarme'):
        building_instance_geoenergy, geoenergy_instance = calculate_geoenergy(
            outdoor_temperature=outdoor_temperature,
            building_standard=BUILDING_STANDARD,
            building_type=BUILDING_TYPE,
            building_area=BUILDING_AREA
            )
        electric_array_geoenergy, thermal_array_geoenergy = display_geoenergy_results(building_instance_geoenergy, geoenergy_instance)

    with st.expander('Luft-vann'):
        building_instance_air_water, air_water_instance = calculate_air_water(
            outdoor_temperature=outdoor_temperature,
            building_standard=BUILDING_STANDARD,
            building_type=BUILDING_TYPE,
            building_area=BUILDING_AREA
            )
        electric_array_air_water, thermal_array_air_water = display_air_water_results(building_instance_air_water, air_water_instance)