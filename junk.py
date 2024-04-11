import numpy as np

def find_energy_arrays(self):
    numpy_arrays = {}
    for attr_name, value in self.__dict__.items():
        if isinstance(value, np.ndarray) and len(value) == 8760:
            numpy_arrays[attr_name] = value
    return numpy_arrays