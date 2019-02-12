from mesa import Agent
from source.wallet import Wallet
import source.const as const
import logging
pv_log = logging.getLogger("electrolyzer")


class Pv(Agent):
    """ Electrolyzer agents are created through this class """
    def __init__(self, _unique_id, model):
        super().__init__(_unique_id, self)
        pv_log.info('agent%d created', _unique_id)

        self.id = _unique_id
        self.model = model
        # Simulation time [min].
        self.interval_time = self.model.data.market_interval
        self.current_step = 0
        # Define the installed power of the PV panel [kW].
        self.power_installed = 1000

        """ H2 demand list. """
        # Timeseries data of the power produced [kW/kW_peak]
        self.power_production = self.model.data.pv_commercial_list
        # Track the produced energy [kWh].
        self.track_electricity_produced = []

        """ Trading. """
        # In case a forecast based bidding strategy is chosen, define how many time steps the method is supposed to look
        # in the future [steps].
        self.wallet = Wallet(_unique_id)
        self.trading_state = None
        # Bid in the format [price, quantity, self ID]
        self.bids = None
        self.offers = None
        self.sold_energy = None
        self.bought_energy = None

        pv_log.info("PV object was generated.")

    def pre_auction_round(self):
        # Update the current time step.
        self.current_step = self.model.step_count
        # Check, if PV energy is produced this round. If so, bid it.
        print('This energy produced by pv is {}'.format(self.power_production[self.current_step]))
        if self.power_production[self.current_step] > 0:
            self.trading_state = 'supplying'
            # Calculate the energy produced in this time step [kWh].
            this_energy_produced = \
                self.power_production[self.current_step] * self.interval_time / 60 * self.power_installed
            # Set the selling bid as price [EUR/kWh] and energy sold [kWh] and the PV ID.
            self.offers = [0, this_energy_produced, self.id]
        else:
            this_energy_produced = 0.0
            self.trading_state = 'passive'
            self.offers = [0, this_energy_produced, self.id]

        # Track the energy produced [kWh].
        self.track_electricity_produced.append(this_energy_produced)

        self.announce_bid()

    def post_auction_round(self):
        # No post auction step required.
        # TODO: settle money made  by selling energy
        pass

    def announce_bid(self):
        # If the electrolyzer is bidding on electricity, the bid is added to the bidding list.
        pv_log.info('PV bidding state is {}'.format(self.trading_state))

        if self.trading_state == 'supplying':
            print("pv offer", self.offers)
            self.model.auction.offer_list.append(self.offers)








