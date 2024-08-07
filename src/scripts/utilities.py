import numpy as np
from sklearn.linear_model import LinearRegression
import pygfunction as gt
import plotly.graph_objects as go

def linear_interpolation(x, x1, x2, y1, y2):
    y = y1 + (x - x1) * (y2 - y1) / (x2 - x1)
    return y

def linear_regression(x, y):
    x = x.reshape((-1, 1))
    model = LinearRegression()
    model.fit(x, y)
    model = LinearRegression().fit(x, y)
    r_sq = model.score(x, y)
    y_pred = model.predict(x)
    y_pred = model.intercept_ + np.sum(model.coef_ * x, axis=1)
    linear_y = model.predict(x)
    slope = (linear_y[-1]-linear_y[0])/(x[-1]-x[0])
    intersect = linear_y[-1]-slope*x[-1]
    return slope, intersect

def coverage_calculation(coverage_percentage, array):
    if coverage_percentage == 100:
        return array, np.zeros(8760)
    elif coverage_percentage == 0:
        return np.zeros(8760), array
    array_sorted = np.sort(array)
    timeserie_sum = np.sum(array)
    timeserie_N = len(array)
    startpunkt = timeserie_N // 2
    i = 0
    avvik = 0.0001
    pm = 2 + avvik
    while abs(pm - 1) > avvik:
        cutoff = array_sorted[startpunkt]
        array_tmp = np.where(array > cutoff, cutoff, array)
        beregnet_dekningsgrad = (np.sum(array_tmp) / timeserie_sum) * 100
        pm = beregnet_dekningsgrad / coverage_percentage
        gammelt_startpunkt = startpunkt
        if pm < 1:
            startpunkt = startpunkt + timeserie_N // 2 ** (i + 2) - 1
        else:
            startpunkt = startpunkt - timeserie_N // 2 ** (i + 2) - 1
        if startpunkt == gammelt_startpunkt:
            break
        i += 1
        if i > 13:
            break
    return array_tmp, array - array_tmp