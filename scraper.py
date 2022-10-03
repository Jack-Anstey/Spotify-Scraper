from sre_constants import SUCCESS
import spotipy as sp
from spotipy.oauth2 import SpotifyClientCredentials
import secrets
from bs4 import BeautifulSoup
import requests
import pandas as pd

def getTrackFeatures(spotify: sp.Spotify, artist: str, track: str, queryType: str) -> dict:
    """Given a connection to the Spotify API, an artist name, a track name, and a query type,
    get a bunch of information Spotify has on said track

    Args:
        spotify (sp.Spotify): the connection to the Spotify API
        artist (str): the artist
        track (str): the song name
        queryType (str): whether you want to use the long or short query

    Returns:
        dict: A dictionary of the results, None if nothing was found
    """

    if queryType == "long":
        q = "track:%s artist:%s" % (track, artist)
    elif queryType == "short":
         q = "track:%s" % (track)
    success = False
    while(not success):
        try:
            result = spotify.search(q, limit=1, offset=0, type='track', market='US')  # use the query
            totalArtists = len(result['tracks']['items'][0]['artists'])
            featuredArtists = ""
            for features in range(1, totalArtists):
                featuredArtists += result['tracks']['items'][0]['artists'][features]['name'] + ","
                if features == totalArtists-1:
                    featuredArtists = featuredArtists[:-1]  # get rid of the extra comma at the end
            success = True

            return {'song': result['tracks']['items'][0]['name'], 'artist': result['tracks']['items'][0]['artists'][0]['name'], 
                'features': featuredArtists, 'track_id': result['tracks']['items'][0]['id'], 'popularity': result['tracks']['items'][0]['popularity'],
                'release_date': result['tracks']['items'][0]['album']['release_date'], 
                'release_date_precision': result['tracks']['items'][0]['album']['release_date_precision']}  # returns a dictionary
        except requests.exceptions.Timeout:
            print("Timed out. Trying again")
        except Exception as e:  # if spotify returned basically nothing, print what happened
            print("Exception \"" + str(e) + "\" with the artist input: \"" + str(artist) + "\" and the song input: \"" + str(track) + "\"", end="")
            print(" with the query: \"" + q + "\"")
            success = True
            return None

def getAudioFeatures(spotify: sp.Spotify, trackID: str) -> dict:
    """Get a bunch more data about a particular song from Spotify

    Args:
        spotify (sp.Spotify): the connection to the Spotify API
        trackID (str): the Spotify track ID

    Returns:
        dict: a dictionary of the results from Spotify, None if nothing was found
    """
    success = False
    while(not success):
        try:
            result = spotify.audio_features([trackID])[0]  # get the track features
            success = True
        except requests.exceptions.Timeout:
            print("Timed out. Trying again")

    try:
        return {'danceability': result['danceability'], 'energy': result['energy'], 'key': result['key'], 
        'loudness': result['loudness'], 'mode': result['mode'], 'speechiness': result['speechiness'], 
        'acousticness': result['acousticness'], 'instrumentalness': result['instrumentalness'], 
        'liveness': result['liveness'], 'valence': result['valence'], 'tempo': result['tempo'], 
        'time_signature': result['time_signature'], 'duration_ms': result['duration_ms']}
    except Exception as e:  # if spotify returned basically nothing, print what happened
        print("Exception \"" + str(e) + "\" with the track ID: \"" + str(trackID) + "\"")
        return None


def getLyrics(artist: str, track: str) -> str:
    """Scrape the lyrics from Genius, using the input to generate a webpage

    Args:
        artist (str): the artist name
        track (str): the song name

    Returns:
        str: the lyrics of the song if found, None if it wasn't
    """

    # do some string formatting for genius
    artist = artist.translate(artist.maketrans("", "", "',.\"&+':()^#@_{=}|\\`~/<>;*?"))
    artist = str(artist.replace(' ','-')) if ' ' in artist else str(artist)
    artist = artist.replace("$", "-").replace("!", "-").replace("--", "-")  # replace with a dash instead of nothing
   
    track = track.translate(track.maketrans("", "", "',.\"&+':()^#@_{=}|\\`~/<>;*?"))
    track = str(track.replace(' ','-')) if ' ' in track else str(track)
    track = track.replace("$", "-").replace("!", "-").replace("--", "-")  # replace with a dash instead of nothing
    

    # build the page
    page = requests.get('https://genius.com/'+ artist + '-' + track + '-' + 'lyrics')
    print("Page:", page)  # debugging

    html = BeautifulSoup(page.text, 'html.parser')  # parse the page

    # find the lyrics using the parser
    lyrics1 = html.find("div", class_="lyrics")
    lyrics2 = html.find("div", class_="Lyrics__Container-sc-1ynbvzw-6 YYrds")

    # interpret results
    if lyrics1:
        lyrics = lyrics1.get_text(separator="\n")
    elif lyrics2:
        lyrics = lyrics2.get_text(separator="\n")
    elif lyrics1 == lyrics2 == None:
        print("Failed to get lyrics with the artist input: \"" + str(artist) + "\" and the song input: \"" + str(track) + "\"")
        lyrics = None
    return lyrics

def dfToCsv(df: pd.DataFrame, filename: str) -> None:
    """Output a given df to a csv with a given filename

    Args:
        df (pd.DataFrame): the data that you want put into a csv
        filename (str): the name of the file (the parameter must include .csv at the end)
    """

    df.to_csv(filename, index=False)

def generateOutput(csvName: str, spotify: sp.Spotify, chunksize: int) -> None:
    """Take the songs and artist pairs that you want more information on, and find the information! Outputs to a csv intermittently. 

    Args:
        csvName (str): the name of the csv that you are getting the song and artist names from
        spotify (sp.Spotify): the Spotify object that interfaces with the Spotify API
        chunksize (int): the size of the csv chunks that you want
    """

    # construct a dataframe with all the columns we'll ever need
    results = pd.DataFrame(columns=['song', 'artist', 'features', 'track_id', 'popularity', 'release_date', 'release_date_precision', 'danceability', 'energy', 'key', 'loudness',
    'mode', 'speechiness', 'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo', 'time_signature', 'duration_ms', 'lyrics'])

    input = pd.read_csv(csvName)  # get the (song, artist) tuples to use as input for getting more data
    count = 0  # keeps track of how many songs you have looked at in this chunk
    iteration = 0  # keeps track of how many chunks you have made

    for tuple in input.itertuples():
        features = dict()  # make an empty dictionary
        artist = tuple[2]
        track = tuple[1]

        trackFeatures = getTrackFeatures(spotify, artist, track, "long")
        if trackFeatures != None:
            features.update(trackFeatures)  # add to the dictionary
            audioFeatures = getAudioFeatures(spotify, features['track_id'])
            if audioFeatures != None:
                features.update(audioFeatures)  # add more!
        else:  # if an exception is thrown, use the regular artist and song titles
            trackFeatures = getTrackFeatures(spotify, artist, track, "short")
            if trackFeatures != None:
                features.update(trackFeatures)
                audioFeatures = getAudioFeatures(spotify, features['track_id'])
                if audioFeatures != None:
                    features.update(audioFeatures)  # add more!
            else:  # if we still can't find anything, use the artist and track names that we already have
                features.update({'artist': artist, 'song': track})

        # get the lyrics
        lyrics = getLyrics(artist, track)
        if lyrics != None:  # we got the lyrics!
            lyricsFixed = lyrics.replace("\n", "\\n")
            features['lyrics'] = lyricsFixed
        else:  # if we didn't get the lyrics, try again with the spotify names
            lyrics = getLyrics(features['artist'], features['song'])
            if lyrics != None:
                lyricsFixed = lyrics.replace("\n", "\\n")
                features['lyrics'] = lyricsFixed

        if count < chunksize:
            # add to the dataframe
            results = results.append(pd.Series(features), ignore_index=True)
            count += 1
        else:
            count = 0
            dfToCsv(results, "output"+str(iteration)+".csv")
            # get an empty dataframe
            results = pd.DataFrame(columns=['song', 'artist', 'features', 'track_id', 'popularity', 'release_date', 'release_date_precision', 'danceability', 'energy', 'key', 'loudness',
                'mode', 'speechiness', 'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo', 'time_signature', 'duration_ms', 'lyrics'])
            iteration += 1

    # output the remaining/finished dataframe to output.csv
    if iteration == 0:
        dfToCsv(results, "output.csv")
    else:
        dfToCsv(results, "output"+str(iteration)+".csv")

def main():
    auth_manager = SpotifyClientCredentials(client_id=secrets.SPOTIPY_CLIENT_ID, client_secret=secrets.SPOTIPY_CLIENT_SECRET)
    spotify = sp.Spotify(auth_manager=auth_manager)
    
    generateOutput('input.csv', spotify, 3000)  # use a default chunksize of 3000

if __name__ == "__main__":
    main()