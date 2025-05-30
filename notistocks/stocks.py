import os
import time
import json
import threading
import datetime as dt
import requests

# Load configuration
with open('config.json') as f:
    config = json.load(f)

stock_symbols = config['symbols']
api_key = config['api_key']

# Simple notifier function as requested
def notify(title, message):
    os.system(f'termux-notification --title "{title}" --content "{message}"')

# Menu to select a stock
def show_menu():
    print(" Choose a stock to track:")
    for i, symbol in enumerate(stock_symbols):
        print(f"{i+1}. {symbol}")
    selection = int(input(f"\nEnter your choice (1-{len(stock_symbols)}): "))
    return stock_symbols[selection - 1]

# Fetch the current stock price
def fetch_price(symbol):
    url = f"https://api.twelvedata.com/price?symbol={symbol}&apikey={api_key}"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception("API Error")
    data = response.json()
    return float(data['price'])

# Main logic
def main():
    os.system('termux-wake-lock')

    stock = show_menu()

    def update_loop():
        while True:
            try:
                current_price = fetch_price(stock)
                now = dt.datetime.now().strftime("%H:%M")
                notify(f"{stock} Price", f"${current_price:.2f} at {now}")
            except Exception as e:
                print(" Error:", e)

            time.sleep(360)  # 6 minutes

    # Run in background thread
    thread = threading.Thread(target=update_loop)
    thread.start()

    try:
        thread.join()
    except KeyboardInterrupt:
        print("\nExiting...")
        os.system('termux-wake-unlock')

if __name__ == "__main__":
    main()
