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

# Aandeelkeuzemenu
def show_menu():
    print("📊 Kies een aandeel om te volgen:")
    for i, symbol in enumerate(stock_symbols):
        print(f"{i+1}. {symbol}")
    while True:
        try:
            selection = int(input(f"\nVoer je keuze in (1-{len(stock_symbols)}): "))
            if 1 <= selection <= len(stock_symbols):
                return stock_symbols[selection - 1]
            else:
                print("❌ Ongeldige keuze. Probeer opnieuw.")
        except ValueError:
            print("❌ Ongeldige invoer. Gebruik een nummer.")

# Huidige prijs ophalen via API
def fetch_price(symbol):
    url = f"https://api.twelvedata.com/price?symbol={symbol}&apikey={api_key}"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception("API Error")
    data = response.json()
    return float(data['price'])

# Vraag voorkeuren van gebruiker
def get_user_preferences():
    # Doelprijs
    target_price = input("🎯 Wil je een koersdoel instellen? Voer bedrag in (of laat leeg voor geen): ")
    target_price = float(target_price) if target_price.strip() != "" else None

    # Real-time updates
    real_time = input("⏱️ Real-time koers volgen? (ja/nee): ").strip().lower()
    interval = 30  # standaard: elke 30 seconden

    if real_time == "ja":
        print("\n🔁 Kies update-interval:")
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
                print("❌ Ongeldige keuze. Probeer opnieuw.")
    
    return target_price, interval

# Hoofdfunctie
def main():
    os.system('termux-wake-lock')

    stock = show_menu()
    target_price, interval = get_user_preferences()
    notified_target = False

    def update_loop():
        nonlocal notified_target
        while True:
            try:
                current_price = fetch_price(stock)
                now = dt.datetime.now().strftime("%H:%M")
                notify(f"{stock} Koers", f"${current_price:.2f} om {now}")

                # Controle op doelkoers
                if target_price is not None and not notified_target:
                    if current_price >= target_price:
                        notify("🎯 Doelwaarde bereikt!", f"{stock} is ${current_price:.2f}!")
                        notified_target = True

            except Exception as e:
                print("⚠️ Fout bij ophalen koers:", e)

            time.sleep(interval)

    # Achtergrondthread starten
    thread = threading.Thread(target=update_loop)
    thread.start()

    try:
        thread.join()
    except KeyboardInterrupt:
        print("\n📴 Afsluiten...")
        os.system('termux-wake-unlock')

if __name__ == "__main__":
    main()