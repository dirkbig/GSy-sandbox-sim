import math
import warnings
from mesa import Agent
from source.wallet import Wallet
import logging
import numpy as np
from scipy.optimize import linprog as lp
electrolyzer_log = logging.getLogger("electrolyzer")


class Electrolyzer(Agent):
    """ Electrolyzer agents are created through this class """
    def __init__(self, _unique_id, model):
        super().__init__(_unique_id, self)
        electrolyzer_log.info('agent%d created', _unique_id)

        self.id = _unique_id
        self.model = model
        # Simulation time [min].
        self.interval_time = model.data.market_interval
        self.current_step = 0

        """ H2 demand list. """
        self.h2_demand = self.model.data.electrolyzer_list
        # Track the used demand [kg], the energy bought [kWh], the hydrogen produced [kg] and the stored mass [kg].
        self.track_demand = []
        self.track_bought_energy = []
        self.track_produced_hydrogen = []
        self.track_stored_hydrogen = []

        """ Trading. """
        # Different methods can be chosen for deriving the bidding of the electrolyzer. Options are 'linprog' and
        # 'quadprog'. Quadprog by now seems to be the superior method in regard to result and computation time.
        # 'stepwise' uses a stepwise bid
        self.bidding_solver = 'stepwise'
        # In case a forecast based bidding strategy is chosen, define how many time steps the method is supposed to look
        # in the future [steps].
        self.forecast_horizon = self.model.data.forecast_horizon
        self.wallet = Wallet(_unique_id)
        self.trading_state = None
        # Bid in the format [price, quantity, self ID]
        self.bid = None
        self.offer = None
        self.sold_energy = None
        self.bought_energy = None
        self.track_cost = 0

        # Max. power that can be requested (current model can at least use 179.71 kW)[kW].
        # self.p_max = 179

        """ States of the electrolyzer. """
        # Current density (i = I/A) in [A / cm^2]
        self.cur_dens = 0
        # current in [A]
        self.current = 0
        # voltage in [V]
        self.voltage = 0
        # power in [kW]
        self.power = 0
        # temperature in [K]
        self.temp = 293.15

        # Parameters for the hydrogen station.
        # Define the storage buffer size wanted (class very small requires on avg. 56 kg/d) [kg]
        self.storage_buffer = 56
        # Amount of (usable) hydrogen stored [kg].
        self.stored_hydrogen = self.storage_buffer * 2
        # Max. amount of (usable) hydrogen stored [kg].
        self.storage_size = 200
        # Tracker for the hydrogen demand that couldn't be fulfilled [kg].
        self.demand_not_fulfilled = 0
        # Tracker for the hydrogen overproduced (that couldn't be stored) [kg].
        self.hydrogen_not_storable = 0

        # Parameter for the electrolyzer
        # size of cell surface [cm²].
        self.area_cell = 1500
        # Number of cell amount on one stack.
        self.z_cell = 140
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
        # pressure of hydrogen in the system in [Pa]
        self.pressure = 40 * 10**5
        # upper heating value in [MJ / kg]
        self.upp_heat_val = 141.8
        # efficiency of the electrolysis system (efficiency factor between H2 power and elects. power)
        self.eta_ely = 0.65

        # The fitting parameter exchange current density [A/cm²].
        self.fitting_value_exchange_current_density = 1.4043839e-3
        # The thickness of the electrolyte layer [cm].
        self.fitting_value_electrolyte_thickness = 0.2743715938

        # Min. temperature of the electrolyzer (completely cooled down) [K].
        self.temp_min = 293.15
        # Highest temperature the electrolyzer can be [K].
        self.temp_max = 353.15
        # Maximal current density given by the manufacturer [A/cm^2].
        self.cur_dens_max = 0.4
        # Current density at which the maximal temperature is reached [A/cm^2].
        self.cur_dens_max_temp = 0.35
        # Max. hydrogen that can be produced in one time step [kg].
        self.max_production_per_step = self.cur_dens_max * self.area_cell * self.interval_time * 60 * self.z_cell / \
            (2 * self.faraday) * self.molarity / 1000

        # saves last value of current density
        self.cur_dens_before = self.cur_dens
        # saves last temperature value
        self.temp_before = self.temp

        electrolyzer_log.info("Electrolyzer object was generated.")

    def pre_auction_round(self):
        # Update the current time step.
        self.current_step = self.model.step_count

        # Get the new bid.
        self.update_bid()
        self.announce_bid()

    def post_auction_round(self):
        # This energy bought [kWh].
        energy_bought = sum(self.model.auction.who_gets_what_dict[self.id])
        self.track_bought_energy.append(energy_bought)
        # Before the auction the physical states are renewed.
        self.update_power(energy_bought)
        # Track the total costs [EUR].
        # self.track_cost += self.power * self.interval_time / 60 * \
        #     self.model.data.utility_pricing_profile[self.current_step]
        # Update the stored mass hydrogen.
        self.update_storage()

    def update_storage(self):
        # Update the mass of the hydrogen stored.
        mass_old = self.stored_hydrogen
        # Calculate the produced mass of hydrogen by Faraday's law of electrolysis [kg].
        mass_produced = self.current * self.interval_time * 60 * self.z_cell / (2 * self.faraday) * self.molarity / 1000
        # Get the demand of this time step.
        mass_demanded = float(self.h2_demand[self.current_step])
        # Update the mass in the storage
        self.stored_hydrogen = mass_old + mass_produced - mass_demanded
        # Check if hydrogen demand could't be fulfilled. If so, track it and set the storage to empty.
        if self.stored_hydrogen < 0:
            self.demand_not_fulfilled += abs(self.stored_hydrogen)
            self.stored_hydrogen = 0
        elif self.stored_hydrogen > self.storage_size:
            # Case: the storage is more than full, thus iteratively the power has to be reduced
            mass_overload = self.stored_hydrogen - self.storage_size
            self.hydrogen_not_storable += mass_overload
            # Set the storage to the max. storage capacity [kg].
            self.stored_hydrogen = self.storage_size

        # Track values.
        self.track_stored_hydrogen.append(self.stored_hydrogen)
        self.track_produced_hydrogen.append(mass_produced)
        self.track_demand.append(mass_demanded)

    # Determine new measurement data for next step.
    def update_power(self, bought_energy):
        # Update the power value within the physical limits of the electrolyzer.
        # Parameter:
        #  bought_energy: Power value for the next time step [kWh].

        if bought_energy is None:
            return

        self.power = bought_energy / (self.interval_time / 60)
        # Update voltage, current, current density and power in an iterative process.
        self.update_voltage()
        # Check if the current density is above the max. allowed value.
        if self.cur_dens > self.cur_dens_max:
            warnings.warn("Electrolyzer bought more electricity than it can use.")
            # Update current density to max. allowed value
            self.cur_dens = self.cur_dens_max
            # Calculate the current.
            self.current = self.cur_dens * self.area_cell

            # Calculate the three parts the voltage consists of.
            v_rev = self.ely_voltage_u_rev(self.temp)
            v_act = self.ely_voltage_u_act(self.cur_dens, self.temp)
            v_ohm = self.ely_voltage_u_ohm(self.cur_dens, self.temp)

            # Calculate the total voltage.
            if self.cur_dens == 0:
                # If there are numeric deviation because of the value 0 set the voltage to the value 0.
                self.voltage = 0
            else:
                # Calculate the voltage [V].
                self.voltage = (v_act + v_rev + v_ohm) * self.z_cell

            # Calculate the power [kW].
            self.power = self.voltage * self.current / 1000

        # Calculate the temperature.
        self.temp = self.get_cell_temp()

    def update_bid(self):
        # Define the number of steps the perfect foresight optimization should look in the future.
        n_step = self.forecast_horizon

        if self.bidding_solver == "linprog":
            """ Linear program """

            # To derive the bid for this time step, a linear optimization (linprog) determines the optimal amount of
            # hydrogen that should be produced depending on the electricity price and the demand for the next ?2 weeks?.
            # This requires perfect foresight and in order to formulate a linear optimization problem, the temperature
            # dependent electrolyzer efficiency is not taken into account.
            #
            # The optimization problem is formulated in the way:
            # min  c * x
            # s.t. A * x <= b
            # x >= 0 and x < max. producible hydrogen
            #
            # Here, x is a vector with the amount of hydrogen produced each time step, c is the estimated cost function
            # for each time step (EEX spot marked costs are used), A * x <= b is used to make sure that the storage
            # never falls below the min. storage level (safety buffer).
            # Number of time steps of the future used for the optimization.

            # Define the electricity costs [EUR/kWh].
            c = self.model.data.utility_pricing_profile[self.current_step:self.current_step+n_step]
            # Define the inequality matrix (A) and vector (b) that make sure that at no time step the storage is below
            # the wanted buffer value.
            # The matrix A is supposed to sum up all hydrogen produced for each time step, therefore A is a lower
            # triangular matrix with all entries being -1 (- because we want to make sure that the hydrogen amount does
            # not fall below a certain amount, thus the <= must be turned in a >=, therefore A and b values are all set
            # negative).
            A = [[-1] * (i + 1) + [0] * (n_step - i - 1) for i in range(n_step)]
            # Append A by the negative of itself to set the boundaries that the storage cannot be more than full.
            A_append = [[1] * (i + 1) + [0] * (n_step - i - 1) for i in range(n_step)]
            A += A_append
            # The b value is the sum of the demand for each time step (- because see comment above).
            cumsum_h2_demand = self.h2_demand[self.current_step:self.current_step+n_step]
            cumsum_h2_demand = [-float(x) for x in cumsum_h2_demand]

            # Accumulate all demands over time.
            cumsum_h2_demand = np.cumsum(cumsum_h2_demand).tolist()
            # Now the usable hydrogen is added to all values of b except the last one. This allows stored hydrogen to be
            # used but will force the optimization to have at least as much hydrogen stored at the end of the looked at
            # time frame as there is now stored.
            b = [x + self.stored_hydrogen - self.storage_buffer for x in cumsum_h2_demand]
            b_append = [-x + self.storage_size for x in b]
            b[-1] -= self.stored_hydrogen - self.storage_buffer
            b += b_append
            # Define the bounds for the hydrogen produced.
            x_bound = ((0, self.max_production_per_step),) * n_step
            # Do the optimization with linprog.
            opt_res = lp(c, A, b, method="interior-point", bounds=x_bound)
            # Return the optimal value for this time slot [kg]
            if opt_res.success:
                opt_production = opt_res.x.tolist()
            else:
                # Case: Linprog couldn't derive optimal result, thus produce as much H2 as possible.
                opt_production = [self.max_production_per_step]
            print("Electrolyzer bidding - Optimization success is {}".format(opt_res.success))
            electrolyzer_log.info("Electrolyzer bidding - Optimization success is {}".format(opt_res.success))

        elif self.bidding_solver == "quadprog":
            """ Quadratic program """
            from cvxopt import matrix, solvers
            # The optimization problem is formulated in the way:
            # min  0.5 x^T * P * x + q^T * x
            # s.t. G * x <= d
            # x >= 0 and x < max. producible hydrogen

            # Define the electricity costs [EUR/kWh].
            c = self.model.data.utility_pricing_profile[self.current_step:self.current_step+n_step]
            # The quadratic matrix P is a diagonal matrix containing the values of c on the diagonal.
            # Create an eye matrix with the size of c.
            P = np.eye(len(c))
            # Multiply c with the eye matrix and convert the matrix back to a list.
            P = P * c

            # q is a vector consisting of 1.5 * max_production_per_step / 0.4 * 2 * c. The formula is derived by the
            # assumption, that the electrolyzer cell voltage rises linearly from 1.5 V when off to 1.9 V when on max.
            # power. The costs are the energy needed multiplied by the energy costs, which can be boiled down to the
            # form (w/o constants) C = (1.5 + 0.4 x / x_max) * x * c, where x_max is the max. H2 production per step.
            # Hereof the quadratic formulation can be derived.
            q = [1.5 * self.max_production_per_step / 0.4 * 2 * cost for cost in c]

            # Define the inequality matrix (A) and vector (b) that make sure that at no time step the storage is below
            # the wanted buffer value.
            # The matrix A is supposed to sum up all hydrogen produced for each time step, therefore A is a lower
            # triangular matrix with all entries being -1 (- because we want to make sure that the hydrogen amount does
            # not fall below a certain amount, thus the <= must be turned in a >=, therefore A and b values are all set
            # negative).
            A = [[-1.0] * (i + 1) + [0.0] * (n_step - i - 1) for i in range(n_step)]
            # Append A by the negative of itself to set the boundaries that the storage cannot be more than full.
            A_append = [[1.0] * (i + 1) + [0.0] * (n_step - i - 1) for i in range(n_step)]
            A += A_append
            # The constraints that x can only be between 0 and max. production have to be inserted via the matrix A.
            A += np.eye(n_step).tolist()
            eye_neg = -np.eye(n_step)
            A += eye_neg.tolist()

            A = np.array(A).T.tolist()
            # The b value is the sum of the demand for each time step (- because see comment above).
            cumsum_h2_demand = self.h2_demand[self.current_step:self.current_step+n_step]
            cumsum_h2_demand = [-float(x) for x in cumsum_h2_demand]

            # Accumulate all demands over time.
            cumsum_h2_demand = np.cumsum(cumsum_h2_demand).tolist()
            # Now the usable hydrogen is added to all values of b except the last one. This allows stored hydrogen to be
            # used but will force the optimization to have at least as much hydrogen stored at the end of the looked at
            # time frame as there is now stored.
            """ IDEA: Maybe the goal should be to have a filling level of half the storage at the end of the opt. """
            b = [x + self.stored_hydrogen - self.storage_buffer for x in cumsum_h2_demand]
            b_append = [-x + self.storage_size for x in b]
            b[-1] -= self.stored_hydrogen - self.storage_buffer
            b += b_append
            # Set the x boundaries (0 <= x <= max. H2 production per step).
            b += [self.max_production_per_step for _ in range(n_step)]
            b += [0 for _ in range(n_step)]

            # Convert all the lists needed to cvxopt matrix format.
            P = matrix(P)
            q = matrix(q)
            G = matrix(A)
            d = matrix(b)

            # Silence the optimizer output.
            solvers.options['show_progress'] = False
            # Do the optimization with linprog.
            opt_res = solvers.qp(P, q, G, d)
            # Transform cvxopt matrix format to list.
            if opt_res['status'] == 'optimal':
                opt_production = np.array(opt_res['x']).tolist()
                opt_production = [x[0] for x in opt_production]
            else:
                opt_production = [self.max_production_per_step]

            # Return the optimal value for this time slot [kg]
            print("Electrolyzer bidding - Optimization status is '{}'".format(opt_res['status']))
            electrolyzer_log.info("Optimization status is '{}'".format(opt_res['status']))

        elif self.bidding_solver == "dummy":
            """ Return a dummy bid """
            opt_production = [0.1]
            c = [30]

        elif self.bidding_solver == "stepwise":
            # Get the amount of hydrogen missing from the storage buffer [kg].
            min_amount_needed = min(self.max_production_per_step, max(0, self.storage_buffer - self.stored_hydrogen))
            # Approximate the electricity needed to produce the missing buffer mass (assume efficiency of 65 %) [kWh].
            min_bid = min_amount_needed * 33.3 / 0.65
            # Amount of H2 that can be stored [kg]
            max_mass_storable = min(self.max_production_per_step, self.storage_size - self.stored_hydrogen)
            # Approximate the electricity buyable to fill storage (assume efficiency of 65 %) [kWh].
            max_bid = max_mass_storable * 33.3 / 0.65
            # Generate the bids.
            # Bids are in the format [price [EUR/kWh], volume[kWh], ID]
            bids = []
            if min_bid > 0:
                # Case: There is an amount that should definitely be bought.
                bids.append([0.25, min_bid, self.id])
                # Subtract the amount needed from the amount that could be bought on top of that.
                max_bid -= min_bid

            if max_bid > 0:
                # Split max bid to 4 equal sections, one for 20 ct/kWh, one for 15, 10, and 5.
                bids.append([0.10, max_bid / 4, self.id])
                bids.append([0.12, max_bid / 4, self.id])
                bids.append([0.15, max_bid / 4, self.id])
                bids.append([0.18, max_bid / 4, self.id])

            # Place the bids
            for bid in bids:
                self.model.auction.bid_list.append(bid)

            return

        else:
            """ No valid solver """
            raise ValueError('Electrolyzer: No valid solver name given.')

        # self.plot_optimization_result(opt_production, cumsum_h2_demand, c)

        # Return the energy value needed for the optimized production and the price [kWh, EUR/kWh]
        energy_demand = self.get_power_by_production(opt_production[0]) * self.interval_time / 60
        price = c[0]

        if energy_demand == 0:
            # Case: Do not bid.
            self.bid = None
            self.trading_state = None
        else:
            # Case: Bid on energy.
            self.bid = [price, energy_demand, self.id]
            self.trading_state = "buying"

    def announce_bid(self):
        # If the electrolyzer is bidding on electricity, the bid is added to the bidding list.
        electrolyzer_log.info('Electrolyzer bidding state is {}'.format(self.trading_state))

        if self.trading_state == 'buying':
            self.model.auction.bid_list.append(self.bid)


    def plot_optimization_result(self, h2_produced, cumsum_h2_demand, electricity_price):
        import matplotlib.pyplot as plt
        cumsum_h2_produced = np.cumsum(h2_produced).tolist()
        """ Plot """
        font = {'weight': 'bold', 'size': 18}
        fig, (ax1, ax3) = plt.subplots(2, 1, gridspec_kw={'height_ratios': [3.5, 1]})
        # Plot 1.1
        ax1.tick_params(axis='both', which='major', labelsize=font['size'])
        ax1.step(list(range(len(h2_produced))),
            np.array(cumsum_h2_produced) + np.array(cumsum_h2_demand) + self.stored_hydrogen, 'k')
        ax1.set_ylabel("Storage filling level [kg]", fontsize=font['size'], fontweight=font['weight'])
        # Plot 1.2
        ax2 = ax1.twinx()
        ax2.step(list(range(len(h2_produced))), electricity_price, color='r')
        ax2.set_ylabel("Electricity price [EUR/kWh]", color='r', fontsize=font['size'], fontweight=font['weight'])
        ax2.tick_params(axis='both', which='major', labelsize=font['size'])
        # Plot 2
        ax3.step(list(range(len(h2_produced))), h2_produced/self.max_production_per_step * 100, color='g')
        ax3.set_ylabel("ELY utilization [%]", color='g', fontsize=font['size'], fontweight=font['weight'])
        ax3.tick_params(axis='both', which='major', labelsize=font['size'])
        ax3.set_xlabel("Step [-]", fontsize=font['size'], fontweight=font['weight'])
        # Show the plot.
        plt.show()

    def get_power_by_production(self, h2_production):
        # Calculate the power needed for a certain H2 production.

        # If no hydrogen is supposed to be produced, the power is 0.
        if h2_production == 0:
            return 0

        # Current needed for the H2 production [A].
        current = h2_production / (self.interval_time * 60 * self.z_cell / (2 * self.faraday) * self.molarity / 1000)
        # Current density [A/cm²].
        cur_dens = current/self.area_cell
        # Calculate the three components of the cell voltage [V].
        v_rev = (self.ely_voltage_u_rev(self.temp))
        v_act = (self.ely_voltage_u_act(cur_dens, self.temp))
        v_ohm = (self.ely_voltage_u_ohm(cur_dens, self.temp))
        # Total cell voltage [V].
        cell_voltage = v_rev + v_act + v_ohm
        # Total power of the electrolyzer [kW].
        power = current * cell_voltage * self.z_cell / 1000
        return power

    def get_cell_temp(self):
        # Calculate the electrolyzer temperature for the next time step.

        # Check if current density is higher than the given density at the highest possible temperature. If so,
        # set the current density to its maximum.
        if self.cur_dens > self.cur_dens_max_temp:
            cur_dens_now = self.cur_dens_max_temp
        else:
            cur_dens_now = self.cur_dens

        # Save the temperature calculated one step before.
        temp_before = self.temp
        # Calculate the temperature to which the electrolyzer is heating up depending on the given current density.
        # Lin. interpolation
        temp_aim = self.temp_min + (self.temp_max - self.temp_min) * cur_dens_now / self.cur_dens_max_temp
        # Calculate the new temperature of the electrolyzer by Newtons law of cooling. The exponent (-t[s]/2310) was
        # parameterized such that the 98 % of the temperature change are reached after 2.5 hours.
        temp_new = temp_aim + (temp_before - temp_aim) * math.exp(-self.interval_time*60 / 2310)
        # Return the new electrolyzer temperature [K].
        return temp_new

    def update_voltage(self):
        # Update the voltage and current for a given power.
        [voltage, current, cur_dens, power] = self.get_electricity_by_power(self.power)
        self.voltage = voltage
        self.current = current
        self.cur_dens = cur_dens
        self.power = power

    def get_electricity_by_power(self, power):
        # The total electrolysis voltage consists out of three different voltage parts (u_act, u_ohm, u_ref).
        # If the current isn't given an iteration is needed to get the total voltage.
        # This is the tolerance within the el. power is allowed to differ as a result of the iteration.
        relative_error = 1e-5
        # Create a dummy for the power calculated within the iteration.
        power_iteration = 0
        # Create a dummy for the voltage calculated within the iteration.
        voltage_iteration = 0
        # The current temperature [K].
        this_temp = self.temp
        # Estimate the current density through the chemical power to start the iteration [A/cm²].
        # P_H2 = P_elec * eta (self.power = P_elec)
        cur_dens_iteration = (power * self.eta_ely * 2.0 * self.faraday) / (self.area_cell * self.z_cell *
                                                                               self.molarity * self.upp_heat_val)
        # Calculate the current for the iteration start [A].
        current_iteration = cur_dens_iteration * self.area_cell
        # Determine the power deviation between the power target and the power reach within the iteration [kW].
        power_deviation = abs(power_iteration - power)
        # Execute the iteration until the power deviation is within the relative error which means the deviation is
        # accepted.
        while power_deviation > relative_error:
            # Calculate the voltage existing of three different parts [V].
            v_rev = (self.ely_voltage_u_rev(this_temp))
            v_act = (self.ely_voltage_u_act(cur_dens_iteration, this_temp))
            v_ohm = (self.ely_voltage_u_ohm(cur_dens_iteration, this_temp))
            # Get the voltage for this iteration step [V].
            voltage_iteration = (v_rev + v_act + v_ohm) * self.z_cell
            # Get the power for this iteration step [kW].
            power_iteration = voltage_iteration * current_iteration / 1000
            # Get the current for this iteration step [A].
            current_iteration = power / voltage_iteration * 1000
            # Get the current density for this iteration step [A/cm²].
            cur_dens_iteration = current_iteration / self.area_cell
            # Calculate the new power deviation [kW].
            power_deviation = abs(power_iteration - power)

        output = [voltage_iteration, current_iteration, cur_dens_iteration, power_iteration]
        return output



    def ely_voltage_u_act(self, cur_dens, temp):
        # This voltage part describes the activity losses within the electolyser.
        # Source: 'Modeling an alkaline electrolysis cell through reduced-order and loss estimate approaches'
        # from Milewski et al. (2014)!
        # Parameter:
        #  cur_dens: Current density [A/cm²]
        #  temp: Temperature [K]

        j0 = self.fitting_value_exchange_current_density

        '# COMPUTATION FOR EACH NODE'
        # The temperature of this loop run[K].
        this_temp = temp
        # The "alpha" values are valid for Ni - based electrodes.
        alpha_a = 0.0675 + 0.00095 * this_temp
        alpha_c = 0.1175 + 0.00095 * this_temp
        # The two parts of the activation voltage for this node[V].
        u_act_a = 2.306 * (self.gas_const * this_temp) / (self.n * self.faraday * alpha_a) * math.log10(cur_dens / j0)
        u_act_c = 2.306 * (self.gas_const * this_temp) / (self.n * self.faraday * alpha_c) * math.log10(cur_dens / j0)
        # The activation voltage for this node[V].
        voltage_activation = u_act_a + u_act_c

        return voltage_activation

    def ely_voltage_u_ohm(self, cur_dens, temp):
        # This model takes into account two ohmic losses, one being the resistance of the electrolyte itself
        # (resistanceElectrolyte) and other losses like the presence of bubbles (resistanceOther).
        # Source: 'Modeling an alkaline electrolysis cell through reduced-order and loss estimate approaches'
        # from Milewski et al. (2014)
        # Parameter:
        #  cur_dens: Current density [A/cm²]
        #  temp: Temperature [K]

        electrolyte_thickness = self.fitting_value_electrolyte_thickness

        # Temperature of this loop run [K].
        this_temp = temp
        # The conductivity of the the potassium hydroxide (KOH) solution [1/(Ohm*cm)].
        conductivity_electrolyte = -2.041 * self.molarity_KOH - 0.0028 * self.molarity_KOH ** 2 + 0.001043 * \
                                   self.molarity_KOH ** 3 + 0.005332 * self.molarity_KOH * this_temp + 207.2 * \
                                   self.molarity_KOH / this_temp - 0.0000003 * self.molarity_KOH ** 2 * this_temp ** 2
        # The electrolyte resistance [Ohm*cm²].
        resistance_electrolyte = electrolyte_thickness / conductivity_electrolyte
        # Void fraction of the electrolyte (j is multiplied by 10^4 because the units the formula is made for is A/m²
        # and j is in A/cm²) [-].
        epsilon = 0.023 * 2 / 3 * (cur_dens * 10 ** 4) ** 0.3
        # The conductivity of bubbles and other effects [1/(Ohm*cm)].
        conductivity_other = (1 - epsilon) ** 1.5 * conductivity_electrolyte
        # Computing the resistance of bubbles in the electrolyte and other effects [Ohm*cm²].
        resistance_other = electrolyte_thickness / conductivity_other
        # Total ohmic resistance [Ohm*cm²].
        resistance_total = resistance_electrolyte + resistance_other
        # Cell voltage loss due to ohmic resistance [V].
        # (j is the current density with the unit A/cm²).
        voltage_ohm = resistance_total * cur_dens
        return voltage_ohm

    def ely_voltage_u_rev(self, temp):
        # The reversible voltage can be calculated by two parts, one takes into account changes of the reversible cell
        # voltage due to temperature changes, the second part due to pressure changes.
        # Source: 'Modeling an alkaline electrolysis cell through reduced-order and loss estimate approaches'
        # from Milewski et al. (2014)
        # This calculations are valid in a temperature range from 0°C - 250°C, a pressure range from 1 bar - 200 bar and
        # a concentration range from 2 mol/kg - 18 mol/kg.
        # Parameter:
        #  temp: Temperature [K]

        # Coefficient 1 for the vapor pressure of the KOH solution.
        c1 = -0.0151 * self.molality_KOH - 1.6788e-03 * self.molarity_KOH ** 2 + 2.2588e-05 * self.molality_KOH ** 3
        # Coefficient 2 for the vapor pressure of the KOH solution.
        c2 = 1.0 - 1.2062e-03 * self.molality_KOH + 5.6024e-04 * self.molality_KOH ** 2 - 7.8228e-06 * self.molality_KOH**3

        '# COMPUTATION FOR ALL REQUESTED TEMPERATURES'
        # Get the temperature for this loop run [K].
        this_temp = temp
        # Compute the part of the reversible cell voltage that changes due to temperature [V].
        voltage_temperature = 1.5184 - 1.5421e-03 * this_temp + 9.526e-05 * this_temp * math.log(this_temp) + 9.84e-08 \
                              * this_temp ** 2
        # Calculate the vapor pressure of water [bar].
        pressure_water = math.exp(81.6179 - 7699.68 / this_temp - 10.9 * math.log(this_temp) + 9.5891e-03 * this_temp)
        # Calculate the vapor pressure of KOH solution [bar].
        pressure_koh = math.exp(2.302 * c1 + c2 * math.log(pressure_water))
        # Calculate the water activity value.
        water_activity = math.exp(
            -0.05192 * self.molality_KOH + 0.003302 * self.molality_KOH ** 2 + (3.177 * self.molality_KOH -
                                                                            2.131 * self.molality_KOH ** 2) / this_temp)
        # Compute the part of the reversible cell voltage that changes due to pressure [V].
        voltage_pressure = self.gas_const * this_temp / (self.n * self.faraday) *\
                    math.log((self.pressure - pressure_koh) * (self.pressure - pressure_koh) ** 0.5 / water_activity)
        # Calculate the reversible voltage [V].
        voltage_reversible = voltage_temperature + voltage_pressure

        return voltage_reversible

    def track_data(self):
        pass