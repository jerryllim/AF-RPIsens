import tkinter
from tkinter import ttk
import string  # TODO for testing

import matplotlib

matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class TempClassWithRandomData:  # TODO to delete for testing
    def __init__(self):
        self.sensorList = []
        for index in range(13):
            self.sensorList.append('Machine {}'.format(string.ascii_uppercase[index]))


class MainWindow(ttk.Frame):
    def __init__(self, parent, data_class: TempClassWithRandomData, **kwargs):
        self.data_class = data_class
        ttk.Frame.__init__(self, parent, **kwargs)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=100)
        self.columnconfigure(0, weight=1)
        top_frame = ttk.Frame(self)
        top_frame.grid(row=0, column=0, sticky='nsew')
        temp_label = ttk.Label(top_frame, text='Some text')
        temp_label.pack()
        bottom_scrollable_frame = VerticalScrollFrame(self)
        bottom_scrollable_frame.grid(row=1, column=0, sticky='nsew')

        # Loop to place all graphs
        bottom_scrollable_frame.get_interior_frame().columnconfigure(0, weight=1)
        bottom_scrollable_frame.get_interior_frame().columnconfigure(1, weight=1)
        # graph = GraphFrameTemp(bottom_scrollable_frame.get_interior_frame())
        # graph.pack()
        graph = GraphFrame(bottom_scrollable_frame.get_interior_frame())
        graph.pack(fill=tkinter.BOTH, expand=tkinter.TRUE)
        for sensor in self.data_class.sensorList:
            graph.add_subplots(lambda: temp_get_data(title=sensor))
        graph.show_figure()


class VerticalScrollFrame(ttk.Frame):

    def __init__(self, parent, **kwargs):
        ttk.Frame.__init__(self, parent, **kwargs)
        self.canvas = tkinter.Canvas(self, bg='pink')
        self.canvas.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=tkinter.TRUE)
        v_scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        v_scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y, expand=tkinter.FALSE)
        self.canvas.config(yscrollcommand=v_scrollbar.set, scrollregion=self.canvas.bbox('all'))

        self.interior_frame = tkinter.Frame(self.canvas, bg='green')
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


class GraphFrame(ttk.Frame):
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent, relief='ridge', borderwidth=2, width=50)
        self.figure = Figure()
        self.figure.set_tight_layout(True)
        self.data_funcs = []

    def add_subplots(self, data_func):
        self.data_funcs.append(data_func)

    def plot_subplot(self, row, col, num, data_func):
        subplot = self.figure.add_subplot(row, col, num)

        title, x, y = data_func()
        subplot.plot(x, y, 'b-o')
        subplot.grid(linestyle='dashed')
        subplot.set_title(title)

    def show_figure(self):
        length = len(self.data_funcs)
        col = 2
        row = length//col + length%col

        for pos in range(length):
            self.plot_subplot(row, col, (pos + 1), self.data_funcs[pos])

        canvas = FigureCanvasTkAgg(figure=self.figure, master=self)
        canvas.show()
        canvas.get_tk_widget().pack(fill=tkinter.BOTH, expand=True)


class GraphFrameTemp(ttk.Frame):
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent, relief='ridge', borderwidth=2, width=50)
        self.figure = Figure()
        self.figure.set_tight_layout(True)
        self.data_funcs = []

        subplot1 = self.figure.add_subplot(2, 2, 1)
        title, x, y = temp_get_data()
        subplot1.plot(x, y, 'b-o')
        subplot1.grid(linestyle='dashed')
        subplot1.set_title(title)

        subplot2 = self.figure.add_subplot(2, 2, 2)
        title, x, y = temp_get_data()
        subplot2.plot(x, y, 'b-o')
        subplot2.grid(linestyle='dashed')
        subplot2.set_title(title)

        subplot3 = self.figure.add_subplot(2, 2, 3)
        title, x, y = temp_get_data()
        subplot3.plot(x, y, 'b-o')
        subplot3.grid(linestyle='dashed')
        subplot3.set_title(title)

        subplot4 = self.figure.add_subplot(2, 2, 4)
        title, x, y = temp_get_data()
        subplot4.plot(x, y, 'b-o')
        subplot4.grid(linestyle='dashed')
        subplot4.set_title(title)

        canvas = FigureCanvasTkAgg(figure=self.figure, master=self)
        canvas.show()
        canvas.get_tk_widget().pack(fill=tkinter.BOTH, expand=True)


def temp_get_data(title=None, y=None, x=None):  # TODO change this
    if title is None:
        title = 'Machine A - 1 Jan 2018 Morning'
    if y is None:
        y = [103, 23, 34, 21, 36, 42, 48, 58, 77, 89, 92, 100]
    if x is None:
        x = []
        for i in range(len(y)):
            x.append(str(i + 8).zfill(2))
    return title, x, y


if __name__ == '__main__':
    # root = tkinter.Tk()
    # root.title = 'Hello'
    # root.minsize(width=1000, height=10)
    # some = VerticalScrollFrame(root)
    # some.pack(fill=tkinter.BOTH, expand=tkinter.TRUE)
    # another1 = GraphRowFrame(some.get_interior_frame(), lambda: temp_get_data(title='Machine A - 1 Jan 2018 Morning'))
    # another1.pack(side=tkinter.TOP, fill=tkinter.X)
    # another2 = GraphRowFrame(some.get_interior_frame(), lambda: temp_get_data(title='Machine B - 1 Jan 2018 Morning'))
    # another2.pack(side=tkinter.TOP, fill=tkinter.X)
    # another3 = GraphRowFrame(some.get_interior_frame(), lambda: temp_get_data(title='Machine C - 1 Jan 2018 Morning'))
    # another3.pack(side=tkinter.TOP, fill=tkinter.X)
    # # root.mainloop()
    # while True:
    #     try:
    #         root.mainloop()
    #     except UnicodeDecodeError:
    #         continue
    #     else:
    #         break

    root = tkinter.Tk()
    root.title('Test')
    root.minsize(width=1000, height=100)
    main_frame = MainWindow(root, TempClassWithRandomData())
    main_frame.pack(fill=tkinter.BOTH, expand=tkinter.TRUE)
    while True:
        try:
            root.mainloop()
        except UnicodeDecodeError:
            continue
        else:
            break
