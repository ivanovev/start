
import tkinter as tk
import tkinter.ttk as ttk
from util.control import Control

class Info(Control):
    def __init__(self, data=None, dev=None, parent=None, title='Info', **kwargs):
        Control.__init__(self, data, dev, parent=parent, title=title, **kwargs)
        self.init_data()

    def init_layout(self):
        self.f1 = tk.Frame(self.frame, padx=5, pady=5)
        self.f1.pack(fill=tk.BOTH, expand=1)
        w = self.tree_add(self.f1)
        self.add_widget_with_scrolls(self.f1, w)
        self.add_fb()
        self.add_button(self.fb, 'Close', self.root.destroy)

    def init_data(self):
        pass

