from typing import List, Dict
from datamodel import Order, OrderDepth, TradingState, Symbol

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

        for product, order_depth in state.order_depths.items():
            orders: List[Order] = []
            position = state.position.get(product, 0)
            history = self.price_history[product]

            if order_depth.buy_orders and order_depth.sell_orders:
                best_bid = max(order_depth.buy_orders)
                best_ask = min(order_depth.sell_orders)
                mid_price = (best_bid + best_ask) / 2
                history.append(mid_price)
                if len(history) > 200:
                    history.pop(0)
            else:
                continue

            # Run strategy
            if product == "RAINFOREST_RESIN":
                orders = self.improved_mean_reversion(product, order_depth, position)
            elif product == "KELP":
                orders = self.improved_momentum(product, order_depth, position)
            elif product == "SQUID_INK":
                orders = self.improved_moving_average_crossover(product, order_depth, position)

            result[product] = orders

        return result

    def improved_mean_reversion(self, product: Symbol, order_depth: OrderDepth, position: int) -> List[Order]:
        orders = []
        history = self.price_history[product]
        if len(history) < 20:
            return orders

        mean = sum(history[-20:]) / 20
        stddev = (sum((x - mean) ** 2 for x in history[-20:]) / 20) ** 0.5
        threshold = stddev * 0.75  # adaptive threshold

        best_bid = max(order_depth.buy_orders, default=None)
        best_ask = min(order_depth.sell_orders, default=None)

        if best_ask and best_ask < mean - threshold:
            qty = min(POSITION_LIMITS[product] - position, order_depth.sell_orders[best_ask])
            orders.append(Order(product, best_ask, qty))

        if best_bid and best_bid > mean + threshold:
            qty = min(position + POSITION_LIMITS[product], order_depth.buy_orders[best_bid])
            orders.append(Order(product, best_bid, -qty))

        return orders

    def improved_momentum(self, product: Symbol, order_depth: OrderDepth, position: int) -> List[Order]:
        orders = []
        history = self.price_history[product]
        if len(history) < 20:
            return orders

        short = sum(history[-5:]) / 5
        long = sum(history[-15:]) / 15
        momentum_strength = short - long

        best_bid = max(order_depth.buy_orders, default=None)
        best_ask = min(order_depth.sell_orders, default=None)

        if momentum_strength > 0.5 and best_ask:
            size = int(min(POSITION_LIMITS[product] - position, order_depth.sell_orders[best_ask]) * (momentum_strength / 2))
            if size > 0:
                orders.append(Order(product, best_ask, size))

        elif momentum_strength < -0.5 and best_bid:
            size = int(min(position + POSITION_LIMITS[product], order_depth.buy_orders[best_bid]) * (-momentum_strength / 2))
            if size > 0:
                orders.append(Order(product, best_bid, -size))

        return orders

    def improved_moving_average_crossover(self, product: Symbol, order_depth: OrderDepth, position: int) -> List[Order]:
        orders = []
        history = self.price_history[product]
        if len(history) < 30:
            return orders

        short = sum(history[-5:]) / 5
        medium = sum(history[-10:]) / 10
        long = sum(history[-20:]) / 20

        best_bid = max(order_depth.buy_orders, default=None)
        best_ask = min(order_depth.sell_orders, default=None)

        # Buy signal if trend upward across all
        if short > medium > long and best_ask:
            qty = min(POSITION_LIMITS[product] - position, order_depth.sell_orders[best_ask])
            orders.append(Order(product, best_ask, qty))
        elif short < medium < long and best_bid:
            qty = min(position + POSITION_LIMITS[product], order_depth.buy_orders[best_bid])
            orders.append(Order(product, best_bid, -qty))

        return orders
