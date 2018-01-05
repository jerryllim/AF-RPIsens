import tkinter
from tkinter import ttk
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib import style


class BarChartFrame(ttk.Frame):
    WIDTH = 0.75

    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)

        self.figure = Figure()
        self.subplot = self.figure.add_subplot(111)
        matplotlib.style.use('seaborn')

        sensor, title, x, y = self.get_data()
        bar_plot = self.subplot.bar(range(len(y)), y, self.WIDTH, color='r')

        self.subplot.set_ylabel('Count')
        self.subplot.set_title(title)
        self.subplot.set_xlabel(sensor)
        self.subplot.set_xticklabels(x)
        self.subplot.set_xticks(range(len(y)))
        canvas = FigureCanvasTkAgg(figure=self.figure, master=self)
        canvas.show()
        canvas.get_tk_widget().pack(fill=tkinter.BOTH, expand=True)

    def get_data(self):
        sensor_name = 'Machine A'
        title = 'Hourly Output (Morning)'
        y = [100, 20, 30, 20, 30, 40, 40, 50, 70, 80, 90, 100]
        x= []
        for i in range(12):
            x.append(str(i+8).zfill(2))
        print(x)
        print(len(y))
        return sensor_name, title, x, y


if __name__ == '__main__':
    root = tkinter.Tk()
    someFrame = BarChartFrame(root)
    someFrame.pack(fill=tkinter.BOTH, expand=True)
    root.mainloop()