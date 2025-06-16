import tkinter as tk
import os
import time

class GlyphWindow:
    def __init__(self, glyph=''):
        self.root = tk.Tk()
        self.root.title("Glyph Window")
        self.glyph = glyph
        self.window_is_open = False

        self.canvas = tk.Canvas(self.root, width=200, height=200)
        self.canvas.pack()

        self.draw_glyph()

        # self.root.after(5000, self.update_glyph, "☁️")  # Schedule update after 5 seconds

    def draw_glyph(self):
        self.canvas.delete("all")
        self.canvas.create_text(100, 100, text=self.glyph, font=("Arial", 16), justify=tk.CENTER, width=178)

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
            self.canvas = tk.Canvas(self.root, width=50, height=50)
            self.canvas.pack()
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
