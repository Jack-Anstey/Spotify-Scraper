import spotipy as sp
from spotipy.oauth2 import SpotifyClientCredentials
import secrets
import json
from bs4 import BeautifulSoup
import requests
import pandas as pd

def getTrackID(spotify, artist, track):
    q = "track:\"%s\"artist:\"%s\"" % (track, artist)
    result = spotify.search(q, limit=1, offset=0, type='track', market='US')

    # file = json.dumps(result, indent=4)

    # # Write JSON
    # with open("jsons/"+artist+track+".json", "w") as outfile:
    #     outfile.write(file)

    return result['tracks']['items'][0]['id']  # returns the trackID

def getAudioFeatures(spotify, trackID):
    result = spotify.audio_features([trackID])[0]

    return {'danceability': result['danceability'], 'energy': result['energy'], 'key': result['key'], 
    'loudness': result['loudness'], 'mode': result['mode'], 'speechiness': result['speechiness'], 
    'acousticness': result['acousticness'], 'instrumentalness': result['instrumentalness'], 
    'liveness': result['liveness'], 'valence': result['valence'], 'tempo': result['tempo'], 
    'time_signature': result['time_signature'], 'duration_ms': result['duration_ms']}


def getLyrics(artist, track):
    artist = str(artist.replace(' ','-')) if ' ' in artist else str(artist)
    track = str(track.replace(' ','-')) if ' ' in track else str(track)
    page = requests.get('https://genius.com/'+ artist + '-' + track + '-' + 'lyrics')
    print("Page:", page)
    html = BeautifulSoup(page.text, 'html.parser')
    lyrics1 = html.find("div", class_="lyrics")
    lyrics2 = html.find("div", class_="Lyrics__Container-sc-1ynbvzw-6 YYrds")
    if lyrics1:
        lyrics = lyrics1.get_text(separator="\n")
    elif lyrics2:
        lyrics = lyrics2.get_text(separator="\n")
    elif lyrics1 == lyrics2 == None:
        lyrics = None
    return lyrics

def dfToCsv(df):
    df.to_csv('output.csv', index=False)  

def main():
    auth_manager = SpotifyClientCredentials(client_id=secrets.SPOTIPY_CLIENT_ID, client_secret=secrets.SPOTIPY_CLIENT_SECRET)
    spotify = sp.Spotify(auth_manager=auth_manager)
    
    results = pd.DataFrame(columns=['song', 'artist', 'trackID', 'danceability', 'energy', 'key', 'loudness',
    'mode', 'speechiness', 'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo', 'time_signature', 'duration_ms', 'lyrics'])

    artist = "Adele"
    track = "Easy On Me"

    trackID = getTrackID(spotify, artist, track)
    lyrics = getLyrics(artist, track)
    features = getAudioFeatures(spotify, trackID)

    features['lyrics'] =  str(lyrics)
    features['artist'] = artist
    features['song'] = track
    features['trackID'] = trackID

    results = results.append(pd.Series(features), ignore_index=True)
    dfToCsv(results)

if __name__ == "__main__":
    main()