import spotipy as sp
from spotipy.oauth2 import SpotifyClientCredentials
import secrets
import json

def main():
    auth_manager = SpotifyClientCredentials(client_id=secrets.SPOTIPY_CLIENT_ID, client_secret=secrets.SPOTIPY_CLIENT_SECRET)
    spotify = sp.Spotify(auth_manager=auth_manager)
    artist = "Adele"
    title = "Easy On Me"
    q = "track:\"%s\"artist:\"%s\"" % (title, artist)
    print(q)
    result = spotify.search(q, limit=1, offset=0, type='track', market='US')
    file = json.dumps(result, indent=4)

    # Writing to sample.json
    with open("test.json", "w") as outfile:
        outfile.write(file)

if __name__ == "__main__":
    main()