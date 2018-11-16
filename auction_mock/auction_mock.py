from source.auctioneer_agent import Auctioneer
from source.microgrid_environment import MicroGrid
from source.auctioneer_methods import pac_pricing, pab_pricing
mock_id = 'test auction'
mock_model = MicroGrid()
mock_auctioneer = Auctioneer(mock_id, mock_model)
mock_auctioneer.model.utility = None

# [bid price, quantity, id]
mock_auctioneer.bid_list = [
    [50, 1, 0],
    [54, 2, 10],
    [55, 2, 20]
]

# [offer price, quantity, id]
mock_auctioneer.offer_list = [
    [39, 6, 30],
    [51, 1, 40]
]

sorted_bid_list, sorted_offer_list, sorted_x_x_y_pairs_list = mock_auctioneer.sorting()
print(sorted_bid_list)
print(sorted_offer_list)
print(sorted_x_x_y_pairs_list)

""" PAC pricing test"""
# clearing_quantity, clearing_price, total_turnover, trade_pairs =\
#     pac_pricing(sorted_x_x_y_pairs_list,
#                 sorted_bid_list,
#                 sorted_offer_list)

""" PAB pricing test"""
clearing_quantity, clearing_price, total_turnover, trade_pairs =\
    pab_pricing(sorted_x_x_y_pairs_list,
                sorted_bid_list,
                sorted_offer_list)

print(clearing_quantity)
print(clearing_price)
print(total_turnover)
print(trade_pairs)