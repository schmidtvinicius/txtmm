import re
import time
import numpy as np
from random import randint
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

SONG_URLS = [f'https://maistocadas.mus.br/{year}' for year in range(1958, 2024)]
SONGS_DIR = 'songs/'
LYRICS_URL = 'https://www.letras.mus.br/'
ACCENTS_MAPPING = {'é': 'e', 'á': 'a', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ã': 'a', 'ç': 'c', 'à': 'a', 'ê': 'e', 'ô': 'o', 'õ': 'o'}

def get_random_geolocation():
    return {'latitude': randint(-90,90), 'longitude':randint(-180,180)}

def get_random_viewport():
    return {'width': randint(800, 1920), 'height': randint(600, 1080)}

def remove_accents(string):
    for accent, replacement in ACCENTS_MAPPING.items():
        string = string.replace(accent, replacement)
    return string

def remove_non_alphanumeric_characters(string):
    return re.sub(pattern=r'[^a-zA-Z0-9\s]', repl='', string=string)

songs_without_lyrics = []
non_portuguese_songs = []

def main():
    with sync_playwright() as playwright:
        browser = None
        if np.random.random() > 0.5:
            browser =  playwright.firefox.launch(headless = False,)
        else:
            browser =  playwright.chromium.launch(headless = False,)
        for url in SONG_URLS:
            csv_lines = []
            songs_page =  browser.new_page(viewport=get_random_viewport(), geolocation=get_random_geolocation())
            songs_page.goto(url)
            track_list =  songs_page.locator('#tracklist').locator('li').all()
            lyrics_browser = None
            if np.random.random() > 0.5:
                lyrics_browser =  playwright.chromium.launch(headless = False,)
            else:
                lyrics_browser =  playwright.firefox.launch(headless = False,)
            lyrics_page =  lyrics_browser.new_page(viewport=get_random_viewport(), geolocation=get_random_geolocation())
            lyrics_page.goto(LYRICS_URL)
            lyrics_page.set_default_timeout(1500)
            lyrics_page.get_by_role('button', name='Consent', exact=True).click()
            for track_card in track_list:
                song_title = str( track_card.locator('span.musicas').text_content()).strip()
                song_title_transformed = remove_accents(remove_non_alphanumeric_characters(song_title.replace('feat', 'part'))).lower()
                artist = str( track_card.locator('span.artista').text_content()).strip()
                artist_transformed = remove_accents(remove_non_alphanumeric_characters(artist.replace('feat', 'part'))).lower()
                lyrics_page.locator('#main_suggest').fill(song_title + ' ' + artist)
                lyrics_page.locator("button.header-search-submit").click()
                song_lyrics_link = lyrics_page.locator('a.gs-title').nth(0)
                try:
                    song_lyrics_link_title, song_lyrics_link_artist = ( song_lyrics_link.text_content()).split('-')[0:2]
                except PlaywrightTimeoutError:
                    songs_without_lyrics.append((song_title, artist))
                    continue
                if (remove_accents(remove_non_alphanumeric_characters(song_lyrics_link_title.strip().replace('feat', 'part'))).lower() != song_title_transformed or 
                    remove_accents(remove_non_alphanumeric_characters(song_lyrics_link_artist.strip().replace('feat', 'part'))).lower() != artist_transformed):
                    print(f'Did not find lyrics for {song_title}, {artist}')
                    songs_without_lyrics.append((song_title, artist))
                    continue
                song_lyrics_link.click()
                try:
                    translation =  lyrics_page.locator('a.js-filterTranslation').text_content()
                    if translation == 'Tradução':
                        non_portuguese_songs.append((song_title, artist))
                        continue    
                except PlaywrightTimeoutError:
                    non_portuguese_songs.append((song_title, artist))
                    continue
                translation_languages =  lyrics_page.locator('label.translationModal-label').all_text_contents()
                if 'Português' in translation_languages:
                    non_portuguese_songs.append((song_title, artist))
                    continue
                lyrics =  lyrics_page.locator('div.lyric-original').all_inner_texts()

                csv_lines.append(f'"{song_title}","{artist}","{lyrics[0]}"\n')
                time.sleep(2)
            lyrics_page.close()
            songs_page.close()
            with open(SONGS_DIR+url.split('/')[-1]+'.csv', 'w') as f:
                f.write('title,artist\n')
                f.writelines(csv_lines)

if __name__ == '__main__':
    main()
