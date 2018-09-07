from mesa import Agent
import seaborn as sns
import numpy as np
import logging
from plots import clearing_snapshot
sns.set()
auction_log = logging.getLogger('auctioneer')


class Auctioneer(Agent):
    """ Pay as Clear auction market is created here"""
    def __init__(self, _unique_id, _microgrid):
        auction_log.info('auction of type %s created', _unique_id)
        super().__init__(_unique_id, _microgrid)
        self.snapshot_plot = True
        self.id = _unique_id
        self.microgrid = _microgrid
        self.pricing_rule = 'pac'
        self.aggregate_demand_curve = []
        self.aggregate_supply_curve = []

        self.list_of_bids = []
        self.list_of_offers = []

        self.clearing_quantity = None
        self.clearing_price = None

    # def listing_of_offers(self, microgrid):
    #     """creates a list of all offers by creating a discrete aggregate supply curve"""
    #     # TODO: here, the auctioneer should visit each agent directly instead of pulling offers from environments
    #     for agent in microgrid.agents[:]:
    #         if agent is "supplier":
    #             self.list_of_offers.append(self, agent.offer)
    #         else:
    #             pass
    #
    # def listing_of_bids(self, microgrid):
    #     """creates a list of all bids by creating a discrete aggregate demand curve"""
    #     for agent in microgrid.agents[:]:
    #         if agent is "supplier":
    #             self.list_of_bids.append(agent.bid)
    #         else:
    #             pass
    #     print(self.list_of_bids)

    # @staticmethod
    # def sorting(list_of_bids, list_of_offers):
    #     """sorts bids and offers into an aggregated demand/supply curve"""
    #     sorted_bid_list = sorted(list_of_bids, key=lambda price_point: price_point[1])
    #     sorted_offer_list = sorted(list_of_offers, key=lambda price_point: price_point[1])
    #
    #
    #     return sorted_bid_list, sorted_offer_list

    def sorting(self):
        """sorts bids and offers into an aggregated demand/supply curve"""

        # TODO: inherently link bids/offers with agents id
        # sort on price, not quantity, so price_point[1]
        sorted_bid_list = sorted(self.list_of_bids, key=lambda price_point: price_point[1], reverse=True)
        sorted_offer_list = sorted(self.list_of_offers, key=lambda price_point: price_point[1])

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

            x_bid_pairs_list.append([aggregate_quantity_points[i], sorted_bid_list[i][1], None])
        prev = 0
        for j in range(len(sorted_offer_list)):
            aggregate_quantity_points.append(sorted_offer_list[j][0])
            aggregate_quantity_points[len(sorted_bid_list) + j] += prev
            prev = aggregate_quantity_points[len(sorted_bid_list) + j]

            x_supply_pairs_list.append([aggregate_quantity_points[len(sorted_bid_list) + j], None, sorted_offer_list[j][1]])

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
        # stupid comprehension proxy stop here

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

        x_quantities = []
        y_bid_prices = []
        y_offer_prices = []

        # print("")
        # for i in sorted_x_y_y_pairs_list:
        #     print(i)
        # print("")

        """filter out None values and save as quantity/price series for plotting"""
        for i in range(len(sorted_x_y_y_pairs_list)):
            if sorted_x_y_y_pairs_list[i][1] is None:
                sorted_x_y_y_pairs_list[i][1] = 0
            if sorted_x_y_y_pairs_list[i][2] is None:
                sorted_x_y_y_pairs_list[i][2] = 0
            x_quantities.append(sorted_x_y_y_pairs_list[i][0])
            y_bid_prices.append(sorted_x_y_y_pairs_list[i][1])
            y_offer_prices.append(sorted_x_y_y_pairs_list[i][2])

        return sorted_bid_list, sorted_offer_list, sorted_x_y_y_pairs_list, x_quantities, y_bid_prices, y_offer_prices

    def pay_as_clear_pricing(self, sorted_x_y_y_pairs_list):
        """ pay-as-clear pricing rule """
        # TODO: make sure the steps are set from previous q (or 0) until announced quantity. It should be backwards.
        # now I make range(len(sorted_x_y_y_pairs_list)-1), -1 because of the forwards-step bug (see TODO_above)
        for i in range(len(sorted_x_y_y_pairs_list) - 1):
            """ if bid is still higher than offer, then save it as potential clearing quantity and next "losing?" bid
                as clearing price"""
            # TODO: this is very ugly... alas, everything around here is ugly
            if sorted_x_y_y_pairs_list[i][1] < sorted_x_y_y_pairs_list[i][2]:
                clearing_quantity = sorted_x_y_y_pairs_list[i - 1][0]
                clearing_price = sorted_x_y_y_pairs_list[i][1]
                print(i)
                break
        auction_log.info(clearing_quantity, clearing_price)

        return clearing_quantity, clearing_price,

    @staticmethod
    def pay_as_bid_pricing(self):
        """ pay-as-bid pricing rule """

    def auction_setup(self):
        """ auctioneer sets up the market and clears it according pricing rule """

        """ sorts collected bids and offers """
        # sorted_"kind"_list[agent][quantity/price]
        sorted_bid_list, sorted_offer_list, sorted_x_y_y_pairs_list, quantities, bid_prices, offer_prices = \
            self.sorting()

        """ picks pricing rule """
        if self.pricing_rule == 'pab':
            self.clearing_quantity = None
            self.clearing_price = None
            pass

        elif self.pricing_rule == 'pac':
            self.clearing_quantity, self.clearing_price = self.pay_as_clear_pricing(sorted_x_y_y_pairs_list)
            """ intermediate plot of cleared market? """
            if self.snapshot_plot:
                clearing_snapshot(self.clearing_quantity, self.clearing_price, quantities, bid_prices, offer_prices)

        """make a similar aggregated bid/offer list"""
        if self.id == 'pay_as_clear':
            if len(sorted_bid_list) is not 0:
                total_demand = np.sum(sorted_bid_list, axis=0)[0]
            else:
                total_demand = 0

            if len(sorted_offer_list) is not 0:
                total_supply = np.sum(sorted_offer_list, axis=0)[0]
            else:
                total_supply = 0

            if total_demand >= total_supply:
                """more demand than supply"""
                # checks, until supply is gone, if an intersection exist
                # allocation_to_buyer = np.zeros(sorted_bid_list)

            else:
                """more supply than demand"""
                # checks, until demand is gone, if an intersection exist
                for i in range(len(sorted_bid_list)):
                    # if sorted_bid_list[i] >= sorted_offer_list:
                    # allocation_to_buyer[i] = sorted_bid_list[i]
                    pass

    def clearing_of_market(self):
        """clears market """

    def auction_round(self, _bid_list, _offer_list):
        """check whether all agents have submitted their bids"""
        # TODO: how can we fix that agents can have direct communication, not through the microgrid as medium...
        # self.listing_of_offers(_offer_list)
        # self.listing_of_bids(_bid_list)
        self.list_of_offers = _offer_list
        self.list_of_bids = _bid_list
        self.auction_setup()





