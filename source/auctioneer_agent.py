from source.auction_methods import *
from plots import clearing_snapshot

from mesa import Agent
import seaborn as sns

sns.set()
auction_log = logging.getLogger('auctioneer')


class Auctioneer(Agent):
    """ Pay as Clear auction market is created here"""
    def __init__(self, _unique_id, model):
        super().__init__(_unique_id, self)
        auction_log.info('auction of type %s created', _unique_id)
        self.model = model

        self.snapshot_plot = True
        self.id = _unique_id
        self.pricing_rule = 'pac'
        self.aggregate_demand_curve = []
        self.aggregate_supply_curve = []

        self.bid_list = []
        self.offer_list = []

        self.sorted_bid_list = None
        self.sorted_offer_list = None
        self.clearing_quantity = None
        self.clearing_price = None
        self.trade_pairs = None

    def auction_round(self):
        """check whether all agents have submitted their bids"""
        # TODO: measure that part of agents submitted bids?
        # TODO: how can we fix that agents can have direct communication, not through the microgrid as medium...
        """ resets the acquired energy for all households """
        for agent in self.model.agents[:]:
            self.model.agents[agent.id].sold_energy = None
            self.model.agents[agent.id].bought_energy = None

        """ sorts collected bids and offers """
        # TODO: when ALL supply falls (far) under demand price, all supply is of course matched by pricing rule??
        # I think this creates a bug, which I currently avoid by breaking the sequence. But should be fixed
        # source of the bug is at the sorting algorithm, should allow a clearing also when supply completely falls
        # BELOW demand curve

        self.sorted_bid_list, self.sorted_offer_list, sorted_x_y_y_pairs_list = self.sorting()
        self.execute_auction(sorted_x_y_y_pairs_list)
        self.clearing_of_market(self.trade_pairs)

    def execute_auction(self, sorted_x_y_y_pairs_list):
        """ auctioneer sets up the market and clears it according pricing rule """

        check_demand_supply(self.sorted_bid_list, self.sorted_offer_list)
        if len(self.sorted_bid_list) == 0 or len(self.sorted_offer_list) == 0:
            auction_log.warning("no trade at this step")

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

        if self.snapshot_plot:
            clearing_snapshot(self.clearing_quantity, self.clearing_price, sorted_x_y_y_pairs_list)

    def sorting(self):
        """sorts bids and offers into an aggregated demand/supply curve"""

        # sort on price, not quantity, so price_point[1]
        sorted_bid_list = sorted(self.bid_list, key=lambda price_point: price_point[1], reverse=True)
        sorted_offer_list = sorted(self.offer_list, key=lambda price_point: price_point[1])

        # creation of aggregate supply/demand points
        aggregate_quantity_points = []
        x_y_y_pairs_list = []
        x_bid_pairs_list = []
        x_supply_pairs_list = []

        prev = 0
        for i in range(len(sorted_bid_list)):
            aggregate_quantity_points.append(sorted_bid_list[i][0])
            aggregate_quantity_points[i] += prev
            prev = aggregate_quantity_points[i]

            x_bid_pairs_list.append([aggregate_quantity_points[i], sorted_bid_list[i][1], None,
                                    sorted_bid_list[i][2], None])
        prev = 0
        for j in range(len(sorted_offer_list)):
            aggregate_quantity_points.append(sorted_offer_list[j][0])
            aggregate_quantity_points[len(sorted_bid_list) + j] += prev
            prev = aggregate_quantity_points[len(sorted_bid_list) + j]

            x_supply_pairs_list.append([aggregate_quantity_points[len(sorted_bid_list) + j], None, sorted_offer_list[j][1],
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

        for i in range(len(sorted_x_y_y_pairs_list)):
            j = 1
            _offer_list_proxy = offer_list_proxy[i:]
            if not all(v is None for v in _offer_list_proxy):
                while sorted_x_y_y_pairs_list[i][2] is None:
                    if sorted_x_y_y_pairs_list[i+j][2] is not None:
                        sorted_x_y_y_pairs_list[i][2] = sorted_x_y_y_pairs_list[i+j][2]
                    else:
                        j += 1
            else:
                break

        for i in range(len(sorted_x_y_y_pairs_list)):
            j = 1
            _bid_list_proxy = bid_list_proxy[i:]

            if not all(v is None for v in _bid_list_proxy):
                while sorted_x_y_y_pairs_list[i][1] is None:
                    if sorted_x_y_y_pairs_list[i+j][1] is not None:
                        sorted_x_y_y_pairs_list[i][1] = sorted_x_y_y_pairs_list[i+j][1]
                    else:
                        j += 1
            else:
                break

        """filter out None values and save as quantity/price series for plotting"""
        for i in range(len(sorted_x_y_y_pairs_list)):
            if sorted_x_y_y_pairs_list[i][1] is None:
                sorted_x_y_y_pairs_list[i][1] = 0
            if sorted_x_y_y_pairs_list[i][2] is None:
                sorted_x_y_y_pairs_list[i][2] = 0

        return sorted_bid_list, sorted_offer_list, sorted_x_y_y_pairs_list

    def clearing_of_market(self, trade_pairs):
        """clears market """

        """ listing of all offers/bids selected for trade """
        if trade_pairs is not None:
            for trade in range(len(trade_pairs)):
                # data structure: [seller_id, buyer_id, trade_quantity, payment]
                id_seller = trade_pairs[trade][0]
                id_buyer = trade_pairs[trade][1]
                trade_quantity = trade_pairs[trade][2]
                payment = trade_pairs[trade][3]
                """ execute trade buy calling household agent's wallet settlement """

                self.model.agents[id_seller].sold_energy = trade_quantity
                self.model.agents[id_buyer].bought_energy = trade_quantity
                self.model.agents[id_seller].wallet.settle_revenue(payment)
                self.model.agents[id_buyer].wallet.settle_payment(payment)
        else:
            auction_log.warning("no trade at this step")

        """ clear lists for later use in next step """
        self.bid_list = []
        self.offer_list = []

