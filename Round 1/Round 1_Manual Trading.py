# Currency index map
currencies = ["Snowballs", "Pizza's", "Silicon Nuggets", "SeaShells"]
currency_index = {name: i for i, name in enumerate(currencies)}

# Trading table (from -> to)
exchange = [
    [1, 1.45, 0.52, 0.72],
    [0.7, 1, 0.31, 0.48],
    [1.95, 3.1, 1, 1.49],
    [1.34, 1.98, 0.64, 1]
]

# Start with SeaShells (index 3), 500
start_currency = 3
start_amount = 500
max_trades = 5

best_path = []
max_profit = 0

def dfs(path, current_currency, amount, depth):
    global max_profit, best_path

    if depth == max_trades:
        if current_currency == start_currency and amount > max_profit:
            max_profit = amount
            best_path = path[:]
        return

    for next_currency in range(4):
        rate = exchange[current_currency][next_currency]
        new_amount = amount * rate
        dfs(path + [(current_currency, next_currency, rate)], next_currency, new_amount, depth + 1)

# Start DFS from SeaShells
dfs([], start_currency, start_amount, 0)

# Print best path
print(f"Maximum Profit: {max_profit:.2f} SeaShells")
print("Best Trade Path:")
for i, (from_idx, to_idx, rate) in enumerate(best_path, 1):
    print(f"{i}. Trade {currencies[from_idx]} → {currencies[to_idx]} at rate {rate}")

