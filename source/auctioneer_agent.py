from source.auctioneer_methods import *

from plots import clearing_snapshot
from mesa import Agent
import seaborn as sns

sns.set()
auction_log = logging.getLogger('run_microgrid.auctioneer')


class Auctioneer(Agent):
    """ Pay as Clear auction market is created here"""
    def __init__(self, _unique_id, model):
        super().__init__(_unique_id, self)
        auction_log.info('auction of type %s created', _unique_id)
        self.model = model

        self.snapshot_plot = True
        self.snapshot_plot_interval = 15

        self.id = _unique_id
        self.pricing_rule = self.model.data.pricing_rule
        self.aggregate_demand_curve = []
        self.aggregate_supply_curve = []

        self.bid_list = []
        self.offer_list = []
        self.utility_market_maker_rate = 10

        self.sorted_bid_list = None
        self.sorted_offer_list = None
        self.clearing_quantity = None
        self.clearing_price = None
        self.trade_pairs = None

        self.percentage_sellers = None
        self.percentage_buyers = None
        self.percentage_passive = None

        self.who_gets_what_dict = None

    def auction_round(self):
        """check whether all agents have submitted their bids"""
        self.user_participation()

        """ resets the acquired energy for all households """
        self.who_gets_what_dict = {}
        for agent in self.model.agents[:]:
            self.who_gets_what_dict[agent.id] = []

        if len(self.offer_list) is not 0 and len(self.bid_list) is not 0 \
                or (self.model.utility is not None and len(self.bid_list) is not 0):
            """ only proceed to auction if there is demand and supply (i.e. supply in the form of
                prosumers or utility grid) """
            self.sorted_bid_list, self.sorted_offer_list, sorted_x_y_y_pairs_list = self.sorting()
            self.execute_auction(sorted_x_y_y_pairs_list)
            self.clearing_of_market()
            """ clear lists for later use in next step """
            self.bid_list = []
            self.offer_list = []
            return

        else:
            """ clear lists for later use in next step """
            self.bid_list = []
            self.offer_list = []
            auction_log.warning("no trade at this step")
            return

    def execute_auction(self, sorted_x_y_y_pairs_list):
        """ auctioneer sets up the market and clears it according pricing rule """

        check_demand_supply(self.sorted_bid_list, self.sorted_offer_list)

        self.trade_pairs = None
        self.clearing_quantity = None
        self.clearing_price = None

        """ picks pricing rule and generates trade_pairs"""
        if self.pricing_rule == 'pab':
            self.clearing_quantity, total_turnover, self.trade_pairs = \
                pab_pricing(sorted_x_y_y_pairs_list, self.sorted_bid_list, self.sorted_offer_list)

            auction_log.info("Clearing quantity %f, total turnover is %f",
                             self.clearing_quantity, total_turnover)

        elif self.pricing_rule == 'pac':
            self.clearing_quantity, self.clearing_price, total_turnover, self.trade_pairs = \
                pac_pricing(sorted_x_y_y_pairs_list, self.sorted_bid_list, self.sorted_offer_list)
            auction_log.info("Clearing quantity %f, price %f, total turnover is %f",
                             self.clearing_quantity, self.clearing_price, total_turnover)

        print('bids', self.sorted_bid_list)
        print('offers', self.sorted_offer_list)

        print('trade_pairs', self.trade_pairs)
        if self.snapshot_plot is True and self.model.step_count % self.snapshot_plot_interval == 0:
            clearing_snapshot(self.clearing_quantity, self.clearing_price, sorted_x_y_y_pairs_list)
        # TODO: save "clearing_quantity, clearing_price, sorted_x_y_y_pairs_list" in an export file, to plots afterwards

    def sorting(self):
        """sorts bids and offers into an aggregated demand/supply curve"""

        # TODO: when ALL supply falls (far) under demand price, all supply is of course matched by pricing rule??
        # this creates a bug, which I currently avoid by breaking the sequence. But should be fixed
        # source of the bug is at the sorting algorithm, should allow a clearing also when supply completely falls
        # BELOW demand curve

        # sort on price, not quantity, so location[0]
        np.array(self.bid_list)

        if len(np.array(self.bid_list).shape) == 1:
            self.bid_list = [self.bid_list]
            assert len(np.array(self.bid_list).shape) == 2

        if len(np.array(self.offer_list).shape) == 1:
            self.offer_list = [self.offer_list]
            assert len(np.array(self.offer_list).shape) == 2

        sorted_bid_list = sorted(self.bid_list, key=lambda location: location[0], reverse=True)
        sorted_offer_list = sorted(self.offer_list, key=lambda location: location[0])

        if self.model.utility is not None:
            """ append (in a clever, semi-aesthetic way) the utility offer to the offer list according to the 
                utility_market_maker_rate """
            sorted_bid_list, sorted_offer_list = self.append_utility_offer(sorted_bid_list, sorted_offer_list)

        # creation of aggregate supply/demand points
        aggregate_quantity_points = []

        aggregate_quantity_points_bid = []
        aggregate_quantity_points_offer = []

        x_y_y_pairs_list = []
        x_bid_pairs_list = []
        x_supply_pairs_list = []

        """ appending bid quantities to aggregate demand and supply curve, effort to make curves overlap """
        # start with construction of x-axis, starting at 0.
        prev = 0
        for i in range(len(sorted_bid_list)):
            # append bid quantity to aggregate demand/supply curve;
            # first create x-axis of curve
            aggregate_quantity_points_bid.append(sorted_bid_list[i][1])
            # move on this x-axis of curve for next item to be appended
            aggregate_quantity_points_bid[i] += prev
            prev = aggregate_quantity_points_bid[i]
            # append bid item to main bid curve: [x-axis location, bid price, offer quantity, buyer id, seller id]
            x_bid_pairs_list.append([aggregate_quantity_points_bid[i],
                                     sorted_bid_list[i][0], None,
                                     sorted_bid_list[i][2], None])

        """ appending offer quantities to aggregate demand and supply curve, effort to make curves overlap """
        # continuing where we left of while appending the bids on the x-axis.
        prev = 0
        for j in range(len(sorted_offer_list)):
            # append offer quantity to aggregate demand/supply curve
            aggregate_quantity_points_offer.append(sorted_offer_list[j][1])
            # move on this x-axis of curve for next item to be appended
            aggregate_quantity_points_offer[j] += prev
            prev = aggregate_quantity_points_offer[j]
            # append offer item to main bid curve: [x-axis location, bid quantity, offer price, buyer id, seller id]
            x_supply_pairs_list.append([aggregate_quantity_points_offer[j],
                                        None, sorted_offer_list[j][0],
                                        None, sorted_offer_list[j][2]])

        x_y_y_pairs_list.extend(x_bid_pairs_list)
        x_y_y_pairs_list.extend(x_supply_pairs_list)

        """sorted_x_y_y_pairs_list[agents][quantity_point, bid_price, offer_price]"""
        sorted_x_y_y_pairs_list = sorted(x_y_y_pairs_list, key=lambda l: l[0])

        # stupid comprehension proxy begins here...
        bid_list_proxy = []
        offer_list_proxy = []
        for i in range(len(sorted_x_y_y_pairs_list)):
            bid_list_proxy.append(sorted_x_y_y_pairs_list[i][1])
            offer_list_proxy.append(sorted_x_y_y_pairs_list[i][2])
        # stupid comprehension proxy stops here...

        # the sorted_x_x_y_pairs_list contains all bids and offers ordered by trade volume on x-axis
        # now, bids are linked to offers, searching for the next offer to be linked to it previous bid
        for segment in range(len(sorted_x_y_y_pairs_list)):
            j = 1
            _offer_list_proxy = offer_list_proxy[segment:]
            # this check "if offer_price_proxy is not empty", is pretty redundant
            if not all(offer_price is None for offer_price in _offer_list_proxy):
                # find next offer in line: run through sorted_x_x_y_pairs_list
                # starting from current quantity
                while sorted_x_y_y_pairs_list[segment][2] is None:
                    # if current selected quantity block is an offer
                    if sorted_x_y_y_pairs_list[segment+j][2] is not None:
                        # then the current selected quantity (which is a bid) is linked to this offer
                        # since sorted_x_x_y_pairs_list is sorted on
                        sorted_x_y_y_pairs_list[segment][2] = sorted_x_y_y_pairs_list[segment+j][2]
                        sorted_x_y_y_pairs_list[segment][4] = sorted_x_y_y_pairs_list[segment+j][4]
                    else:
                        j += 1
            else:
                break

        for segment in range(len(sorted_x_y_y_pairs_list)):
            j = 1
            _bid_list_proxy = bid_list_proxy[segment:]
            # this check "if bid_price_proxy is not empty", is pretty redundant
            if not all(v is None for v in _bid_list_proxy):
                #
                while sorted_x_y_y_pairs_list[segment][1] is None:
                    if sorted_x_y_y_pairs_list[segment+j][1] is not None:
                        sorted_x_y_y_pairs_list[segment][1] = sorted_x_y_y_pairs_list[segment+j][1]
                        sorted_x_y_y_pairs_list[segment][3] = sorted_x_y_y_pairs_list[segment+j][3]

                    else:
                        j += 1
            else:
                break


        return sorted_bid_list, sorted_offer_list, sorted_x_y_y_pairs_list

    def clearing_of_market(self):
        """clears market """

        """ resets the acquired energy for all households """
        for agent in self.model.agents[:]:
            self.model.agents[agent.id].energy_trade_flux = 0

        """ listing of all offers/bids selected for trade """
        if self.trade_pairs is not None:
            for trade in range(len(self.trade_pairs)):
                # data structure: [seller_id, buyer_id, trade_quantity, turnover]
                id_seller = self.trade_pairs[trade][0]
                id_buyer = self.trade_pairs[trade][1]
                trade_quantity = self.trade_pairs[trade][2]
                turnover = self.trade_pairs[trade][3]

                """ execute trade buy calling household agent's wallet settlement """
                if id_seller is 'utility':
                    """ seller was utility """
                    self.who_gets_what_dict[id_seller].append(-trade_quantity)
                    self.model.utility.wallet.settle_revenue(turnover)
                else:
                    self.who_gets_what_dict[id_seller].append(-trade_quantity)
                    self.model.agents[id_seller].wallet.settle_revenue(turnover)

                self.who_gets_what_dict[id_buyer].append(trade_quantity)
                self.model.agents[id_buyer].wallet.settle_payment(turnover)

        else:
            auction_log.warning("no trade at this step")

    def user_participation(self):
        """ small analysis on user participation per step"""
        num_selling = 0
        num_buying = 0
        num_passive = 0

        for agent in self.model.agents[:]:
            if agent.trading_state == 'supplying':
                num_selling += 1
            elif agent.trading_state == 'buying':
                num_buying += 1
            else:
                num_passive += 1
        total_num = num_selling + num_buying + num_passive

        # assert total_num == self.model.data.num_households

        # TODO: translate this to percentage of households actually capable of selling or buying...
        # of course pure consumers will never be able to trade energy...
        self.percentage_sellers = num_selling / total_num
        self.percentage_buyers = num_buying / total_num
        self.percentage_passive = num_passive / total_num

    def append_utility_offer(self, sorted_bid_list, sorted_offer_list):
        """ function is only called when an utility is present, it supplements the offer list of auctioneer
            with an 'infinite' supply of energy up to the necessary amount to cover all demand, bought or not """

        bid_total = sum(np.asarray(sorted_bid_list)[:, 1])

        try:
            prosumer_offer_total = sum(np.asarray(sorted_offer_list)[:, 1])
        except IndexError:
            prosumer_offer_total = 0
            auction_log.info("no prosumers in the grid supplying energy")

        """ Append utility"""
        total_offer_below_mmr = 0
        utility_id = self.model.utility.id
        if len(sorted_offer_list) is 0:
            utility_quantity = bid_total
            sorted_offer_list.insert(0, [self.utility_market_maker_rate, utility_quantity, utility_id])

        else:
            for offer in range(len(sorted_offer_list)):
                if sorted_offer_list[offer][0] <= self.utility_market_maker_rate:
                    total_offer_below_mmr += sorted_offer_list[offer][1]
                    """ offer is less expensive than market maker rate """
                    pass
                if sorted_offer_list[offer][0] > self.utility_market_maker_rate or offer == len(sorted_offer_list) - 1:
                    """ offer is more expensive that market maker rate, 
                        utility is only activated if market maker rate is competitive (lower than prosumer rate)"""
                    if bid_total > total_offer_below_mmr:
                        utility_quantity = bid_total - total_offer_below_mmr
                        sorted_offer_list.insert(offer + 1, [self.utility_market_maker_rate, utility_quantity, utility_id])

                    else:
                        auction_log.info("no utility import into community needed at this step")

        sorted_bid_list = sorted(sorted_bid_list, key=lambda price_point: price_point[0], reverse=True)
        sorted_offer_list = sorted(sorted_offer_list, key=lambda price_point: price_point[0])

        """ append utility ot who_gets_what dictionary """
        self.who_gets_what_dict[utility_id] = []

        print("bid", sorted_bid_list)
        print("offers", sorted_offer_list)

        return sorted_bid_list, sorted_offer_list
