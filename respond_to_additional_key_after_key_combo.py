# DESCRIPTION
# Demonstrates a keyboard macro which is a key combination and release followed by another key. While this is running, press CTRL+ALT+SHIFT+B, and then within the next 2.3 seconds, press any other alphanumeric key. After 2.3 seconds it stops listening for that additional key and resumes listening for the original hotkey combination.

import keyboard
import threading
import time

# Flag to track if a timer is running
timer_active = False

# Function to handle the timer logic
def start_timer():
    global timer_active
    timer_active = True
    start_time = time.time()

    # Wait for 2 seconds or a key press
    while time.time() - start_time < 2.3:
        if timer_active:
            # Check for any key press during the timer
            for key in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0']:  # Add more keys if needed
                if keyboard.is_pressed(key) and key not in ['ctrl', 'shift', 'b']:
                    print(f"Key '{key}' pressed during timer.")
                    timer_active = False
                    return
        time.sleep(0.01)  # Short delay to prevent high CPU usage

    # If timer completes without interruption, print expiration message
    if timer_active:
        print("Timer expired.")
    timer_active = False

# Function to check for Control + Shift + B key combination
def check_combination():
    if keyboard.is_pressed('ctrl') and keyboard.is_pressed('shift') and keyboard.is_pressed('b'):
        if not timer_active:
            print("Control + Alt + Shift + B pressed, starting timer.")
            threading.Thread(target=start_timer).start()

# Register the combination checking function
keyboard.add_hotkey('ctrl+alt+shift+b', check_combination)

# Keep checking for key combination and handle key events
while True:
    check_combination()  # Continuously check for the combination
    time.sleep(0.03)  # Short delay to prevent high CPU usage
