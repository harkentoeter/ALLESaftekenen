import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    driver_service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=driver_service, options=chrome_options)
    return driver

def scrape_songs(driver):
    base_url = "https://www.listchallenges.com/top-1000-songs-of-all-time-acclaimed-music"
    driver.get(base_url)
    wait = WebDriverWait(driver, 30)
    all_songs = []
    page_num = 1
    while page_num <= 25:
        print(f"Scraping page {page_num}...")
        try:
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "item-name")))
            songs = driver.find_elements(By.CLASS_NAME, "item-name")
            for song in songs:
                try:
                    song_name = song.text
                    artist = song.find_element(By.XPATH, ".//following-sibling::div").text
                    print(f"Scraping song: {song_name} by {artist}")
                    all_songs.append((song_name, artist))
                except Exception as e:
                    print(f"Error scraping song or artist: {e}")
            next_page_url = f"https://www.listchallenges.com/top-1000-songs-of-all-time-acclaimed-music/list/{page_num + 1}"
            if page_num < 25:
                print(f"Moving to next page: {page_num + 1}...")
                driver.get(next_page_url)
                time.sleep(random.uniform(3, 6))
                page_num += 1
            else:
                print("Reached the last page, stopping.")
                break
        except Exception as e:
            print(f"Error during scraping page {page_num}: {e}")
            break
    return all_songs

def save_songs(songs, file_name):
    with open(file_name, "w", encoding="utf-8") as file:
        for song_name, artist in songs:
            file.write(f"{song_name} by {artist}\n")

def create_playlist(songs, num_songs):
    playlist = random.sample(songs, num_songs)
    return playlist

def main():
    driver = init_driver()
    try:
        all_songs = scrape_songs(driver)
        print("Scraping complete. Would you like to:")
        print("1. Save all songs.")
        print("2. Create a playlist of random songs.")
        choice = input("Enter your choice (1 or 2): ").strip()
        if choice == "1":
            save_songs(all_songs, "all_songs.txt")
            print("All songs have been saved to 'all_songs.txt'.")
        elif choice == "2":
            while True:
                try:
                    num_songs = int(input("Enter the number of songs for your playlist (1-1000): ").strip())
                    if 1 <= num_songs <= 1000:
                        break
                    else:
                        print("Please enter a number between 1 and 1000.")
                except ValueError:
                    print("Invalid input. Please enter a valid number between 1 and 1000.")
            playlist = create_playlist(all_songs, num_songs)
            save_songs(playlist, "playlist.txt")
            print(f"Your playlist of {num_songs} random songs has been saved to 'playlist.txt'.")
        else:
            print("Invalid choice. Exiting.")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
