# Spotify Scraper

This program takes an input of songs and artists and returns tons of interesting statistics about them, including the number of streams the song has on Spotify and its lyrics.

## How This Works

Utilizing the Spotify API, an song artist pair get's the associated track ID, where Spotify hosts a ton of interesting statistics about tracks and Genius hosts the lyrics for said song artist pair. These values are then gathered and then manipulated so that they are dumped into a csv file, which can then be used for any purpose, including but not limited to data analysis.

## How To Use

Have a .csv in the same folder as this code entiled `output.csv` with the same columns labled `song` and `artist` respectively. Input your `SPOTIPY_CLIENT_ID` and `SPOTIPY_CLIENT_SECRET` in `secrets.py`, and then run! A file `output.csv` will be created when finished that will contain tons of interesting information about the songs that you requested.
