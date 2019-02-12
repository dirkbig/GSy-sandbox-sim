# The reversible voltage can be calculated by two parts, one takes into account changes of the reversible cell voltage
# due to temperature changes, the second part due to pressure changes.
# Source: 'Modeling an alkaline electrolysis cell through reduced-order and loss estimate approaches'
# from Milewski et al. (2014)

import math


def ely_voltage_u_rev(ely, temp):
    # This calculations are valid in a temperature range from 0°C - 250°C, a pressure range from 1 bar - 200 bar and a
    # concentration range from 2 mol/kg - 18 mol/kg.

    # Coefficient 1 for the vapor pressure of the KOH solution.
    c1 = -0.0151 * ely.molality_KOH - 1.6788e-03 * ely.molarity_KOH**2 + 2.2588e-05 * ely.molality_KOH**3
    # Coefficient 2 for the vapor pressure of the KOH solution.
    c2 = 1.0 - 1.2062e-03 * ely.molality_KOH + 5.6024e-04 * ely.molality_KOH**2 - 7.8228e-06 * ely.molality_KOH**3

    '# COMPUTATION FOR ALL REQUESTED TEMPERATURES'
    # Get the temperature for this loop run [K].
    this_temp = temp
    # Compute the part of the reversible cell voltage that changes due to temperature [V].
    voltage_temperature = 1.5184 - 1.5421e-03 * this_temp + 9.526e-05 * this_temp * math.log(this_temp) + 9.84e-08 \
                           * this_temp**2
    # Calculate the vapor pressure of water [bar].
    pressure_water = math.exp(81.6179 - 7699.68 / this_temp - 10.9 * math.log(this_temp) + 9.5891e-03 * this_temp)
    # Calculate the vapor pressure of KOH solution [bar].
    pressure_koh = math.exp(2.302 * c1 + c2 * math.log(pressure_water))
    # Calculate the water activity value.
    water_activity = math.exp(-0.05192 * ely.molality_KOH + 0.003302 * ely.molality_KOH**2 + (3.177 * ely.molality_KOH -
                              2.131 * ely.molality_KOH**2) / this_temp)
    # Compute the part of the reversible cell voltage that changes due to pressure [V].
    voltage_pressure = ely.gas_const * this_temp / (ely.n * ely.faraday) * math.log((ely.pressure - pressure_koh) *
                       (ely.pressure - pressure_koh)**0.5 / water_activity)
    # Calculate the reversible voltage [V].
    voltage_reversible = voltage_temperature + voltage_pressure

    return voltage_reversible
