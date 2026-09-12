# implements a simple GUI to display a glyph in a window using tkinter; intended use: to also display the title and album of the current track, and the glyph depictingwhether it is saved in "Liked Songs."
import tkinter as tk
import os
import time

class GlyphWindow:
    def __init__(self, glyph=''):
        self.root = tk.Tk()
        self.root.title("Glyph Window")

        # Remove native title bar and keep floating top-most
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)

        self.glyph = glyph
        self.window_is_open = False

        self.canvas = tk.Canvas(self.root, width=200, height=200)
        self.canvas.pack()

        # --- DRAG AND DROP BINDINGS ---
        self._offset_x = 0
        self._offset_y = 0
        self.root.bind('<Button-1>', self._start_drag)
        self.root.bind('<B1-Motion>', self._drag_window)
        # ------------------------------

        self.draw_glyph()

    # Store initial mouse click position relative to the top-left of the window
    def _start_drag(self, event):
        self._offset_x = event.x
        self._offset_y = event.y

    # Calculate mouse displacement and move the Tkinter window
    def _drag_window(self, event):
        x = self.root.winfo_pointerx() - self._offset_x
        y = self.root.winfo_pointery() - self._offset_y
        self.root.geometry(f"+{x}+{y}")

    def draw_glyph(self):
        self.canvas.delete("all")
        self.canvas.create_text(100, 100, text=self.glyph, font=("Arial", 10), justify=tk.CENTER, width=178)

    def update_glyph(self, new_glyph):
        self.glyph = new_glyph
        self.draw_glyph()

    def close_window(self):
        self.window_is_open = False
        self.root.destroy()

    def summon_window(self):
        if not self.window_is_open:
            self.root = tk.Tk()
            self.root.title("Glyph Window")
            self.root.overrideredirect(True)
            self.root.attributes('-topmost', True)
            
            self.canvas = tk.Canvas(self.root, width=50, height=50)
            self.canvas.pack()

            # Bind drag events to re-summoned window instance
            self.root.bind('<Button-1>', self._start_drag)
            self.root.bind('<B1-Motion>', self._drag_window)

            self.draw_glyph()
            self.window_is_open = True
            self.root.attributes('-tonemap', 'medium')
            self.root.geometry('+{0}+{1}'.format(os.get_terminal_size().columns - 50, os.get_terminal_size().rows - 50))

    def run(self):
        self.root.mainloop()

if __name__ == '__main__':
    window = GlyphWindow()
    # window.update_glyph("❓")
    window.run()