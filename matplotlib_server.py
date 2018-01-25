import tkinter
from tkinter import ttk
import string  # TODO for testing

import matplotlib

matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  # noqa
from matplotlib.figure import Figure  # noqa


class TempClassWithRandomData:  # TODO to delete for testing
    def __init__(self):
        self.sensorList = []
        for index in range(13):
            self.sensorList.append('Machine {}\n1 Jan 2018 Morning'.format(string.ascii_uppercase[index]))


class MainWindow(ttk.Frame):
    NUM_COL = 2

    def __init__(self, parent, data_class: TempClassWithRandomData, **kwargs):
        self.data_class = data_class
        ttk.Frame.__init__(self, parent, **kwargs)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=100)
        self.columnconfigure(0, weight=1)

        # Top Frame settings
        top_frame = ttk.Frame(self, relief='raise', borderwidth=2)
        top_frame.grid(row=0, column=0, sticky='nsew')
        top_frame.columnconfigure(0, weight=1)
        top_frame.columnconfigure(1, weight=1)
        top_frame.rowconfigure(0, weight=1)
        top_frame.rowconfigure(1, weight=2)
        request_label = ttk.Label(top_frame, text='Request every {} minutes'.format('X'))  # TODO add tkinter variable?
        request_label.grid(row=0, column=0, sticky='w')
        request_button = ttk.Button(top_frame, text='Request now')  # TODO add command
        request_button.grid(row=0, column=1)
        quick_frame = ttk.LabelFrame(top_frame, text='Quick Access: ')
        quick_frame.grid(row=1, column=0, columnspan=2, sticky='nsew')

        # Quick Access TODO temporary
        for col in range(MainWindow.NUM_COL):
            quick_frame.columnconfigure(col, weight=1)
        for index in range(4):
            row = index//MainWindow.NUM_COL
            col = index % MainWindow.NUM_COL
            button = ttk.Button(quick_frame, text='Button {}'.format(index))
            button.grid(row=row, column=col)

        # Make graphs
        # bottom_scrollable_frame = VerticalScrollFrame(self, relief='sunken')
        # bottom_scrollable_frame.grid(row=1, column=0, sticky='nsew')
        # for col in range(MainWindow.NUM_COL):
        #     bottom_scrollable_frame.get_interior_frame().columnconfigure(col, weight=1)
        #
        # for index in range(len(self.data_class.sensorList)):
        #     row = index//MainWindow.NUM_COL
        #     col = index % MainWindow.NUM_COL
        #     # graph = GraphFrame(bottom_scrollable_frame.get_interior_frame(),
        #     #                    lambda: temp_get_data(title=self.data_class.sensorList[index]))
        #     # graph.grid(row=row, column=col, sticky='nsew', padx=(0, 5), pady=5)
        #     canvas = GraphCanvas(bottom_scrollable_frame.get_interior_frame(),
        #                          lambda: temp_get_data(title=self.data_class.sensorList[index]))
        #     canvas.show()
        #     canvas.grid(row=row, column=col, sticky='nsew', padx=5, pady=5)


class VerticalScrollFrame(ttk.Frame):

    def __init__(self, parent, **kwargs):
        ttk.Frame.__init__(self, parent, **kwargs)
        self.canvas = tkinter.Canvas(self)
        self.canvas.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=tkinter.TRUE)
        v_scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        v_scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y, expand=tkinter.FALSE)
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


class GraphFrame(ttk.Frame):
    def __init__(self, parent, data_func):
        ttk.Frame.__init__(self, parent, relief='ridge', borderwidth=2, width=50)
        self.figure = Figure()
        self.figure.set_tight_layout(True)
        self.data_func = data_func

        subplot = self.figure.add_subplot(1, 1, 1)
        title, x, y = data_func()
        subplot.plot(x, y, 'b-o')
        subplot.grid(linestyle='dashed')
        subplot.set_title(title)

        self.canvas = FigureCanvasTkAgg(figure=self.figure, master=self)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(fill=tkinter.BOTH, expand=tkinter.TRUE)


class GraphCanvas(FigureCanvasTkAgg):
    def __init__(self, parent, data_func):
        self.figure = Figure()
        self.figure.set_tight_layout(True)

        subplot = self.figure.add_subplot(1, 1, 1)
        title, x, y = data_func()
        subplot.plot(x, y, 'b-o')
        subplot.grid(linestyle='dashed')
        subplot.set_title(title)
        FigureCanvasTkAgg.__init__(self, self.figure, parent)

    def grid(self, **kwargs):
        self.get_tk_widget().grid(**kwargs)


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
    root = tkinter.Tk()
    root.title('Test')
    root.minsize(width=1000, height=100)
    main_frame = MainWindow(root, TempClassWithRandomData())
    main_frame.pack(fill=tkinter.BOTH, expand=tkinter.TRUE)
    root.mainloop()
    # while True:
    #     try:
    #         root.mainloop()
    #     except UnicodeDecodeError:
    #         continue
    #     else:
    #         break
