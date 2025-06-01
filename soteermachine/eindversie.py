import time
import random
import os
import re
from collections import defaultdict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def init_driver():
    chrome_options = Options()
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 "
        "Safari/537.36 Edg/91.0.864.59"
    )
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    driver_service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=driver_service, options=chrome_options)
    return driver

def scrape_songs(driver):
    """
    Scrape de top 1000 songs. Veronderstel dat elem.text altijd het formaat heeft:
    'Artiest - Songtitel by <nummer>'. Verwijder de trailing ' by <nummer>' en splits
    op de eerste ' - '. Alles vóór ' - ' is artiest, alles erna is songtitel.
    """
    base_url = "https://www.listchallenges.com/top-1000-songs-of-all-time-acclaimed-music"
    driver.get(base_url)
    wait = WebDriverWait(driver, 30)
    all_songs = []
    page_num = 1

    while page_num <= 25:
        print(f"Scraping pagina {page_num}...")
        try:
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "item-name")))
            elements = driver.find_elements(By.CLASS_NAME, "item-name")
            for elem in elements:
                raw_text = elem.text.strip()
                # Verwijder trailing ' by <nummer>'
                raw_text = re.sub(r"\s+by\s+\d+$", "", raw_text)
                # Veronderstel dat alles vóór ' - ' artiest is
                if " - " in raw_text:
                    artist, title = raw_text.split(" - ", 1)
                else:
                    artist = ""
                    title = raw_text
                artist = artist.strip()
                title = title.strip()
                all_songs.append((title, artist))
            if page_num < 25:
                next_url = (
                    "https://www.listchallenges.com/"
                    "top-1000-songs-of-all-time-acclaimed-music"
                    f"/list/{page_num + 1}"
                )
                driver.get(next_url)
                time.sleep(random.uniform(3, 6))
                page_num += 1
            else:
                break
        except Exception as e:
            print(f"Fout bij scrapen pagina {page_num}: {e}")
            break

    return all_songs

def save_all_songs_and_artists(songs, file_name):
    """Optie 1: Sla 'Song Title by Artist' op."""
    with open(file_name, "w", encoding="utf-8") as f:
        for title, artist in songs:
            if artist:
                f.write(f"{title} by {artist}\n")
            else:
                f.write(f"{title}\n")

def save_only_songs(songs, file_name):
    """Optie 2: Sla alleen de songtitels op."""
    with open(file_name, "w", encoding="utf-8") as f:
        for title, _ in songs:
            f.write(f"{title}\n")

def save_songs_by_artist(file_name_in, file_name_out):
    """
    Optie 3: Lees 'file_name_in', parse iedere regel als 'Song Title by Artist',
    splits op de laatste ' by ' om title en artist te verkrijgen. Groepeer per artist,
    sorteer artiesten case-insensitive, en binnen elke artiest sorteertitel case-insensitive.
    Schrijf naar file_name_out:
        Artiest:
            Titel1
            Titel2
    """
    artist_dict = defaultdict(list)
    with open(file_name_in, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Zoek laatste ' by ' om te splitsen
            if " by " in line:
                idx = line.rfind(" by ")
                title = line[:idx].strip()
                artist = line[idx + 4:].strip()
            else:
                title = line
                artist = "Unknown Artist"
            key = artist
            artist_dict[key].append(title)

    sorted_artists = sorted(artist_dict.keys(), key=lambda a: a.lower())
    with open(file_name_out, "w", encoding="utf-8") as f:
        for artist in sorted_artists:
            f.write(f"{artist}:\n")
            sorted_titles = sorted(artist_dict[artist], key=lambda t: t.lower())
            for title in sorted_titles:
                f.write(f"    {title}\n")
            f.write("\n")

def save_songs_alphabetical(songs, file_name):
    """
    Optie 5: Sorteer alle (title, artist)-paren op titel (case-insensitive)
    en sla op als 'Song Title by Artist'.
    """
    sorted_list = sorted(songs, key=lambda sa: sa[0].lower())
    with open(file_name, "w", encoding="utf-8") as f:
        for title, artist in sorted_list:
            if artist:
                f.write(f"{title} by {artist}\n")
            else:
                f.write(f"{title}\n")

def create_playlist(songs, num_songs, file_name):
    """Optie 4: Kies willekeurig num_songs uit de lijst en sla op."""
    if num_songs > len(songs):
        num_songs = len(songs)
    playlist = random.sample(songs, num_songs)
    with open(file_name, "w", encoding="utf-8") as f:
        for title, artist in playlist:
            if artist:
                f.write(f"{title} by {artist}\n")
            else:
                f.write(f"{title}\n")

def main():
    driver = init_driver()
    try:
        print("Start met scrapen van Top 1000 nummers...")
        all_songs = scrape_songs(driver)
        print(f"Scraping voltooid: {len(all_songs)} nummers gevonden.\n")

        # Direct na scrapen: zorg dat we altijd een actuele 'all_songs_and_artists.txt' hebben
        temp_all_file = "all_songs_and_artists.txt"
        save_all_songs_and_artists(all_songs, temp_all_file)

        print("Kies een optie:")
        print("1. Save all songs and artists")
        print("2. Save only the songs")
        print("3. Save all songs per artist")
        print("4. Make a playlist of random songs")
        print("5. Save all songs in alphabetical order")
        choice = input("Voer je keuze in (1-5): ").strip()

        if choice == "1":
            # 'all_songs_and_artists.txt' is al aangemaakt
            print(f"Alle nummers en artiesten zijn opgeslagen in '{temp_all_file}'.")

        elif choice == "2":
            out_file = "only_songs.txt"
            save_only_songs(all_songs, out_file)
            print(f"Alleen de songtitels zijn opgeslagen in '{out_file}'.")

        elif choice == "3":
            out_file = "songs_by_artist.txt"
            # Hergebruik het bestand dat we bij optie 1 maakten
            save_songs_by_artist(temp_all_file, out_file)
            print(f"Alle nummers gegroepeerd per artiest zijn opgeslagen in '{out_file}'.")

        elif choice == "4":
            while True:
                try:
                    num_songs = int(input("Hoeveel nummers voor playlist (1-1000)? ").strip())
                    if 1 <= num_songs <= 1000:
                        break
                    else:
                        print("Voer een getal tussen 1 en 1000 in.")
                except ValueError:
                    print("Ongeldige invoer. Probeer opnieuw.")
            out_file = "playlist.txt"
            create_playlist(all_songs, num_songs, out_file)
            print(f"Playlist met {num_songs} nummers opgeslagen in '{out_file}'.")

        elif choice == "5":
            out_file = "all_songs_alphabetical.txt"
            save_songs_alphabetical(all_songs, out_file)
            print(f"Alle nummers alfabetisch gesorteerd opgeslagen in '{out_file}'.")

        else:
            print("Ongeldige keuze. Programma stopt.")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
