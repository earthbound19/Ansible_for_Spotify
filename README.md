# Ansible for Spotify
Desktop Python script (not mobile phone app) that provides global hotkeys to manipulate Spotify playback and user library, including advanced playlist creation/manipulation (see section: Advanced functionality / library manipulation hotkeys). Although it could potentially be integrated or proted into some other application context.

# Installation / Usage
Alas that it's not necessarily simple to set up or use. But, as an overview:
- Get a Spotify Premium account? :/
- Clone this repository
- Install Python and the dependency libraries
- Set up a Spotify Developer app with client id, secret, and web landing page / redirect URL
- Run this script from the directory it is in:
    python Ansible_for_Spotify.py
- Examine the source code `bindings = [` section to figure out which of the function correspond to which of the below detailed hotkeys, and use said hotkeys while playing music from Spotify :)

# Current functionality and hotkeys/functions:
## General functionality
- create client authorized to manipulate user library, via spotipy library
- read/write/assist setting client keys and user variable in .ini

## Library manipulation functionality / hotkeys

See the see "bindings" comment/section in source code for details.

### Basic playback/library manipulation hotkeys
- pause / resume playback
- like (save) currently playing song (add to user "Liked Songs" playlist/library)
- unlike (unsave) currently playing song (remove from the same)
- jump to previous track
- jump to next track
- change repeat mode (none/list/single)

### Advanced functionality / library manipulation hotkeys
- remove currently playing track from current playlist
- unlike currently playing song, remove from current playlist, and shuffle to discards playlist. (Won't check for nor remove song from additional playlists if it is on them.)
- set currently playing playlist as playlist 1, for operations such as:
  - add currently playing track (from any other playlist or play context, such as recommends queue) to playlist 1
  - shuffle currently playing track (from playlist other than playlist 1) to playlist 1 (remove from current playlist and move to playlist 1)
- Get artist(s) information from currently playing track (artist credit), and create new playlist(s) of all songs of all credited artists (complete discography playlists)
- print currently playing list, song and playlist variables information

Also, a hotkey to exit the program.

# TO DO
- hotkey for toggle shuffle/no shuffle/smart shuffle
- dynamic hotkey assignment
- UI to manage playlist definitions and display hotkeys
- platform-universal systray that displays solid heart if currently playing track in user library, empty heart if not (to help overcome one of Spotify's greatest UI annoyances: the removal of at-a-glance information of whether a song is in the "liked songs" list!) - but to overcome that further, try the old UI via [Spot-X](https://github.com/SpotX-Official/SpotX) 
- multiple playlist definitions and associated playlist manipulation hotkeys?
- figure out auth and client insantiation better such that it:
  - never crashes if possible
  - prompts for auth renewal, if possible
- fix KNOWN ISSUE: the Spotify API seems to routinely reject API authentication, at least the way it's set up here, effectively terminating session/control. More likely to happen after hourse of not using the API. Possible solutions [here](https://stackoverflow.com/questions/48883731/refresh-token-spotipy).

# WISH LIST
Playlist building by advanced control / recommendation / parametric control, for example:
- Build playlists from recommended songs (by base genre/songs seeds), using multigraphs of desired track attributes and genres over time. A sine wave of valence of songs, a constant linear rise of tempo, etc.
- Use Spotify's own shuffle logic and user library information to build or extend another playlist: filter all liked tracks from a playlist into a temporary list, set shuffle mode, and append everything from the queue to the end of another playlist.

### See Also
Things that inspired this:
- [Advanced Controls for Spotify](https://spotifyadvancedcontrols.rekord.cloud/)
- [Spotify All Artist's Tracks](https://chromewebstore.google.com/detail/spotify-artists-all-songs/jdicfniianljldbajoghhnilmnghgmno) - which generally works well but failed for an artist I _really_ wanted to get the discography for :) and also only creates a discography for one artist; where this here Ansible for Spotify gets discographies for all credited artists for a song.

# Why?

Because I like to have absolute control of what music I try, and try _a lot_ of music, with _a lot_ of playlists, and these hotkeys help me burn through music I don't like likety-split, and find and listen to music I do like faster.