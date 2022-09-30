import spotipy as sp
from spotipy.oauth2 import SpotifyClientCredentials
import secrets
import json
from bs4 import BeautifulSoup
import requests
import pandas as pd

def getTrackFeatures(spotify, artist, track):
    q = "track:\"%s\"artist:\"%s\"" % (track, artist)

    result = spotify.search(q, limit=1, offset=0, type='track', market='US')

    try:
        totalArtists = len(result['tracks']['items'][0]['artists'])
        featuredArtists = ""
        for features in range(1, totalArtists):
            featuredArtists += result['tracks']['items'][0]['artists'][features]['name'] + ","
            if features == totalArtists-1:
                featuredArtists = featuredArtists[:-1]  # get rid of the extra comma at the end

        return {'song': result['tracks']['items'][0]['name'], 'artist': result['tracks']['items'][0]['artists'][0]['name'], 
            'features': featuredArtists, 'track_id': result['tracks']['items'][0]['id'], 'popularity': result['tracks']['items'][0]['popularity'],
            'release_date': result['tracks']['items'][0]['album']['release_date'], 
            'release_date_precision': result['tracks']['items'][0]['album']['release_date_precision']}  # returns a dictionary
    except Exception as e:
        print("Exception \"" + str(e) + "\" with the artist input: " + str(artist) + " and the song input: " + str(track))
        return None

def getAudioFeatures(spotify, trackID):
    result = spotify.audio_features([trackID])[0]

    return {'danceability': result['danceability'], 'energy': result['energy'], 'key': result['key'], 
    'loudness': result['loudness'], 'mode': result['mode'], 'speechiness': result['speechiness'], 
    'acousticness': result['acousticness'], 'instrumentalness': result['instrumentalness'], 
    'liveness': result['liveness'], 'valence': result['valence'], 'tempo': result['tempo'], 
    'time_signature': result['time_signature'], 'duration_ms': result['duration_ms']}


def getLyrics(artist, track):

    # do some string formatting for genius
    artist = artist.replace(",", "")
    artist = artist.replace(".", "")
    artist = artist.replace("\"", "")
    artist = artist.replace("&", "and")
    artist = artist.replace("+", "")
    artist = str(artist.replace(' ','-')) if ' ' in artist else str(artist)

    track = track.replace(",", "")
    track = track.replace(".", "")
    track = track.replace("\"", "")
    track = track.replace("+", "")
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

def generateOutput(csvName, spotify):
    results = pd.DataFrame(columns=['song', 'artist', 'features', 'track_id', 'popularity', 'release_date', 'release_date_precision', 'danceability', 'energy', 'key', 'loudness',
    'mode', 'speechiness', 'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo', 'time_signature', 'duration_ms', 'lyrics'])

    input = pd.read_csv(csvName)

    index = 0

    for tuple in input.itertuples():
        features = dict()
        artist = tuple[2]
        track = tuple[1]

        # features.update({'artist': artist, 'song': track})
        trackFeatures = getTrackFeatures(spotify, artist, track)
        if trackFeatures != None:
            features.update(trackFeatures)
            features.update(getAudioFeatures(spotify, features['track_id']))
            # artist = features['artist']
            # track = features['song']

        lyrics = getLyrics(artist, track)
        if lyrics != None:
            lyricsFixed = lyrics.replace("\n", "\\n")
            features['lyrics'] = lyricsFixed

        results = results.append(pd.Series(features), ignore_index=True)

        if index > 10:
            break
        else:
            index += 1

    dfToCsv(results)

def main():
    auth_manager = SpotifyClientCredentials(client_id=secrets.SPOTIPY_CLIENT_ID, client_secret=secrets.SPOTIPY_CLIENT_SECRET)
    spotify = sp.Spotify(auth_manager=auth_manager)
    
    generateOutput('input.csv', spotify)

if __name__ == "__main__":
    main()