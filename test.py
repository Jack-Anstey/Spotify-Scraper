track = "M Y . L I F E"

track = track.translate(track.maketrans("", "", "',.\"&+':()^#@_{=}|\\`~/<>;*?"))  # remove most puncuation
track = str(track.replace(' ','-')) if ' ' in track else str(track)  # replace spaces with dashes
track = track.replace("$", "-").replace("!", "-").replace("--", "-")  # replace with a dash instead of nothing

print(track)