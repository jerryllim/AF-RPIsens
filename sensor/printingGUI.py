import tkinter
from tkinter import ttk
from tkinter import messagebox
from collections import OrderedDict
import cv2
from pyzbar import pyzbar


class PrintingGUI:
    def __init__(self, root):
        pass


class NewJobPage(ttk.Frame):
    def __init__(self, parent, **kwargs):
        ttk.Frame.__init__(self, parent, **kwargs)
        self.configure(padding=5)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)
        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=100)
        self.columnconfigure(1, weight=1)

        job_label = ttk.Label(self, text='Job number:')
        job_label.grid(row=0, column=0, sticky='sw')
        self.job_var = tkinter.StringVar()
        job_entry = ttk.Entry(self, textvariable=job_var, state=tkinter.DISABLED)
        job_entry.grid(row=1, column=0, stick='ew')
        scan_button = ttk.Button(self, text='Scan', command=self.scan_barcode)
        scan_button.grid(row=1, column=1, sticky='w')
        button_frame = ttk.Frame(self)
        button_frame.grid(row=2, column=0, columnspan=2, sticky='n')
        start_button = ttk.Button(button_frame, text='Start', command=self.start_job)
        start_button.pack()

    def scan_barcode(self):
        cam = cv2.VideoCapture(0)
        found = False

        while not found:
            _, frame = cam.read()

            barcodes = pyzbar.decode(frame)

            if barcodes:
                barcode = barcodes[0]
                barcodeData = barcode.data.decode("utf-8")
                found = True
                self.job_var.set(barcodeData)
            elif cam.get(cv2.CAP_PROP_POS_FRAMES) > cam.get(cv2.CV_CAP_PROP_FPS):
                break

        cam.release()

    def start_job(self):
        pass


class JobPage(ttk.Frame):
    def __init__(self, parent, **kwargs):
        ttk.Frame.__init__(self, parent, **kwargs)


class VerticalScrollFrame(ttk.Frame):
    def __init__(self, parent, **kwargs):
        ttk.Frame.__init__(self, parent, **kwargs)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.canvas = tkinter.Canvas(self)
        self.canvas.grid(row=0, column=0, sticky='nsew')
        v_scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        v_scrollbar.grid(row=0, column=1, sticky='nsw')
        self.canvas.config(yscrollcommand=v_scrollbar.set, scrollregion=self.canvas.bbox('all'))

        self.interior_frame = ttk.Frame(self.canvas)
        self.interior_frame_id = self.canvas.create_window((0, 0), window=self.interior_frame, anchor=tkinter.NW)

        self.interior_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind('<Configure>', self._on_canvas_configure)

    def _on_canvas_configure(self, event):
        canvas_width = event.width
        self.canvas.itemconfig(self.interior_frame_id, width=canvas_width)

    def _on_frame_configure(self, _event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def get_interior_frame(self):
        return self.interior_frame


if __name__ == '__main__':
    root = tkinter.Tk()
    app = NewJobPage(root)
    app.pack(fill=tkinter.BOTH, expand=tkinter.TRUE)
    root.mainloop()
