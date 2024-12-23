# Ansible for Spotify
Desktop Python script (not mobile phone app) that provides global hotkeys to manipulate Spotify playback and user library, including advanced playlist creation/manipulation (see section: Advanced functionality / library manipulation hotkeys). Although it could potentially be integrated or ported into some other application context.

# Installation / Usage
Alas that it's not necessarily simple to set up or use. But, as an overview:
- Get a Spotify Premium account? :/
- Clone this repository
- Install Python and the dependency libraries
- Set up a Spotify Developer app with client id, secret, and web landing page / redirect URL
- Run this script from the directory it is in: `python Ansible_for_Spotify.py`
- Examine the source code `bindings = [` section to figure out which of the function correspond to which of the below detailed hotkeys, and use said hotkeys while playing music from Spotify :) Sorry, at this writing if you don't like the hotkey assignments you must hack them to change them. (See TO DO.)

# Current functionality and hotkeys/functions:
## General functionality
- create client authorized to manipulate user library, via spotipy library
- read/write/assist setting client keys and user variable in .ini

## Library manipulation functionality / hotkeys

See the see `bindings = [` comment/section in source code for details.

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

### Known Issues
It seems that the API call to delete a track from a list also deletes everything by the same artist from a list if you filter a playlist view by search term. This may also happen with the API to unsave a track from your Liked Songs. Untested.

# TO DO (up next if not already in progress)
- platform-universal systray that displays solid heart if currently playing track in user library, empty heart if not (to help overcome one of Spotify's greatest UI annoyances: the removal of at-a-glance information of whether a song is in the "liked songs" list!) - but to overcome that further, try the old UI via [Spot-X](https://github.com/SpotX-Official/SpotX) 
- bookmarks save / load. by hotkey chord? e.g. [key combo to tell script we're saving a bookmark], [key to say which number of bookmark (1-9?)]
- figure out auth and client insantiation better such that it:
  - never crashes if possible
  - maintians or consistently renews authorization (and/or prompts for auth renewal, if possible), to FIX KNOWN ISSUE: the Spotify API seems to routinely reject API authentication, at least the way it's set up here, effectively terminating session/control. More likely to happen after hours of not using the API. Possible solutions [here](https://stackoverflow.com/questions/48883731/refresh-token-spotipy).
- Dynamic (re)defining playlists from/to .ini (including code that dynamically reassigns their associated hotkeys live)
- A dynamic HUD GUI for display / search / assignment of various playlists to various variables (playlist numbers, sort playlist, discard playlist)
- multiple playlist definitions and associated playlist manipulation hotkeys?
- Upgrade discography playlist creation to be split into multiple playlists if it breaks the limit - Frederic Chopin broke it at 11,000!

# WISH LIST (backlog)
- Option to split music found by other artists into other discography playlists when building discography playlist(s)?
- A local synced database to do some of the following (and potentially other things) much faster
Playlist building by advanced control / recommendation / parametric control, for example:
- Find every instance of a song in your library (in every playlists, at the custom sort position it is in), and swap it with with another song. Use cases: updating one performance of a standard work (or "classic") for another, or swapping a single for an album track of the same song
  - and optionally delete the replaced song from liked songs
- Build playlists from recommended songs (by base genre/songs seeds), using multigraphs of desired track attributes and genres over time. For example, a rising sine wave of valence of songs, a linear rise of songs tempo, etc.
- Use Spotify's own shuffle logic and user library information to build or extend another playlist: filter all tracks in a playlist which are also in the "Liked Songs" library (playlist) into a temporary list, set shuffle mode, and append everything from the queue to the end of another playlist.
   - Similar multigraphing of track attributes to build or extend a playlists that way
- library import / export (re [exportify](https://exportify.net/), but with import also, for example to import arbitrary music (e.g. from prior/other library exports))

### See Also
Things that inspired this:
- [Advanced Controls for Spotify](https://spotifyadvancedcontrols.rekord.cloud/)
- [Spotify All Artist's Tracks](https://chromewebstore.google.com/detail/spotify-artists-all-songs/jdicfniianljldbajoghhnilmnghgmno) - which generally works well but failed for an artist I _really_ wanted to get the discography for :) and also only creates a discography for one artist; where this here Ansible for Spotify gets discographies for all credited artists for a song.

# Why?

Because I like to have absolute control of what music I try (instead of relying on nebulous, undefinable AI features--although those have found me many things I love), and try _a lot_ of music, with _a lot_ of playlists, and these hotkeys help me burn through music I don't like likety-split, and find and listen to music I do like faster.