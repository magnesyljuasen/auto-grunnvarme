import streamlit as st
import numpy as np
import pandas as pd
from src.scripts import Building, EnergyDemand, GeoEnergy, SolarPanels, HeatPump, DistrictHeating, OperationCosts, GreenEnergyFund, Visualization

def energy_demand_tests():
    # instansiering av klassene
    st.write("---")
    building_instance = Building()
    energydemand_instance = EnergyDemand(building_instance)
    geoenergy_instance = GeoEnergy(building_instance)
    solar_instance = SolarPanels(building_instance)
    heatpump_instance = HeatPump(building_instance)
    districtheating_instance = DistrictHeating(building_instance)
    st.write(building_instance, energydemand_instance, geoenergy_instance, solar_instance, heatpump_instance, districtheating_instance)

    # sette nye parametere til Building
    st.write("---")
    building_instance = Building()
    energydemand_instance = EnergyDemand(building_instance)
    energydemand_instance.set_spaceheating_array(array=[1,2,3,4,5])
    energydemand_instance.set_dhw_array(array=np.zeros(8760))
    energydemand_instance.set_electric_array(array=[10,9,95,4,3,2])
    st.write(building_instance.dict_energy['spaceheating_array'])
    st.write(building_instance.dict_energy['dhw_array'])
    st.write(building_instance.dict_energy['electric_array'])

    # bruk PROFet til å sette energibehov med default temperatur på kombinasjonsbygg
    st.write("---")
    building_instance = Building()
    building_instance.profet_building_standard = ["Lite energieffektivt", "Veldig energieffektivt"]
    building_instance.profet_building_type = ["Leilighet", "Hus"]
    building_instance.area = [5000, 3000]
    energydemand_instance = EnergyDemand(building_instance)
    energydemand_instance.profet_calculation()
    st.write(building_instance.dict_energy['spaceheating_array'])
    st.write(building_instance.dict_energy['dhw_array'])
    st.write(building_instance.dict_energy['electric_array'])

    # bruk PROFet til å sette energibehov med egen temperatur på kombinasjonsbygg
    st.write("---")
    building_instance = Building()
    building_instance.profet_building_standard = ["Lite energieffektivt", "Veldig energieffektivt"]
    building_instance.profet_building_type = ["Leilighet", "Hus"]
    building_instance.area = [5000, 3000]
    df = pd.read_csv('src/testdata/temperatures_dummy.csv', sep=',', index_col=0)
    temperature_array = df['2021-2022'].to_list()
    building_instance.outdoor_temperature_array = temperature_array
    energydemand_instance = EnergyDemand(building_instance)
    energydemand_instance.profet_calculation()
    st.write(building_instance.dict_energy['spaceheating_array'])
    st.write(building_instance.dict_energy['dhw_array'])
    st.write(building_instance.dict_energy['electric_array'])

    # hent inn energibehov fra fil
    st.write("---")
    df = pd.read_csv('src/testdata/energy_demand_dummy.csv', sep=',', index_col=0)
    space_heating_array = df['SpaceHeating'].to_list()
    dhw_array = df['DHW'].to_list()
    electric_array = df['Electric'].to_list()
    building_instance = Building()
    energydemand_instance = EnergyDemand(building_instance)
    energydemand_instance.set_spaceheating_array(array = space_heating_array)
    energydemand_instance.set_dhw_array(array = dhw_array)
    energydemand_instance.set_electric_array(array = electric_array)
    st.write(building_instance.dict_energy['spaceheating_array'])
    st.write(building_instance.dict_energy['dhw_array'])
    st.write(building_instance.dict_energy['electric_array'])

def geoenergy_tests():
    # energibehov fra fil -> grunnvarme dekker romoppvarming og tappevann
    st.write("---")
    df = pd.read_csv('src/testdata/energy_demand_dummy.csv', sep=',', index_col=0)
    spaceheating_array = df['SpaceHeating'].to_list()
    dhw_array = df['DHW'].to_list()
    building_instance = Building()
    energydemand_instance = EnergyDemand(building_instance)
    energydemand_instance.set_spaceheating_array(array = spaceheating_array)
    energydemand_instance.set_dhw_array(array = dhw_array)
    geoenergy_instance = GeoEnergy(building_instance)
    geoenergy_instance.set_base_parameters(spaceheating_cop=3.5, spaceheating_coverage=90, dhw_cop=2, dhw_coverage=80)
    geoenergy_instance.set_demand(spaceheating_demand=building_instance.dict_energy['spaceheating_array'], dhw_demand=building_instance.dict_energy['dhw_array'])
    geoenergy_instance.simple_coverage_cop_calculation()
    st.write(np.sum(building_instance.dict_energy['spaceheating_array'] + building_instance.dict_energy['dhw_array']))
    st.write(np.sum(building_instance.dict_energy['geoenergy_production_array']))
    st.write(np.sum(building_instance.dict_energy['geoenergy_consumption_array']))

    # energibehov fra fil -> grunnvarme dekker kun romoppvarming
    st.write("---")
    df = pd.read_csv('src/testdata/energy_demand_dummy.csv', sep=',', index_col=0)
    spaceheating_array = df['SpaceHeating'].to_list()
    dhw_array = df['DHW'].to_list()
    building_instance = Building()
    energydemand_instance = EnergyDemand(building_instance)
    energydemand_instance.set_spaceheating_array(array = spaceheating_array)
    energydemand_instance.set_dhw_array(array = dhw_array)
    geoenergy_instance = GeoEnergy(building_instance)
    geoenergy_instance.set_base_parameters(spaceheating_cop=3.5, spaceheating_coverage=90, dhw_cop=2, dhw_coverage=0)
    geoenergy_instance.set_demand(spaceheating_demand=building_instance.dict_energy['spaceheating_array'], dhw_demand=building_instance.dict_energy['dhw_array'])
    geoenergy_instance.simple_coverage_cop_calculation()
    st.write(np.sum(building_instance.dict_energy['spaceheating_array'] + building_instance.dict_energy['dhw_array']))
    st.write(np.sum(building_instance.dict_energy['geoenergy_production_array']))
    st.write(np.sum(building_instance.dict_energy['geoenergy_consumption_array']))

    # energibehov fra fil + solceller -> grunnvarme dekker romoppvarming + tappevann og solcelleproduksjon, få ut varmepumpestørrelse
    st.write("---")
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
    st.line_chart(geoenergy_instance.heatpump_array)


def operation_costs_tests():
    # energibehov fra fil + solceller + grunnvarmeberegning -> få ut spotpris array
    st.write("---")
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
    operation_costs_instance = OperationCosts(building_instance)
    operation_costs_instance.set_spotprice_array(year=2021, region='NO1')
    st.line_chart(operation_costs_instance.spotprice_array)

    # energibehov fra fil + solceller + grunnvarmeberegning -> få ut spotpris array med påslag
    st.write("---")
    df = pd.read_csv('src/testdata/solar_dummy.csv', sep=';')
    solar_array = df['Småhus'] * 100
    df = pd.read_csv('src/testdata/energy_demand_dummy.csv', sep=',', index_col=0)
    spaceheating_array = df['SpaceHeating'].to_list()
    dhw_array = df['DHW'].to_list()
    electric_array = df['Electric'].to_list()
    building_instance = Building()
    energydemand_instance = EnergyDemand(building_instance)
    energydemand_instance.set_spaceheating_array(array = spaceheating_array)
    energydemand_instance.set_dhw_array(array = dhw_array)
    energydemand_instance.set_electric_array(array = electric_array)
    geoenergy_instance = GeoEnergy(building_instance)
    geoenergy_instance.set_base_parameters(spaceheating_cop=2.5, spaceheating_coverage=50, dhw_cop=2.5, dhw_coverage=70)
    geoenergy_instance.set_demand(spaceheating_demand=building_instance.dict_energy['spaceheating_array'], dhw_demand=building_instance.dict_energy['dhw_array'])
    geoenergy_instance.simple_coverage_cop_calculation()
    geoenergy_instance.calculate_heat_pump_size()
    geoenergy_instance.simple_sizing_of_boreholes()
    solar_instance = SolarPanels(building_instance)
    solar_instance.set_solar_array(array = solar_array)
    operation_costs_instance = OperationCosts(building_instance)
    operation_costs_instance.set_spotprice_array(year=2021, region='NO1', surcharge=2)
    st.line_chart(operation_costs_instance.spotprice_array)
    st.write(vars(building_instance))

    # energibehov fra fil + solceller + grunnvarmeberegning med investering -> få ut df_operation_costs på building med spotpris, nettleie 
    st.write("---")
    df = pd.read_csv('src/testdata/solar_dummy.csv', sep=';')
    solar_array = df['Småhus'] * 100
    df = pd.read_csv('src/testdata/energy_demand_dummy.csv', sep=',', index_col=0)
    spaceheating_array = df['SpaceHeating'].to_list()
    dhw_array = df['DHW'].to_list()
    electric_array = df['Electric'].to_list()
    building_instance = Building()
    energydemand_instance = EnergyDemand(building_instance)
    energydemand_instance.set_spaceheating_array(array = spaceheating_array)
    energydemand_instance.set_dhw_array(array = dhw_array)
    energydemand_instance.set_electric_array(array = electric_array)
    geoenergy_instance = GeoEnergy(building_instance)
    geoenergy_instance.set_base_parameters(spaceheating_cop=3.5, spaceheating_coverage=90, dhw_cop=2.5, dhw_coverage=70)
    geoenergy_instance.set_demand(spaceheating_demand=building_instance.dict_energy['spaceheating_array'], dhw_demand=building_instance.dict_energy['dhw_array'])
    geoenergy_instance.simple_coverage_cop_calculation()
    geoenergy_instance.calculate_heat_pump_size()
    geoenergy_instance.simple_sizing_of_boreholes()
    geoenergy_instance.calculate_investment_costs()
    solar_instance = SolarPanels(building_instance)
    solar_instance.set_solar_array(array = solar_array)
    operation_costs_instance = OperationCosts(building_instance)
    operation_costs_instance.set_spotprice_array(year=2021, region='NO3', surcharge=0)
    operation_costs_instance.set_network_tariffs()
    operation_costs_instance.set_network_energy_component()
    operation_costs_instance.get_operation_costs()
    st.line_chart(operation_costs_instance.network_energy_array)
    st.line_chart(building_instance.dict_operation_costs['spaceheating_array'])
    st.write(round(np.sum(building_instance.dict_operation_costs['spaceheating_array']))/round(np.sum(building_instance.dict_energy['spaceheating_array'])))
    st.line_chart(building_instance.dict_operation_costs['geoenergy_consumption_compressor_array'])
    st.write(round(np.sum(building_instance.dict_operation_costs['geoenergy_consumption_compressor_array']))/round(np.sum(building_instance.dict_energy['geoenergy_consumption_compressor_array'])))
    st.write(vars(building_instance))

def green_energy_fund_tests():
    # green_energy_fund_test
    st.write("---")
    df = pd.read_csv('src/testdata/solar_dummy.csv', sep=';')
    solar_array = df['Småhus'] * 100
    df = pd.read_csv('src/testdata/energy_demand_dummy.csv', sep=',', index_col=0)
    spaceheating_array = df['SpaceHeating'].to_list()
    dhw_array = df['DHW'].to_list()
    electric_array = df['Electric'].to_list()
    building_instance = Building()
    energydemand_instance = EnergyDemand(building_instance)
    energydemand_instance.set_spaceheating_array(array = spaceheating_array)
    energydemand_instance.set_dhw_array(array = dhw_array)
    energydemand_instance.set_electric_array(array = electric_array)
    geoenergy_instance = GeoEnergy(building_instance)
    geoenergy_instance.set_base_parameters(spaceheating_cop=3.5, spaceheating_coverage=90, dhw_cop=2.5, dhw_coverage=70)
    geoenergy_instance.set_demand(spaceheating_demand=building_instance.dict_energy['spaceheating_array'], dhw_demand=building_instance.dict_energy['dhw_array'])
    geoenergy_instance.simple_coverage_cop_calculation()
    geoenergy_instance.calculate_heat_pump_size()
    geoenergy_instance.simple_sizing_of_boreholes()
    geoenergy_instance.calculate_investment_costs()
    solar_instance = SolarPanels(building_instance)
    solar_instance.set_solar_array(array = solar_array)
    operation_costs_instance = OperationCosts(building_instance)
    operation_costs_instance.set_spotprice_array(year=2021, region='NO3', surcharge=0)
    operation_costs_instance.set_network_tariffs()
    operation_costs_instance.set_network_energy_component()
    operation_costs_instance.get_operation_costs()
    green_energy_fund_instance = GreenEnergyFund(building_instance)
    green_energy_fund_instance.set_economic_parameters()
    green_energy_fund_instance.set_energy_parameters()
    #green_energy_fund_instance.set_base_parameters(driftskostnad_per_år=building_instance.dict_operation_costs['geoenergy_consumption_compressor_array'])
    green_energy_fund_instance.calculation_15_year(leasingavgift_år_1=round(green_energy_fund_instance.INVESTERING*0.102), amortering_lån_år=15)
    st.write(vars(building_instance))
    st.write(green_energy_fund_instance.df_profit_and_loss_15)
    st.write(f"**{round(green_energy_fund_instance.irr_value_15*100, 3)} %**")

def visualization_tests():
    # test simple plot 
    df = pd.read_csv('src/testdata/energy_demand_dummy.csv', sep=',', index_col=0)
    spaceheating_array = df['SpaceHeating'].to_list()
    dhw_array = df['DHW'].to_list()
    electric_array = df['Electric'].to_list()
    building_instance = Building()
    energydemand_instance = EnergyDemand(building_instance)
    energydemand_instance.set_spaceheating_array(array = spaceheating_array)
    energydemand_instance.set_dhw_array(array = dhw_array)
    energydemand_instance.set_electric_array(array = electric_array)
    visualization_instance = Visualization()
    figure_thermal = visualization_instance.plot_hourly_series(
        building_instance.dict_energy['dhw_array'],
        'Tappevannsbehov',
        building_instance.dict_energy['spaceheating_array'],
        'Oppvarmingsbehov',
        height=250,
    )
    figure_electric = visualization_instance.plot_hourly_series(
        np.sort(building_instance.dict_energy['electric_array'])[::-1],
        'Elektrisk',
        height=250,
        xtick_datemode=False,
        linemode=True
    )
    st.plotly_chart(figure_thermal, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': False})
    st.plotly_chart(figure_electric, use_container_width=True, config = {'displayModeBar': False, 'staticPlot': False})
    


if __name__ == "__main__":
    #energy_demand_tests()
    #geoenergy_tests()
    #operation_costs_tests()
    #green_energy_fund_tests()
    visualization_tests()