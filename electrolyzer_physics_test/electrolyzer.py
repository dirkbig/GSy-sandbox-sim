import u_act
import u_ohm
import u_rev
import cell_temp_new
import get_U_I


class Electrolyzer:
    def __init__(self, cell_area=1500, n_cell=140, p=1.5):
        # size of cell surface [cm²]
        self.area_cell = cell_area
        # Number of cell amount on one stack
        self.z_cell = n_cell
        # Faraday constant F [As/mol].
        self.faraday = 96485
        # Gas constant R [J /(mol K)].
        self.gas_const = 8.3144621
        # Moles of electrons needed to produce a mole of hydrogen[-].
        self.n = 2
        # Molar mass M_H2 [g / mol].
        self.molarity = 2.01588
        # Molar concentration of the KOH solution (10 mol/l for 28 wt% KOH) [mol/l].
        self.molarity_KOH = 10
        # Molal concentration of the KOH solution (7.64 mol/kg for 30 wt% KOH) [mol/kg].
        self.molality_KOH = 7.64
        # pressure of hydrogen in the system in [Pa]=
        self.pressure = p * 10**5
        # upper heating value in [MJ / kg]
        self.upp_heat_val = 141.8
        # efficiency of the electrolysis system (efficiency factor between H2 power and elects. power)
        self.eta_ely = 0.65

        # The fitting parameter exchange current density[A / cm²].
        self.fitting_value_exchange_current_density = 1.4043839e-3
        # The thickness of the electrolyte layer [cm].
        self.fitting_value_electrolyte_thickness = 0.2743715938

        # current density (i = I/A) in [A / cm^2]
        self.cur_dens = 0
        # current in [A]
        self.current = 0
        # voltage in [V]
        self.voltage = 0
        # power in [kW]
        self.power = 0
        # temperature in [K]
        self.temp = 293.15

        # Time the electrolyzer needs to heat up [s]
        self.heating_time = 2.5 * 3600
        # start temperature when the electrolyzer is totally cooled down / wasn't in use for a long time
        # (ambient temperature) in [K]
        self.temp_0 = 293.15
        # highest temperature the electrolyzer can be in [K]
        self.temp_end = 353.15
        # maximal current density given by the manufacturer in [A/cm^2]
        self.cur_dens_max = 0.4
        # at this current density the maximal temperature is reached in [A/cm^2]
        self.cur_dens_max_temp = 0.35
        # minimal current density given by the manufacturer in [mA/cm^2]
        self.cur_dens_min = 0

        # counts the number of seconds the simulation is running
        self.sec_counter = 1
        # saves last value of current density
        self.cur_dens_before = self.cur_dens
        # saves last temperature value
        self.temp_before = self.temp

    # Determine new measurement data for next step.
    def update_power(self, optimization_data):

        # There could be a case where power or current is given from the opt data. So check which data is given.
        # If power is given.
        if optimization_data[2] > 0 and optimization_data[3] == 0:
            # Get the power from the opt data.
            self.power = optimization_data[2]
            # It get the current and voltage an iteration is needed. Execute iteration:
            get_U_I.get_v_i(self)

        # If current is given.
        elif optimization_data[2] == 0 and optimization_data[3] > 0:
            # Get the current from the opt data.
            self.current = optimization_data[3]
            # Calculate the current density.
            self.cur_dens = self.current / self.area_cell

            # Calculate the voltage existing of three different parts.
            self.v_rev = u_rev.ely_voltage_u_rev(self, self.temp)
            self.v_act = u_act.ely_voltage_u_act(self, self.cur_dens, self.temp)
            self.v_ohm = u_ohm.ely_voltage_u_ohm(self, self.cur_dens, self.temp)

            # Calculate the total voltage.
            if self.cur_dens == 0:
                # If there are numeric deviation because of the value 0 set the voltage to the value 0.
                self.voltage = 0
            else:
                self.voltage = (self.v_act + self.v_rev + self.v_ohm) * self.z_cell

            # Calculate the power.
            self.power = self.voltage * self.current

        # If power and current are zero the electrolyzer is shut off.
        else:
            self.current = 0
            self.cur_dens = 0
            self.power = 0
            self.voltage = 0

        # Calculate the temperature.
        self.temp = cell_temp_new.cell_temp(self)


