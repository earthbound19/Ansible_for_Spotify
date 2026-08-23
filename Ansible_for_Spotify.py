# DESCRIPTION
# Does various Spotify playback, playlist and user library modifitions with hotkeys (keyboard shortcuts), via Python, with the os, spotipy and the global_hotkeys library.

# DEPENDENCIES
# - a Spotify developer app with cryptography secrets shared with this script.
# - Python and the Spotipy library
# Install spotipy via:
#    pip install spotipy --upgrade
# - A web host you control, to upload /ansible-web-auth-php/index.php at
#  - set the permissions for the containing folder to 755
#  - set the permissions for index.php to 644
# - set variables in Ansible_for_Spotify.ini such that they include the path to that PHP page at your host, e.g.:
# redirect_uri = https://earthbound.io/ansible-spotify/
#
# Alternate install method for Spotipy:
#    pip install git+https://github.com/plamere/spotipy.git@master
# install python global hotkeys via:
#    pip install global-hotkeys -U
# code for hotkeys here adapted from example at: https://pypi.org/project/global-hotkeys/

# USAGE
# Install dependencies (See DEPENDENCIES), and run this script with Python, like so, from the directory it is in:
#    python Ansible_for_Spotify.py
# On first run it will interactively prompt for needed INI values (see below for INI config), then open an authentication workflow.

# CONFIGURATION - Ansible_for_Spotify.ini
# The script creates Ansible_for_Spotify.ini on first run if it doesn't exist.
# You'll be prompted interactively for required values.
#
# Required fields (prompted on first run):
#   [API_VARIABLES]
#   USERNAME        - Your Spotify account email or username
#   CLIENT_ID       - From Spotify Developer Dashboard
#   CLIENT_SECRET   - From Spotify Developer Dashboard  
#   REDIRECT_URI    - Your web host callback URL (e.g., https://earthbound.io/ansible-spotify/)
#
#   [USER_VARIABLES]
#   DISCARDS_PLAYLIST_ID - Playlist ID for "recycled" tracks (e.g., spotify:playlist:xxx)
#   BACK_SEEK_MS         - Milliseconds to skip backward (e.g., 5000 = 5 seconds)
#   FORWARD_SEEK_MS      - Milliseconds to skip forward (e.g., 5000 = 5 seconds)
#
# Optional field (can be set manually or via Ctrl+Alt+Shift+1 hotkey):
#   [USER_VARIABLES]
#   PLAYLIST_ID_1   - Target playlist for move/shuffle operations
#
# Auto-generated bookmark sections (10 slots, BOOKMARK 0 through BOOKMARK 9):
#   Each stores playlist_id, playlist_name, track_id, position_ms, and key


# CODE
# TO DO
# - move error handling of info window update into that function instead of handling that many places outside that function (which I think I'm doing)?
# / (maybe done?) error handling of everything so script execution never breaks and I can still infinitely retry creating the auth keys and client :)
# - fetching recommended songs by genre? re https://stackoverflow.com/questions/61624487/extract-artist-genre-and-song-release-date-using-spotipy - although those genres can't be used directly? - but also https://tryapis.com/spotify/api/endpoint-get-recommendations
# - things in the readme

THIS_SCRIPT_FRIENDLY_NAME = "Ansible for Spotify"
SCRIPT_VERSION_STRING = "4.5.37"

import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException
import threading
from threading import Thread
from functools import wraps

import tent_pole_sort_for_ansible_for_spotify as tent_pole_sort

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
CLIENT_ID = set_option_if_not('API_VARIABLES', 'CLIENT_ID', 'API client ID for this application:', True)
CLIENT_SECRET = set_option_if_not('API_VARIABLES', 'CLIENT_SECRET', 'API client secret for this application:', True)
REDIRECT_URI = set_option_if_not('API_VARIABLES', 'REDIRECT_URI', 'URL to open on setup of API authentication:', True)
# PLAYLIST ID that tracks which are removed from any currently playing playlist are shuffled to; a recycle bin of sorts:
DISCARDS_PLAYLIST_ID = set_option_if_not('USER_VARIABLES', 'DISCARDS_PLAYLIST_ID', 'Playlist for tracks removed from playists and liked songs; effectively a recycle bin:', True)
REDIRECT_URI = set_option_if_not('API_VARIABLES', 'REDIRECT_URI', 'URL to open on setup of API authentication:')
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
            set_option(bookmark_name, 'key', i)

    # Save the INI file with these default bookmark sections
    with open('Ansible_for_Spotify.ini', 'w', encoding='UTF-8') as configfile:
        config.write(configfile)
        print("Initialized default blank bookmark sections in INI.")

initialize_bookmarks_in_ini()

API_SCOPE = "user-read-playback-state user-modify-playback-state user-read-currently-playing app-remote-control app-remote-control streaming playlist-read-private playlist-read-collaborative playlist-modify-private playlist-modify-public user-read-playback-position user-library-modify user-library-read"

AUTH_MANAGER = SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI, scope=API_SCOPE, username=USERNAME)

# Instantiate API client.
sp = spotipy.Spotify(auth_manager=AUTH_MANAGER)

# hotkeys setup:
from global_hotkeys import *
import time

# Declare global control flags for polling & exception suppression
continue_keepalive_poll = True
keepalive_playback_paused_poll_count = 0
track_info_exception_raised = False

# Helper function to reset keepalive and exception states
def reset_keepalive_state():
    global continue_keepalive_poll
    global track_info_exception_raised
    global keepalive_playback_paused_poll_count
    continue_keepalive_poll = True
    track_info_exception_raised = False
    keepalive_playback_paused_poll_count = 0

# Decorator to catch Spotify exceptions safely in hotkey threads
def handle_spotify_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            reset_keepalive_state()
            return result
        except SpotifyException as e:
            if e.http_status == 404:
                print("~\n[Spotify API 404] No active playback session or valid track found.")
            elif e.http_status == 403:
                print(f"~\n[Spotify API 403] Action restricted: {e}")
            else:
                print(f"~\n[Spotify Error {e.http_status}]: {e}")
        except Exception as e:
            print(f"~\n[Unexpected Error in {func.__name__}]: {e}")
        return None
    return wrapper

# Declare functions that key bindings will use.
# re https://stackoverflow.com/a/1489838 : forget managing threads, just destroy all of them with the whole program execution. DO IT.
def exit_program():
    os._exit(3)

# Helper function to extract Spotify ID from URI or URL
def extract_spotify_id(uri_or_url):
    # Handle URLs like https://open.spotify.com/track/123abc
    if 'spotify.com' in uri_or_url:
        return uri_or_url.split('/')[-1].split('?')[0]
    # Handle URIs like spotify:track:123abc
    if uri_or_url.startswith('spotify:'):
        return uri_or_url.split(':')[-1]
    # Assume it's already an ID
    return uri_or_url

# Function to find an active device. Returns the first active device's ID or None if no devices are found.
@handle_spotify_errors
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
@handle_spotify_errors
def switch_to_device(device_id):
    try:
        sp.transfer_playback(device_id=device_id, force_play=True)
        print(f"Playback transferred to device: {device_id}")
    except Exception as e:
        print("Error transferring playback:", e)

# Function: pause or start playback, using other functions to find and switch to an active player if no player found:
@handle_spotify_errors
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
            # Reset polling state and exception suppression when manually starting playback
            reset_keepalive_state()
    except Exception as e:
        print("~\nWARNING: no information retrieved for current_playback. If you're playing a device, maybe play and pause the player manually, then retry control from this script.")
        print(e)
    update_info_window()
    
@handle_spotify_errors
def previous_track():
    reset_keepalive_state()
    ret = sp.previous_track()
    update_info_window()

# Function: advance playback to next track
@handle_spotify_errors
def next_track():
    reset_keepalive_state()
    ret = sp.next_track()
    update_info_window()

# Function: save currently playing track to user library ("like" current song)
@handle_spotify_errors
def save_track():
    try:
        info = sp.current_user_playing_track()
        track_URL = info['item']['external_urls']['spotify']
        track_id = extract_spotify_id(track_URL)
        list_of_track_ids = [track_id]
        sp.current_user_saved_tracks_add(list_of_track_ids)
        print("Saved currently playing track", list_of_track_ids, "to Liked Songs.")
        print("Attempted confirm:")
        update_info_window(CLI_print = True)
    except Exception as e:
        print("~\nCould not save current track (could not add to Liked Songs).")
        print(e)

@handle_spotify_errors
def unsave_track():
    try:
        info = sp.current_user_playing_track()
        track_URL = info['item']['external_urls']['spotify']
        track_id = extract_spotify_id(track_URL)
        list_of_track_ids = [track_id]
        sp.current_user_saved_tracks_delete(list_of_track_ids)
        print("Remove currently playing track", list_of_track_ids, "from Liked Songs.")
        print("Attempted confirmation:")
        update_info_window(CLI_print = True)
    except Exception as e:
        print("~\nCould not unsave current track (could not add to Liked Songs).")
        print(e)

# change repeat mode; cycles from current to previous mode and wraps around; e.g. no repeat, playlist repeat, then track repeat:
REPEAT_MODES = ['track', 'context', 'off']
@handle_spotify_errors
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
@handle_spotify_errors
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
@handle_spotify_errors
def seek_to_track_start():
    sp.seek_track(0)

# set playback position forward or backward by seek_ms (milleseconds, negative or positive)
@handle_spotify_errors
def relative_seek(seek_ms):
    # nested function call here: set current playback progress to current + ms (with ms neg. or positive)
    new_seek_ms_pos = int(sp.current_playback()['progress_ms']) + seek_ms
    # set that to zero if it's negative, to avoid error:
    if new_seek_ms_pos < 0:
        new_seek_ms_pos = 0
    sp.seek_track(new_seek_ms_pos)

@handle_spotify_errors
def get_album_tracks(album):
    tracks = []
    results = sp.album_tracks(album['id'])
    tracks.extend(results['items'])
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])
    return tracks

@handle_spotify_errors
def get_artist_albums(artist):
    albums = []
    results = sp.artist_albums(artist['id'], album_type='album')
    albums.extend(results['items'])
    while results['next']:
        results = sp.next(results)
        albums.extend(results['items'])
    return albums

# Print information related to currenlty playing track. Also a gatekeeper function returning False if no playing track, and True and a playback info object from sp.current_user_playing_track().
@handle_spotify_errors
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

@handle_spotify_errors
def print_information():
    print_playlist_1_info()
    success = True
    info = sp.current_user_playing_track()
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

# Non-blocking thread launcher to update UI display window
def update_info_window(CLI_print = False):
    thread = threading.Thread(target=threaded_update_info_window, args = [CLI_print])
    thread.start()

# Updates info window glyph with saved track status
@handle_spotify_errors
def threaded_update_info_window(CLI_print = False):
    global track_info_exception_raised

    try:
        info_window.update_glyph("❓")
    except:
        print("No glyph info_window object to update (yet?), apparently.")
    
    time.sleep(0.67)
    info = None
    try:
        info = sp.current_user_playing_track()
        track_info_exception_raised = False
    except Exception as e:
        if not track_info_exception_raised:
            print("In threaded_update_info_window call, error running function to attempt to retrieve playing track info. If you have an active player, maybe play and pause the player manually, then retry control from this script. OR There was some other error. Printing the error response:")
            print(e)
            track_info_exception_raised = True

    if info != None and info.get('item'):
        track_id = info['item']['id']
        album = info['item']['album']['name']
        if len(album) > 46:
            album = album[:46] + " ..."
        track_name = info['item']['name']
        if len(track_name) > 54:
            track_name = track_name[:54] + " ..."
        
        is_in_user_saved_tracks = sp.current_user_saved_tracks_contains([track_id])
        if is_in_user_saved_tracks[0]:
            if CLI_print != False:
                print("💚🎵💛 Currently playing track ID " + track_id + " is in user saved tracks (Liked Songs)!")
            info_window.update_glyph("🖤\n" + album + "\n~ " + track_name)
        else:
            if CLI_print != False:
                print("🖤 Currently playing track ID " + track_id + " is NOT in user saved tracks (Liked Songs).")
            info_window.update_glyph("🤍\n~ " + album + "\n ~" + track_name)

# make discography playlist from the artist of the currently playing song.
@handle_spotify_errors
def make_discography_playlist():
    print("Attempting to make discography playlist..")
    to_continue, info = print_information()
    if to_continue:
        try:
            import random
            artists = info['item']['artists']
            print("  Artist(s):")
            for artist in artists:
                discography_artist_name = artist['name']; artist_id = artist['id']; artist_URL = artist['external_urls']['spotify']
                print(" ", discography_artist_name, artist_id, artist_URL)
                all_artists_tracks = []
                albums = get_artist_albums(artist)
                print("Collecting and filtering tracks by credit to artist", discography_artist_name, ". .")
                for album in albums:
                    tracks = get_album_tracks(album)
                    for track in tracks:
                        track_artists = track['artists']
                        for track_artist in track_artists:
                            print(". ", end="")
                            if track_artist['name'] == discography_artist_name:
                                all_artists_tracks.append(track['external_urls']['spotify'])
                print("Done collectiong all tracks for artist. Building discography playlist . . .")
                random_playlist_name_suffix = ''.join((random.choice(' ▔▀▆▄▂▌▐█▊▎░▒▓▖▗▘▙▚▛▜▝▞▟') for i in range(4)))
                new_playlist_name = discography_artist_name + " ~" + random_playlist_name_suffix
                print("MAKING PLAYLIST: ", new_playlist_name)
                user_id = sp.me()['id']
                global THIS_SCRIPT_FRIENDLY_NAME
                playlist_description = 'Everything by this artist on Spotify (or albums etc. in which this artist appears!), courtesy ' + THIS_SCRIPT_FRIENDLY_NAME
                new_playlist_info = sp.user_playlist_create(user_id, new_playlist_name, public=True, collaborative=False, description=playlist_description)
                new_playlist_id = new_playlist_info['external_urls']['spotify']
                print('new_playlist_id', new_playlist_id)
                
                idx = 0
                print("Number of songs collected for playlist: ", len(all_artists_tracks))
                how_many_at_a_time = 100
                while True:
                    tracks_to_add = all_artists_tracks[idx:][:how_many_at_a_time]
                    idx += how_many_at_a_time
                    if tracks_to_add == []:
                        print("Reached end of available tracks to add to playlist.")
                        break
                    else:
                        try:
                            track_uris = []
                            for track_url in tracks_to_add:
                                track_id = extract_spotify_id(track_url)
                                track_uris.append(f"spotify:track:{track_id}")
                            sp.playlist_add_items(new_playlist_id, track_uris)
                        except Exception as e:
                            print("WARNING: error attempting to add tracks to playlist ", new_playlist_id)
                            print(e)
        except Exception as e:
            print("Could not get albums (nor songs) information.")
            print(e)

# function: set a playlist for operations (such as adding a song from another playing list)
@handle_spotify_errors
def set_playlist_1():
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
                set_option('USER_VARIABLES', 'PLAYLIST_ID_1', PLAYLIST_ID_1, 'Optional playlist for track/library moves/deletes:')
            else:
                print("~\nCurrent playlist not owned by current user. Can't assign to playlist 1.")
        except Exception as e:
            print("~\nCurrent play context (not a playlist?) not owned by current user. Can't assign to playlist 1.")
            print(e)
    except Exception as e:
        print("~\nCouldn't obtain track info from current context somehow, or other error?")
        print(e)

@handle_spotify_errors
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
@handle_spotify_errors
def add_current_track_to_playlist_1():
    global PLAYLIST_ID_1
    if PLAYLIST_ID_1 == None:
        print("Can't move anything to playlist 1: playlist 1 not defined.")
        return False
    else:
        info = sp.current_user_playing_track()
        track_url = info['item']['external_urls']['spotify']
        track_id = extract_spotify_id(track_url)
        track_uri = f"spotify:track:{track_id}"
        playlist_id = extract_spotify_id(PLAYLIST_ID_1)

        print_current_track_information()
        print("Retrieving all tracks in target playlist to determine whether track proposed to add is already in playlist . .")
        
        result = sp.playlist_items(playlist_id, fields=None, limit=100, offset=0, market=None)
        items = result['items']
        while True:
            for item in items:
                track_uri_from_target_list = item['track']['uri']
                if track_uri_from_target_list == track_uri:
                    print('track_uri_from_target_list', track_uri_from_target_list, " == track_uri ", track_uri)
                    print("That's already in the target playlist! Not adding.")
                    return False
            if result['next']:
                result = sp.next(result)
                items = result['items']
                continue
            
            sp.playlist_add_items(playlist_id, [track_uri])
            print("ADDED track to playlist ID", playlist_id)
            print_playlist_1_info()
            return True

# function: remove the current song from the current playlist
@handle_spotify_errors
def remove_current_track_from_current_playlist():
    info = sp.current_user_playing_track()
    try:
        playlist_URL = info['context']['external_urls']['spotify']
        playlist_id = extract_spotify_id(playlist_URL)
        track_url = info['item']['external_urls']['spotify']
        track_id = extract_spotify_id(track_url)
        track_uri = f"spotify:track:{track_id}"
        print("~\nIn a playlist context; will remove currently playing track from the current playlist.")
        print("Current playlist ID:", playlist_id)
        print("track ID:", track_id)
        sp.playlist_remove_all_occurrences_of_items(playlist_id, [track_uri])
    except Exception as e:
        print("~\nRemove current track from current playlist: cannot; no playlist context.")
        print(e)

@handle_spotify_errors
def shuffle_current_track_to_playlist_1():
    try:
        proceed = add_current_track_to_playlist_1()
        if proceed:
            remove_current_track_from_current_playlist()
        else:
            print("~\nConditions said don't add to playlist 1; didn't move anything.")
    except Exception as e:
        print("~\nFailure shuffling current track to playlist 1 from current list.")
        print(f"Error details: {e}")

# Function: if in a playlist context, add currently playing track to discards playlist, remove it from currently playing playlist and user library (liked songs), and play the next song in the playlist.
@handle_spotify_errors
def unsave_and_move_from_current_playlist_to_discards():
    info = sp.current_user_playing_track()
    try:
        playlist_URL = info['context']['external_urls']['spotify']
        playlist_id = extract_spotify_id(playlist_URL)
        print("~\nDiscards playlist ID:", DISCARDS_PLAYLIST_ID)
        print("Current playlist ID:", playlist_id)
        print_current_track_information()
        track_url = info['item']['external_urls']['spotify']
        track_id = extract_spotify_id(track_url)
        track_uri = f"spotify:track:{track_id}"
        discards_playlist_id = extract_spotify_id(DISCARDS_PLAYLIST_ID)
        
        sp.playlist_add_items(discards_playlist_id, [track_uri])
        sp.current_user_saved_tracks_delete([track_id])
        sp.playlist_remove_all_occurrences_of_items(playlist_id, [track_uri])
        print("Added current track to discards playlist, removed it from current playlist and from liked songs, and will play the next song in the playlist.")
        print("Attempted confirm:")
        update_info_window(CLI_print = True)
        sp.next_track()
    except Exception as e:
        print("~\nUnsave and shuffle current track to discard playlist: no playlist context; cannot remove currently playing track from any playlist. Printing the error response:")
        print(e)

# START BOOKMARK FUNCTIONS REGION
# NOTE THAT LOAD AND SAVE BOOKMARK HOTKEYS are hard-coded in one of these functions (see below).
# A BOOKMARK IS A PLAYLIST, TRACK IN THE PLAYLIST, PLAYBACK POSITION IN THE TRACK, AND PLAYLIST NAME.
# Function: Save the current playback as a bookmark with a specific key
# TO DO:
# - fix that on saving ANY bookmark it throws: Possible error saving bookmark: The hotkey [[['control', 'alt', 'shift', 'b'], ['1']]] is already registered.
# - fix difficulty triggering bookmark hotkeys, if possible? I have to press the second hotkey in the sequence so fast. A way to tell the hotkey library to wait longer to register a second key combo in a sequence?
# - fix that nothing can call the following function unless a bookmark is defined - cannot dynamally make a NEW bookmark definition; WORKAROUND: have initialize_bookmarks_in_ini() pre-save 10 of them which can be overwritten, as they pre-exist:
# - make it clearer in INI and / or somewhere in code how the chained (sequence) bookmark hotkeys work
@handle_spotify_errors
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
                playlist_id_for_api = extract_spotify_id(playlist_id)
                playlist_info = sp.playlist(playlist_id_for_api, fields="name")
                playlist_name = playlist_info.get('name', 'Unknown Playlist')
            except:
                pass

        if not config.has_section(bookmark_name):
            config.add_section(bookmark_name)

        set_option(bookmark_name, 'playlist_id', playlist_id or 'None')
        set_option(bookmark_name, 'playlist_name', playlist_name)
        set_option(bookmark_name, 'track_id', track_id)
        set_option(bookmark_name, 'position_ms', str(position_ms))
        set_option(bookmark_name, 'key', bookmark_key)

        print('Bookmark saved (hopefully) for ', bookmark_key, '.')
        register_bookmark_hotkeys_from_ini()
        print(f"Bookmark '{bookmark_name}' saved and hotkeys updated.")
    except Exception as e:
        print(f"\tPossible error saving bookmark.")
        print(e)

@handle_spotify_errors
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

# ============================================
# TENT-POLE REORDERING FUNCTIONS
# ============================================

@handle_spotify_errors
def get_all_playlist_tracks(playlist_id):
    all_tracks = []
    try:
        results = sp.playlist_items(
            playlist_id, 
            fields='items(track(uri)),next,total',
            limit=100
        )
        all_tracks.extend(results['items'])
        
        while results['next']:
            results = sp.next(results)
            all_tracks.extend(results['items'])
            
        return all_tracks
    except Exception as e:
        print(f"Error fetching playlist tracks: {e}")
        return []

def build_reorder_mapping(original_uris, new_order_uris):
    uri_to_new_pos = {uri: idx for idx, uri in enumerate(new_order_uris)}
    position_map = {}
    for old_pos, uri in enumerate(original_uris):
        if uri in uri_to_new_pos:
            new_pos = uri_to_new_pos[uri]
            if old_pos != new_pos:
                position_map[old_pos] = new_pos
    return position_map

@handle_spotify_errors
def reorder_playlist_in_chunks(playlist_id, position_map, total_tracks):
    if not position_map:
        print("No reordering needed - positions unchanged.")
        return True
    
    start_time = time.time()
    sorted_moves = sorted(position_map.items(), key=lambda x: x[1], reverse=True)
    total_moves = len(sorted_moves)
    success_count = 0
    error_count = 0
    rate_limit_hits = 0
    DELAY_BETWEEN_CALLS = 0.46
    report_every = max(1, min(10, total_moves // 20))
    
    print(f"Starting reorder of {total_moves} track moves...")
    if total_moves > 50:
        print(f"Estimated time: ~{total_moves * DELAY_BETWEEN_CALLS / 60:.1f} minutes")
    
    for idx, (old_pos, new_pos) in enumerate(sorted_moves, 1):
        try:
            if new_pos >= total_tracks:
                insert_before = total_tracks
            else:
                insert_before = new_pos
                
            sp.playlist_reorder_items(
                playlist_id,
                range_start=old_pos,
                range_length=1,
                insert_before=insert_before
            )
            success_count += 1
            
            if idx % report_every == 0 or idx == total_moves:
                percent = int((idx / total_moves) * 100)
                elapsed = time.time() - start_time
                print(f"Progress: {percent}% ({idx}/{total_moves} tracks moved) - Elapsed: {elapsed:.1f}s")
                
            if idx < total_moves:
                time.sleep(DELAY_BETWEEN_CALLS)
                
        except Exception as e:
            error_msg = str(e)
            if "rate limit" in error_msg.lower() or "429" in error_msg:
                rate_limit_hits += 1
                print(f"WARNING: Rate limit hit! Pausing for 10 seconds...")
                time.sleep(10)
                try:
                    sp.playlist_reorder_items(
                        playlist_id,
                        range_start=old_pos,
                        range_length=1,
                        insert_before=insert_before
                    )
                    success_count += 1
                    print(f"Retry successful for position {old_pos}")
                except Exception as retry_error:
                    error_count += 1
                    print(f"Retry failed for position {old_pos}: {retry_error}")
            else:
                error_count += 1
                print(f"Error moving item from position {old_pos} to {new_pos}: {e}")
    
    total_time = time.time() - start_time
    print(f"Reordering complete: {success_count} items moved, {error_count} errors in {total_time:.1f} seconds.")
    if rate_limit_hits > 0:
        print(f"  (Recovered from {rate_limit_hits} rate limit hits)")
    return error_count == 0

# Hotkey function for tent-pole reordering
@handle_spotify_errors
def reorder_playlist_by_tent_pole():
    global continue_keepalive_poll

    print("\n" + "="*50)
    print("TENT-POLE REORDERING")
    print("="*50)
    
    # Suspend background checks while in interactive sorting mode
    continue_keepalive_poll = False

    try:
        print("\nIMPORTANT: Please manually pause playback before continuing.")
        print("(This prevents playback jumps/interruptions during reordering)")
        input("Press ENTER when playback is paused...")
        
        print("\nEnter the playlist to reorder:")
        print("(You can paste a Spotify URL, URI, or just the ID)")
        playlist_input = input("Playlist: ").strip()
        
        if not playlist_input:
            print("No playlist entered. Operation cancelled.")
            return
        
        playlist_id = extract_spotify_id(playlist_input)
        print(f"Using playlist ID: {playlist_id}")
        
        try:
            playlist_info = sp.playlist(playlist_id, fields="name,owner.display_name")
            playlist_name = playlist_info.get('name', 'Unknown Playlist')
            owner_name = playlist_info.get('owner', {}).get('display_name', 'Unknown Owner')
            print(f"Playlist: '{playlist_name}' by {owner_name}")
        except Exception as e:
            print(f"Could not verify playlist: {e}")
            return
        
        n_input = input("\nNumber of tent poles (default 5, min 2): ").strip()
        N = int(n_input) if n_input else 5
        
        if N < 2:
            print("N must be at least 2. Operation cancelled.")
            return
        
        print(f"Using N={N} tent poles")
        print(f"\nFetching tracks from playlist...")
        track_items = get_all_playlist_tracks(playlist_id)
        
        if not track_items:
            print("No tracks found in playlist.")
            return
        
        valid_tracks = [t for t in track_items if t and t.get('track')]
        if not valid_tracks:
            print("No valid tracks found in playlist.")
            return
        
        track_count = len(valid_tracks)
        print(f"Found {track_count} tracks.")
        
        if N > track_count:
            print(f"Warning: N={N} is greater than track count ({track_count}).")
            print("Proceeding with N = track count.")
            N = track_count
        
        track_uris = [t['track']['uri'] for t in valid_tracks]
        
        print("\nApplying tent-pole sorting algorithm...")
        print("(This may take a moment for large playlists)")
        sorted_uris = tent_pole_sort.sort_tent_pole(track_uris, N)
        
        print(f"\nSorting complete. Playlist will be reordered from:")
        print(f"Original: {track_count} tracks")
        print(f"To: {len(sorted_uris)} tracks")
        print(f"Using N={N} tent poles")
        
        position_map = build_reorder_mapping(track_uris, sorted_uris)
        moves_needed = len(position_map)
        print(f"{moves_needed} tracks will be moved")
        
        if moves_needed == 0:
            print("No changes needed - playlist is already in tent-pole order.")
            return
        
        print("\nThis will modify the playlist in-place.")
        print("(Track metadata like 'added on' dates will be preserved)")
        confirm = input("Proceed with reordering? (y/N): ").strip().lower()
        
        if confirm != 'y' and confirm != 'yes':
            print("Operation cancelled by user.")
            return
        
        print(f"\nReordering playlist...")
        print(f"(Processing {moves_needed} track moves...)")
        
        success = reorder_playlist_in_chunks(playlist_id, position_map, track_count)
        
        if success:
            print(f"\nPlaylist reordered successfully with {N} tent poles!")
            print(f"Playlist: '{playlist_name}'")
            print(f"Tracks: {track_count} tracks reordered")
            update_info_window(CLI_print=True)
        else:
            print("\nReordering completed with some errors. Please check the logs above.")
        
    except ValueError as e:
        print(f"Invalid input: {e}")
        print("Operation cancelled.")
    except KeyboardInterrupt:
        print("\n\nOperation interrupted by user (Ctrl+C).")
        print("Playlist may be partially reordered.")
    except Exception as e:
        print(f"\nUnexpected error reordering playlist:")
        print(f"{e}")
        import traceback
        traceback.print_exc()
        print("\nOperation failed. Playlist may be in an inconsistent state.")
    finally:
        # Resume background checks and clear exception flags after operation completes or cancels
        reset_keepalive_state()

def register_bookmark_hotkeys_from_ini():
    dynamic_bindings = []
    for section in config.sections():
        if section.startswith("BOOKMARK "):
            bookmark_key = config.get(section, 'key', fallback=None)
            if bookmark_key:
                save_sequence = f"control + alt + shift + b, {bookmark_key}"
                load_sequence = f"control + alt + shift + l, {bookmark_key}"
                dynamic_bindings.append([save_sequence, None, save_bookmark, True, None, bookmark_key])
                dynamic_bindings.append([load_sequence, None, load_bookmark, True, None, bookmark_key])
    
    for binding in dynamic_bindings:
        if not register_hotkey(binding[0], binding[1], binding[2], binding[3], binding[4], binding[5]):
            removed_success = remove_hotkey(binding[0])
            register_hotkey(binding[0], binding[1], binding[2], binding[3], binding[4], binding[5])
# END BOOKMARK FUNCTIONS REGION


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
    ["control + alt + shift + t", None, reorder_playlist_by_tent_pole, False, None, None],
]

register_hotkeys(bindings)
register_bookmark_hotkeys_from_ini()
start_checking_hotkeys()


# UNIFIED BACKGROUND TIMER & KEEPALIVE POLLING
# Periodically polls current playing track (every 6.5s) using sp.current_user_playing_track().
# Handles both active UI info update triggers and keepalive polling in a single thread loop.
last_remembered_track_id = ''
wait_between_checks = 6.5

class BackgroundTimer(Thread):
    def run(self):
        global last_remembered_track_id
        global continue_keepalive_poll
        global keepalive_playback_paused_poll_count
        global track_info_exception_raised

        while True:
            time.sleep(wait_between_checks)
            if continue_keepalive_poll:
                info = None
                try:
                    info = sp.current_user_playing_track()
                    # Success: clear error logging flag
                    track_info_exception_raised = False
                except Exception as e:
                    if not track_info_exception_raised:
                        print("In repeat timer query of playing track check, controlled by boolean continue_keepalive_poll, error running function to attempt to retrieve playing track info. If you have an active player, maybe play and pause the player manually, then retry control from this script. OR There was some other error. Printing the error response:")
                        print(e)
                        track_info_exception_raised = True

                if info is not None and info.get('is_playing'):
                    keepalive_playback_paused_poll_count = 0
                    current_track_id = info['item']['id'] if info.get('item') else None
                    if current_track_id and last_remembered_track_id != current_track_id:
                        print("Active playback polling: DIFFERENT track ID ", current_track_id, " than last seen " + last_remembered_track_id + " -- will try to update user saved tracks (Liked Songs) track info_window.")
                        update_info_window(CLI_print = True)
                        last_remembered_track_id = current_track_id
                else:
                    # Increment paused/inactive checks counter when no active item/playing status is returned
                    keepalive_playback_paused_poll_count += 1
                    if keepalive_playback_paused_poll_count >= 19:
                        continue_keepalive_poll = False
                        print("Playback found to be paused or unavailable through 19 checks (~2 mins); suspending track monitoring until playback is resumed via this script.")

timer = BackgroundTimer()
timer.start()

import current_track_in_user_tracks_display
info_window = current_track_in_user_tracks_display.GlyphWindow()
update_info_window()
info_window.run()

while True:
    time.sleep(0.1)