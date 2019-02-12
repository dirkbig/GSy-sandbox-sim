# This model takes into account two ohmic losses, one being the resistance of the electrolyte itself
# (resistanceElectrolyte) and other losses like the presence of bubbles (resistanceOther).
# Source: 'Modeling an alkaline electrolysis cell through reduced-order and loss estimate approaches'
# from Milewski et al. (2014)


# cur_dens separate because of U / I iteration
def ely_voltage_u_ohm(ely, cur_dens, temp):

    electrolyte_thickness = ely.fitting_value_electrolyte_thickness

    # Temperature of this loop run [K].
    this_temp = temp
    # The conductivity of the the potassium hydroxide (KOH) solution [1/(Ohm*cm)].
    conductivity_electrolyte = -2.041 * ely.molarity_KOH - 0.0028 * ely.molarity_KOH**2 + 0.001043 * \
                                ely.molarity_KOH**3 + 0.005332 * ely.molarity_KOH * this_temp + 207.2 * \
                                ely.molarity_KOH / this_temp - 0.0000003 * ely.molarity_KOH**2 * this_temp**2
    # The electrolyte resistance [Ohm*cm²].
    resistance_electrolyte = electrolyte_thickness / conductivity_electrolyte
    # Void fraction of the electrolyte (j is multiplied by 10^4 because the units the formula is made for is A/m²
    # and j is in A/cm²) [-].
    epsilon = 0.023 * 2/3 * (cur_dens * 10**4)**0.3
    # The conductivity of bubbles and other effects [1/(Ohm*cm)].
    conductivity_other = (1 - epsilon)**1.5 * conductivity_electrolyte
    # Computing the resistance of bubbles in the electrolyte and other effects [Ohm*cm²].
    resistance_other = electrolyte_thickness / conductivity_other
    # Total ohmic resistance [Ohm*cm²].
    resistance_total = resistance_electrolyte + resistance_other
    # Cell voltage loss due to ohmic resistance [V].
    # (j is the current density with the unit A/cm²).
    voltage_ohm = resistance_total * cur_dens
    return voltage_ohm
