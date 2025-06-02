import os
import time
import json
import threading
import datetime as dt
import requests

with open('config.json') as f:
    config = json.load(f)

stock_symbols = config['symbols']
api_key = config['api_key']
use_sound = config.get('notification_sound', False)

def notify(title, message):
    sound_option = "--sound" if use_sound else ""
    os.system(f'termux-notification --title "{title}" --content "{message}" {sound_option}')

def fetch_price(symbol):
    url = f"https://api.twelvedata.com/price?symbol={symbol}&apikey={api_key}"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"API Error bij het ophalen van {symbol}: {response.status_code}")
    try:
        data = response.json()
        return float(data['price'])
    except json.JSONDecodeError:
        raise Exception(f"Fout bij het verwerken van de API-response voor {symbol}")

def show_menu(current_prices):
    print("Kies een aandeel om te volgen:")
    for i, symbol in enumerate(stock_symbols):
        price = current_prices.get(symbol)
        price_display = f" (Huidige koers: ${price:.2f})" if price is not None else " (Huidige koers: N/A)"
        print(f"{i+1}. {symbol}{price_display}")
    
    while True:
        try:
            selection = int(input(f"\nVoer je keuze in (1-{len(stock_symbols)}): "))
            if 1 <= selection <= len(stock_symbols):
                return stock_symbols[selection - 1]
            else:
                print("Ongeldige keuze. Probeer opnieuw.")
        except ValueError:
            print("Ongeldige invoer. Gebruik een nummer.")

def get_user_preferences(stock, current_price):
    target_price_str = input(
        f"Huidige koers van {stock}: ${current_price:.2f}\n"
        "Wil je een koersdoel instellen? Voer bedrag in (of laat leeg voor geen): "
    )
    target_price = float(target_price_str) if target_price_str.strip() != "" else None

    real_time = input("Real-time koers volgen? (ja/nee): ").strip().lower()
    interval = 30

    if real_time == "ja":
        print("\nKies update-interval:")
        print("1. Elke minuut")
        print("2. Elk uur")
        print("3. Elke 2 uur")
        while True:
            choice = input("Voer je keuze in (1-3): ").strip()
            if choice == "1":
                interval = 60
                break
            elif choice == "2":
                interval = 3600
                break
            elif choice == "3":
                interval = 7200
                break
            else:
                print("Ongeldige keuze. Probeer opnieuw.")

    return target_price, interval

def main():
    os.system('termux-wake-lock')

    current_prices = {}
    for symbol in stock_symbols:
        try:
            current_prices[symbol] = fetch_price(symbol)
        except Exception as e:
            print(f"Waarschuwing: Kon de initiële koers voor {symbol} niet ophalen. {e}")
            current_prices[symbol] = None

    stock = show_menu(current_prices)
    initial_price = current_prices.get(stock)
    if initial_price is None:
        print("Kon de initiële koers niet ophalen, het programma stopt.")
        os.system('termux-wake-unlock')
        return

    target_price, interval = get_user_preferences(stock, initial_price)
    notified_target = False

    def update_loop():
        nonlocal notified_target
        while True:
            try:
                current_price = fetch_price(stock)
                now = dt.datetime.now().strftime("%H:%M")
                notify(stock, f"${current_price:.2f} om {now}")
                if target_price is not None and not notified_target:
                    if current_price >= target_price:
                        notify("Doelwaarde bereikt!", f"{stock} is ${current_price:.2f}!")
                        notified_target = True
            except Exception as e:
                print("Fout bij ophalen koers:", e)
            time.sleep(interval)

    thread = threading.Thread(target=update_loop)
    thread.start()

    try:
        thread.join()
    except KeyboardInterrupt:
        print("\nAfsluiten...")
        os.system('termux-wake-unlock')

if __name__ == "__main__":
    main()
