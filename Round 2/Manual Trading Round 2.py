from typing import Dict, List
from datamodel import Order, OrderDepth, TradingState
import jsonpickle

POSITION_LIMITS = {
    "RAINFOREST_RESIN": 50,
    "KELP": 50,
    "SQUID_INK": 50,
    "CROISSANT": 250,
    "JAM": 350,
    "DJEMBE": 60,
    "PICNIC_BASKET1": 60,
    "PICNIC_BASKET2": 100,
}

BASKET1_COMPOSITION = {"CROISSANT": 6, "JAM": 3, "DJEMBE": 1}
BASKET2_COMPOSITION = {"CROISSANT": 4, "JAM": 2}


class Trader:
    def run(self, state: TradingState):
        result = {}
        conversions = 0

        # === Load memory ===
        if state.traderData:
            memory = jsonpickle.decode(state.traderData)
        else:
            memory = {"price_history": {}}

        price_history = memory["price_history"]

        # === Update price history ===
        for product, order_depth in state.order_depths.items():
            if product not in price_history:
                price_history[product] = []

            if order_depth.buy_orders and order_depth.sell_orders:
                best_bid = max(order_depth.buy_orders)
                best_ask = min(order_depth.sell_orders)
                mid_price = (best_bid + best_ask) / 2
                price_history[product].append(mid_price)
                if len(price_history[product]) > 100:
                    price_history[product].pop(0)

        # === Estimate fair values ===
        fair_values = {
            product: sum(prices) / len(prices)
            for product, prices in price_history.items()
            if len(prices) >= 5
        }

        # === Trade baskets based on arbitrage ===
        for basket, composition in [("PICNIC_BASKET1", BASKET1_COMPOSITION), ("PICNIC_BASKET2", BASKET2_COMPOSITION)]:
            if basket not in state.order_depths:
                continue
            # Calculate basket value from fair value of components
            basket_value = sum(fair_values.get(prod, 0) * qty for prod, qty in composition.items())
            basket_orders = self.arbitrage_basket(state, basket, basket_value)
            result[basket] = basket_orders

        # === Trade individual products ===
        for product in POSITION_LIMITS:
            if product not in state.order_depths:
                continue
            if product in ["PICNIC_BASKET1", "PICNIC_BASKET2"]:
                continue
            orders = self.mean_reversion(product, state.order_depths[product], state.position.get(product, 0), price_history)
            result[product] = orders

        # === Save memory ===
        traderData = jsonpickle.encode({"price_history": price_history})
        return result, conversions, traderData

    def arbitrage_basket(self, state, basket, component_value):
        order_depth = state.order_depths[basket]
        position = state.position.get(basket, 0)
        orders = []

        best_ask = min(order_depth.sell_orders, default=None)
        best_bid = max(order_depth.buy_orders, default=None)

        if best_ask is not None and best_ask < component_value * 0.98:
            qty = min(POSITION_LIMITS[basket] - position, order_depth.sell_orders[best_ask])
            if qty > 0:
                orders.append(Order(basket, best_ask, qty))

        if best_bid is not None and best_bid > component_value * 1.02:
            qty = min(position + POSITION_LIMITS[basket], order_depth.buy_orders[best_bid])
            if qty > 0:
                orders.append(Order(basket, best_bid, -qty))

        return orders

    def mean_reversion(self, product, order_depth, position, price_history) -> List[Order]:
        orders = []
        prices = price_history.get(product, [])
        if len(prices) < 20:
            return orders

        mean = sum(prices) / len(prices)
        std = (sum((x - mean) ** 2 for x in prices) / len(prices)) ** 0.5
        threshold = std * 0.8  # Adaptive threshold

        best_ask = min(order_depth.sell_orders, default=None)
        best_bid = max(order_depth.buy_orders, default=None)

        if best_ask and best_ask < mean - threshold:
            qty = min(order_depth.sell_orders[best_ask], POSITION_LIMITS[product] - position)
            if qty > 0:
                orders.append(Order(product, best_ask, qty))

        if best_bid and best_bid > mean + threshold:
            qty = min(order_depth.buy_orders[best_bid], position + POSITION_LIMITS[product])
            if qty > 0:
                orders.append(Order(product, best_bid, -qty))

        return orders
