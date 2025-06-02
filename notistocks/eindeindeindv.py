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

def show_menu():
    print("Kies een aandeel om te volgen:")
    for i, symbol in enumerate(stock_symbols):
        print(f"{i+1}. {symbol}")
    while True:
        try:
            selection = int(input(f"\nVoer je keuze in (1-{len(stock_symbols)}): "))
            if 1 <= selection <= len(stock_symbols):
                return stock_symbols[selection - 1]
            else:
                print("Ongeldige keuze. Probeer opnieuw.")
        except ValueError:
            print("Ongeldige invoer. Gebruik een nummer.")

def fetch_price(symbol):
    url = f"https://api.twelvedata.com/price?symbol={symbol}&apikey={api_key}"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception("API Error")
    data = response.json()
    return float(data['price'])

def get_user_preferences():
    target_price = input("Wil je een koersdoel instellen? Voer bedrag in (of laat leeg voor geen): ")
    target_price = float(target_price) if target_price.strip() != "" else None

    direction = None
    if target_price is not None:
        while True:
            direction = input("Melding bij (1) stijgen naar doel of (2) dalen naar doel? (1/2): ").strip()
            if direction in ("1", "2"):
                break
            else:
                print("Ongeldige keuze. Kies 1 of 2.")

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

    return target_price, direction, interval

def main():
    os.system('termux-wake-lock')

    stock = show_menu()
    target_price, direction, interval = get_user_preferences()
    notified_target = False

    def update_loop():
        nonlocal notified_target
        while True:
            try:
                current_price = fetch_price(stock)
                now = dt.datetime.now().strftime("%H:%M")
                notify(f"{stock} Koers", f"${current_price:.2f} om {now}")

                if target_price is not None and not notified_target:
                    if direction == "1" and current_price >= target_price:
                        notify("Doelwaarde bereikt!", f"{stock} is gestegen naar ${current_price:.2f}!")
                        notified_target = True
                    elif direction == "2" and current_price <= target_price:
                        notify("Doelwaarde bereikt!", f"{stock} is gedaald naar ${current_price:.2f}!")
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

