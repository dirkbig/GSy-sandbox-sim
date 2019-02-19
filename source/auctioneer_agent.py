from source.auctioneer_methods import *

from plots import clearing_snapshot
from mesa import Agent
import seaborn as sns
from source.wallet import Wallet

sns.set()
auction_log = logging.getLogger('run_microgrid.auctioneer')


class Auctioneer(Agent):
    """ Pay as Clear auction market is created here"""
    def __init__(self, _unique_id, model):
        super().__init__(_unique_id, self)
        auction_log.info('auction of type %s created', _unique_id)
        self.model = model
        self.wallet = Wallet(_unique_id)

        self.snapshot_plot = True
        self.snapshot_plot_interval = 15

        self.id = _unique_id
        self.pricing_rule = self.model.data.pricing_rule
        self.aggregate_demand_curve = []
        self.aggregate_supply_curve = []

        self.bid_list = [[]]
        self.offer_list = [[]]
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

        # """ resets the acquired energy for all households """
        # self.who_gets_what_dict = {}
        # for agent_id in self.model.agents:
        #     self.who_gets_what_dict[agent_id] = []

        # While an empty bid list may arrive as an empty list or as a list containing an empty list, the outer list is
        # removed here for the later check, if there are bids at all (which is done taking the length of the bid list).
        if len(self.bid_list) == 0:
            bid_list_check = self.bid_list
        elif len(self.bid_list) > 1:
            bid_list_check = self.bid_list[1]
            # While the first list entry can be an empty list, if there are multiple bids don't use the first one.
        else:
            bid_list_check = self.bid_list[0]

        def empty(seq):
            try:
                return all(map(empty, seq))
            except TypeError:
                return False

        if empty(self.offer_list) is False and empty(self.bid_list) is False \
                or (self.model.data.utility_presence is True and empty(self.bid_list) is False):
            """ only proceed to auction if there is demand and supply (i.e. supply in the form of
            prosumers or utility grid) 
            """
            self.sorted_bid_list, self.sorted_offer_list, sorted_x_y_y_pairs_list = self.sorting()
            self.execute_auction(sorted_x_y_y_pairs_list)
            self.clearing_of_market()
            """ clear lists for later use in next step """
            self.bid_list = [[]]
            self.offer_list = [[]]
            return

        else:
            """ clear lists for later use in next step """
            self.bid_list = [[]]
            self.offer_list = [[]]
            auction_log.error("no trade at this step")
            return

    def market_rules(self, sorted_x_y_y_pairs_list):
        # No zero volume trade pairs and no self-trades
        # TODO: find the source of zero volume bids and self-trades and fix it there!
        sorted_x_y_y_pairs_list[:] = [segment for segment in sorted_x_y_y_pairs_list
                                      if
                                      segment[3] != segment[4]
                                      and
                                      segment[0] != 0]

        # assert success of market rule filtering
        for segment in sorted_x_y_y_pairs_list:
            # agents buying from themselves; this should, rationally, never happen!!!
            assert segment[3] != segment[4]
            assert segment[0] != 0

        return sorted_x_y_y_pairs_list

    def execute_auction(self, sorted_x_y_y_pairs_list):
        """ auctioneer sets up the market and clears it according pricing rule """

        check_demand_supply(self.sorted_bid_list, self.sorted_offer_list)

        self.trade_pairs = None
        self.clearing_quantity = None
        self.clearing_price = None

        # filer sorted_x_y_y_pairs_list for market anomalies
        sorted_x_y_y_pairs_list = self.market_rules(sorted_x_y_y_pairs_list)

        """ picks pricing rule and generates trade_pairs"""
        if self.pricing_rule == 'pab':
            self.clearing_quantity, average_clearing_price, total_turnover, self.trade_pairs = \
                pab_pricing(sorted_x_y_y_pairs_list, self.sorted_bid_list, self.sorted_offer_list)

            auction_log.info("Clearing quantity %f, avg price %f, total turnover is %f",
                             self.clearing_quantity, average_clearing_price,  total_turnover)

        elif self.pricing_rule == 'pac':
            self.clearing_quantity, self.clearing_price, total_turnover, self.trade_pairs = \
                pac_pricing(sorted_x_y_y_pairs_list, self.sorted_bid_list, self.sorted_offer_list)
            auction_log.info("Clearing quantity %f, price %f, total turnover is %f",
                             self.clearing_quantity, self.clearing_price, total_turnover)

        elif self.pricing_rule == 'mcafee':
            self.clearing_quantity, self.clearing_price, total_turnover, self.trade_pairs = \
                mcafee_pricing(sorted_x_y_y_pairs_list)

        # Make snapshot of market clearing for market analysis
        if self.snapshot_plot is True and self.model.step_count % self.snapshot_plot_interval == 0:
            clearing_snapshot(self.clearing_quantity, self.clearing_price, sorted_x_y_y_pairs_list)

        # Save "clearing_quantity, clearing_price, sorted_x_y_y_pairs_list" in an export file, to plots afterwards

        # Update track values for later plots and evaluation.
        self.model.data.clearing_price[self.model.step_count] = self.clearing_price
        self.model.data.clearing_quantity[self.model.step_count] = self.clearing_quantity

        # Track the demand of all households
        household_demand = 0.0
        for agent in self.model.agents:
            if type(self.model.agents[agent]).__name__ == 'HouseholdAgent':
                household_demand += self.model.agents[agent].load_data[self.model.step_count]
        self.model.data.household_demand[self.model.step_count] = household_demand
        # If there is a utility grid track the selling price of the grid.
        if self.model.data.utility_presence is True:
            self.model.data.utility_price[self.model.step_count] = self.model.agents['Utility'].sell_rate_utility

        print('bids [price, quantity, id]:', self.sorted_bid_list)
        print('offers [price, quantity, id]', self.sorted_offer_list)
        print('trade_pairs [id_seller, id_buyer, quantity, price*quantity]:', self.trade_pairs)

        if self.model.data.pricing_rule is 'pab':
            self.clearing_price = None

    def sorting(self):
        """sorts bids and offers into an aggregated demand/supply curve"""

        # TODO: when ALL supply falls (far) under demand price, all supply is of course matched by pricing rule??
        # this creates a bug, which I currently avoid by breaking the sequence. But should be fixed
        # source of the bug is at the sorting algorithm, should allow a clearing also when supply completely falls
        # BELOW demand curve

        # sort on price, not quantity, so location[0]
        # print(self.bid_list)

        for bid in self.bid_list:
            if len(bid) is 0:
                self.bid_list.remove(bid)

        for offer in self.offer_list:
            if len(offer) is 0:
                self.offer_list.remove(offer)

        # print(self.bid_list)

        # bid = (price, quantity, id)
        sorted_bid_list = sorted(self.bid_list, key=lambda location: location[0], reverse=True)
        try:
            sorted_offer_list = sorted(self.offer_list, key=lambda location: location[0])
        except TypeError:
            pass
        '''
        if self.model.data.utility_presence is not None:
            """ append (in a clever, semi-aesthetic way) the utility offer to the offer list according to the 
                utility_market_maker_rate """
            sorted_bid_list, sorted_offer_list = self.append_utility_offer(sorted_bid_list, sorted_offer_list)
        '''

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
        self.who_gets_what_dict = {}
        for agent_id in self.model.agents:
            self.who_gets_what_dict[agent_id] = []

        def who_gets_what_bb(_id_seller, _id_buyer, _trade_quantity, _turnover):
            """ execute trade buy calling household agent's wallet settlement """
            # Settlement of seller revenue if market is budget balanced
            # Is this if statement necessary?
            assert _id_seller != _id_buyer

            if id_seller is 'Utility':
                """ seller was utility """
                self.who_gets_what_dict[_id_seller].append(-_trade_quantity)
                self.model.agents['Utility'].wallet.settle_revenue(_turnover)
            else:
                self.who_gets_what_dict[_id_seller].append(-_trade_quantity)
                self.model.agents[_id_seller].wallet.settle_revenue(_turnover)

            # Settlement of buyer payments
            self.who_gets_what_dict[_id_buyer].append(_trade_quantity)
            self.model.agents[_id_buyer].wallet.settle_payment(_turnover)

        def who_gets_what_not_bb(_id_seller, _id_buyer, _trade_quantity, _trade_payment):
            """ execute trade buy calling household agent's wallet settlement """
            # Settlement of seller revenue if market is NOT budget balanced
            trade_revenue_seller, trade_payment_buyer = _trade_payment
            assert trade_payment_buyer >= trade_revenue_seller
            assert _id_seller != _id_buyer
            clearing_inbalance = trade_payment_buyer - trade_revenue_seller

            self.who_gets_what_dict[_id_seller].append(-_trade_quantity)
            self.who_gets_what_dict[_id_buyer].append(_trade_quantity)

            self.model.agents[_id_seller].wallet.settle_revenue(trade_revenue_seller)
            self.model.agents[_id_buyer].wallet.settle_payment(trade_payment_buyer)

            # tokens to be burned according to McAfee budget imbalance
            self.model.auction.wallet.settle_revenue(clearing_inbalance)

        """ listing of all offers/bids selected for trade """
        if self.trade_pairs != [] and self.pricing_rule in ['pac', 'pab']:
            assert np.shape(self.trade_pairs)[1] is 4
            for trade in range(len(self.trade_pairs)):
                # data structure: [seller_id, buyer_id, trade_quantity, turnover]
                id_seller = self.trade_pairs[trade][0]
                id_buyer = self.trade_pairs[trade][1]
                trade_quantity = self.trade_pairs[trade][2]
                turnover = self.trade_pairs[trade][3]
                who_gets_what_bb(id_seller, id_buyer, trade_quantity, turnover)

        elif self.trade_pairs != [] and self.pricing_rule in ['mcafee']:
            # McAfee pricing settlement
            print(self.trade_pairs)
            try:
                # check whether trade_pairs elements contain 5 components
                # this will check in case the mcafee clearing is budget balanced
                assert np.shape(self.trade_pairs)[1] is 5
            except ValueError:
                # and this checks whether the 5th element is a list of two values
                # in case budget imbalanced; 5th element list are payments of both seller or buyer
                assert len(self.trade_pairs[0][4]) is 2

            for trade in range(len(self.trade_pairs)):
                id_seller = self.trade_pairs[trade][0]
                id_buyer = self.trade_pairs[trade][1]
                trade_quantity = self.trade_pairs[trade][2]
                budget_balanced = self.trade_pairs[trade][3]
                trade_payment = self.trade_pairs[trade][4]

                if budget_balanced is True:
                    # McAfee pricing settlement if budget balanced
                    # data structure: [seller_id, buyer_id, trade_quantity, budget_balanced, trade_payment]
                    assert np.shape(trade_payment) is ()
                    who_gets_what_bb(id_seller, id_buyer, trade_quantity, trade_payment)
                else:
                    # Mcafee pricing settlement if NOT budget balanced
                    # data structure: [seller_id, buyer_id, trade_quantity, budget_balanced, trade_payment_tuple]
                    assert len(trade_payment) is 2
                    who_gets_what_not_bb(id_seller, id_buyer, trade_quantity, trade_payment)

        else:
            auction_log.warning("Auction clearing did not result in trade at this interval")


        # Should happen inside the agent class
        """ resets the acquired energy for all households """
        for agent_id in self.model.agents:
            self.model.agents[agent_id].energy_trade_flux = 0
        # Should happen inside the agent class

    def user_participation(self):
        """ small analysis on user participation per step"""
        num_selling = 0
        num_buying = 0
        num_undefined = 0

        for agent_id in self.model.agents:
            if self.model.agents[agent_id].trading_state == 'supplying':
                num_selling += 1
            elif self.model.agents[agent_id].trading_state == 'buying':
                num_buying += 1
            else:
                num_undefined += 1
        total_num = num_selling + num_buying + num_undefined

        # assert total_num == self.model.data.num_households

        # TODO: translate this to percentage of households actually capable of selling or buying...
        # of course pure consumers will never be able to trade energy...
        self.percentage_sellers = num_selling / total_num
        self.percentage_buyers = num_buying / total_num
        self.percentage_passive = num_undefined / total_num

    def append_utility_offer(self, sorted_bid_list, sorted_offer_list):
        """ function is only called when an utility is present, it supplements the offer list of auctioneer
            with an 'infinite' supply of energy up to the necessary amount to cover all demand, bought or not """

        bid_total = sum(np.asarray(sorted_bid_list, dtype=object)[:, 1])

        try:
            prosumer_offer_total = sum(np.asarray(sorted_offer_list, dtype=object)[:, 1])
        except IndexError:
            prosumer_offer_total = 0
            auction_log.info("no prosumers in the grid supplying energy")

        """ Append utility"""
        total_offer_below_mmr = 0
        utility_id = self.model.agents['Utility'].id
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

        """ append utility to who_gets_what dictionary """
        self.who_gets_what_dict[utility_id] = []

        print(f"sorted offers: {sorted_offer_list}")
        print(f"sorted bid: {sorted_bid_list}")

        return sorted_bid_list, sorted_offer_list
