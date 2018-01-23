import tkinter
from tkinter import ttk

import matplotlib

matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class VerticalScrollFrame(ttk.Frame):

    def __init__(self, parent, **kwargs):
        ttk.Frame.__init__(self, parent, **kwargs)
        self.canvas = tkinter.Canvas(self, bg='blue')
        self.canvas.pack(fill=tkinter.BOTH, expand=tkinter.TRUE, side=tkinter.LEFT)
        v_scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        v_scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y, expand=tkinter.FALSE)
        self.canvas.config(yscrollcommand=v_scrollbar.set, scrollregion=self.canvas.bbox('all'))

        self.interior_frame = tkinter.Frame(self.canvas, bg='green')
        self.interior_frame_id = self.canvas.create_window((0, 0), window=self.interior_frame, anchor=tkinter.NW)

        self.interior_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind('<Configure>', self.on_canvas_configure)

    def on_canvas_configure(self, event):
        canvas_width = event.width
        self.canvas.itemconfig(self.interior_frame_id, width=canvas_width)

    def _on_frame_configure(self, _event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def get_interior_frame(self):
        return self.interior_frame


class GraphRowFrame(ttk.Frame):
    class GraphFrame(ttk.Frame):
        WIDTH = 0.75

        def __init__(self, parent, data_func):
            ttk.Frame.__init__(self, parent, relief='ridge', borderwidth=2, width=50)
            self.figure = Figure()
            self.subplot = self.figure.add_subplot(111)
            self.figure.set_tight_layout(True)

            sensor_name, x, y = data_func()
            self.subplot.plot(x, y, 'b-o')
            self.subplot.grid(linestyle='dashed')

            self.subplot.set_title(sensor_name)
            canvas = FigureCanvasTkAgg(figure=self.figure, master=self)
            canvas.show()
            canvas.get_tk_widget().pack(fill=tkinter.BOTH, expand=True)

    def __init__(self, parent, data_func, **kwargs):
        ttk.Frame.__init__(self, parent, **kwargs)
        self.data = data_func
        self.columnconfigure(0, weight=10)
        self.columnconfigure(1, weight=1)
        self.graph_frame = GraphRowFrame.GraphFrame(self, self.graph_data)
        # self.graph_frame.pack(side=tkinter.LEFT)
        self.graph_frame.grid(column=0, sticky='nsew', padx=5, pady=5)
        self.label_frame = ttk.Frame(self, width=10)
        # self.label_frame.pack(side=tkinter.LEFT)
        self.label_frame.grid(row=0, column=1, sticky='nsew', padx=5, pady=5)
        for data in self.label_data():
            label = ttk.Label(self.label_frame, text=data)
            label.pack(side=tkinter.TOP, anchor=tkinter.W)

    def graph_data(self):
        sensor_name, mode, mode_info, x, y = self.data()
        return sensor_name, x, y

    def label_data(self):
        sensor_name, mode, mode_info, x, y = self.data()
        return sensor_name, mode, mode_info


def temp_get_data():  # TODO change this
    mode = 'Morning Shift'
    mode_info = '01 Jan 2018'
    sensor_name = 'Machine A'
    y = [103, 23, 34, 21, 36, 42, 48, 58, 77, 89, 92, 100]
    x = []
    for i in range(len(y)):
        x.append(str(i + 8).zfill(2))
    return sensor_name, mode, mode_info, x, y


if __name__ == '__main__':
    root = tkinter.Tk()
    root.title = 'Hello'
    root.minsize(width=1000, height=500)
    some = VerticalScrollFrame(root)
    some.pack(fill=tkinter.BOTH, expand=tkinter.TRUE)
    another1 = GraphRowFrame(some.get_interior_frame(), temp_get_data)
    another1.pack(side=tkinter.TOP, fill=tkinter.X)
    another2 = GraphRowFrame(some.get_interior_frame(), temp_get_data)
    another2.pack(side=tkinter.TOP, fill=tkinter.X)
    another3 = GraphRowFrame(some.get_interior_frame(), temp_get_data)
    another3.pack(side=tkinter.TOP, fill=tkinter.X)
    # root.mainloop()
    while True:
        try:
            root.mainloop()
        except UnicodeDecodeError:
            continue
        else:
            break
