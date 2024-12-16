# DESCRIPTION
# Does various Spotify playback, playlist and user library modifitions with hotkeys (keyboard shortcuts), via Python, with the os, spotipy and the global_hotkeys library.

# DEPENDENCIES
# - a Spotify developer app with cryptography secrets shared with this script.
# - Python and the Spotipy library
# Install spotipy via:
#    pip install spotipy --upgrade
# OR TRY:
#    pip install git+https://github.com/plamere/spotipy.git@master
# install python global hotkeys via:
#    pip install global-hotkeys -U
# code for hotkeys here adapted from example at: https://pypi.org/project/global-hotkeys/

# USAGE
# Install dependencies (See DEPENDENCIES), and run this script with Python, like so, from the directory it is in:
#    python Ansible_for_Spotify.py
# At this writing, 

# CODE
# TO DO
# - error handling of everything so script execution never breaks and I can still infinitely retry creating the auth keys and client :)
# - fetching recommended songs by genre? re https://stackoverflow.com/questions/61624487/extract-artist-genre-and-song-release-date-using-spotipy - although those genres can't be used directly? - but also https://tryapis.com/spotify/api/endpoint-get-recommendations
# - things in the readmy

THIS_SCRIPT_FRIENDLY_NAME = "Ansible for Spotify"

import os, spotipy
from spotipy.oauth2 import SpotifyOAuth
# !----------------------------------------------------------------------
# BEGIN INI PARSER create / read variables from ini into global variables
from extended_configparser.parser import ExtendedConfigParser

# instantiate
config = ExtendedConfigParser()

# check if config file exists; if not, create it blank; otherwise open it:
if not os.path.exists('Ansible_for_Spotify.ini'):
    with open('Ansible_for_Spotify.ini', 'w') as configfile:
            config.write('')
# parse file (does nothing if empty file) :
config.read('Ansible_for_Spotify.ini')

# Function to check for options in section and create them if they don't exist. NOTES:
# - config.read() must be run first.
# - DESCRIPTIVE_COMMENT is optional, and if passed it will be used as a comment on the field in the .ini. If it not passed (if its value is None), no comment will be left for the field.
# - REQUIRED, if passed as True, prompts the user for values to put in the config (.ini) if they don't exist. If passed as False, values are only read if found, but the user isn't prompted for any values).
def set_option_if_not(SECTION_NAME, OPTION_NAME, DESCRIPTIVE_COMMENT = None, REQUIRED = False):
    # check for section and create it if it doesn't exist:
    if not config.has_section(SECTION_NAME) and REQUIRED == True:
        config.add_section(SECTION_NAME)
    if not config.has_option(SECTION_NAME, OPTION_NAME) and REQUIRED == True:
        if DESCRIPTIVE_COMMENT != None:
            print('\n' + DESCRIPTIVE_COMMENT)
        option_value = input(OPTION_NAME + " not set. Enter it:\n")
        config.set(SECTION_NAME, OPTION_NAME, option_value, comment = DESCRIPTIVE_COMMENT)
        with open('Ansible_for_Spotify.ini', 'w') as configfile:
            config.write(configfile)
            # print("Wrote section ", SECTION_NAME, "option/value ", OPTION_NAME, option_value, "To .ini and variable.")
        return option_value
    else:
        try:
            option_value = config[SECTION_NAME][OPTION_NAME]
            print("Have read value for section/option ", SECTION_NAME, OPTION_NAME, " into variable.")
            return option_value
        except:
            return None

def set_option(SECTION_NAME, OPTION_NAME, OPTION_VALUE, DESCRIPTIVE_COMMENT = None):
    if not config.has_section(SECTION_NAME):
        config.add_section(SECTION_NAME)
    config.set(SECTION_NAME, OPTION_NAME, OPTION_VALUE, comment = DESCRIPTIVE_COMMENT)
    with open('Ansible_for_Spotify.ini', 'w') as configfile:
        config.write(configfile)
        # print("Wrote section ", SECTION_NAME, "option/value ", OPTION_NAME, OPTION_VALUE, "To .ini and variable.")


# SETTING GLOBALS HERE:
# function signature reference:
# set_option_if_not(SECTION_NAME, OPTION_NAME, DESCRIPTIVE_COMMENT = None, REQUIRED = None):
USERNAME = set_option_if_not('API_VARIABLES', 'USERNAME', 'Your spotify username, the probably long, unfriendly one, not your display username:', True)
# print("rEAD Wrote section ", SECTION_NAME, " option ", OPTION_NAME, option_value, " to .ini.")
CLIENT_ID = set_option_if_not('API_VARIABLES', 'CLIENT_ID', 'API client ID for this application:', True)
CLIENT_SECRET = set_option_if_not('API_VARIABLES', 'CLIENT_SECRET', 'API client secret for this application:', True)
REDIRECT_URI = set_option_if_not('API_VARIABLES', 'REDIRECT_URI', 'URL to open on setup of API authentication:', True)
# PLAYLIST ID that tracks which are removed from any currently playing playlist are shuffled to; a recycle bin of sorts:
DISCARDS_PLAYLIST_ID = set_option_if_not('USER_VARIABLES', 'DISCARDS_PLAYLIST_ID', 'Playlist for tracks removed from playists and liked songs; effectively a recycle bin:', True)
# REDIRECT_URI = set_option_if_not('API_VARIABLES', 'REDIRECT_URI', 'URL to open on setup of API authentication:')
BACK_SEEK_MS = int(set_option_if_not('USER_VARIABLES', 'BACK_SEEK_MS', 'On skip back, skip this many ms e.g. 5000ms = 5 seconds:', True))
# if that's positive, change it to negative (for intended use of plus a negative number in seeking back):
if (BACK_SEEK_MS > 0):
    BACK_SEEK_MS = (BACK_SEEK_MS * -1)
FORWARD_SEEK_MS = int(set_option_if_not('USER_VARIABLES', 'FORWARD_SEEK_MS', 'On skip forward, skip this many ms e.g. 5000ms = 5 seconds:', True))
# PLAYLIST_ID_1 will here be init as None from the function call if it's not found in the .ini; otherwise it will be set to what is found:
PLAYLIST_ID_1 = set_option_if_not('USER_VARIABLES', 'PLAYLIST_ID_1', 'Optional playlist for track/library moves/deletes:', False)
# END INI PARSER create / read variables from ini into global variables
# !--------------------------------------------------------------------

# SET DEFAULT / BLANK INI BOOKMARKS IF THERE ARE NONE
def initialize_bookmarks_in_ini():
    # Create bookmark sections if they don't exist
    for i in range(0, 10):  # Let's assume you want to create 10 bookmarks
        bookmark_name = f"BOOKMARK {i}"
        if not config.has_section(bookmark_name):
            config.add_section(bookmark_name)
            set_option(bookmark_name, 'playlist_id', 'None')
            set_option(bookmark_name, 'playlist_name', 'Unknown Playlist')
            set_option(bookmark_name, 'track_id', 'None')
            set_option(bookmark_name, 'position_ms', '0')
            set_option(bookmark_name, 'key', str(i).lower())  # Key is 1, 2, 3, etc.

    # Save the INI file with these default bookmark sections
    with open('Ansible_for_Spotify.ini', 'w') as configfile:
        config.write(configfile)
        print("Initialized default blank bookmark sections in INI.")

initialize_bookmarks_in_ini()

API_SCOPE = "user-read-playback-state user-modify-playback-state user-read-currently-playing app-remote-control app-remote-control streaming playlist-read-private playlist-read-collaborative playlist-modify-private playlist-modify-public user-read-playback-position user-library-modify user-library-read"


# BEGIN SET UP API/SPOTIFY CLIENT SpotifyOAuth
# can also be spotipy.oauth2.SpotifyOAuth:
	# DEPRECATED on recommendation of AI code review:
	# AUTH_MANAGER = spotipy.oauth2.SpotifyPKCE(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, scope=API_SCOPE)
# TRYING INSTEAD on recommendation of AI code review:
AUTH_MANAGER = SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI, scope=API_SCOPE)

# Instantiate API client.
sp = spotipy.Spotify(auth_manager=AUTH_MANAGER)

# hotkeys setup:
from global_hotkeys import *
# NOTE: for debug print uncomment the following import:
# import json
import time

# Declare functions that key bindings will use.
# re: https://stackoverflow.com/a/1489838 - forget managing threads, just destroy all of them with the whole program execution. DO IT.
def exit_program():
    os._exit(3)

# Function to find an active device. Returns the first active device's ID or None if no devices are found.
def find_active_device():
    try:
        devices = sp.devices()  # Retrieve all available devices
        # print("Devices List:", devices)
        for device in devices.get('devices', []):
            if device.get('is_active') or device.get('id'):
                # print("Active Device Found:", device['name'], device['id'])
                return device['id']  # Return the first active device's ID
        print("No active devices found.")
        return None
    except Exception as e:
        print("Error finding active device:", e)
        return None

# Function to switch playback to a specified device using its ID
def switch_to_device(device_id):
    try:
        sp.transfer_playback(device_id=device_id, force_play=True)
        print(f"Playback transferred to device: {device_id}")
    except Exception as e:
        print("Error transferring playback:", e)

# Function: pause or start playback, using other functions to find and switch to an active player if no player found:
def pause_or_start_playback():
    # get player playback state and init global boolean of whether paused or playing.
    # TO DO: function outside this that wraps sp.current_playback(), to handle if null or other return from the following because the API isn't connecting this script with any active player?
    try:
        playback = sp.current_playback()
        if not playback:  # If there's no playback context, find and switch to an active device
            print("No active player found. Searching for active devices...")
            active_device_id = find_active_device()
            if active_device_id:
                switch_to_device(active_device_id)
            else:
                print("No active device available. Cannot resume playback.")
                return

        if playback and playback['is_playing']:
            sp.pause_playback()
        else:
            sp.start_playback()
    except Exception as e:
        print(e)
        print("~\nWARNING: no information retrieved for current_playback. Maybe play and pause the player manually, then retry control from this script.")
    
def previous_track():
    ret = sp.previous_track()

# Function: advance playback to next track
def next_track():
    ret = sp.next_track()

# Function: save currently playing track to user library ("like" current song)
def save_track():
    info = sp.current_user_playing_track()
    try:
        playlist_ID = info['context']['external_urls']['spotify']
        track_ID = info['item']['external_urls']['spotify']
        list_of_track_IDs = [track_ID]
        sp.current_user_saved_tracks_add(list_of_track_IDs)
        print("Saved currently playing track", list_of_track_IDs, "to Liked Songs.")
    except Exception as e:
        print(e)
        print("~\nCould not save current track (could not add to Liked Songs).")

def unsave_track():
    info = sp.current_user_playing_track()
    try:
        playlist_ID = info['context']['external_urls']['spotify']
        track_ID = info['item']['external_urls']['spotify']
        list_of_track_IDs = [track_ID]
        sp.current_user_saved_tracks_delete(list_of_track_IDs)
        print("Remove currently playing track", list_of_track_IDs, "from Liked Songs.")
    except Exception as e:
        print(e)
        print("~\nCould not unsave current track (could not add to Liked Songs).")

# change repeat mode; cycles from current to next mode through track mode, context mode, and off:
REPEAT_MODES = ['track', 'context', 'off']
def change_repeat_mode():
    global REPEAT_MODES
    retrieved_playback_state = sp.current_playback()['repeat_state']
    current_repeat_mode_idx = REPEAT_MODES.index(retrieved_playback_state)
    current_repeat_mode_idx += 1
    if current_repeat_mode_idx > 2:
        current_repeat_mode_idx = 0
    state_parameter = REPEAT_MODES[current_repeat_mode_idx]
    sp.repeat(state_parameter)

SHUFFLE_STATES = [True, False]
def toggle_playback_shuffle():
    global SHUFFLE_STATES
    retrieved_playback_state = sp.current_playback()['shuffle_state']
    current_shuffle_state_idx = SHUFFLE_STATES.index(retrieved_playback_state)
    current_shuffle_state_idx += 1
    if current_shuffle_state_idx > 1:
        current_shuffle_state_idx = 0
    state_parameter = SHUFFLE_STATES[current_shuffle_state_idx]
    sp.shuffle(state_parameter)

# set playback position to start of current track
def seek_to_track_start():
    sp.seek_track(0)
    info = sp.current_playback()['progress_ms']
    print(info)

# set playback position forward or backward by seek_ms (milleseconds, negative or positive)
def relative_seek(seek_ms):
    # nested function call here: set current playback progress to current + ms (with ms neg. or positive)
    new_seek_ms_pos = int(sp.current_playback()['progress_ms']) + seek_ms
    # set that to zero if it's negative, to avoid error:
    if new_seek_ms_pos < 0:
        new_seek_ms_pos = 0
    sp.seek_track(new_seek_ms_pos)

# adapted from: https://github.com/spotipy-dev/spotipy/blob/master/examples/artist_discography.py
# def get_artist(name):
#     results = sp.search(q='artist:' + name, type='artist')
#     items = results['artists']['items']
#     if len(items) > 0:
#         return items[0]
#     else:
#         return None

# adapted from: https://github.com/spotipy-dev/spotipy/blob/master/examples/artist_discography.py
def get_album_tracks(album):
    tracks = []
    results = sp.album_tracks(album['id'])
    tracks.extend(results['items'])
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])
    # for i, track in enumerate(tracks):
    # for track in tracks:
        # print(track)
        # logger.info('%s. %s', i + 1, track['name'])
    return tracks

# adapted from: https://github.com/spotipy-dev/spotipy/blob/master/examples/artist_discography.py
def get_artist_albums(artist):
    albums = []
    results = sp.artist_albums(artist['id'], album_type='album')
    albums.extend(results['items'])
    while results['next']:
        results = sp.next(results)
        albums.extend(results['items'])
    # logger.info('Total albums: %s', len(albums))
    # unique = set()  # skip duplicate albums
    # for album in albums:
        # print(album)
    #     name = album['name'].lower()
    #     if name not in unique:
    #         logger.info('ALBUM: %s', name)
    #         unique.add(name)
    #         show_album_tracks(album)
    return albums

# adapted from: https://github.com/spotipy-dev/spotipy/blob/master/examples/artist_discography.py
# def show_artist(artist):
#     logger.info('====%s====', artist['name'])
#     logger.info('Popularity: %s', artist['popularity'])
#     if len(artist['genres']) > 0:
#         logger.info('Genres: %s', ','.join(artist['genres']))

# Print information related to currenlty playing track. Also a gatekeeper function returning False if no playing track, and True and a playback info object from sp.current_user_playing_track().
# print track info; must be passed an info object obtained via: info = sp.current_user_playing_track()
def print_current_track_information(info):
    try:
        track_ID = info['item']['external_urls']['spotify']
        artists = info['item']['artists']
        print("Current track ID:", track_ID)
        print("Artist(s):")
        for artist in artists:
            print("\t", artist['name'])                
        album = info['item']['album']['name']
        track_name = info['item']['name']
        print("Album:\t", album)
        print("Track:\t", track_name)
        return True
    except Exception as e:
        print(e)
        print("No current track context or not found?")
        return False

# TO DO: simplify other places that print this info if they do? By using this function?
def print_information():
    # boolean that may be overriden depending:
    success = True
    info = sp.current_user_playing_track()
    # because in some settings that can result that info is None or there may be other errors:
    try:
        playlist_ID = info['context']['external_urls']['spotify']
        print("~\nCurrent playlist or ID: ", playlist_ID, sep='')
        try:
            playlist_ID = info['context']['external_urls']['spotify']
            playlist_name = sp.playlist(playlist_ID, fields="name")['name']
            print("  name:", playlist_name)
        except Exception as e:
            print(e)
            print("No currently playing playlist context? An album or podcast?")
        success = print_current_track_information(info)
    except Exception as e:
        print(e)
        print("Couldn't obtain track info from current context somehow, or other error?")
        success = False
    print_playlist_1_info()
    if DISCARDS_PLAYLIST_ID:
        print("~\nDiscards playlist ID:", DISCARDS_PLAYLIST_ID)
        try:
            playlist_name = sp.playlist(DISCARDS_PLAYLIST_ID, fields="name")['name']
            print("  name:", playlist_name)
        except Exception as e:
            print(e)
            print("~\nCouldn't obtain playlist information from current context somehow, or other error?")
    else:
        print("~\nNo discards playlist id is set. Things may break if you try to use such a list.")
    if success == False:
        return False
    else:
        return True, info

# make discography playlist from the artist of the currently playing song.
def make_discography_playlist():
    print("Attempting to make discography playlist..")
    to_continue, info = print_information()
    if to_continue:
        playlist_ID = info['context']['external_urls']['spotify']
        try:
            import random
            artists = info['item']['artists']
            print("  Artist(s):")
            for artist in artists:
                # optional dev empty of debug.txt:
                f = open("debug.txt", "w")
                f.write("")
                f.close()
                discography_artist_name = artist['name']; artist_id = artist['id']; artist_URL = artist['external_urls']['spotify']
                print(" ", discography_artist_name, artist_id, artist_URL)
                all_artists_tracks = []
                # all_related_artists_tracks = []
                # get all albums of artist!
                albums = get_artist_albums(artist)
                # get all tracks of albums!
                print("Collecting and filtering tracks by credit to artist", discography_artist_name, ". .")
                for album in albums:
                    tracks = get_album_tracks(album)
                    # check tracks for credit to the artist we're building a playlist for, and only add to an array of tracks if it matches (as artists can end up on albums with other artists where they didn't contribute to other tracks) :
                    for track in tracks:
                        track_artists = track['artists']
                        for track_artist in track_artists:
                            print(". ", end="")
                            if track_artist['name'] == discography_artist_name:
                                all_artists_tracks.append(track['external_urls']['spotify'])
                            # TO DO? - make a separate playlist with these? Or a config item to optionally include them?
                            # else:
                                # all_related_artists_tracks.append(track['external_urls']['spotify'])
                        # f = open("debug.txt", "a")
                        # f.write("\n------------------------------------\n")
                        # f.write(json.dumps(track, indent=4))
                        # f.close()
                        # print("Wrote info from write_currently_playing_track_info() call to debug.txt.")
                print("Done collectiong all tracks for artist. Building discography playlist . . .")
                random_playlist_name_suffix = ''.join((random.choice(' ▔▀▆▄▂▌▐█▊▎░▒▓▖▗▘▙▚▛▜▝▞▟') for i in range(4)))
                new_playlist_name = discography_artist_name + " ~" + random_playlist_name_suffix
                print("MAKING PLAYLIST: ", new_playlist_name)
                user_id = sp.me()['id']
                global THIS_SCRIPT_FRIENDLY_NAME
                playlist_description = 'Everything by this artist on Spotify (or albums etc. in which this artist appears!), courtesy ' + THIS_SCRIPT_FRIENDLY_NAME
                # function reference: user_playlist_create(user, name, public=True, collaborative=False, description='')
                new_playlist_info = sp.user_playlist_create(user_id, new_playlist_name, public=True, collaborative=False, description=playlist_description)
                new_playlist_id = new_playlist_info['external_urls']['spotify']
                print('new_playlist_id', new_playlist_id)
                # API reference for this function: "A maximum of 100 items can be added in one request." So, split them up:
                # Because the list index/slice syntax returns an empty array if we query out of bounds, we can do an infinite loop over elements getting batches of elements from it until it returns empty.
                idx = 0
                print("Number of songs collected for playlist: ", len(all_artists_tracks))
                # . . AND ADD ALL THOSE SONGS TO IT:
                how_many_at_a_time = 100
                while True:
                    tracks_to_add = all_artists_tracks[idx:][:how_many_at_a_time]
                    idx += how_many_at_a_time
                    if tracks_to_add == []:
                        print("Reached end of available tracks to add to playlist.")
                        break
                    else:
                        # this function call adds to the end of a playlist by default, and we're doing that:
                        try:
                            sp.playlist_add_items(new_playlist_id, tracks_to_add)
                        except Exception as e:
                            print(e)
                            print("WARNING: error attempting to add tracks to playlist ", new_playlist_id)
        except Exception as e:
            print(e)
            print("Could not get albums (nor songs) information.")

# function: set a playlist for operations (such as adding a song from another playing list)
def set_playlist_1():
    # check currently playing context or "playlist", check owner of it, and see if the owner is the same as me. If so, save the playlist ID of it to PLAYLIST_ID_1. If it's not the same as me or there's an error trying to get the "playlist" owner, don't set playlist 1 to anything, and notify me (the user).
    info = sp.current_user_playing_track()
    try:
        playlist_ID = info['context']['external_urls']['spotify']
        playlist_name = sp.playlist(playlist_ID, fields="name")['name']
        try:
            playlist_owner = sp.playlist(playlist_ID)['owner']['external_urls']['spotify']
            current_user = sp.me()['external_urls']['spotify']
            global PLAYLIST_ID_1
            if playlist_owner == current_user:
                PLAYLIST_ID_1 = playlist_ID
                print("~\n! SET playlist 1.")
                print_playlist_1_info()
                # write that to the ini for fast setting again on script reload!
                # function signature reference:
                # def set_option(SECTION_NAME, OPTION_NAME, OPTION_VALUE, DESCRIPTIVE_COMMENT = None):
                set_option('USER_VARIABLES', 'PLAYLIST_ID_1', PLAYLIST_ID_1, 'Optional playlist for track/library moves/deletes:')
            else:
                print("~\nCurrent playlist not owned by current user. Can't assign to playlist 1.")
        except Exception as e:
            print(e)
            print("~\nCurrent play context (not a playlist?) not owned by current user. Can't assign to playlist 1.")
    except Exception as e:
        print(e)
        print("~\nCouldn't obtain track info from current context somehow, or other error?")

def print_playlist_1_info():
    global PLAYLIST_ID_1
    if PLAYLIST_ID_1:
        print("~\nPlaylist 1 ID:", PLAYLIST_ID_1)
        try:
            playlist_name = sp.playlist(PLAYLIST_ID_1, fields="name")['name']
            print("  name:", playlist_name)
        except Exception as e:
            print(e)
            print("~\nCouldn't obtain playlist information from current context somehow, or other error?")
    else:
        print("~\nno PLAYLIST_ID_1 is set.")

# Append the currently playing track to playlist 1, if playlist 1 is defined, and only if the track is not already on it.
def add_current_track_to_playlist_1():
    global PLAYLIST_ID_1
    if PLAYLIST_ID_1 == None:
        print("Can't move anything to playlist 1: playlist 1 not defined.")
        return False
    else:
        # get currently playing track:
        info = sp.current_user_playing_track()
        track_id_to_add = info['item']['external_urls']['spotify']
        list_of_track_IDs = [track_id_to_add]
        print_current_track_information(info)
        # get info of target playlist to parse:
        # prior, deprecated track retrieve method; seems I couldn't paginate with it though:
        # items = sp.playlist(PLAYLIST_ID_1)['tracks']['items']
        # last track of prev dev ref.: https://open.spotify.com/track/7tfZ04mgD2fNU2dQ1SrMzG
        print("Retrieving all tracks in target playlist to determine whether track proposed to add is already in playlist . .")
        result = sp.playlist_tracks(PLAYLIST_ID_1, fields=None, limit=100, offset=0, market=None)
        items = result['items']
    while True:
        for item in items:
            track_from_target_list = item['track']['external_urls']['spotify']
            if track_from_target_list == track_id_to_add:
                print('track_from_target_list', track_from_target_list, " == track_id_to_add ", track_id_to_add)
                print("That's already in the target playlist! Not adding.")
                return False
        if result['next']:
            result = sp.next(result)
            items = result['items']
            # without this continue statement the program would go on to the code below to add the track, perhaps erroneously :)
            continue
        # if the check for whether it's already in the list never returned False, we're good to add the track, and this code will do so:
        # this function call adds to the end of a playlist by default, and we're doing that:
        sp.playlist_add_items(PLAYLIST_ID_1, list_of_track_IDs)
        print("ADDED track to playlist ID", PLAYLIST_ID_1)
        print_playlist_1_info()
        return True
    print("FLOW SHOULD NOT SHOW THIS. BLRO")

# function: remove the current song from the current playlist
def remove_current_track_from_current_playlist():
    info = sp.current_user_playing_track()
    try:
        playlist_ID = info['context']['external_urls']['spotify']
        track_ID = info['item']['external_urls']['spotify']
        list_of_track_IDs = [track_ID]
        print("~\nIn a playlist context; will remove currently playing track from the current playlist.")
                # , and play the next song in the playlist
        print("Current playlist ID:", playlist_ID)
        print("track ID:", track_ID)
        sp.playlist_remove_all_occurrences_of_items(playlist_ID, list_of_track_IDs)
        # I've gone back and forth on wanting the following; now I don't :p
        # sp.next_track()
    except Exception as e:
        print(e)
        print("~\nRemove current track from current playlist: cannot; no playlist context.")

def shuffle_current_track_to_playlist_1():
    try:
        proceed = add_current_track_to_playlist_1()
        if proceed:
            remove_current_track_from_current_playlist()
        else:
            print("~\nConditions said don't add to playlist 1; didn't move anything.")
    except Exception as e:
        print(e)
        print("~\nFailure shuffling current track to playlist 1 from current list.")

# Function: if in a playlist context, add currently playing track to discards playlist, remove it from currently playing playlist and user library (liked songs), and play the next song in the playlist.
def unsave_and_move_from_current_playlist_to_discards():
    info = sp.current_user_playing_track()
    try:
        playlist_ID = info['context']['external_urls']['spotify']
        print("~\nDiscards playlist ID:", DISCARDS_PLAYLIST_ID)
        print("Current playlist ID:", playlist_ID)
        print_current_track_information(info)
        track_ID = info['item']['external_urls']['spotify']
        list_of_track_IDs = [track_ID]
        sp.playlist_add_items(DISCARDS_PLAYLIST_ID, list_of_track_IDs)
        sp.current_user_saved_tracks_delete(list_of_track_IDs)
        sp.playlist_remove_all_occurrences_of_items(playlist_ID, list_of_track_IDs)
        print("Added current track to discards playlist, removed it from current playlist and from liked songs, and will play the next song in the playlist.")
        sp.next_track()
    except Exception as e:
        print(e)
        print("~\nUnsave and shuffle current track to discard playlist: no playlist context; cannot remove currently playing track from any playlist.")

# function: if the player is paused, seek 25 ms ahead, sleep for a fraction of a second, then seek back to where it was. attempt to keep the client engaged with the API if playback is paused, which seems to cause at least the API client to forget the player. 
def keepalive_attempt_hack_conditional_wiggle_seek():
    try:
        info = sp.current_playback()
        # possible workaround to keep player connection active; commented out for now:
        if info is None:  # Handle case when no active playback is detected
            print("No active playback. Searching for active player...")
            active_device_id = find_active_device()
            if active_device_id:
                switch_to_device(active_device_id)
                print("Switched to active device.")
            else:
                print("No devices available. Keepalive failed.")
                return
        # Continue only if playback info exists
        if not info['is_playing']:
            current_position  = info['progress_ms'] or 0  # Default to 0 if progress_ms
            # deprecated current ms time acquire method:
            # current_position  = sp.current_user_playing_track()['progress_ms']
            sp.seek_track(current_position  + 64)
            time.sleep(0.02)
            sp.seek_track(current_position)
            # print("~\nRan keepalive_attempt_hack_conditional_wiggle_seek.")
    except Exception as e:
        print("~\nWARNING: no information retrieved for current_playback. Maybe play and pause the player manually, then retry control from this script. OR There was some other error in run of playback position wiggle / keepalive.")

# START BOOKMARK FUNCTIONS REGION
# NOTE THAT LOAD AND SAVE BOOKMARK HOTKEYS are hard-coded in one of these functions (see below).
# A BOOKMARK IS A PLAYLIST, TRACK IN THE PLAYLIST, PLAYBACK POSITION IN THE TRACK, AND PLAYLIST NAME.
# Function: Save the current playback as a bookmark with a specific key
# TO DO:
# - fix difficulty triggering bookmark hotkeys, if possible? I have to press the second hotkey in the sequence so fast. A way to tell the hotkey library to wait longer to register a second key combo in a sequence?
# - fix that nothing can call the following function  unless a bookmark is defined - cannot dynamally make a NEW bookmark definition; WORKAROUND: have initialize_bookmarks_in_ini() pre-save 10 of them which can be overwritten, as they pre-exist:
# - make it clearer in INI and / or somewhere in code how the chained (sequence) bookmark hotkeys work
def save_bookmark(bookmark_key):
    try:
        playback = sp.current_playback()
        if not playback:
            print("No playback context found. Cannot save bookmark.")
            return

        playlist_id = playback['context']['uri'] if playback.get('context') else None
        track_id = playback['item']['id'] if playback.get('item') else None
        position_ms = playback['progress_ms']

        if not track_id:
            print("No track currently playing. Cannot save bookmark.")
            return

        bookmark_name = f"BOOKMARK {bookmark_key}"
        playlist_name = "None"
        if playlist_id and "playlist" in playlist_id:
            try:
                playlist_info = sp.playlist(playlist_id.split(":")[-1], fields="name")
                playlist_name = playlist_info.get('name', 'Unknown Playlist')
            except:
                pass

        # Ensure the bookmark section exists and overwrite the values
        if not config.has_section(bookmark_name):
            config.add_section(bookmark_name)

        # Overwrite the existing bookmark
        set_option(bookmark_name, 'playlist_id', playlist_id or 'None')
        set_option(bookmark_name, 'playlist_name', playlist_name)
        set_option(bookmark_name, 'track_id', track_id)
        set_option(bookmark_name, 'position_ms', str(position_ms))
        set_option(bookmark_name, 'key', bookmark_key)

        # Re-read the configuration file to ensure changes are applied?
        # config.read('Ansible_for_Spotify.ini')
        
        print('Bookmark saved (hopefully) for ', bookmark_key, '.')

        # Re-register hotkeys based on the updated INI
        register_bookmark_hotkeys_from_ini()

        print(f"Bookmark '{bookmark_name}' saved and hotkeys updated.")
    except Exception as e:
        print(f"\tPossible error saving bookmark: {e}")


# Function: Load a bookmark by its second-level key
def load_bookmark(bookmark_key):
    try:
        bookmark_name = f"BOOKMARK {bookmark_key}"
        if not config.has_section(bookmark_name):
            print(f"No bookmark found for key '{bookmark_key}'.")
            return

        playlist_id = config.get(bookmark_name, 'playlist_id', fallback=None)
        playlist_name = config.get(bookmark_name, 'playlist_name', fallback='Unknown Playlist')
        track_id = config.get(bookmark_name, 'track_id', fallback=None)
        position_ms = int(config.get(bookmark_name, 'position_ms', fallback=0))

        if playlist_id and playlist_id != 'None':
            sp.start_playback(context_uri=playlist_id, offset={'uri': f"spotify:track:{track_id}"})
        else:
            sp.start_playback(uris=[f"spotify:track:{track_id}"])

        sp.seek_track(position_ms)
        print(f"Loaded bookmark '{playlist_id}'")
        print(f"Playlist Name '{playlist_name}'.")
    except Exception as e:
        print(f"\tPossible error loading bookmark: {e}")

# LOAD AND SAVE BOOKMARK HOTKEYS HARDCODED HERE:
# Function: Dynamically generate and register bookmark hotkeys from the .ini file
from functools import partial

def register_bookmark_hotkeys_from_ini():
    dynamic_bindings = []
    for section in config.sections():
        if section.startswith("BOOKMARK "):
            bookmark_key = config.get(section, 'key', fallback=None)
            if bookmark_key:
                save_sequence = f"control + alt + shift + b, {bookmark_key}"
                load_sequence = f"control + alt + shift + l, {bookmark_key}"
# binding structure: ["hotkey", on_press_callback, on_release_callback, actuate_on_partial_release, press_callback_params, release_callback_params]
# apparently failed binding dict definition? :
# dynamic_bindings.append({
#     "hotkey": save_sequence,
#     "on_press_callback": None,
#     "on_release_callback": save_bookmark,
#     "actuate_on_partial_release": True,
#     "callback_params": None,
#     "release_callback_params": bookmark_key
# })
                dynamic_bindings.append([
                    save_sequence, None, save_bookmark, True, None, bookmark_key
                ])
                dynamic_bindings.append([
                    load_sequence, None, load_bookmark, True, None, bookmark_key
                ])
                # print(f"Registered hotkeys: '{save_sequence}' (save) and '{load_sequence}' (load) for bookmark '{section}'")
    
    # Register the hotkeys
    for binding in dynamic_bindings:
        # print('binding: ', binding)
        # register_hotkey: Register a single keybinding (if it's not already registered). Returns True if the key didn't already exist and was added, else False (the binding is already registered - remove it first if  you wish to overwrite it with new event handlers).
        if not register_hotkey(binding[0], binding[1], binding[2], binding[3], binding[4], binding[5]):
            removed_success = remove_hotkey(binding[0])
            print('removed_success for hotkey that was already registered: ', removed_success)
            register_hotkey(binding[0], binding[1], binding[2], binding[3], binding[4], binding[5])
        # else:
        #     reg_success = register_hotkey(binding[0], binding[1], binding[2], binding[3], binding[4], binding[5])
        #     print('reg_success for hotkey that was not registered: ', reg_success)
            
    # register_hotkeys(dynamic_bindings)
    # print("Dynamic bookmark hotkeys registered.")

# END BOOKMARK FUNCTIONS REGION


# TO USE??? recommendations(seed_artists=None, seed_genres=None, seed_tracks=None, limit=20, country=None, **kwargs) re recommendations(seed_artists=None, seed_genres=None, seed_tracks=None, limit=20, country=None, **kwargs)

# Declare some key bindings.
# for bindings object structure see the "Explanation of the binding structure" section in the same page; to copy the variant for square brackets:
# ["hotkey", on_press_callback, on_release_callback, actuate_on_partial_release, press_callback_params,release_callback_params]
# Bindings take on the form of:
#   <binding>, on_press_callback, on_release_callback, actuate_on_partial_release_flag, callback_params
# Also, a binding that is keys separated by commas is I think a chord? - a _sequence_ of keys or key combination. If for example it's "a, b", then pressing those two keys in sequence (typing one after the other) will trigger it.
# It's useful to have 'actuate_on_partial_release_flag' set to False, 
# so your modifier keys don't get in the way of any automatic keyboard output you're doing in response.
# Note the actual hotkey syntax. Key combinations are denoted via the '+' character, 
# and additional key chords are separated by commas. Spaces are ignored.

# TO DO: hotkey that prints these bindings with descriptions :)
# For list of available keys see the section with that heading at https://pypi.org/project/global-hotkeys/
# also, binding structure: ["hotkey", on_press_callback, on_release_callback, actuate_on_partial_release, press_callback_params, release_callback_params]
# NOTE: although the documentation for that function says the release callback parameter should be a dict, I could not get that to work and it accepted just a value for it. ?
bindings = [
    # basic:
    ["control + alt + shift + home", None, pause_or_start_playback, True, None, None],
    ["control + alt + shift + s", None, save_track, True, None, None],
    ["control + alt + shift + u", None, unsave_track, True, None, None],
    ["control + alt + shift + page_up", None, previous_track, True, None, None],
    ["control + alt + shift + page_down", None, next_track, True, None, None],
    ["control + alt + shift + r", None, change_repeat_mode, True, None, None],
    ["control + alt + shift + f", None, toggle_playback_shuffle, False, None, None],
    ["control + alt + shift + insert", None, seek_to_track_start, True, None, None],
    ["control + alt + shift + left", None, relative_seek, True, None, BACK_SEEK_MS],
    ["control + alt + shift + right", None, relative_seek, True, None, FORWARD_SEEK_MS],
    # advanced:
    ["control + alt + shift + d", None, remove_current_track_from_current_playlist, False, None, None],
    ["control + alt + shift + x", None, unsave_and_move_from_current_playlist_to_discards, False, None, None],
    ["control + alt + shift + 1", None, set_playlist_1, False, None, None],
    ["control + alt + shift + a", None, add_current_track_to_playlist_1, True, None, None],
    ["control + alt + shift + m", None, shuffle_current_track_to_playlist_1, False, None, None],
    ["control + alt + shift + c", None, make_discography_playlist, False, None, None],
    ["control + alt + shift + i", None, print_information, True, None, None],
    ["control + alt + shift + q", None, exit_program, True, None, None],
]

# Register all of our keybindings
register_hotkeys(bindings)

# Register dynamic keybindings from .ini file.
register_bookmark_hotkeys_from_ini()

# Finally, start listening for keypresses
start_checking_hotkeys()

# START: THINGS BETWEEN THIS AND THE END THIS COMMENT WILL RUN INDEFINITELY
# re: https://stackoverflow.com/a/2223182
# THIS IS AN ATTEMPT TO MAINTAIN API CLIENT AWARENESS OF THE MUSIC PLAYER.
timer_interval = 55

import threading
def f(f_stop):
    keepalive_attempt_hack_conditional_wiggle_seek()
    if not f_stop.is_set():
        # call f() again in timer_interval seconds
        threading.Timer(timer_interval, f, [f_stop]).start()
f_stop = threading.Event()
# start calling f now and every timer_interval seconds thereafter
f(f_stop)
# END: THINGS BETWEEN THIS AND THE END THIS COMMENT WILL RUN INDEFINITELY

# everything after this will only run once
# Monitor global keybindings with an eternal while loop:
while True:
    time.sleep(0.1)