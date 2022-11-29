import spotipy as sp
from spotipy.oauth2 import SpotifyClientCredentials
import secrets
from bs4 import BeautifulSoup
import requests
import pandas as pd
import string
import os
import re

def getTrackFeatures(spotify: sp.Spotify, artist: str, track: str) -> dict:
    """Given a connection to the Spotify API, an artist name, a track name, and a query type,
    get a bunch of information Spotify has on said track

    Args:
        spotify (sp.Spotify): the connection to the Spotify API
        artist (str): the artist
        track (str): the song name

    Returns:
        dict: A dictionary of the results, None if nothing was found
    """

    q = "track:%s artist:%s" % (track, artist)  # make the query
    
    success = False  # keep trying if you timeout
    while(not success):
        try:
            # Set the limit to 2. Why? Ask Spotify. Returns more consistent results
            result = spotify.search(q, limit=2, offset=0, type='track', market='US')  # use the query
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

    success = False  # keep trying if you timeout
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


def getLyricsWebScrape(artist: str, track: str) -> str:
    """Scrape the lyrics from Genius, using the input to generate a webpage

    Args:
        artist (str): the formatted artist name
        track (str): the formatted song name

    Returns:
        str: the lyrics of the song if found, None if it wasn't
    """

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
    return lyrics.replace("\n", "\\n")  # fix the lyrics so that there are all on one line

def formatWord(input: str, spaceInterior: bool) -> str:
    """Take a input and output a formatted word for Genius

    Args:
        input (str): The string input
        spaceInterior (bool): True if you want punctuation inside a word to be a space, 
                                False otherwise

    Returns:
        str: the formatted output
    """

    if spaceInterior:
        fixedArtistWords = []
        for word in input.split():  # iterate through the words in the input
            if (len(word) == 1):  # if the length of the word is only 1 character, only test that character
                fixedArtistWords.append(word.translate(str.maketrans('', '', string.punctuation)))
            else:  # otherwise see if the first and last character is punctuation. If so, delete
                fixedArtistWords.append(word[0].translate(str.maketrans('', '', string.punctuation)) + word[1:len(word)-1] + word[len(word)-1].translate(str.maketrans('', '', string.punctuation)))

        output = ' '.join(fixedArtistWords).replace("  ", " ")  #  make the edited array back into one string
        output = output.strip().translate(str.maketrans(string.punctuation, '-'*len(string.punctuation)))  # any remaining puncuation then turns into a dash
    else:
        output = input.translate(str.maketrans('', '', string.punctuation))

    output = output.strip().replace(" ", "-").replace("--", "-")  # replace any double dashes with a single dash
    return output

def bruteForceGetLyrics(artist: str, track: str) -> str:
    """Repeatedly try to get the lyrics using different string formatting techniques for Genius

    Args:
        artist (str): the original artist string
        track (str): the original track string

    Returns:
        str: the lyrics if found, None otherwise
    """
    
    # do some string formatting for genius. Try until you get it
    artistTrue = formatWord(artist, True)
    trackFalse = formatWord(track, False)
    artistFalse = formatWord(artist, False)
    trackTrue = formatWord(track, True)

    differentArtist = artistTrue != artistFalse
    differentTrack = trackFalse != trackTrue

    lyrics = getLyricsWebScrape(artistTrue, trackFalse)
    if lyrics == None:
        if differentTrack:
            lyrics = getLyricsWebScrape(artistTrue, trackTrue)
        if lyrics == None:
            if differentArtist:
                lyrics = getLyricsWebScrape(artistFalse, trackFalse)
            if lyrics == None:
                if differentArtist and differentTrack:
                    lyrics = getLyricsWebScrape(artistFalse, trackTrue)
    return lyrics

def dfToCsv(df: pd.DataFrame, filename: str) -> None:
    """Output a given df to a csv with a given filename

    Args:
        df (pd.DataFrame): the data that you want put into a csv
        filename (str): the name of the file (the parameter must include .csv at the end)
    """

    df.to_csv(filename, index=False)


def coalesce() -> None:
    """Takes all of the generated numbered output csv's and coalesces them all into one
    """

    # get only output.csv's that have a number after them (as generated by the program)
    outputs = list(filter(re.compile("output[0-9]*\.csv").match, os.listdir()))
    
    if len(outputs) < 2:  # if there is only 1, output.csv was used. If there is none, don't bother!
        return
    
    outputs.sort(key=len)  # sorts in order gathered

    output = pd.DataFrame(columns=['song', 'artist', 'features', 'track_id', 'popularity', 'release_date', 'release_date_precision', 'danceability', 'energy', 'key', 'loudness',
    'mode', 'speechiness', 'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo', 'time_signature', 'duration_ms', 'lyrics'])
    
    for filename in outputs:
        portion = pd.read_csv(filename)
        output = pd.concat([output, portion])  # add to the data
    
    dfToCsv(output, "output.csv")  # the final output

def getSongData(spotify: sp.Spotify, artist: str, track: str) -> dict:
    """Find out data about a song by a particular artist

    Args:
        spotify (sp.Spotify): the link to the Spotify API
        artist (str): the artist name
        track (str): the song that you want more information about

    Returns:
        dict(): Return a dictionary of the found information, a dict with only the input otherwise
    """

    foundFeatures = dict()
    trackFeatures = getTrackFeatures(spotify, artist.replace("'", ""), track.replace("'", ""))
    if trackFeatures == None:
        trackFeatures = getTrackFeatures(spotify, artist, track)  # try it without deleting apostrophies
    
    # check to see if either version worked
    if trackFeatures != None:
        foundFeatures.update(trackFeatures)  # add to the dictionary
        audioFeatures = getAudioFeatures(spotify, foundFeatures['track_id'])
        if audioFeatures != None:
            foundFeatures.update(audioFeatures)  # add more
    else:  # if we couldn't find anything, put the default artist and song into the features dictionary
        foundFeatures.update({'artist': artist, 'song': track})

    return foundFeatures

def generateOutput(input: pd.DataFrame, spotify: sp.Spotify, chunksize=2000, iteration=0) -> None:
    """Take the songs and artist pairs that you want more information on, and find the information! Outputs to a csv intermittently. 

    Args:
        input (pd.DataFrame): the dataframe that has song and artist columns
        spotify (sp.Spotify): the Spotify object that interfaces with the Spotify API
        chunksize (int): the size of the csv chunks that you want (defaults to 2000)
        iteration (int): the number of iteration that you are on (defaults to 0)
    """

    # construct a dataframe with all the columns we'll ever need
    results = pd.DataFrame(columns=['song', 'artist', 'features', 'track_id', 'popularity', 'release_date', 'release_date_precision', 'danceability', 'energy', 'key', 'loudness',
    'mode', 'speechiness', 'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo', 'time_signature', 'duration_ms', 'lyrics'])

    count = 0  # keeps track of how many songs you have looked at in this chunk

    input = input[iteration*chunksize:].reset_index(drop=True)  # resize the input given the current iteration

    for tuple in input.itertuples():
        features = dict()  # make an empty dictionary
        artist = tuple[2]
        track = tuple[1]

        # get data from Spotify about the song
        features.update(getSongData(spotify, str(artist), str(track)))

        # get the lyrics
        features['lyrics'] = bruteForceGetLyrics(str(artist), str(track))

        # if we didn't get the lyrics, try again with the spotify names (assuming the names were were found through spotify)
        if features['lyrics'] == None and artist != features['artist'] and track != features['song']:
            features['lyrics'] = bruteForceGetLyrics(features['artist'], features['song'])

        # add to the dataframe if smaller than chunksize, print to csv and reset index otherwise
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
        coalesce()

def main():
    auth_manager = SpotifyClientCredentials(client_id=secrets.SPOTIPY_CLIENT_ID, client_secret=secrets.SPOTIPY_CLIENT_SECRET)
    spotify = sp.Spotify(auth_manager=auth_manager)
    
    input = pd.read_csv('input.csv')  # get the (song, artist) tuples to use as input for getting more data
    generateOutput(input, spotify)

if __name__ == "__main__":
    main()