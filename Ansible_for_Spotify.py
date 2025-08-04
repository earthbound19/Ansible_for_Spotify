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
# - move error handling of info window update into that function instead of handling that many places outside that function (which I think I'm doing)?
# / (maybe done?) error handling of everything so script execution never breaks and I can still infinitely retry creating the auth keys and client :)
# - fetching recommended songs by genre? re https://stackoverflow.com/questions/61624487/extract-artist-genre-and-song-release-date-using-spotipy - although those genres can't be used directly? - but also https://tryapis.com/spotify/api/endpoint-get-recommendations
# - things in the readme

THIS_SCRIPT_FRIENDLY_NAME = "Ansible for Spotify"

import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import threading
from threading import Thread

# !----------------------------------------------------------------------
# BEGIN INI PARSER create / read variables from ini into global variables
from extended_configparser.parser import ExtendedConfigParser

# instantiate
config = ExtendedConfigParser()

# check if config file exists; if not, create it blank; otherwise open it:
if not os.path.exists('Ansible_for_Spotify.ini'):
    with open('Ansible_for_Spotify.ini', 'w', encoding='UTF-8') as configfile:
            config.write('')
# parse file (does nothing if empty file) :
config.read('Ansible_for_Spotify.ini', encoding='UTF-8')

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
        with open('Ansible_for_Spotify.ini', 'w', encoding='UTF-8') as configfile:
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
    # mitigate possible rong type error, though apparently name doesn't have to be a string:
    SECTION_NAME = str(SECTION_NAME); OPTION_NAME = str(OPTION_NAME); OPTION_VALUE = str(OPTION_VALUE)
    if not config.has_section(SECTION_NAME):
        config.add_section(SECTION_NAME)
    config.set(SECTION_NAME, OPTION_NAME, OPTION_VALUE, comment = DESCRIPTIVE_COMMENT)
    with open('Ansible_for_Spotify.ini', 'w', encoding='UTF-8') as configfile:
        config.write(configfile)
        # print("Wrote section ", SECTION_NAME, "option/value ", OPTION_NAME, OPTION_VALUE, "To .ini and variable.")


# SETTING GLOBALS HERE:
# function signature reference:
# set_option_if_not(SECTION_NAME, OPTION_NAME, DESCRIPTIVE_COMMENT = None, REQUIRED = None):
USERNAME = set_option_if_not('API_VARIABLES', 'USERNAME', 'Your spotify username, probably your email address associated with your user at developer.spotify.com/dashboard - or possibly a long random characters username, and not your display username:', True)
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
# TO DO: clearer messages about whether / what it initialized? Because it says it did even if it didn't, I think.
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
            set_option(bookmark_name, 'key', i)

    # Save the INI file with these default bookmark sections
    with open('Ansible_for_Spotify.ini', 'w', encoding='UTF-8') as configfile:
        config.write(configfile)
        print("Initialized default blank bookmark sections in INI.")

initialize_bookmarks_in_ini()

API_SCOPE = "user-read-playback-state user-modify-playback-state user-read-currently-playing app-remote-control app-remote-control streaming playlist-read-private playlist-read-collaborative playlist-modify-private playlist-modify-public user-read-playback-position user-library-modify user-library-read"


# BEGIN SET UP API/SPOTIFY CLIENT SpotifyOAuth
# can also be spotipy.oauth2.SpotifyOAuth:
	# DEPRECATED on recommendation of AI code review:
	# AUTH_MANAGER = spotipy.oauth2.SpotifyPKCE(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, scope=API_SCOPE)
# TRYING INSTEAD on recommendation of AI code review:
# import sys
# print("USERNAME IS", USERNAME)
# sys.exit(0)
AUTH_MANAGER = SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI, scope=API_SCOPE, username=USERNAME)

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
            # global used elsewhere to determine whether to poll API based on playback state:
            global continue_keepalive_poll
            continue_keepalive_poll = True
            # debug print only; comment out for production:
            # print("Set continue_keepalive_poll to True.")
    except Exception as e:
        print("~\nWARNING: no information retrieved for current_playback. If you're playing a device, maybe play and pause the player manually, then retry control from this script.")
        print(e)
    update_info_window()
    
def previous_track():
    ret = sp.previous_track()
    update_info_window()

# Function: advance playback to next track
def next_track():
    ret = sp.next_track()
    update_info_window()

# Function: save currently playing track to user library ("like" current song)
def save_track():
    info = sp.current_user_playing_track()
    try:
        playlist_ID = info['context']['external_urls']['spotify']
        track_ID = info['item']['external_urls']['spotify']
        list_of_track_IDs = [track_ID]
        sp.current_user_saved_tracks_add(list_of_track_IDs)
        print("Saved currently playing track", list_of_track_IDs, "to Liked Songs.")
        print("Attempted confirm:")
        update_info_window(CLI_print = True)
    except Exception as e:
        print("~\nCould not save current track (could not add to Liked Songs).")
        print(e)

def unsave_track():
    info = sp.current_user_playing_track()
    try:
        playlist_ID = info['context']['external_urls']['spotify']
        track_ID = info['item']['external_urls']['spotify']
        list_of_track_IDs = [track_ID]
        sp.current_user_saved_tracks_delete(list_of_track_IDs)
        print("Remove currently playing track", list_of_track_IDs, "from Liked Songs.")
        print("Attempted confirmation:")
        update_info_window(CLI_print = True)
    except Exception as e:
        print("~\nCould not unsave current track (could not add to Liked Songs).")
        print(e)

# change repeat mode; cycles from current to previous mode and wraps around; e.g. no repeat, playlist repeat, then track repeat:
REPEAT_MODES = ['track', 'context', 'off']
def change_repeat_mode():
    global REPEAT_MODES
    retrieved_playback_state = sp.current_playback()['repeat_state']
    current_repeat_mode_idx = REPEAT_MODES.index(retrieved_playback_state)
    current_repeat_mode_idx -= 1
    if current_repeat_mode_idx < 0:
        current_repeat_mode_idx = 2
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
def print_current_track_information():
    try:
        info = sp.current_user_playing_track()
        track_URL = info['item']['external_urls']['spotify']
        artists = info['item']['artists']
        print("Current track URL (ends with ID) :", track_URL)
        print("Artist(s):")
        for artist in artists:
            print("\t", artist['name'])                
        album = info['item']['album']['name']
        track_name = info['item']['name']
        print("Album:\t", album)
        print("Track:\t", track_name)
        return True
    except Exception as e:
        print("No current track context, or not found, or other API error?")
        print(e)
        return False

# TO DO: simplify other places that print this info if they do? By using this function?
def print_information():
    print_playlist_1_info()
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
            success = print_current_track_information()
        except Exception as e:
            print("No currently playing playlist context? An album or podcast?")
            print(e)
        try:
            update_info_window(CLI_print = True)
        except Exception as e:
            print("Error attempting to update user saved tracks (Liked Songs) track info_window:")
            print(e)
    except Exception as e:
        print("Couldn't obtain track info from current context somehow, or other error?")
        print(e)
        success = False
    if DISCARDS_PLAYLIST_ID:
        print("~\nDiscards playlist ID:", DISCARDS_PLAYLIST_ID)
        try:
            playlist_name = sp.playlist(DISCARDS_PLAYLIST_ID, fields="name")['name']
            print("  name:", playlist_name)
        except Exception as e:
            print("~\nCouldn't obtain playlist information from current context somehow, or other error?")
            print(e)
    else:
        print("~\nNo discards playlist id is set. Things may break if you try to use such a list.")
    if success == False:
        return False
    else:
        return True, info

# this function is a stub that creates a threaded function call, because if the called function was not threaded, it would be blocking, as it uses time.sleep. If it weren't threaded, the time.sleep wait could block user hotkey presses, which would annoyingly prevent the user from using the hotkeys during time.sleep. Threaded, it's non-blocking, and the user can use the hotkeys while it's running.
# First required parameter is an object that is an instance of class GlyphWindow
# Can take an optional parameter CLI_print which when passed to the threaded function causes it to print info to CLI.
def update_info_window(CLI_print = False):
    global info_window
    # pass on the CLI_print parameter:
    thread = threading.Thread(target=threaded_update_info_window, args = [CLI_print])
    thread.start()

# can pass along optional parameter; if this parameter is passed and is anything other than False, info is printed to the CLI about whether the currently playing track is in the user's saved tracks (Liked Songs) :
def threaded_update_info_window(CLI_print = False):
    # It seems that right at script launch, info_window doesn't exist for a bit, so this has to be tried end excepted:
    try:
        info_window.update_glyph("❓")
    except:
        print("No glyph info_window object to update (yet?), apparently.")
    # wait a bit before calling print track info because it can take a bit before a track change happens:
    time.sleep(0.67)
    # avoids runtime error of info variable being undeclared:
    info = None
    try:
        info = sp.current_user_playing_track()
    except Exception as e:
        print("Error running function to attempt to retrieve playing track info. If you have an active player, maybe play and pause the player manually, then retry control from this script. OR There was some other error. Printing the error response:")
        print(e)
    if info != None:
        track_ID = info['item']['id']
        album = info['item']['album']['name']
        # truncate to a number of characters displayable in the info window:
        if len(album) > 46:
            album = album[:46] + " ..."
        track_name = info['item']['name']
        # truncate this also:
        if len(track_name) > 54:
            track_name = track_name[:54] + " ..."
        # This function expects a list, so track_ID is put into on in the call by surrounding it with []:
        is_in_user_saved_tracks = sp.current_user_saved_tracks_contains([track_ID])
        # That's a 1-lenght array, odd. The first and only element in it can be used as True or False:
        if is_in_user_saved_tracks[0]:
            if CLI_print != False:
                print("💚🎵💛 Currently playing track ID " + track_ID + " is in user saved tracks (Liked Songs)!")
            info_window.update_glyph("🖤\n" + album + "\n~ " + track_name)
            #  + "\n" + album_name + "\n" + track_name
        else:
            if CLI_print != False:
                print("🖤 Currently playing track ID " + track_ID + " is NOT in user saved tracks (Liked Songs).")
            info_window.update_glyph("🤍\n~ " + album + "\n ~" + track_name)

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
                # TO DO: open and close that file only once instead of repeatedly in a loop over artists here?
                # f = open("debug.txt", "w", encoding='utf_8')
                # f.write("")
                # f.close()
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
                            print("WARNING: error attempting to add tracks to playlist ", new_playlist_id)
                            print(e)
        except Exception as e:
            print("Could not get albums (nor songs) information.")
            print(e)

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
            print("~\nCurrent play context (not a playlist?) not owned by current user. Can't assign to playlist 1.")
            print(e)
    except Exception as e:
        print("~\nCouldn't obtain track info from current context somehow, or other error?")
        print(e)

def print_playlist_1_info():
    global PLAYLIST_ID_1
    if PLAYLIST_ID_1:
        print("~\nPlaylist 1 ID:", PLAYLIST_ID_1)
        try:
            playlist_name = sp.playlist(PLAYLIST_ID_1, fields="name")['name']
            print("  name:", playlist_name)
        except Exception as e:
            print("~\nCouldn't obtain playlist information from current context somehow, or other error?")
            print(e)
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
        print_current_track_information()
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
        print("~\nRemove current track from current playlist: cannot; no playlist context.")
        print(e)

def shuffle_current_track_to_playlist_1():
    try:
        proceed = add_current_track_to_playlist_1()
        if proceed:
            remove_current_track_from_current_playlist()
        else:
            print("~\nConditions said don't add to playlist 1; didn't move anything.")
    except Exception as e:
        print("~\nFailure shuffling current track to playlist 1 from current list.")
        print(e)

# Function: if in a playlist context, add currently playing track to discards playlist, remove it from currently playing playlist and user library (liked songs), and play the next song in the playlist.
def unsave_and_move_from_current_playlist_to_discards():
    info = sp.current_user_playing_track()
    try:
        playlist_ID = info['context']['external_urls']['spotify']
        print("~\nDiscards playlist ID:", DISCARDS_PLAYLIST_ID)
        print("Current playlist ID:", playlist_ID)
        print_current_track_information()
        track_ID = info['item']['external_urls']['spotify']
        list_of_track_IDs = [track_ID]
        sp.playlist_add_items(DISCARDS_PLAYLIST_ID, list_of_track_IDs)
        sp.current_user_saved_tracks_delete(list_of_track_IDs)
        sp.playlist_remove_all_occurrences_of_items(playlist_ID, list_of_track_IDs)
        print("Added current track to discards playlist, removed it from current playlist and from liked songs, and will play the next song in the playlist.")
        print("Attempted confirm:")
        update_info_window(CLI_print = True)
        sp.next_track()
    except Exception as e:
        print("~\nUnsave and shuffle current track to discard playlist: no playlist context; cannot remove currently playing track from any playlist. Printing the error response:")
        print(e)

keepalive_playback_paused_poll_count = 0
continue_keepalive_poll = True
# function: if the player is paused, seek 25 ms ahead, sleep for a fraction of a second, then seek back to where it was. attempt to keep the client engaged with the API if playback is paused, which seems to cause at least the API client to forget the player. 
def keepalive_poll():
    global keepalive_playback_paused_poll_count
    global continue_keepalive_poll
    # NOTE: because this will lever execute if that's false, the following boolean must be set True somewhere else!
    if continue_keepalive_poll:
        try:
            info = sp.current_playback()
            # OPTIONAL info write to txt file; comment out for production:
            # f = open("debug.txt", "a")        # alternately use this to append instead of overwrite
            # f = open("debug.txt", "w", encoding='utf_8')
            # f.write("\n------------------------------------\n")
            # f.write(json.dumps(info, indent=4))
            # f.close()
            # print("------Wrote info from current_playback() call to debug.txt.")
            if info['is_playing'] == False or info['is_playing'] == None:
                keepalive_playback_paused_poll_count += 1
                # debug print only; comment out in production:
                # print("Playback may be paused; keepalive_playback_paused_poll_count is", keepalive_playback_paused_poll_count)
                # if we've queried this 4 times and it's paused, stop spamming the API; exit the script.
                if keepalive_playback_paused_poll_count == 6:
                    continue_keepalive_poll = False
                    print("Playback found to be paused through 6 checks; suspending keepalive attempts until you manually resume playback with a hotkey from this script _or_ restart the script.")
                    # print("Playback found to be paused through 6 checks; quitting script to avoid API queries. Exit code 1.")
                    # os._exit(1)
            else:
                # reset paused playback counter:
                keepalive_playback_paused_poll_count = 0
                # debug print only; comment out in production:
                # print("Playback may be active; keepalive_playback_paused_poll_count is", keepalive_playback_paused_poll_count)
            # That's it. I'm just hoping that querying playback status keeps this API client authenticated / active as far as the API host is concerned.
            # print("~\nRan keepalive_poll.")
        except Exception as e:
            print("~\nError running function to attempt to retrieve playback info. If you have an active player, maybe play and pause the player manually, then retry control from this script. OR There was some other error. Printing the error response:")
            print(e)
        # OPTIONAL: uncomment the remainder of this function to turn this script into a keepalive tool, by using a hotkey (key combination) that does nothing:
        # if 'pyautogui' not in globals():
        #     import pyautogui
        # pyautogui.FAILSAFE = False
        # pyautogui.hotkey('altleft', 'pageup')     # a keypress instead would look like: pyautogui.typewrite(['fn', '\r'])

# START BOOKMARK FUNCTIONS REGION
# NOTE THAT LOAD AND SAVE BOOKMARK HOTKEYS are hard-coded in one of these functions (see below).
# A BOOKMARK IS A PLAYLIST, TRACK IN THE PLAYLIST, PLAYBACK POSITION IN THE TRACK, AND PLAYLIST NAME.
# Function: Save the current playback as a bookmark with a specific key
# TO DO:
# - fix that on saving ANY bookmark it throws: Possible error saving bookmark: The hotkey [[['control', 'alt', 'shift', 'b'], ['1']]] is already registered.
# - fix difficulty triggering bookmark hotkeys, if possible? I have to press the second hotkey in the sequence so fast. A way to tell the hotkey library to wait longer to register a second key combo in a sequence?
# - fix that nothing can call the following function unless a bookmark is defined - cannot dynamally make a NEW bookmark definition; WORKAROUND: have initialize_bookmarks_in_ini() pre-save 10 of them which can be overwritten, as they pre-exist:
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
        # config.read('Ansible_for_Spotify.ini', encoding='UTF-8')
        
        print('Bookmark saved (hopefully) for ', bookmark_key, '.')

        # Re-register hotkeys based on the updated INI
        register_bookmark_hotkeys_from_ini()

        print(f"Bookmark '{bookmark_name}' saved and hotkeys updated.")
    except Exception as e:
        print(f"\tPossible error saving bookmark.")
        print(e)


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
        print(f"\tPossible error loading bookmark.")
        print(e)

# LOAD AND SAVE BOOKMARK HOTKEYS HARDCODED HERE:
# Function: Dynamically generate and register bookmark hotkeys from the .ini file
def register_bookmark_hotkeys_from_ini():
    dynamic_bindings = []
    for section in config.sections():
        if section.startswith("BOOKMARK "):
            bookmark_key = config.get(section, 'key', fallback=None)
            if bookmark_key:
                save_sequence = f"control + alt + shift + b, {bookmark_key}"
                load_sequence = f"control + alt + shift + l, {bookmark_key}"
# binding structure: ["hotkey", on_press_callback, on_release_callback, actuate_on_partial_release, press_callback_params, release_callback_params]
                dynamic_bindings.append([save_sequence, None, save_bookmark, True, None, bookmark_key])
                dynamic_bindings.append([load_sequence, None, load_bookmark, True, None, bookmark_key])
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
    ["control + alt + shift + r", None, change_repeat_mode, True, None, None],
    ["control + alt + shift + f", None, toggle_playback_shuffle, False, None, None],
    ["control + alt + shift + home", None, pause_or_start_playback, True, None, None],
    ["control + alt + shift + insert", None, seek_to_track_start, True, None, None],
    ["control + alt + shift + left", None, relative_seek, True, None, BACK_SEEK_MS],
    ["control + alt + shift + right", None, relative_seek, True, None, FORWARD_SEEK_MS],
    ["control + alt + shift + page_up", None, previous_track, True, None, None],
    ["control + alt + shift + page_down", None, next_track, True, None, None],
    ["control + alt + shift + s", None, save_track, True, None, None],
    ["control + alt + shift + u", None, unsave_track, True, None, None],
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

# START: THINGS BETWEEN THIS AND THE END OF THIS COMMENT WILL RUN INDEFINITELY
# re: https://stackoverflow.com/a/2223182
# THIS IS AN ATTEMPT TO MAINTAIN API CLIENT AWARENESS OF THE MUSIC PLAYER.
timer_interval = 82

import threading
def f(f_stop):
    keepalive_poll()
    update_info_window()
    if not f_stop.is_set():
        # call f() again in timer_interval seconds
        threading.Timer(timer_interval, f, [f_stop]).start()
f_stop = threading.Event()
# start calling f now and every timer_interval seconds thereafter
f(f_stop)
# END: THINGS BETWEEN THIS AND THE END OF THIS COMMENT WILL RUN INDEFINITELY

# START: OTHER THINGS BETWEEN THIS AND THE END OF THIS COMMENT WILL RUN INDEFINITELY
# re https://stackoverflow.com/a/2223191 - another answer with the above linked, which seems like a far simpler way to implement a repeated threaded task? And maybe would obviate other code my above timer calls needing threading?
# TO DO: ^ EXAMINE THAT and re-implement it if it is simpler
# POLL the current playing track ID every N seconds (wait_between_checks), and update the info window glyph if it has changed, to keep display of whether the current playing track is in the user saved tracks (Liked Songs) pretty current:
last_remembered_track_ID = ''
wait_between_checks = 6.5
class BackgroundTimer(Thread):
    def run(self):
        global last_remembered_track_ID
        global continue_keepalive_poll
        while 1:
            time.sleep(wait_between_checks)
            # only do things if a booloean modified in keepalive_poll() is true; this will avoid pointlessly spamming the API for track info if there's little reason to believe it's updated:
            # avoids runtime error of info being undeclared:
            info = None
            if continue_keepalive_poll:
                try:
                    info = sp.current_user_playing_track()
                except Exception as e:
                    print("Error running function to attempt to retrieve playing track info. If you have an active player, maybe play and pause the player manually, then retry control from this script. OR There was some other error. Printing the error response:")
                    print(e)
                if info != None:
                    current_track_ID = info['item']['id']
                    if last_remembered_track_ID != current_track_ID:
                        print("Active playback polling: DIFFERENT track ID ", current_track_ID, " than last seen " + last_remembered_track_ID + " -- will try to update user saved tracks (Liked Songs) track info_window.")
                        update_info_window(CLI_print = True)
                        last_remembered_track_ID = current_track_ID
                        # reset this that another loop uses :/ complicated
                        global keepalive_playback_paused_poll_count
                        keepalive_playback_paused_poll_count = 0
            # optional; probably was more useful in development:
            # else:
            #     print("Monitoring of playing track info suspended because of paused or unknown playback state over time; to resume track monitoring, unpause playback with the hotkey of this script.")
timer = BackgroundTimer()
timer.start()
# END: OTHER THINGS BETWEEN THIS AND THE END OF THIS COMMENT WILL RUN INDEFINITELY

import current_track_in_user_tracks_display
# info_window is a global used all over the place!
info_window = current_track_in_user_tracks_display.GlyphWindow()
# info_window.update_glyph("_")
update_info_window()
info_window.run()

# everything after this will only run once
# Monitor global keybindings with an eternal while loop:
while True:
    time.sleep(0.1)