# Developed in collaboration with ChatGPT 3.5

import tkinter as tk
from tkinter.font import Font
import keyboard
import os

# Dictionary to store hotkey information
hotkeys_info = {
    'ctrl + shift + alt + h': {'description': 'Hide or display the hotkey info HUD', 'function': 'toggle_hud'},
    'ctrl + shift + alt + q': {'description': 'Exit the program', 'function': 'exit_program'},
    # Add more hotkeys if needed
}

# Create the HUD window
hud_window = tk.Tk()
hud_window.title("Hotkey Info")
hud_window.attributes("-topmost", True)  # Keep HUD on top of other windows

# Function to display the HUD with hotkey information
def show_hud():
    # Clear any previous content
    for widget in hud_window.winfo_children():
        widget.destroy()
        
    size25 = Font(size=25)
    # Display hotkey information
    for hotkey, info in hotkeys_info.items():
        hotkey_label = tk.Label(hud_window, text=hotkey + ":\t" + info['description'], font=size25)
        hotkey_label.pack(padx=15, pady=10)

# Function to toggle HUD visibility
def toggle_hud():
    global hud_visible
    try:
        if hud_window.winfo_exists():
            if hud_window.state() == "withdrawn":
                hud_window.deiconify()  # Show the window
            else:
                hud_window.withdraw()  # Withdraw the window to hide it
        else:
            show_hud()
    except tk.TclError:
        pass  # Window has already been destroyed, ignore the error

def exit_program():
    os._exit(0)

# Bind hotkey combinations to their respective functions
for hotkey, info in hotkeys_info.items():
    function_name = info['function']
    function = globals()[function_name]  # Get the function by name from the global scope
    keyboard.add_hotkey(hotkey, function)

# Initially show the HUD
show_hud()

# Run the Tkinter main loop
hud_window.protocol("WM_DELETE_WINDOW", lambda: hud_window.withdraw())  # Withdraw the window on close
hud_window.mainloop()
