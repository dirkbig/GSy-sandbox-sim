""" DATA """

""" Constants """
ambient_temp = 293.15
num_minutes_in_a_day = 1440

""" Money matters """
initial_coins_household = 10000000000


""" ESS constants"""
# initial_capacity = 0
# max_size_ess = 10

horizon = 24

""" Electrolyzer constants """
# Faraday constant F [As/mol].
faraday = 96485
# Gas constant R [J /(mol K)].
gas_const = 8.3144621
# Moles of electrons needed to produce a mole of hydrogen[-].
n = 2
# Molar mass M_H2 [g / mol].
molarity = 2.01588
# Molar concentration of the KOH solution (10 mol/l for 28 wt% KOH) [mol/l].
molarity_KOH = 10
# Molal concentration of the KOH solution (7.64 mol/kg for 30 wt% KOH) [mol/kg].
molality_KOH = 7.64
# pressure of hydrogen in the system in [Pa]=
pressure_factor = 10**5
# upper heating value in [MJ / kg]
upp_heat_val = 141.8
# efficiency of the electrolysis system (efficiency factor between H2 power and elects. power)
eta_ely = 0.65
# The fitting parameter exchange current density[A / cm²].
fitting_value_exchange_current_density = 1.4043839e-3
# The thickness of the electrolyte layer [cm].
fitting_value_electrolyte_thickness = 0.2743715938
# temperature in [K]
temp = 293.15

# Time the electrolyzer needs to heat up [s]
heating_time = 2.5 * 3600
# start temperature when the electrolyzer is totally cooled down / wasn't in use for a long time
# (ambient temperature) in [K]
temp_0 = 293.15
# highest temperature the electrolyzer can be in [K]
temp_end = 353.15
# maximal current density given by the manufacturer in [A/cm^2]
cur_dens_max = 0.4
# at this current density the maximal temperature is reached in [A/cm^2]
cur_dens_max_temp = 0.35
# minimal current density given by the manufacturer in [mA/cm^2]
cur_dens_min = 0

# counts the number of seconds the simulation is running
sec_counter = 1

""" Hydrogen refueling station """
hrs_storage_size = 100



