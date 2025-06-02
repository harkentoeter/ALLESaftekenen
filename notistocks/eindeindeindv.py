import os
import time
import json
import threading
import datetime as dt
import requests

# Laad config.json
with open('config.json') as f:
    config = json.load(f)

stock_symbols = config['symbols']
api_key = config['api_key']
use_sound = config.get('notification_sound', False)

# Notificatiefunctie
def notify(title, message):
    sound_option = "--sound" if use_sound else ""
    os.system(f'termux-notification --title "{title}" --content "{message}" {sound_option}')

# Huidige prijs ophalen via API
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

# Aandeelkeuzemenu
def show_menu(current_prices):
    print("📊 Kies een aandeel om te volgen:")
    for i, symbol in enumerate(stock_symbols):
        price_display = f" (Huidige koers: ${current_prices.get(symbol, 'N/A'):.2f})"
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

# Vraag voorkeuren van gebruiker
def get_user_preferences(stock, current_price):
    target_price = None
    target_type = None

    while True:
        target_choice = input(f"Huidige koers van {stock}: ${current_price:.2f}\nWil je een koersdoel instellen?\n1. Stijgend doel (bereiken of overschrijden)\n2. Dalend doel (bereiken of onderschrijden)\n3. Geen doel instellen\nVoer je keuze in (1-3): ").strip()
        if target_choice == "1":
            target_price_str = input("Voer de gewenste stijgende koers in: ")
            try:
                target_price = float(target_price_str)
                target_type = "stijgend"
                break
            except ValueError:
                print("Ongeldige invoer. Gebruik een numerieke waarde.")
        elif target_choice == "2":
            target_price_str = input("Voer de gewenste dalende koers in: ")
            try:
                target_price = float(target_price_str)
                target_type = "dalend"
                break
            except ValueError:
                print("Ongeldige invoer. Gebruik een numerieke waarde.")
        elif target_choice == "3":
            break
        else:
            print("Ongeldige keuze. Probeer opnieuw.")

    # Real-time updates
    real_time = input("Real-time koers volgen? (ja/nee): ").strip().lower()
    interval = 30  # standaard: elke 30 seconden

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

    return target_price, target_type, interval

# Hoofdfunctie
def main():
    os.system('termux-wake-lock')

    # Haal de initiële koersen op
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

    target_price, target_type, interval = get_user_preferences(stock, initial_price)
    notified_target = False

    def update_loop():
        nonlocal notified_target
        while True:
            try:
                current_price = fetch_price(stock)
                # Notificatie zonder de tijd
                notify(stock, f"${current_price:.2f}")

                # Controle op doelkoers
                if target_price is not None and not notified_target:
                    if target_type == "stijgend" and current_price >= target_price:
                        notify("Doelwaarde bereikt!", f"{stock} is ${current_price:.2f} (Stijgend doel bereikt)!")
                        notified_target = True
                    elif target_type == "dalend" and current_price <= target_price:
                        notify("Doelwaarde bereikt!", f"{stock} is ${current_price:.2f} (Dalend doel bereikt)!")
                        notified_target = True

            except Exception as e:
                print("Fout bij ophalen koers:", e)

            time.sleep(interval)

    # Achtergrondthread starten
    thread = threading.Thread(target=update_loop)
    thread.start()

    try:
        thread.join()
    except KeyboardInterrupt:
        print("\nAfsluiten...")
        os.system('termux-wake-unlock')

if __name__ == "__main__":
    main()
