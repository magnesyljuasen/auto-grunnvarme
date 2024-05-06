import numpy as np

def borefield_sizing(load, borefield):
    # function that calculates the temperature of the load and borefield - could be wrapped in a for loop for optimizing the borefield
    # return borehole temperature year 12-13
    well_temperature = np.zeros(8760)
    return well_temperature

def technical_sheet(source_temperature, demand, flow_temperature):
    # lookup table with demand -> source temperature -> flow temperature
    # get COP and P
    COP = 3
    P = 5
    return COP, P, 

spaceheating_array = np.zeros(8760)
dhw_array = np.zeros(8760)
borehole_temperature = np.zeros(8760)
outdoor_temperature = np.zeros(8760)
flow_temperature_dhw = np.zeros(8760)
flow_temperature_spaceheating = np.zeros(8760)

compressor_array = []
load_array = []
peak_array = []

borefield = 100 # set borefield here

for i in range(0, 10):
    for j in range(0, 8760):
        dhw_COP, dhw_P = technical_sheet(borehole_temperature[j], dhw_array[j], flow_temperature_dhw[j])
        spaceheating_COP, spaceheating_P = technical_sheet(borehole_temperature[j], spaceheating_array[j], flow_temperature_spaceheating[j])

        compressor = dhw_P/dhw_COP + spaceheating_P/spaceheating_COP
        load = (dhw_P - dhw_P/dhw_COP) + (spaceheating_P - spaceheating_P/spaceheating_COP)
        peak = spaceheating_array[j] + dhw_array[j] - compressor - load

        compressor_array.append(compressor)
        load_array.append(load)
        peak_array.append(peak)

    borehole_temperature = borefield_sizing(load_array, borefield)

    