# This voltage part describes the activity losses within the electolyser.
# Source: 'Modeling an alkaline electrolysis cell through reduced-order and loss estimate approaches'
# from Milewski et al. (2014)!

import math


def ely_voltage_u_act(ely, cur_dens, temp):

    j0 = ely.fitting_value_exchange_current_density

    '# COMPUTATION FOR EACH NODE'
    # The temperature of this loop run[K].
    this_temp = temp
    # The "alpha" values are valid for Ni - based electrodes.
    alpha_a = 0.0675 + 0.00095 * this_temp
    alpha_c = 0.1175 + 0.00095 * this_temp
    # The two parts of the activation voltage for this node[V].
    u_act_a = 2.306 * (ely.gas_const * this_temp) / (ely.n * ely.faraday * alpha_a) * math.log10(cur_dens / j0)
    u_act_c = 2.306 * (ely.gas_const * this_temp) / (ely.n * ely.faraday * alpha_c) * math.log10(cur_dens / j0)
    # The activation voltage for this node[V].
    voltage_activation = u_act_a + u_act_c

    return voltage_activation
