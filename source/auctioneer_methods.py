import logging
import numpy as np
import pdb
method_logger = logging.getLogger('run_microgrid.methods')


def check_demand_supply(sorted_bid_list_, sorted_offer_list_):

    if len(sorted_bid_list_) is not 0:

        total_demand_ = np.sum([x[1] for x in sorted_bid_list_])
    else:
        total_demand_ = 0
    if len(sorted_offer_list_) is not 0:
        total_supply_ = np.sum([x[1] for x in sorted_offer_list_])
    else:
        total_supply_ = 0

    if total_demand_ >= total_supply_:
        method_logger.info('more supply than demand')
    else:
        method_logger.info('more demand than supply')
    return total_demand_, total_supply_


def pac_pricing(sorted_x_y_y_pairs_list_, sorted_bid_list, sorted_offer_list):
    """ trade matching according pay-as-clear pricing rule """
    clearing_quantity, clearing_price, breakeven_index_k = clearing_quantity_calc(sorted_x_y_y_pairs_list_)
    # Give some feedback to the found clearing price and quantity.
    print('~~~\nclearing calculated. Clearing price: {} EUR/kWh; clearing quantity: {} kWh.\n~~~'.format(
        clearing_price, clearing_quantity))
    """ some checks """
    trade_pairs_pac_ = []
    total_turnover_ = 0

    if clearing_quantity is None:
        method_logger.warning("No clearing quantity or price was found")
        return clearing_quantity, clearing_price, None, None

    # filter only on executed segments that have no Non types (meaning) bid/offer but not offer/bid
    # first check if None, if not, check whether under clearing quantity
    executed_segment = [segment for segment in sorted_x_y_y_pairs_list_ if segment[0] is not None
                        and segment[0] <= clearing_quantity]

    total_turnover_ = clearing_quantity * clearing_price
    assert total_turnover_ >= 0 and clearing_quantity >= 0

    total_turnover_internally = 0
    clearing_quantity_internally = 0
    trade_pairs = []
    prev_segment_quantity = 0
    for segment in executed_segment:
        # reading out values from the executed trade segments
        trade_quantity = segment[0] - prev_segment_quantity
        clearing_quantity_internally += trade_quantity
        buyer_price = segment[1]
        seller_price = segment[2]
        buyer_id = segment[3]
        seller_id = segment[4]

        """ Open to market design matching algorithm """
        trade_payment = trade_quantity * clearing_price
        # set up trade pairs
        trade_pair = [seller_id, buyer_id, trade_quantity, trade_payment]
        if trade_pair[1] is None or trade_pair[2] == 0:
            continue

        trade_pairs_pac_.append(trade_pair)
        # finalise
        total_turnover_internally += trade_payment
        prev_segment_quantity = segment[0]

    # this is me having fun I am sorry
    try:
        assert total_turnover_internally == total_turnover_
    except AssertionError:
        print(executed_segment)
        print(clearing_quantity)
        print(clearing_quantity_internally)
        print(total_turnover_internally)
        print(total_turnover_)
        if abs(total_turnover_ - total_turnover_internally) < 0.001:
            pass
        else:
            assert total_turnover_internally == total_turnover_

    for trade in trade_pairs_pac_:
        if any(element is None for element in trade):
            exit('weird stuff is happening')

    method_logger.info('finished matching winning bids and offers')
    return clearing_quantity, clearing_price, total_turnover_, trade_pairs_pac_


def pab_pricing(sorted_x_y_y_pairs_list, sorted_bid_list, sorted_offer_list):
    """ trade matching according pay-as-bid pricing rule """
    clearing_quantity, clearing_price, breakeven_index_k = clearing_quantity_calc(sorted_x_y_y_pairs_list)

    if clearing_quantity is None:
        return clearing_quantity, clearing_price, None, None

    trade_pairs_pab_ = []
    total_turnover_ = 0

    # filter only on executed segments that have no Non types (meaning) bid/offer but not offer/bid
    # first check if None, if not, check whether under clearing quantity
    executed_segment = [segment for segment in sorted_x_y_y_pairs_list if segment[0] is not None
                        and segment[0] <= clearing_quantity]
    """ this function should return a pairing of bids and offers for determined prices"""
    trade_pairs = []
    prev_segment_quantity = 0
    for segment in executed_segment:
        # reading out values from the executed trade segments
        trade_quantity = segment[0] - prev_segment_quantity

        buyer_price = segment[1]
        seller_price = segment[2]
        buyer_id = segment[3]
        seller_id = segment[4]

        """ Open to market design matching algorithm """
        trade_payment = trade_quantity * buyer_price
        # set up trade pairs
        trade_pair = [seller_id, buyer_id, trade_quantity, trade_payment]
        trade_pairs_pab_.append(trade_pair)
        # finalise
        total_turnover_ += trade_payment
        prev_segment_quantity = trade_quantity

    average_clearing_price = total_turnover_ / clearing_quantity
    # lumping together reduces transparency since prices per trade deal are different, so this is omitted here
    return clearing_quantity, average_clearing_price, total_turnover_, trade_pairs_pab_


def mcafee_pricing(sorted_x_y_y_pairs_list):

    # # TEST sorted_x_y_y_pairs_list #
    # # [volume, bid price, offer price, buyer, seller]
    # sorted_x_y_y_pairs_list = \
    #     [
    #         [1.1, 10, 1, 0, 'Utility'],
    #         [1.2, 9, 2, 1, 'Utility'],
    #         [1.3, 9, 2, 0, 'Utility'],
    #         [1.4, 3, 8, 1, 'Utility']
    #     ]

    clearing_quantity, clearing_price, k = clearing_quantity_calc(sorted_x_y_y_pairs_list)

    if clearing_quantity is None:
        return clearing_quantity, clearing_price, None, None

    # k is break even bid/offer index, translated to list index (which starts at 0)
    # problem is what if there is no k+1 buyer/seller
    bid_k = sorted_x_y_y_pairs_list[k][1]
    offer_k = sorted_x_y_y_pairs_list[k][2]

    # dealing with boundary condition; what if there is no k+1 trading pair (boundary at the right)
    try:
        bid_next = sorted_x_y_y_pairs_list[k + 1][1]
    except IndexError:
        bid_next = None
    try:
        offer_next = sorted_x_y_y_pairs_list[k + 1][2]
    except IndexError:
        offer_next = None

    if bid_next is not None and offer_next is not None:
        p_0 = (bid_next + offer_next) / 2
    else:
        print(sorted_x_y_y_pairs_list)
        # omit trading pair k?
        k = k - 1
        # then; recalculate bid_k, offer_k, bid_next, offer_next and p_0 = (bid_next + offer_next) / 2
        bid_next = sorted_x_y_y_pairs_list[k + 1][1]
        offer_next = sorted_x_y_y_pairs_list[k + 1][2]
        bid_k = sorted_x_y_y_pairs_list[k][1]
        offer_k = sorted_x_y_y_pairs_list[k][2]
        p_0 = (bid_next + offer_next) / 2
        # TODO: and what if it hits the boundary at the left? What if there is only 1 bid/offer pair?
        # exit("no idea what to do here yet...")

    if offer_k <= p_0 <= bid_k:
        """ all first k trades will be executed for clearing price p_0"""
        clearing_index = k
        clearing_price = p_0
        buget_balanced = True

        total_turnover_ = 0

        # filter only on executed segments that have no Non types (meaning) bid/offer but not offer/bid
        # first check if None, if not, check whether under clearing quantity
        executed_segment = sorted_x_y_y_pairs_list[0:k+1]

        trade_pairs_mcafee_ = []
        prev_segment_quantity = 0
        for segment in executed_segment:
            # reading out values from the executed trade segments
            trade_quantity = segment[0] - prev_segment_quantity
            buyer_id = segment[3]
            seller_id = segment[4]

            """ Open to market design matching algorithm """
            trade_payment = trade_quantity * clearing_price
            # set up trade pairs
            trade_pair = [seller_id, buyer_id, trade_quantity, buget_balanced, trade_payment]
            trade_pairs_mcafee_.append(trade_pair)
            # finalise
            total_turnover_ += trade_payment
            prev_segment_quantity = trade_quantity
    else:
        """ all first k-1 trades will be executed for selling price :offer_k: and buying price :bid_k: """
        clearing_sell_price = offer_k
        clearing_buy_price = bid_k
        buget_balanced = False
        """ all first k-1 trades will be executed for sell price of offer_k and buy price of bid_k """
        total_turnover_ = 0
        total_imbalance = 0
        total_paid_to_sellers = 0
        # filter only on executed segments that have no Non types (meaning) bid/offer but not offer/bid
        # first check if None, if not, check whether under clearing quantity
        # since p_0 is outside of range, trade k is kicked, thus executed_segment slice is 1 trade smaller.
        executed_segment = sorted_x_y_y_pairs_list[0:k]

        trade_pairs_mcafee_ = []
        prev_segment_quantity = 0
        for segment in executed_segment:
            # reading out values from the executed trade segments
            trade_quantity = segment[0] - prev_segment_quantity
            buyer_id = segment[3]
            seller_id = segment[4]

            """ Open to market design matching algorithm """
            trade_revenue_seller = trade_quantity * clearing_sell_price
            trade_payment_buyer = trade_quantity * clearing_buy_price
            # set up trade pairs
            trade_pair = [seller_id, buyer_id, trade_quantity, buget_balanced, [trade_revenue_seller, trade_payment_buyer]]
            trade_pairs_mcafee_.append(trade_pair)
            # finalise
            total_turnover_ += trade_payment_buyer
            total_imbalance += trade_payment_buyer - trade_revenue_seller
            total_paid_to_sellers += trade_revenue_seller
            try:
                assert total_turnover_ == total_imbalance + total_paid_to_sellers
            except AssertionError:
                raise AssertionError
            prev_segment_quantity = trade_quantity

    # TODO: mcafee_trade_efficiency: all trades that are kicked / execution below full market efficiency

    return clearing_quantity, clearing_price, total_turnover_, trade_pairs_mcafee_


def clearing_quantity_calc(sorted_x_y_y_pairs_list):
    """ This can be used both for PaC as for PaB, returns clearing quantity and uniform clearing price"""
    clearing_quantity_ = None
    clearing_price_ = None
    break_even_index = None

    """ filter out None values and remove these points for they don't add information """
    # for i in range(len(sorted_x_y_y_pairs_list)):
    #     if sorted_x_y_y_pairs_list[-i][1] is None or sorted_x_y_y_pairs_list[-i][2] is None

    assert sorted_x_y_y_pairs_list is not []
    sorted_x_y_y_pairs_list = [segment for segment in sorted_x_y_y_pairs_list if segment[1] is not None
                               and segment[2] is not None]

    list_of_volumes = [sorted_x_y_y_pairs_list[volume][0] for volume in range(len(sorted_x_y_y_pairs_list))]

    # fully execute: all bid prices are higher than offer prices
    if all(sorted_x_y_y_pairs_list[i][1] >= sorted_x_y_y_pairs_list[i][2] for i in range(len(sorted_x_y_y_pairs_list))):
        # clearing quantity is simply last quantity point of aggregate demand and supply curve
        break_even_index = len(sorted_x_y_y_pairs_list) - 1

        clearing_quantity_ = sum(list_of_volumes[0:break_even_index+1])
        # highest winning bid is simply last price point of aggregate demand curve
        clearing_price_ = sorted_x_y_y_pairs_list[-1][1]
        method_logger.info('fully executed')

    # execute nothing: all bids prices are lower than offer prices
    elif all(sorted_x_y_y_pairs_list[i][1] < sorted_x_y_y_pairs_list[i][2] for i in range(len(sorted_x_y_y_pairs_list))):
        clearing_quantity_ = None
        clearing_price_ = None
        break_even_index = None
        method_logger.info('nothing executed')

    # execute partially: some bids prices are lower than some offer prices
    else:
        # search for the first point in sorted_x_x_y_pairs_list where the bid price is lower than the offer price.
        # this will be the point where clearing quantity depends on
        for i in range(len(sorted_x_y_y_pairs_list)):
            # if bid is still higher than offer, then save it as potential clearing quantity and next "losing?" bid
            # as clearing price
            if sorted_x_y_y_pairs_list[i][1] < sorted_x_y_y_pairs_list[i][2]:
                break_even_index = i - 1
                # clearing price is defined as the highest winning bid, sorted_x_x_y_pairs_list[i][1]
                clearing_quantity_ = sum(list_of_volumes[0:break_even_index + 1])
                # WHY IS HERE THE PRICE USED FROM THE BID?? THIS WILL LEAD TO A HIGHER CLEARING PRICE
                clearing_price_ = sorted_x_y_y_pairs_list[i - 1][1]
                # ALTERNATIVELY HERE THE COSTS OF THE OFFER ARE USED!!
                # clearing_price_ = sorted_x_y_y_pairs_list[i - 1][2]
                method_logger.info('partially executed')
                break

    # sorted_x_y_y_pairs_list: [volume, bid price, offer price, buyer, seller]
    return clearing_quantity_, clearing_price_, break_even_index
