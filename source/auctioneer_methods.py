import logging
import numpy as np
method_logger = logging.getLogger('run_microgrid.methods')


def check_demand_supply(sorted_bid_list_, sorted_offer_list_):
    if len(sorted_bid_list_) is not 0:
        total_demand_ = np.sum([x[0] for x in sorted_bid_list_])
    else:
        total_demand_ = 0
    if len(sorted_offer_list_) is not 0:
        total_supply_ = np.sum([x[0] for x in sorted_offer_list_])
    else:
        total_supply_ = 0

    if total_demand_ >= total_supply_:
        method_logger.info('more supply than demand')
    else:
        method_logger.info('more demand than supply')
    return total_demand_, total_supply_


def pac_pricing(sorted_x_y_y_pairs_list_, sorted_bid_list, sorted_offer_list):
    """ trade matching according pay-as-clear pricing rule """
    clearing_quantity, clearing_price = clearing_quantity_calc(sorted_x_y_y_pairs_list_)
    """ some checks """
    if clearing_quantity is None or clearing_price is None:
        method_logger.warning("No clearing quantity or price was found")
        return clearing_quantity, clearing_price, None, None

    total_turnover_ = clearing_quantity * clearing_price
    print("clearing price", clearing_price)
    print("clearing quantity", clearing_quantity)
    # assert total_turnover_ > 0 and clearing_quantity > 0

    trade_pairs_pac_ = []
    matched_quantity = 0
    filled = False

    num_suppliers = len(sorted_offer_list)
    """ start at first supplier """
    supplier = 0
    available_supply_of_selected_seller = sorted_offer_list[supplier][1]
    seller_id = sorted_offer_list[supplier][2]

    method_logger.info('starting market matching, according to Pay-As-Clear')
    while not filled:
        # TODO: test this, also regarding the backwards / forwards issue.
        for i in range(len(sorted_bid_list)):
            buyer_id = sorted_bid_list[i][2]
            to_be_matched_quantity = sorted_bid_list[i][1]
            if matched_quantity + to_be_matched_quantity > clearing_quantity:
                to_be_matched_quantity_filler = clearing_quantity - matched_quantity
                to_be_matched_quantity = to_be_matched_quantity_filler

            while to_be_matched_quantity > 0:
                """ Two cases: either supplier has enough supply for buyer's demand,
                    or buyer has more demand then supplier's supply """
                if available_supply_of_selected_seller > to_be_matched_quantity:
                    """ Case 1: supplier has enough supply to selected buyer, thus update to next buyer """
                    trade_quantity = to_be_matched_quantity
                    payment = trade_quantity * clearing_price

                    available_supply_of_selected_seller -= trade_quantity
                    to_be_matched_quantity -= trade_quantity

                    trade_pairs_pac_.append([seller_id, buyer_id, trade_quantity, payment])
                    matched_quantity += trade_quantity

                elif available_supply_of_selected_seller <= to_be_matched_quantity:
                    """ Case 1: supplier does not have enough supply to selected buyer, thus update to next seller """
                    trade_quantity = available_supply_of_selected_seller
                    payment = trade_quantity * clearing_price

                    available_supply_of_selected_seller -= trade_quantity
                    to_be_matched_quantity -= trade_quantity

                    trade_pairs_pac_.append([seller_id, buyer_id, trade_quantity, payment])
                    matched_quantity += trade_quantity

                    """ Update to next supplier in line, but only if there is still a supplier next in line... """
                    if supplier < num_suppliers - 1:
                        try:
                            available_supply_of_selected_seller = sorted_offer_list[supplier][0]
                        except IndexError:
                            method_logger.error('IndexError somehow')
                        seller_id = sorted_offer_list[supplier][2]
                        supplier += 1
                    else:
                        break

                if matched_quantity >= clearing_quantity:
                    filled = True
                    break

    total_turnover_trade_pairs = np.sum(x[3] for x in trade_pairs_pac_)
    assert matched_quantity == clearing_quantity
    assert total_turnover_trade_pairs - 0.01 <= total_turnover_ <= total_turnover_trade_pairs + 0.01

    method_logger.info('finished matching winning bids and offers')
    return clearing_quantity, clearing_price, total_turnover_, trade_pairs_pac_


def pab_pricing(sorted_x_y_y_pairs_list_, sorted_bid_list, sorted_offer_list):
    """ trade matching according pay-as-bid pricing rule """

    clearing_quantity, clearing_price = clearing_quantity_calc(sorted_x_y_y_pairs_list_)

    trade_pairs_pab_ = None
    total_turnover_ = None
    """ this function should return a pairing of bids and offers for determined prices"""

    return clearing_quantity, total_turnover_, trade_pairs_pab_


def clearing_quantity_calc(sorted_x_y_y_pairs_list):
    """ This can be used both for PaC as for PaB, returns clearing quantity and uniform clearing price"""
    clearing_quantity_ = None
    clearing_price_ = None

    # now I make range(len(sorted_x_y_y_pairs_list)-1), -1 because of the forwards-step bug (see TODO_above)
    # TODO: make sure the steps are set from previous q (or 0) until announced quantity. It should be backwards.
    for i in range(len(sorted_x_y_y_pairs_list) - 1):
        """ if bid is still higher than offer, then save it as potential clearing quantity and next "losing?" bid
            as clearing price"""
        # TODO: this is very ugly... alas, everything around here is ugly
        if sorted_x_y_y_pairs_list[i][1] < sorted_x_y_y_pairs_list[i][2]:
            clearing_price_ = sorted_x_y_y_pairs_list[i][0]
            clearing_quantity_ = sorted_x_y_y_pairs_list[i - 1][1]
            break

    return clearing_quantity_, clearing_price_
