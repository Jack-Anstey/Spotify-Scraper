import spotipy as sp
from spotipy.oauth2 import SpotifyClientCredentials
import secrets
import json
from bs4 import BeautifulSoup
import requests

def getSpotifyJson(spotify, artist, track):
    q = "track:\"%s\"artist:\"%s\"" % (track, artist)
    # print(q)
    result = spotify.search(q, limit=1, offset=0, type='track', market='US')
    file = json.dumps(result, indent=4)

    # Write JSON
    with open("jsons/"+artist+track+".json", "w") as outfile:
        outfile.write(file)

def getLyrics(artist, track):
    artist = str(artist.replace(' ','-')) if ' ' in artist else str(artist)
    track = str(track.replace(' ','-')) if ' ' in track else str(track)
    page = requests.get('https://genius.com/'+ artist + '-' + track + '-' + 'lyrics')
    print("Page:", page)
    html = BeautifulSoup(page.text, 'html.parser')
    lyrics1 = html.find("div", class_="lyrics")
    lyrics2 = html.find("div", class_="Lyrics__Container-sc-1ynbvzw-6 YYrds")
    if lyrics1:
        lyrics = lyrics1.get_text()
    elif lyrics2:
        lyrics = lyrics2.get_text()
    elif lyrics1 == lyrics2 == None:
        lyrics = None
    return lyrics

def main():
    auth_manager = SpotifyClientCredentials(client_id=secrets.SPOTIPY_CLIENT_ID, client_secret=secrets.SPOTIPY_CLIENT_SECRET)
    spotify = sp.Spotify(auth_manager=auth_manager)
    artist = "Adele"
    track = "Easy On Me"
    getSpotifyJson(spotify, artist, track)
    lyrics = getLyrics(artist, track)
    print(lyrics)

if __name__ == "__main__":
    main()