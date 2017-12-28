import tkinter
from tkinter import ttk
from tkinter import messagebox
from collections import OrderedDict
from sensor import sensorGlobal


def multi_func(*fs):
    for f in fs:
        f()


class MainWindow:
    def __init__(self, root, r_pi):
        self.rPi = r_pi
        self.dataHandler = r_pi.dataHandler
        self.advancedWindow = None
        self.mainWindow = root
        self.mainWindow.title('Sensor Reading')
        self.mainWindow.geometry('-8-200')
        self.mainWindow.minsize(width=500, height=200)
        self.mainWindow.columnconfigure(0, weight=1)
        self.mainWindow.rowconfigure(0, weight=1)
        self.main_window_frame = ttk.Frame(self.mainWindow)

        self.count = {}
        for id_key in self.dataHandler.get_id():
            _temp = tkinter.IntVar()
            self.count[id_key] = _temp

        self.main_window_frame.destroy()
        self.main_window_frame = ttk.Frame(self.mainWindow)
        self.main_window_frame.grid(sticky='nsew')
        self.main_window_frame.grid_columnconfigure(0, weight=1, minsize=500)
        self.main_window_frame.grid_rowconfigure(0, weight=10, minsize=150)
        self.main_window_frame.grid_rowconfigure(1, weight=1)

        button_frame = ttk.Frame(self.main_window_frame)
        button_frame.grid(row=1, column=0, padx=5, pady=5)
        advanced_button = ttk.Button(button_frame, text='Advanced', command=self.launch_advanced_window)
        advanced_button.pack(side=tkinter.LEFT)
        # TODO is this the best way to quit and destroy?
        quit_button = ttk.Button(button_frame, text='Quit',
                                 command=lambda: multi_func(self.mainWindow.quit, self.mainWindow.destroy))
        quit_button.pack(side=tkinter.LEFT)

        self.draw_reading_rows()

    def draw_reading_rows(self):
        def readings_row_setup(parent, row):
            row_frame = ttk.Frame(parent)
            row_frame.grid(row=row, column=0, sticky='nsew')
            row_frame.columnconfigure(0, weight=1, uniform='equalColumn')
            row_frame.columnconfigure(1, weight=1, uniform='equalColumn')
            row_frame.columnconfigure(2, weight=1, uniform='equalColumn')
            row_frame.columnconfigure(3, weight=1, uniform='equalColumn')
            row_frame.columnconfigure(4, weight=1, uniform='equalColumn')
            row_frame.rowconfigure(0, weight=1, minsize=50)

            _id_array = self.dataHandler.get_id()
            for index in range(5):
                temp_frame = ttk.Frame(row_frame, relief=tkinter.RIDGE, borderwidth=2)
                temp_frame.grid(row=0, column=index, sticky='nsew')
                loc = index + row*5
                if loc < len(_id_array):
                    _name, _pin, _bounce = self.dataHandler.sensorDict[_id_array[loc]]
                    name_label = ttk.Label(temp_frame, text=_name)
                    name_label.pack()
                    value_label = ttk.Label(temp_frame, textvariable=self.count.get(_id_array[loc]))
                    value_label.pack()

        readings_frame = ttk.Frame(self.main_window_frame)
        readings_frame.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        readings_frame.rowconfigure(0, weight=1)
        readings_frame.rowconfigure(1, weight=1)
        readings_frame.rowconfigure(2, weight=1)
        readings_frame.columnconfigure(0, weight=1)

        readings_row_setup(readings_frame, 0)
        readings_row_setup(readings_frame, 1)
        readings_row_setup(readings_frame, 2)

    def start_gui(self):
        self.mainWindow.mainloop()

    # Advanced Window Setup and Launch
    def launch_advanced_window(self):
        def quit_advanced_window():
            self.advancedWindow.destroy()
            self.draw_reading_rows()

        def delete_item():
            for item in tree_view.selection():
                tree_view.delete(item)

        def launch_edit():
            item = tree_view.focus()
            if item != '':
                launch_item_window(item)

        def move_item(direction):
            item = tree_view.focus()
            if item != '':
                index = tree_view.index(item) + direction
                tree_view.move(item, '', index)

        # Launch window to add/edit new item to Treeview (Add new sensor/change sensor properties)
        def launch_item_window(iid=''):
            def key_validate(P, S, W):
                if W == 'pin' and len(P) > 2:
                    return False
                elif W == 'bounce' and len(P) > 4:
                    return False
                if S.isdigit():
                    return True
                else:
                    return False

            def quit_item_window():
                item_window.destroy()
                advanced_window_frame.grab_set()

            def validate_entries():
                if len(name_entry.get()) == 0:
                    return 'Please enter a name'
                if len(pin_entry.get()) == 0:
                    return 'Please enter a connected pin'

                for item in tree_view.get_children():
                    if item != iid:
                        c_id, c_name, c_pin, c_bounce = tree_view.item(item)['values']
                        if c_id == id_entry.get():
                            return 'Duplicated ID found'
                        if c_name == name_entry.get():
                            return 'Duplicated Name found'
                        if c_pin == int(pin_entry.get()):
                            return 'Duplicated Pin found'

                return True

            def add_item():
                msg = validate_entries()
                if msg is True:
                    tree_view.insert('', tkinter.END, values=(id_entry.get(), name_entry.get(), pin_entry.get(),
                                                              bounce_entry.get()))
                    quit_item_window()
                else:
                    messagebox.showerror('Error', msg)

            def change_and_quit():
                tree_view.item(iid, values=(id_entry.get(), name_entry.get(), pin_entry.get(),
                                            bounce_entry.get()))
                quit_item_window()

            def edit_item():
                msg = validate_entries()
                if msg is True:
                    if iid != '':
                        o_id, o_name, o_pin, o_bounce = tree_view.item(iid)['values']
                        if o_id != id_entry.get():
                            if messagebox.askokcancel('Warning', 'Changing IDs will reset the count'):
                                change_and_quit()
                        else:
                            change_and_quit()

                    else:
                        change_and_quit()

                else:
                    messagebox.showerror('Error', msg)

            item_window = tkinter.Toplevel(self.advancedWindow)
            item_window.title('Item')
            item_window.geometry('-200-200')
            item_window.columnconfigure(0, weight=1)
            item_window.rowconfigure(0, weight=1)
            item_window_frame = ttk.Frame(item_window)
            item_window_frame.grid(sticky='nsew')
            item_window_frame.rowconfigure(0, weight=1)
            item_window_frame.rowconfigure(1, weight=1)
            item_window_frame.columnconfigure(0, weight=1)

            entry_frame = ttk.Frame(item_window_frame)
            entry_frame.grid(row=0, sticky='nsew', padx=5, pady=5)
            entry_frame.rowconfigure(0, weight=1)
            entry_frame.rowconfigure(1, weight=1)
            entry_frame.columnconfigure(0, weight=5)
            entry_frame.columnconfigure(1, weight=6)
            entry_frame.columnconfigure(2, weight=1)
            entry_frame.columnconfigure(3, weight=2)
            id_label = ttk.Label(entry_frame, text='Unique ID')
            id_label.grid(row=0, column=0, sticky='sw')
            id_entry = ttk.Entry(entry_frame, width=10)
            id_entry.grid(row=1, column=0, sticky='nsew', pady=5)
            id_entry.delete(0, tkinter.END)
            id_entry.focus()
            name_label = ttk.Label(entry_frame, text='Name')
            name_label.grid(row=0, column=1, sticky='sw')
            name_entry = ttk.Entry(entry_frame, width=30)
            name_entry.grid(row=1, column=1, sticky='nsew', pady=5)
            name_entry.delete(0, tkinter.END)
            validation = self.mainWindow.register(key_validate)
            pin_label = ttk.Label(entry_frame, text='Pin')
            pin_label.grid(row=0, column=2, sticky='sw')
            pin_entry = ttk.Entry(entry_frame, width=2, justify=tkinter.RIGHT, validate='key',
                                  validatecommand=(validation, '%P', '%S', 'pin'))
            pin_entry.grid(row=1, column=2, sticky='nsew', pady=5)
            pin_entry.delete(0, tkinter.END)
            bounce_label = ttk.Label(entry_frame, text='Debounce')
            bounce_label.grid(row=0, column=3, sticky='sw')
            bounce_entry = ttk.Entry(entry_frame, width=4, justify=tkinter.RIGHT, validate='key',
                                     validatecommand=(validation, '%P', '%S', 'bounce'))
            bounce_entry.grid(row=1, column=3, sticky='nsew', pady=5)

            button_frame = ttk.Frame(item_window_frame)
            button_frame.grid(row=1, padx=5, pady=5)

            if iid != '':
                _edit_button = ttk.Button(button_frame, text='Edit', command=edit_item)
                _edit_button.pack(side=tkinter.LEFT)
                i_id, i_name, i_pin, i_bounce = tree_view.item(iid)['values']
                id_entry.insert(0, i_id)
                name_entry.insert(0, i_name)
                pin_entry.insert(0, i_pin)
                bounce_entry.insert(0, i_bounce)
            else:
                _add_button = ttk.Button(button_frame, text='Add', command=add_item)
                _add_button.pack(side=tkinter.LEFT)

            _cancel_button = ttk.Button(button_frame, text='Cancel', command=quit_item_window)
            _cancel_button.pack(side=tkinter.RIGHT)

            item_window.grab_set()

        def save_configuration():
            _temp_dict = OrderedDict()
            for iid in tree_view.get_children():
                s_id, s_name, s_pin, s_bounce = tree_view.item(iid)['values']
                _temp_dict[s_id] = sensorGlobal.sensorInfo(s_name, s_pin, s_bounce)
                if s_id not in self.count:
                    self.count[s_id] = tkinter.IntVar()
                    self.dataHandler.countDict[s_id] = 0
            to_delete = set(_temp_dict.keys()).difference(set(self.count.keys()))
            for key in to_delete:
                self.count.pop(key)
                self.dataHandler.countDict.pop(key)
            # self.rPi.remove_detections()
            self.dataHandler.sensorDict.clear()
            self.dataHandler.sensorDict.update(_temp_dict)
            self.dataHandler.save_data()
            # self.rPi.reset_pins()  # RPi uncomment here TODO remove when using pigpio?
            quit_advanced_window()

        self.advancedWindow = tkinter.Toplevel(self.mainWindow)
        self.advancedWindow.title('Advanced Options')
        self.advancedWindow.geometry('-200-200')
        self.advancedWindow.columnconfigure(0, weight=1)
        self.advancedWindow.rowconfigure(0, weight=1)
        advanced_window_frame = ttk.Frame(self.advancedWindow)
        advanced_window_frame.grid(sticky='nsew')
        advanced_window_frame.columnconfigure(0, weight=10)
        advanced_window_frame.columnconfigure(1, weight=1)
        advanced_window_frame.rowconfigure(0, weight=5)
        advanced_window_frame.rowconfigure(1, weight=1)

        # Bottom Buttons
        bottom_button_frame = ttk.Frame(advanced_window_frame)
        bottom_button_frame.grid(row=2, column=1, padx=5, pady=5)
        save_button = ttk.Button(bottom_button_frame, text='Save', command=save_configuration)
        save_button.pack(side=tkinter.LEFT)
        cancel_button = ttk.Button(bottom_button_frame, text='Cancel', command=self.advancedWindow.destroy)
        cancel_button.pack(side=tkinter.LEFT)

        # Treeview
        treeview_frame = ttk.Frame(advanced_window_frame)
        treeview_frame.grid(row=0, column=0, rowspan=3, sticky='nsew', padx=5, pady=5)
        treeview_frame.rowconfigure(0, weight=1)
        treeview_frame.columnconfigure(0, weight=10)
        treeview_frame.columnconfigure(1, weight=0)
        tree_view = ttk.Treeview(treeview_frame)
        tree_view.grid(row=0, column=0, sticky='nsew')
        tree_view['show'] = 'headings'
        tree_view['column'] = ('id', 'name', 'pin', 'bounce')
        tree_view.heading('id', text='Unique ID')
        tree_view.heading('name', text='Name')
        tree_view.heading('pin', text='Pin')
        tree_view.heading('bounce', text='Debounce duration')
        tree_view.column('id', width=100)
        tree_view.column('name', width=200)
        tree_view.column('pin', width=60, anchor=tkinter.E)
        tree_view.column('bounce', width=60, anchor=tkinter.E)

        # Populate Treeview
        for _id, (_name, _pin, _bounce) in self.dataHandler.sensorDict.items():
            tree_view.insert('', tkinter.END, values=(_id, _name, _pin, _bounce))

        # Scroll for Treeview
        treeview_vscroll = ttk.Scrollbar(treeview_frame, orient='vertical', command=tree_view.yview)
        treeview_vscroll.grid(row=0, column=1, sticky='nsw')
        tree_view.configure(yscrollcommand=treeview_vscroll.set)

        # Add & Delete buttons
        top_button_frame = ttk.Frame(advanced_window_frame)
        top_button_frame.grid(row=0, column=1, padx=5, pady=5)
        add_button = ttk.Button(top_button_frame, text='Add', command=launch_item_window)
        add_button.pack()
        edit_button = ttk.Button(top_button_frame, text='Edit', command=launch_edit)
        edit_button.pack()
        delete_button = ttk.Button(top_button_frame, text='Delete', command=delete_item)
        delete_button.pack()

        # Move up & down buttons
        middle_button_frame = ttk.Frame(advanced_window_frame)
        middle_button_frame.grid(row=1, column=1, padx=5, pady=5)
        up_button = ttk.Button(middle_button_frame, text=u'\u25B2', command=lambda: move_item(-1))
        up_button.pack(side=tkinter.LEFT)
        down_button = ttk.Button(middle_button_frame, text=u'\u25BC', command=lambda: move_item(1))
        down_button.pack(side=tkinter.LEFT)

        self.advancedWindow.grab_set()


if __name__ == '__main__':
    rPi = sensorGlobal.TempClass(sensorGlobal.DataHandler())
    mainWindow = tkinter.Tk()
    MainWindow(mainWindow, rPi).start_gui()
