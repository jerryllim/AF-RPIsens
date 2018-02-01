import tkinter
from tkinter import ttk
import calendar
import datetime
from collections import namedtuple
import server.serverDB as serverDB
import string  # TODO for testing

import matplotlib

matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  # noqa
from matplotlib.figure import Figure  # noqa

# sensor -> table_name, mode -> (daily, hourly, minutely), datetime -> (either Date, Date or Date, Shift or Date, Hour)
plotSetting = namedtuple('plotSetting', ['machine', 'mode', 'details'])


class TempClassWithRandomData:  # TODO to delete for testing
    def __init__(self):
        self.sensorList = []
        for index in range(13):
            self.sensorList.append('Machine {}\n1 Jan 2018 Morning'.format(string.ascii_uppercase[index]))


class MainWindow(ttk.Frame):
    NUM_COL = 2

    def __init__(self, parent, data_class: TempClassWithRandomData, **kwargs):
        self.parent = parent
        self.data_class = data_class
        ttk.Frame.__init__(self, parent, **kwargs)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=100)
        self.columnconfigure(0, weight=1)

        # Top Frame settings
        self.top_frame = ttk.Frame(self, relief='raise', borderwidth=2)
        self.top_frame.grid(row=0, column=0, sticky='nsew')
        self.top_frame.columnconfigure(0, weight=1, uniform='equalWidth')
        self.top_frame.columnconfigure(1, weight=1, uniform='equalWidth')
        self.top_frame.columnconfigure(2, weight=1, uniform='equalWidth')
        self.top_frame.rowconfigure(0, weight=1)
        self.top_frame.rowconfigure(1, weight=2)
        request_label = ttk.Label(self.top_frame, text='Requesting every {} minutes'.format('X'))  # TODO add tkinter variable?
        request_label.grid(row=0, column=0, sticky='w')
        request_button = ttk.Button(self.top_frame, text='Request now', command=self.launch_another)  # TODO add command
        request_button.grid(row=0, column=1)
        plot_button = ttk.Button(self.top_frame, text='Plot new', command=self.launch_something)  # TODO add command to plot new set of graphs
        plot_button.grid(row=0, column=2)
        self.quick_frame = None
        self.quick_access_setup()

        # Notebook setup
        view_notebook = ttk.Notebook(self)
        view_notebook.grid(row=1, column=0, sticky='nsew')

        # Make graphs
        graph_scrollable_frame = VerticalScrollFrame(view_notebook)
        graph_scrollable_frame.grid(sticky='nsew')
        view_notebook.add(graph_scrollable_frame, text='Graph')
        for col in range(MainWindow.NUM_COL):
            graph_scrollable_frame.get_interior_frame().columnconfigure(col, weight=1)

        for index in range(len(self.data_class.sensorList)):
            row = index//MainWindow.NUM_COL
            col = index % MainWindow.NUM_COL
            canvas = GraphCanvas(graph_scrollable_frame.get_interior_frame(),
                                 temp_get_data(title=self.data_class.sensorList[index]))
            canvas.show()
            canvas.grid(row=row, column=col, sticky='nsew', padx=5, pady=5)

        # TreeView Frame
        treeview_frame = ttk.Frame(self)
        treeview_frame.grid(sticky='nsew', padx=5, pady=5)
        view_notebook.add(treeview_frame, text='Details')
        treeview_frame.rowconfigure(0, weight=1)
        treeview_frame.columnconfigure(0, weight=1)
        treeview_frame.columnconfigure(1, weight=0)
        # TreeView
        self.live_treeview = ttk.Treeview(treeview_frame)
        self.live_treeview.grid(row=0, column=0, sticky='nsew')
        self.live_treeview['show'] = 'headings'
        self.live_treeview['column'] = ('machine', 'sensor', 'count', 'timestamp')
        self.live_treeview.heading('machine', text='Machine')
        self.live_treeview.heading('sensor', text='Sensor')
        self.live_treeview.heading('count', text='Count')
        self.live_treeview.heading('timestamp', text='Timestamp')
        self.live_treeview.column('machine', width=100)
        self.live_treeview.column('sensor', width=100)
        self.live_treeview.column('count', width=60, anchor=tkinter.E)
        self.live_treeview.column('timestamp', width=70)
        # Scroll for Treeview
        treeview_v_scroll = ttk.Scrollbar(treeview_frame, orient='vertical', command=self.live_treeview.yview)
        treeview_v_scroll.grid(row=0, column=1, sticky='nsw')
        self.live_treeview.configure(yscrollcommand=treeview_v_scroll.set)

    def quick_access_setup(self):  # TODO
        if self.quick_frame is not None:
            self.quick_frame.destroy()
        self.quick_frame = ttk.LabelFrame(self.top_frame, text='Quick Access: ')
        self.quick_frame.grid(row=1, column=0, columnspan=3, sticky='nsew')
        for col in range(MainWindow.NUM_COL):
            self.quick_frame.columnconfigure(col, weight=1)
        for index in range(4):
            row = index//MainWindow.NUM_COL
            col = index % MainWindow.NUM_COL
            button = ttk.Button(self.quick_frame, text='Button {}'.format(index))
            button.grid(row=row, column=col)

    def launch_something(self):  # TODO
        test = tkinter.Toplevel(self.parent)
        test.title('Test')
        test.geometry('-200-200')
        test2 = GraphDetailView(test, ('some',))
        test2.pack(fill=tkinter.BOTH, expand=tkinter.TRUE)

    def launch_another(self):  # TODO
        test = tkinter.Toplevel(self.parent)
        test.title('Test')
        test.geometry('-200-200')
        test2 = GraphDetailSettingsPage(test)
        test2.pack(fill=tkinter.BOTH, expand=tkinter.TRUE)


class GraphDetailView(ttk.Frame):
    NUM_COL = 2

    def __init__(self, parent, data, **kwargs):
        ttk.Frame.__init__(self, parent, **kwargs)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=5)
        self.columnconfigure(0, weight=1)
        self.top_frame = ttk.Frame(self)
        self.top_frame.grid(row=0, column=0, sticky='nsew')
        self.data = data

        # Notebook setup
        view_notebook = ttk.Notebook(self)
        view_notebook.grid(row=1, column=0, sticky='nsew')
        # Graph
        self.graph_scrollable_frame = VerticalScrollFrame(view_notebook)
        self.graph_scrollable_frame.grid(sticky='nsew')
        view_notebook.add(self.graph_scrollable_frame, text='Graph')
        # TreeView Frame
        treeview_frame = ttk.Frame(self)
        treeview_frame.grid(sticky='nsew', padx=5, pady=5)
        view_notebook.add(treeview_frame, text='Details')
        treeview_frame.rowconfigure(0, weight=1)
        treeview_frame.columnconfigure(0, weight=1)
        treeview_frame.columnconfigure(1, weight=0)
        # TreeView
        self.treeview = ttk.Treeview(treeview_frame)
        self.treeview.grid(row=0, column=0, sticky='nsew')
        self.treeview['show'] = 'headings'
        self.treeview['column'] = ('machine', 'count', 'timestamp')
        self.treeview.heading('machine', text='Machine')
        self.treeview.heading('count', text='Count')
        self.treeview.heading('timestamp', text='Timestamp')
        self.treeview.column('machine', width=100)
        self.treeview.column('count', width=60, anchor=tkinter.E)
        self.treeview.column('timestamp', width=70)
        # Scroll for Treeview
        treeview_v_scroll = ttk.Scrollbar(treeview_frame, orient='vertical', command=self.treeview.yview)
        treeview_v_scroll.grid(row=0, column=1, sticky='nsw')
        self.treeview.configure(yscrollcommand=treeview_v_scroll.set)

    def graph_setups(self, data):
        for column in range(MainWindow.NUM_COL):
            self.graph_scrollable_frame.get_interior_frame().columnconfigure(column, weight=1)
        # TODO data structure
        for index in range(len(data)):
            row = index//MainWindow.NUM_COL
            col = index % MainWindow.NUM_COL
            canvas = GraphCanvas(self.graph_scrollable_frame.get_interior_frame(),
                                 data[index])
            canvas.show()
            canvas.grid(row=row, column=col, sticky='nsew', padx=5, pady=5)

    def treeview_setups(self, data):
        # TODO data structure
        for machine, sensor, timestamp, count in data:
            self.treeview.insert('', tkinter.END, values=(machine, sensor, count, timestamp))

    def get_data_from_database(self, setting):
        machine, mode, (detail1, detail2) = setting
        if mode == 'Daily':
            date_list, count_list = serverDB.DatabaseManager.get_sums(machine, detail1, detail2, mode)
        elif mode == 'Hourly':
            pass

        title = '{}\n{} - {}'.format(machine, detail1, detail2)
        return title, date_list, count_list


class PlotSettingFrame(tkinter.Frame):
    LABEL_NAMES = ['Machine: ', 'Mode: ', 'Detail: ']

    def __init__(self, parent, settings):
        tkinter.Frame.__init__(self, parent, highlightbackground='black', highlightthickness=2)
        self.settings = settings
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        for index in range(len(PlotSettingFrame.LABEL_NAMES)):
            label = tkinter.Label(self, text=PlotSettingFrame.LABEL_NAMES[index], width=7)
            label.grid(row=index, column=0, sticky='w')
        self.machine_label = tkinter.Label(self, text=self.settings.machine)
        self.machine_label.grid(row=0, column=1)
        mode = self.settings.mode
        self.mode_label = tkinter.Label(self, text=mode)
        self.mode_label.grid(row=1, column=1)
        detail1, detail2 = self.settings.details
        detail_string = u'{} \u2192 {}'.format(detail1, detail2)
        self.detail_label = tkinter.Label(self, text=detail_string)
        self.detail_label.grid(row=2, column=1)


class GraphDetailSettingsPage(ttk.Frame):

    def __init__(self, parent, **kwargs):
        ttk.Frame.__init__(self, parent, **kwargs)
        self.parent = parent
        self.plot_settings_list = []
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(3, weight=1)
        self.columnconfigure(0, weight=1)
        # New
        choice_frame = ttk.Frame(self)
        choice_frame.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        sensor_label = ttk.Label(choice_frame, text='Sensor: ')
        sensor_label.grid(row=0, column=0, sticky='e')
        self.sensor_var = tkinter.StringVar()
        sensor_list = ["Line6-Outer", "Line6-Inner", "Line6-Label", "Line6-Slitter",
                       "Line5-Outer", "Line5-Inner", "Line5-Label", "Line5-Slitter"]  # TODO change this
        self.sensor_var.set(sensor_list[0])
        sensor_option = ttk.OptionMenu(choice_frame, self.sensor_var, self.sensor_var.get(), *sensor_list)
        sensor_option.grid(row=0, column=1, sticky='w')
        mode_label = ttk.Label(choice_frame, text='Mode: ')
        mode_label.grid(row=1, column=0, sticky='e')
        mode_list = ['Daily', 'Hourly', 'Minutely']
        self.mode_var = tkinter.StringVar()
        self.mode_var.set(mode_list[0])
        mode_menu = ttk.OptionMenu(choice_frame, self.mode_var, self.mode_var.get(), *mode_list,
                                   command=self.set_mutable_frame)
        mode_menu.grid(row=1, column=1, sticky='ew')
        # Mutable options
        self.mutable_frame = None
        self.detail1_var = tkinter.StringVar()
        self.detail2_var = tkinter.StringVar()
        self.set_mutable_frame()
        # Add Buttons
        add_button = ttk.Button(self, text='Add', command=self.add_plot_settings)  # TODO add command
        add_button.grid(row=2, column=0, sticky='e')
        # Graphs setting
        self.data_frame = None
        self.set_data_frame()
        # Okay & Cancel Buttons
        button_frame = ttk.Frame(self)
        button_frame.grid(row=4, column=0, sticky='nsew', padx=5, pady=5)
        plot_button = ttk.Button(button_frame, text='Plot')  # TODO add command
        plot_button.pack(side=tkinter.RIGHT)
        cancel_button = ttk.Button(button_frame, text='Cancel', command=self.parent.destroy)
        cancel_button.pack(side=tkinter.RIGHT)

    def set_mutable_frame(self, _selected=None):
        if self.mutable_frame is not None:
            self.mutable_frame.destroy()
        self.mutable_frame = ttk.Frame(self)
        self.mutable_frame.grid(row=1, column=0, sticky='nsew')
        self.mutable_frame.rowconfigure(0, weight=1)
        self.mutable_frame.columnconfigure(0, weight=1)
        self.mutable_frame.columnconfigure(1, weight=1)
        self.mutable_frame.columnconfigure(2, weight=1)
        self.detail1_var.set('')
        self.detail2_var.set('')
        if self.mode_var.get() == 'Daily':
            from_label = ttk.Label(self.mutable_frame, text='From: ')
            from_label.grid(row=0, column=0, sticky='e')
            from_entry = ttk.Entry(self.mutable_frame, textvariable=self.detail1_var, state=tkinter.DISABLED, width=10)
            from_entry.grid(row=0, column=1, sticky='w')
            from_calendar = ttk.Button(self.mutable_frame, text=u'\u2380',
                                       command=lambda: self.launch_calendar(self.detail1_var))
            from_calendar.grid(row=0, column=2, sticky='w')
            to_label = ttk.Label(self.mutable_frame, text='To: ')
            to_label.grid(row=1, column=0, sticky='e')
            to_entry = ttk.Entry(self.mutable_frame, textvariable=self.detail2_var, state=tkinter.DISABLED, width=10)
            to_entry.grid(row=1, column=1, sticky='w')
            to_calendar = ttk.Button(self.mutable_frame, text=u'\u2380',
                                     command=lambda: self.launch_calendar(self.detail2_var))
            to_calendar.grid(row=1, column=2, sticky='w')
        elif self.mode_var.get() == 'Hourly':
            date_label = ttk.Label(self.mutable_frame, text='Date: ')
            date_label.grid(row=0, column=0, sticky='e')
            date_entry = ttk.Entry(self.mutable_frame, textvariable=self.detail1_var, state=tkinter.DISABLED, width=10)
            date_entry.grid(row=0, column=1, sticky='w')
            date_calendar = ttk.Button(self.mutable_frame, text=u'\u2380',
                                       command=lambda: self.launch_calendar(self.detail1_var))
            date_calendar.grid(row=0, column=2, sticky='w')
            shift_label = ttk.Label(self.mutable_frame, text='Shift: ')
            shift_label.grid(row=1, column=0, sticky='e')
            shift_list = ['Morning', 'Night']  # TODO to retrieve
            self.detail2_var.set(shift_list[0])
            shift_option = ttk.OptionMenu(self.mutable_frame, self.detail2_var, self.detail2_var.get(), *shift_list)
            shift_option.grid(row=1, column=1, sticky='w')
        elif self.mode_var.get() == 'Minutely':
            date_label = ttk.Label(self.mutable_frame, text='Date: ')
            date_label.grid(row=0, column=0, sticky='e')
            date_entry = ttk.Entry(self.mutable_frame, textvariable=self.detail1_var, state=tkinter.DISABLED, width=10)
            date_entry.grid(row=0, column=1, sticky='w')
            date_calendar = ttk.Button(self.mutable_frame, text=u'\u2380',
                                       command=lambda: self.launch_calendar(self.detail1_var))
            date_calendar.grid(row=0, column=2, sticky='w')
            hour_label = ttk.Label(self.mutable_frame, text='Hour: ')
            hour_label.grid(row=1, column=0, sticky='e')
            hour_list = [('{}00'.format(str(i).zfill(2))) for i in range(24)]
            self.detail2_var.set(hour_list[0])
            hour_option = ttk.OptionMenu(self.mutable_frame, self.detail2_var, self.detail2_var.get(), *hour_list)
            hour_option.grid(row=1, column=1, sticky='w')

    def set_data_frame(self):
        if self.data_frame is not None:
            self.data_frame.destroy()
        self.data_frame = VerticalScrollFrame(self)
        self.data_frame.grid(row=3, column=0, sticky='nsew', padx=5, pady=5)
        for setting in self.plot_settings_list:
            data = PlotSettingFrame(self.data_frame.get_interior_frame(), setting)
            data.pack(side=tkinter.TOP, fill=tkinter.BOTH)

    def launch_calendar(self, variable):
        calendar_pop = tkinter.Toplevel(self.parent)
        calendar_pop.title('Select date')
        calendar_pop.resizable(False, False)
        calendar_pop_frame = CalendarPop(calendar_pop, variable)
        calendar_pop_frame.pack(fill=tkinter.BOTH, expand=tkinter.TRUE)

    def add_plot_settings(self):
        if self.detail1_var.get() == '' or self.detail2_var.get() == '':
            return
        setting = plotSetting(self.sensor_var.get(), self.mode_var.get(),
                              (self.detail1_var.get(), self.detail2_var.get()))
        self.plot_settings_list.append(setting)
        self.set_data_frame()


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


class GraphCanvas(FigureCanvasTkAgg):
    def __init__(self, parent, data):
        self.figure = Figure()
        self.figure.set_tight_layout(True)

        subplot = self.figure.add_subplot(1, 1, 1)
        title, x, y = data
        subplot.plot(x, y, 'b-o')
        subplot.grid(linestyle='dashed')
        subplot.set_title(title)
        FigureCanvasTkAgg.__init__(self, self.figure, parent)

    def grid(self, **kwargs):
        self.get_tk_widget().grid(**kwargs)


class CalendarPop(tkinter.Frame):
    DAYS_A_WEEK = 7

    def __init__(self, parent, variable, **kwargs):
        self.variable = variable
        self.parent = parent
        today = datetime.date.today()
        self._date = datetime.date(today.year, today.month, 1)
        tkinter.Frame.__init__(self, parent, **kwargs)
        self.columnconfigure(0, weight=0, uniform='equalWidth')
        self.columnconfigure(1, weight=0, uniform='equalWidth')
        self.columnconfigure(2, weight=0, uniform='equalWidth')
        self.columnconfigure(3, weight=0, uniform='equalWidth')
        self.columnconfigure(4, weight=0, uniform='equalWidth')
        self.columnconfigure(5, weight=0, uniform='equalWidth')
        self.columnconfigure(6, weight=0, uniform='equalWidth')
        left_button = tkinter.Button(self, text=u'\u25C0', width=3, command=self._prev_month)
        left_button.grid(row=0, column=0)
        right_button = tkinter.Button(self, text=u'\u25B6', width=3, command=self._next_month)
        right_button.grid(row=0, column=6)
        self.month_var = tkinter.StringVar()
        self.month_var.set(self._date.strftime('%B %Y'))
        month_label = tkinter.Label(self, textvariable=self.month_var)
        month_label.grid(row=0, column=1, columnspan=5)
        self._calendar = calendar.TextCalendar()
        header = [day for day in self._calendar.formatweekheader(3).split(' ')]
        for index in range(CalendarPop.DAYS_A_WEEK):
            temp_label = tkinter.Label(self, text=header[index], background='red', foreground='white', width=4)
            temp_label.grid(row=1, column=index)
        self.day_buttons = []
        self._update_calendar()

    def _update_calendar(self):
        for button in self.day_buttons:
            button.destroy()
        month = self._calendar.monthdayscalendar(self._date.year, self._date.month)
        for week in month:
            for index in range(CalendarPop.DAYS_A_WEEK):
                if week[index] != 0:
                    row = month.index(week)+2
                    date = week[index]
                    button = tkinter.Button(self, text=date, command=lambda x=date: self.button_pressed(x))
                    button.grid(row=row, column=index)
                    self.day_buttons.append(button)
        self.month_var.set(self._date.strftime('%B %Y'))

    def _prev_month(self):
        temp_date = self._date - datetime.timedelta(days=1)
        self._date = datetime.date(temp_date.year, temp_date.month, 1)
        self._update_calendar()

    def _next_month(self):
        temp_date = self._date + datetime.timedelta(days=31)
        self._date = datetime.date(temp_date.year, temp_date.month, 1)
        self._update_calendar()

    def button_pressed(self, day):
        self.variable.set(datetime.date(self._date.year, self._date.month, day).strftime('%d-%m-%Y'))
        self.parent.destroy()


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
    # root.mainloop()
    while True:
        try:
            root.mainloop()
        except UnicodeDecodeError:
            continue
        else:
            break
