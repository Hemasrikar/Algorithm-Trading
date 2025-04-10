from typing import Dict, List
from datamodel import Order, OrderDepth, TradingState
import jsonpickle

POSITION_LIMITS = {
    "RAINFOREST_RESIN": 50,
    "KELP": 50,
    "SQUID_INK": 50,
}

class Trader:
    def run(self, state: TradingState):
        result = {}
        conversions = 0

        # Load persistent data
        if state.traderData:
            memory = jsonpickle.decode(state.traderData)
        else:
            memory = {"price_history": {symbol: [] for symbol in POSITION_LIMITS}}

        price_history = memory["price_history"]

        for product, order_depth in state.order_depths.items():
            orders: List[Order] = []
            position = state.position.get(product, 0)

            # Calculate mid price
            if order_depth.buy_orders and order_depth.sell_orders:
                best_bid = max(order_depth.buy_orders)
                best_ask = min(order_depth.sell_orders)
                mid_price = (best_bid + best_ask) / 2
                price_history[product].append(mid_price)
                if len(price_history[product]) > 100:
                    price_history[product].pop(0)
            else:
                continue

            # Apply strategy per product
            if product == "RAINFOREST_RESIN":
                orders = self.mean_reversion(product, order_depth, position, price_history)
            elif product == "KELP":
                orders = self.momentum(product, order_depth, position, price_history)
            elif product == "SQUID_INK":
                orders = self.crossover(product, order_depth, position, price_history)

            result[product] = orders

        # Save memory back
        traderData = jsonpickle.encode({"price_history": price_history})
        return result, conversions, traderData

    def mean_reversion(self, product, order_depth, position, history) -> List[Order]:
        orders = []
        prices = history[product]
        if len(prices) < 20:
            return orders

        mean = sum(prices) / len(prices)
        best_ask = min(order_depth.sell_orders, default=None)
        best_bid = max(order_depth.buy_orders, default=None)

        if best_ask and best_ask < mean * 0.98:
            qty = min(order_depth.sell_orders[best_ask], POSITION_LIMITS[product] - position)
            if qty > 0:
                orders.append(Order(product, best_ask, qty))

        if best_bid and best_bid > mean * 1.02:
            qty = min(order_depth.buy_orders[best_bid], position + POSITION_LIMITS[product])
            if qty > 0:
                orders.append(Order(product, best_bid, -qty))

        return orders

    def momentum(self, product, order_depth, position, history) -> List[Order]:
        orders = []
        prices = history[product]
        if len(prices) < 15:
            return orders

        recent = sum(prices[-5:]) / 5
        previous = sum(prices[-10:-5]) / 5
        best_ask = min(order_depth.sell_orders, default=None)
        best_bid = max(order_depth.buy_orders, default=None)

        if recent > previous and best_ask:
            qty = min(order_depth.sell_orders[best_ask], POSITION_LIMITS[product] - position)
            if qty > 0:
                orders.append(Order(product, best_ask, qty))
        elif recent < previous and best_bid:
            qty = min(order_depth.buy_orders[best_bid], position + POSITION_LIMITS[product])
            if qty > 0:
                orders.append(Order(product, best_bid, -qty))

        return orders

    def crossover(self, product, order_depth, position, history) -> List[Order]:
        orders = []
        prices = history[product]
        if len(prices) < 20:
            return orders

        short_avg = sum(prices[-5:]) / 5
        long_avg = sum(prices[-20:]) / 20
        best_ask = min(order_depth.sell_orders, default=None)
        best_bid = max(order_depth.buy_orders, default=None)

        if short_avg > long_avg and best_ask:
            qty = min(order_depth.sell_orders[best_ask], POSITION_LIMITS[product] - position)
            if qty > 0:
                orders.append(Order(product, best_ask, qty))
        elif short_avg < long_avg and best_bid:
            qty = min(order_depth.buy_orders[best_bid], position + POSITION_LIMITS[product])
            if qty > 0:
                orders.append(Order(product, best_bid, -qty))

        return orders
