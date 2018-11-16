from source.auctioneer_agent import Auctioneer
from source.microgrid_environment import MicroGrid
from source.auctioneer_methods import pac_pricing, pab_pricing
mock_id = 'test auction'
mock_model = MicroGrid()
mock_auctioneer = Auctioneer(mock_id, mock_model)
mock_auctioneer.model.utility = None

execution = 'complete'
# execution = 'partial'
# execution = 'none'

execution_list = ['complete', 'partial', 'none']

def run_test(_execution):

    if execution == 'complete':
        mock_auctioneer.bid_list = [
            [54, 1, 'buyer 1'],
            [53, 2, 'buyer 2'],
            [53, 2, 'buyer 3']
        ]

        # [offer price, quantity, id]
        mock_auctioneer.offer_list = [
            [39, 6, 'seller 1'],
            [51, 1, 'seller 2']
        ]
        # assert all bids are higher than highest offer
        try:
            assert min(bid[0] for bid in mock_auctioneer.bid_list) > max(offer[0] for offer in mock_auctioneer.offer_list)
        except AssertionError:
            exit("This bid / offer config will not result in a auction that is completely is executed")

    if execution == 'partial':
        mock_auctioneer.bid_list = [
            [54, 1, 'buyer 1'],
            [53, 2, 'buyer 2'],
            [38, 2, 'buyer 3']
        ]

        # [offer price, quantity, id]
        mock_auctioneer.offer_list = [
            [39, 6, 'seller 1'],
            [51, 1, 'seller 2']
        ]

        # assert some bids are higher than highest offer
        try:
            assert max(bid[0] for bid in mock_auctioneer.bid_list) > min(offer[0] for offer in mock_auctioneer.offer_list)
            assert min(bid[0] for bid in mock_auctioneer.bid_list) < min(offer[0] for offer in mock_auctioneer.offer_list)
        except AssertionError:
            exit("This bid / offer config will not result in a auction that is partially is executed")

    if execution == 'none':
        mock_auctioneer.bid_list = [
            [30, 1, 'buyer 1'],
            [31, 2, 'buyer 2'],
            [32, 2, 'buyer 3']
        ]

        # [offer price, quantity, id]
        mock_auctioneer.offer_list = [
            [39, 6, 'seller 1'],
            [51, 1, 'seller 2']
        ]

        try:
            assert max(bid[0] for bid in mock_auctioneer.bid_list) < min(offer[0] for offer in mock_auctioneer.offer_list)
        except AssertionError:
            exit("This bid / offer config will not result in a auction where nothing is executed")

    sorted_bid_list, sorted_offer_list, sorted_x_x_y_pairs_list = mock_auctioneer.sorting()

    """ PAC pricing test"""
    clearing_quantity, clearing_price, total_turnover, trade_pairs =\
        pac_pricing(sorted_x_x_y_pairs_list,
                    sorted_bid_list,
                    sorted_offer_list)

    print('PAY AS CLEAR')
    print('clearing_quantity ', clearing_quantity)
    print('clearing_price ', clearing_price)
    print('total_turnover ', total_turnover)
    print('trade_pairs ', trade_pairs)
    print(' ')
    """ PAB pricing test"""
    clearing_quantity, clearing_price, total_turnover, trade_pairs =\
        pab_pricing(sorted_x_x_y_pairs_list,
                    sorted_bid_list,
                    sorted_offer_list)
    print('PAY AS BID')
    print('clearing_quantity ', clearing_quantity)
    print('clearing_price ', clearing_price)
    print('total_turnover ', total_turnover)
    print('trade_pairs ', trade_pairs)


run_test('none')


for execution in execution_list:
    run_test(execution)


