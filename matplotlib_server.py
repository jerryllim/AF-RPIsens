import tkinter
from tkinter import ttk
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class BarChartFrame(ttk.Frame):
    WIDTH = 0.75

    def __init__(self, parent, get_data):
        ttk.Frame.__init__(self, parent, relief='ridge', borderwidth=2)

        self.figure = Figure()
        self.subplot = self.figure.add_subplot(111)

        sensor, title, x, y = get_data()
        self.subplot.plot(x, y, 'b-o')
        self.subplot.grid(linestyle='dashed')

        self.subplot.set_ylabel('Count')
        self.subplot.set_title(title)
        canvas = FigureCanvasTkAgg(figure=self.figure, master=self)
        canvas.show()
        canvas.get_tk_widget().pack(fill=tkinter.BOTH, expand=True)


def get_data():
    sensor_name = 'Machine A'
    title = 'Hourly Output (Morning)'
    y = [103, 23, 34, 21, 36, 42, 48, 58, 77, 89, 92, 100]
    x= []
    for i in range(len(y)):
        x.append(str(i+8).zfill(2))
    return sensor_name, title, x, y


class GraphData(tkinter.Toplevel):
    def __init__(self, root):
        tkinter.Toplevel.__init__(self, root)
        self.title('Graph')
        self.frame = ttk.Frame(self)
        self.frame.pack(fill=tkinter.BOTH, expand=True)


        self.graphFrame = BarChartFrame(self.frame, get_data)
        self.graphFrame.grid(row=1, column=0, columnspan=4, sticky='nsew', padx=5, pady=5)



if __name__ == '__main__':
    root = tkinter.Tk()
    root.title('Hello Graph')
    GraphData(root)
    root.mainloop()
