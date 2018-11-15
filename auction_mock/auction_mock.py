from source.auctioneer_agent import Auctioneer
from source.microgrid_environment import MicroGrid
from source.auctioneer_methods import pac_pricing
mock_id = 'test auction'
mock_model = MicroGrid()
mock_auctioneer = Auctioneer(mock_id, mock_model)
mock_auctioneer.model.utility = None

# [bid price, quantity, id]
mock_auctioneer.bid_list = [
    [60, 1, 0],
    [40, 2, 1]
]

# [offer price, quantity, id]
mock_auctioneer.offer_list = [
    [39, 2, 2],
    [51, 1, 3]
]

sorted_bid_list, sorted_offer_list, sorted_x_x_y_pairs_list = mock_auctioneer.sorting()
print(sorted_bid_list)
print(sorted_offer_list)
print(sorted_x_x_y_pairs_list)

clearing_quantity, clearing_price, total_turnover, trade_pairs =\
    pac_pricing(sorted_x_x_y_pairs_list,
                sorted_bid_list,
                sorted_offer_list)

print(clearing_quantity)
print(clearing_price)
print(total_turnover)
print(trade_pairs)