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

        self.snapshot_plot = False
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

        self.percentage_sellers = None
        self.percentage_buyers = None
        self.percentage_passive = None

    def auction_round(self):
        """check whether all agents have submitted their bids"""
        self.user_participation()

        """ resets the acquired energy for all households """
        for agent in self.model.agents[:]:
            self.model.agents[agent.id].sold_energy = 0
            self.model.agents[agent.id].bought_energy = 0

        if self.offer_list != [] and self.bid_list != []:
            self.sorted_bid_list, self.sorted_offer_list, sorted_x_y_y_pairs_list = self.sorting()
            self.execute_auction(sorted_x_y_y_pairs_list)
            self.clearing_of_market(self.trade_pairs)

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

        if self.snapshot_plot:
            clearing_snapshot(self.clearing_quantity, self.clearing_price, sorted_x_y_y_pairs_list)

        print('trade pairs', self.trade_pairs)

        # TODO: save "clearing_quantity, clearing_price, sorted_x_y_y_pairs_list" in an export file, to plots afterwards

    def sorting(self):
        """sorts bids and offers into an aggregated demand/supply curve"""

        # TODO: when ALL supply falls (far) under demand price, all supply is of course matched by pricing rule??
        # this creates a bug, which I currently avoid by breaking the sequence. But should be fixed
        # source of the bug is at the sorting algorithm, should allow a clearing also when supply completely falls
        # BELOW demand curve

        # sort on price, not quantity, so price_point[1]
        # print("offers", self.offer_list)
        # print("bids", self.bid_list)
        sorted_bid_list = sorted(self.bid_list, key=lambda price_point: price_point[0], reverse=True)
        sorted_offer_list = sorted(self.offer_list, key=lambda price_point: price_point[0])

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
        for agent in self.model.agents[:]:
            self.model.agents[agent.id].sold_energy = 0
            self.model.agents[agent.id].bought_energy = 0

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

        print("trade pairs", trade_pairs)

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
        assert total_num == self.model.data.num_households

        # TODO: translate this to percentage of households actually capable of selling or buying...
        # of course pure consumers will never be able to trade energy...
        self.percentage_sellers = num_selling / total_num
        self.percentage_buyers = num_buying / total_num
        self.percentage_passive = num_passive / total_num

        # print(self.percentage_sellers, self.percentage_buyers, self.percentage_passive)
