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

        sensor_name, title, x, y = get_data()
        self.subplot.plot(x, y, 'b-o')
        self.subplot.grid(linestyle='dashed')

        self.subplot.set_ylabel('Count')
        self.subplot.set_xlabel(sensor_name)
        self.subplot.set_title(title)
        canvas = FigureCanvasTkAgg(figure=self.figure, master=self)
        canvas.show()
        canvas.get_tk_widget().pack(fill=tkinter.BOTH, expand=True)


def get_data():  # TODO change this
    sensor_name = 'Machine A'
    title = 'Hourly Output (Morning)'
    y = [103, 23, 34, 21, 36, 42, 48, 58, 77, 89, 92, 100]
    x= []
    for i in range(len(y)):
        x.append(str(i+8).zfill(2))
    return sensor_name, title, x, y


class GraphData(tkinter.Toplevel):
    SETTING_LIST_DICT = {'Hourly': ['Morning', 'Night'],
                         'Minutely': [('{}00'.format(str(i).zfill(2))) for i in range(24)]}

    def __init__(self, parent):
        tkinter.Toplevel.__init__(self, parent)
        self.title('Graph')
        self.frame = ttk.Frame(self)
        self.frame.pack(fill=tkinter.BOTH, expand=True)
        self.frame.columnconfigure(0, weight=10)
        self.frame.columnconfigure(1, weight=1)

        option_frame = ttk.Frame(self.frame)
        option_frame.grid(sticky='nsew', padx=5, pady=5)

        # TODO get machine list
        sensor_label = ttk.Label(option_frame, text='Machine:')
        sensor_label.grid(row=0, column=0, sticky='sw')
        sensor_option_list = ['Machine A', 'Machine B', 'Machine C']
        sensor_option = tkinter.StringVar()
        sensor_option.set('Machine A')
        sensor_option_menu = ttk.OptionMenu(option_frame, sensor_option, sensor_option.get(), *sensor_option_list)
        sensor_option_menu.config(width=15)
        sensor_option_menu.grid(row=1, column=0, sticky='nw')
        # Show Mode
        mode_label = ttk.Label(option_frame, text='Mode:')
        mode_label.grid(row=0, column=1, sticky='sw')
        mode_option_list = ['Hourly', 'Minutely']
        self.mode_option = tkinter.StringVar()
        self.mode_option.set(mode_option_list[0])
        mode_option_menu = ttk.OptionMenu(option_frame, self.mode_option, self.mode_option.get(), *mode_option_list,
                                          command=lambda x: self.reset_mode_settings())
        mode_option_menu.config(width=6)
        mode_option_menu.grid(row=1, column=1, sticky='nw')
        # Mode Settings
        self.settings_option_list = self.SETTING_LIST_DICT[self.mode_option.get()]
        self.settings_option = tkinter.StringVar()
        self.settings_option.set(self.settings_option_list[0])
        self.settings_option_menu = ttk.OptionMenu(option_frame, self.settings_option, self.settings_option.get(),
                                                   *self.settings_option_list)
        self.settings_option_menu.config(width=10)
        self.settings_option_menu.grid(row=1, column=2, sticky='nw')

        # Graph
        self.graphFrame = BarChartFrame(self.frame, get_data)
        self.graphFrame.grid(row=1, column=0, sticky='nsew', padx=5, pady=5, columnspan=2)

        # Set button
        button_frame = ttk.Frame(self.frame)
        button_frame.grid(row=0, column=1, sticky='nsew', padx=5, pady=5)
        button_frame.rowconfigure(0, weight=1)
        set_button = ttk.Button(button_frame, text='Set')  # TODO set command
        set_button.grid()

    def reset_mode_settings(self):
        self.settings_option_list = self.SETTING_LIST_DICT[self.mode_option.get()]
        self.settings_option_menu.set_menu(self.settings_option_list[0], *self.settings_option_list)


if __name__ == '__main__':
    root = tkinter.Tk()
    root.title('Hello Graph')
    button = tkinter.Button(root, text='Show Graph', command=lambda: GraphData(root))
    button.pack()
    button2 = tkinter.Button(root, text='Exit', command=root.quit)
    button2.pack()
    root.mainloop()
