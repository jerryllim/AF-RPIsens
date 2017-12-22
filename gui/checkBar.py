from tkinter import *


class Checkbar(Frame):
    def __init__(self, parent=None, picks=[], side=LEFT, anchor=W, button_width=None):
        Frame.__init__(self, parent)
        self.vars = []
        for pick in picks:
            var = IntVar()
            var.set(1)
            chk = Checkbutton(self, text=pick, variable=var)
            if button_width is not None:
                chk.config(width=button_width)
            chk.pack(side=side, anchor=anchor, expand=YES)
            self.vars.append(var)

    def state(self):
        return [var.get() for var in self.vars]
