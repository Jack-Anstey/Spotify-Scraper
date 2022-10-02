artist = "p!nk--szn"

artist = artist.translate(artist.maketrans("", "", "',.\"&+':()^#@_{=}|\\`~/<>;*?"))
artist = artist.replace("$", "-").replace("!", "-").replace("--", "-")  # replace with a dash instead of nothing

print(artist)