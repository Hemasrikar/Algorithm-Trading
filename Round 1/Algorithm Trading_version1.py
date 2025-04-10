from typing import List, Dict
from datamodel import Order, OrderDepth, TradingState, Symbol, Trade, Listing

POSITION_LIMITS = {
    "RAINFOREST_RESIN": 50,
    "KELP": 50,
    "SQUID_INK": 50,
}

class Trader:
    def __init__(self):
        self.price_history = {
            "RAINFOREST_RESIN": [],
            "KELP": [],
            "SQUID_INK": [],
        }

    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        result = {}

        for product in state.order_depths:
            orders: List[Order] = []
            order_depth: OrderDepth = state.order_depths[product]
            position = state.position.get(product, 0)
            history = self.price_history[product]

            # Get mid-price if possible
            if order_depth.buy_orders and order_depth.sell_orders:
                best_bid = max(order_depth.buy_orders.keys())
                best_ask = min(order_depth.sell_orders.keys())
                mid_price = (best_bid + best_ask) / 2
                history.append(mid_price)

                if len(history) > 100:
                    history.pop(0)
            else:
                continue  # Skip this product if no market data

            # === STRATEGY SELECTION === #
            if product == "RAINFOREST_RESIN":
                orders = self.mean_reversion_strategy(product, order_depth, position)
            elif product == "KELP":
                orders = self.momentum_strategy(product, order_depth, position)
            elif product == "SQUID_INK":
                orders = self.moving_average_crossover(product, order_depth, position)

            result[product] = orders

        return result

    def mean_reversion_strategy(self, product: Symbol, order_depth: OrderDepth, position: int) -> List[Order]:
        orders = []
        prices = self.price_history[product]
        if len(prices) < 10:
            return orders

        mean_price = sum(prices) / len(prices)
        best_ask = min(order_depth.sell_orders.keys(), default=None)
        best_bid = max(order_depth.buy_orders.keys(), default=None)

        if best_ask and best_ask < mean_price * 0.98 and position < POSITION_LIMITS[product]:
            buy_qty = min(POSITION_LIMITS[product] - position, order_depth.sell_orders[best_ask])
            orders.append(Order(product, best_ask, buy_qty))

        if best_bid and best_bid > mean_price * 1.02 and position > -POSITION_LIMITS[product]:
            sell_qty = min(position + POSITION_LIMITS[product], order_depth.buy_orders[best_bid])
            orders.append(Order(product, best_bid, -sell_qty))

        return orders

    def momentum_strategy(self, product: Symbol, order_depth: OrderDepth, position: int) -> List[Order]:
        orders = []
        prices = self.price_history[product]
        if len(prices) < 15:
            return orders

        recent = prices[-5:]
        prev = prices[-10:-5]
        best_ask = min(order_depth.sell_orders.keys(), default=None)
        best_bid = max(order_depth.buy_orders.keys(), default=None)

        if sum(recent) > sum(prev) and best_ask and position < POSITION_LIMITS[product]:
            buy_qty = min(POSITION_LIMITS[product] - position, order_depth.sell_orders[best_ask])
            orders.append(Order(product, best_ask, buy_qty))
        elif sum(recent) < sum(prev) and best_bid and position > -POSITION_LIMITS[product]:
            sell_qty = min(position + POSITION_LIMITS[product], order_depth.buy_orders[best_bid])
            orders.append(Order(product, best_bid, -sell_qty))

        return orders

    def moving_average_crossover(self, product: Symbol, order_depth: OrderDepth, position: int) -> List[Order]:
        orders = []
        prices = self.price_history[product]
        if len(prices) < 20:
            return orders

        short_avg = sum(prices[-5:]) / 5
        long_avg = sum(prices[-20:]) / 20
        best_ask = min(order_depth.sell_orders.keys(), default=None)
        best_bid = max(order_depth.buy_orders.keys(), default=None)

        if short_avg > long_avg and best_ask and position < POSITION_LIMITS[product]:
            buy_qty = min(POSITION_LIMITS[product] - position, order_depth.sell_orders[best_ask])
            orders.append(Order(product, best_ask, buy_qty))
        elif short_avg < long_avg and best_bid and position > -POSITION_LIMITS[product]:
            sell_qty = min(position + POSITION_LIMITS[product], order_depth.buy_orders[best_bid])
            orders.append(Order(product, best_bid, -sell_qty))

        return orders

