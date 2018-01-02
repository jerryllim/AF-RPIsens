import tkinter
from tkinter import ttk
from tkinter import messagebox
from collections import OrderedDict
from sensor import sensorGlobal

def multi_func(*fs):
    for f in fs:
        f()


class MainGUI:
    def __init__(self, root, r_pi_controller):
        self.rPiController = r_pi_controller
        self.pinDataManager = r_pi_controller.pinDataManager
        self.networkDataManager = r_pi_controller.networkDataManager
        self.dataManager = r_pi_controller.dataManager
        self.pinConfigWindow = None
        self.networkSettWindow = None
        self.settingsWindow = None
        self.mainWindow = root
        self.mainWindow.title('Sensor Reading')
        self.mainWindow.geometry('-8-200')
        self.mainWindow.minsize(width=500, height=200)
        self.mainWindow.columnconfigure(0, weight=1)
        self.mainWindow.rowconfigure(0, weight=1)
        self.main_window_frame = ttk.Frame(self.mainWindow)

        self.menuBar = tkinter.Menu(self.mainWindow)
        options = tkinter.Menu(self.menuBar, tearoff=0)
        options.add_command(label='Network Settings', command=self.launch_network_settings)
        options.add_command(label='Pin Configurations', command=self.launch_pin_configuration)
        options.add_command(label='Settings', command=self.launch_settings)
        options.add_separator()
        options.add_command(label='Exit', command=lambda: multi_func(self.mainWindow.quit, self.mainWindow.destroy))
        self.menuBar.add_cascade(label='Options', menu=options)
        self.mainWindow.config(menu=self.menuBar)

        self.count = {}
        for id_key in self.pinDataManager.get_id_list():
            _temp = tkinter.IntVar()
            self.count[id_key] = _temp

        self.main_window_frame.destroy()
        self.main_window_frame = ttk.Frame(self.mainWindow)
        self.main_window_frame.grid(sticky='nsew')
        self.main_window_frame.grid_columnconfigure(0, weight=1, minsize=500)
        self.main_window_frame.grid_rowconfigure(0, weight=10, minsize=150)

        # Bottom buttons TODO to delete
        # self.main_window_frame.grid_rowconfigure(1, weight=1)

        # button_frame = ttk.Frame(self.main_window_frame)
        # button_frame.grid(row=1, column=0, padx=5, pady=5)
        # advanced_button = ttk.Button(button_frame, text='Advanced', command=self.launch_advanced_window)
        # advanced_button.pack(side=tkinter.LEFT)
        # quit_button = ttk.Button(button_frame, text='Quit',
        #                          command=lambda: multi_func(self.mainWindow.quit, self.mainWindow.destroy))
        # quit_button.pack(side=tkinter.LEFT)

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

            _id_array = self.pinDataManager.get_id_list()
            for index in range(5):
                temp_frame = ttk.Frame(row_frame, relief=tkinter.RIDGE, borderwidth=2)
                temp_frame.grid(row=0, column=index, sticky='nsew')
                loc = index + row*5
                if loc < len(_id_array):
                    _name, _pin, _bounce = self.pinDataManager.get_sensorDict_item(_id_array[loc])
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

    def launch_settings(self):
        class SaveClass:
            pass

        def quit_window():
            self.settingsWindow.destroy()
            self.settingsWindow = None

        def save_settings():
            # Save Network Configurations
            transfer_time = save_class.transfer_option.get().rsplit(sep=' ', maxsplit=1)[0]
            save_time = save_class.save_option.get().rsplit(sep=' ', maxsplit=1)[0]
            self.rPiController.networkDataManager.set_transfer_time(transfer_time)
            self.rPiController.networkDataManager.set_save_time(save_time)

            # Save Pin Configurations
            _temp_dict = OrderedDict()
            tree_view = save_class.tree_view
            for iid in tree_view.get_children():
                s_id, s_name, s_pin, s_bounce = tree_view.item(iid)['values']
                _temp_dict[s_id] = sensorGlobal.sensorInfo(s_name, s_pin, s_bounce)
                if s_id not in self.count:
                    self.count[s_id] = tkinter.IntVar()
                    self.pinDataManager.set_countDict_item(s_id, 0)
            to_delete = set(self.count.keys()).difference(set(_temp_dict.keys()))
            for key in to_delete:
                self.count.pop(key)
                self.pinDataManager.del_countDict_item(key)
            self.pinDataManager.reset_sensorDict(_temp_dict)

            self.dataManager.save_data()
            # self.rPiController.reset_pins()  # RPi uncomment here TODO remove when using pigpio?
            self.draw_reading_rows()
            quit_window()

        def network_setup():
            network_sett_frame = ttk.Frame(settings_notebook)
            network_sett_frame.grid(sticky='nsew')
            settings_notebook.add(network_sett_frame, text='Network')
            network_sett_frame.columnconfigure(0, weight=1)
            network_sett_frame.rowconfigure(0, weight=1)
            network_sett_frame.rowconfigure(1, weight=1)

            # Options
            option_frame = ttk.Frame(network_sett_frame)
            option_frame.grid(row=0, column=0, padx=5, pady=5)
            option_frame.rowconfigure(0, weight=1)
            option_frame.rowconfigure(1, weight=1)
            option_frame.columnconfigure(0, weight=1)
            option_frame.columnconfigure(1, weight=1)
            transfer_label = ttk.Label(option_frame, text='Timestamp frequency: ', width=20)
            transfer_label.grid(row=0, column=0, sticky='w')
            transfer_option_list = ('1 minute', '5 minutes', '15 minutes', '30 minutes', '60 minutes')
            transfer_option = tkinter.StringVar()
            save_class.transfer_option = transfer_option
            transfer_option.set(self.networkDataManager.transfer_minutes + ' minute(s)')
            transfer_option_menu = ttk.OptionMenu(option_frame, transfer_option,
                                                  transfer_option.get(), *transfer_option_list)
            transfer_option_menu.config(width=10)
            transfer_option_menu.grid(row=0, column=1, sticky='ew')
            save_label = ttk.Label(option_frame, text='Save frequency: ', width=20)
            save_label.grid(row=1, column=0, sticky='w')
            save_option_list = ('2 minutes', '5 minutes', '15 minutes', '30 minutes', '60 minutes')
            save_option = tkinter.StringVar()
            save_class.save_option = save_option
            save_option.set(self.networkDataManager.save_minutes + ' minutes')
            save_option_menu = ttk.OptionMenu(option_frame, save_option, save_option.get(), *save_option_list)
            save_option_menu.config(width=10)
            save_option_menu.grid(row=1, column=1, sticky='ew')

        def pins_setup():
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
                    elif W == 'bounce' and len(P) > 3:
                        return False
                    if S.isdigit():
                        return True
                    else:
                        return False

                def quit_item_window():
                    item_window.destroy()
                    self.settingsWindow.grab_set()

                def validate_entries():
                    messages = []
                    if len(id_entry.get()) == 0:
                        messages.append('Please enter an ID.')
                    if len(name_entry.get()) == 0:
                        messages.append('Please enter a Name.')
                    if len(pin_entry.get()) == 0:
                        messages.append('Please enter a Pin number.')
                    if len(bounce_entry.get()) == 0:
                        messages.append('Please enter debounce time between 0 and 300 (ms).')
                    elif not (0 <= int(bounce_entry.get()) <= 300):
                        messages.append('Please enter debounce time between 0 and 300 (ms).')

                    for item in tree_view.get_children():
                        if item != iid:
                            c_id, c_name, c_pin, c_bounce = tree_view.item(item)['values']
                            if c_id == id_entry.get():
                                messages.append('Duplicated ID found.')
                            if c_name == name_entry.get():
                                messages.append('Duplicated Name found.')
                            if str(c_pin) == pin_entry.get():
                                messages.append('Duplicated Pin found.')

                    if messages:
                        return '\n'.join(messages)
                    else:
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

                item_window = tkinter.Toplevel(self.pinConfigWindow)
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

            # Pin Config Setup
            pin_config_frame = ttk.Frame(settings_notebook)
            pin_config_frame.grid(sticky='nsew')
            settings_notebook.add(pin_config_frame, text='Pins')
            pin_config_frame.columnconfigure(0, weight=10)
            pin_config_frame.columnconfigure(1, weight=1)
            pin_config_frame.rowconfigure(0, weight=5)
            pin_config_frame.rowconfigure(1, weight=1)

            # Treeview
            treeview_frame = ttk.Frame(pin_config_frame)
            treeview_frame.grid(row=0, column=0, rowspan=3, sticky='nsew', padx=5, pady=5)
            treeview_frame.rowconfigure(0, weight=1)
            treeview_frame.columnconfigure(0, weight=10)
            treeview_frame.columnconfigure(1, weight=0)
            save_class.tree_view = ttk.Treeview(treeview_frame)  # TODO check if there's a better solution
            tree_view = save_class.tree_view
            tree_view.grid(row=0, column=0, sticky='nsew')
            tree_view['show'] = 'headings'
            tree_view['column'] = ('id', 'name', 'pin', 'bounce')
            tree_view.heading('id', text='Unique ID')
            tree_view.heading('name', text='Name')
            tree_view.heading('pin', text='Pin')
            tree_view.heading('bounce', text='Debounce')
            tree_view.column('id', width=100)
            tree_view.column('name', width=200)
            tree_view.column('pin', width=60, anchor=tkinter.E)
            tree_view.column('bounce', width=70, anchor=tkinter.E)

            # Populate Treeview
            for _id, (_name, _pin, _bounce) in self.pinDataManager.get_sensorDict_items():
                tree_view.insert('', tkinter.END, values=(_id, _name, _pin, _bounce))

            # Scroll for Treeview
            treeview_vscroll = ttk.Scrollbar(treeview_frame, orient='vertical', command=tree_view.yview)
            treeview_vscroll.grid(row=0, column=1, sticky='nsw')
            tree_view.configure(yscrollcommand=treeview_vscroll.set)

            # Add & Delete buttons
            top_button_frame = ttk.Frame(pin_config_frame)
            top_button_frame.grid(row=0, column=1, padx=5, pady=5)
            add_button = ttk.Button(top_button_frame, text='Add', command=launch_item_window)
            add_button.pack()
            edit_button = ttk.Button(top_button_frame, text='Edit', command=launch_edit)
            edit_button.pack()
            delete_button = ttk.Button(top_button_frame, text='Delete', command=delete_item)
            delete_button.pack()

            # Move up & down buttons
            middle_button_frame = ttk.Frame(pin_config_frame)
            middle_button_frame.grid(row=1, column=1, padx=5, pady=5)
            up_button = ttk.Button(middle_button_frame, text=u'\u25B2', command=lambda: move_item(-1))
            up_button.pack(side=tkinter.RIGHT)
            down_button = ttk.Button(middle_button_frame, text=u'\u25BC', command=lambda: move_item(1))
            down_button.pack(side=tkinter.LEFT)

        if self.settingsWindow is not None:
            self.settingsWindow.lift()
        else:
            self.settingsWindow = tkinter.Toplevel(self.mainWindow)
            self.settingsWindow.title('Settings')
            self.settingsWindow.geometry('-200-200')
            self.settingsWindow.columnconfigure(0, weight=1)
            self.settingsWindow.rowconfigure(0, weight=1)
            self.settingsWindow.protocol('WM_DELETE_WINDOW', quit_window)
            settings_frame = ttk.Frame(self.settingsWindow)
            settings_frame.grid(sticky='nsew')
            settings_frame.columnconfigure(0, weight=1)
            settings_frame.rowconfigure(0, weight=5)
            settings_frame.rowconfigure(1, weight=1)

            # Bottom Buttons
            bottom_button_frame = ttk.Frame(settings_frame)
            bottom_button_frame.grid(row=1, padx=5, pady=5)
            save_button = ttk.Button(bottom_button_frame, text='Save', command=save_settings)
            save_button.pack(side=tkinter.LEFT)
            cancel_button = ttk.Button(bottom_button_frame, text='Cancel', command=quit_window)
            cancel_button.pack(side=tkinter.RIGHT)

            # Notebook
            settings_notebook = ttk.Notebook(settings_frame)
            settings_notebook.grid(row=0, column=0, sticky='nsew')
            save_class = SaveClass()
            pins_setup()
            network_setup()
            self.settingsWindow.grab_set()

    # Pin Configuration Setup and Launch
    def launch_pin_configuration(self):
        def quit_window():
            self.pinConfigWindow.destroy()
            self.pinConfigWindow = None

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
                elif W == 'bounce' and len(P) > 3:
                    return False
                if S.isdigit():
                    return True
                else:
                    return False

            def quit_item_window():
                item_window.destroy()
                pin_config_frame.grab_set()

            def validate_entries():
                messages = []
                if len(id_entry.get()) == 0:
                    messages.append('Please enter an ID.')
                if len(name_entry.get()) == 0:
                    messages.append('Please enter a Name.')
                if len(pin_entry.get()) == 0:
                    messages.append('Please enter a Pin number.')
                if len(bounce_entry.get()) == 0:
                    messages.append('Please enter debounce time between 0 and 300 (ms).')
                elif not (0 <= int(bounce_entry.get()) <= 300):
                    messages.append('Please enter debounce time between 0 and 300 (ms).')

                for item in tree_view.get_children():
                    if item != iid:
                        c_id, c_name, c_pin, c_bounce = tree_view.item(item)['values']
                        if c_id == id_entry.get():
                            messages.append('Duplicated ID found.')
                        if c_name == name_entry.get():
                            messages.append('Duplicated Name found.')
                        if str(c_pin) == pin_entry.get():
                            messages.append('Duplicated Pin found.')

                if messages:
                    return '\n'.join(messages)
                else:
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

            item_window = tkinter.Toplevel(self.pinConfigWindow)
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
                    self.pinDataManager.set_countDict_item(s_id, 0)
            to_delete = set(self.count.keys()).difference(set(_temp_dict.keys()))
            for key in to_delete:
                self.count.pop(key)
                self.pinDataManager.del_countDict_item(key)
            self.pinDataManager.reset_sensorDict(_temp_dict)
            self.pinDataManager.save_data()
            # self.rPiController.reset_pins()  # RPi uncomment here TODO remove when using pigpio?
            self.draw_reading_rows()
            quit_window()

        if self.pinConfigWindow is not None:
            self.pinConfigWindow.lift()
        else:
            self.pinConfigWindow = tkinter.Toplevel(self.mainWindow)
            self.pinConfigWindow.title('Pin Configurations')
            self.pinConfigWindow.geometry('-200-200')
            self.pinConfigWindow.columnconfigure(0, weight=1)
            self.pinConfigWindow.rowconfigure(0, weight=1)
            self.pinConfigWindow.protocol('WM_DELETE_WINDOW', quit_window)
            pin_config_frame = ttk.Frame(self.pinConfigWindow)
            pin_config_frame.grid(sticky='nsew')
            pin_config_frame.columnconfigure(0, weight=10)
            pin_config_frame.columnconfigure(1, weight=1)
            pin_config_frame.rowconfigure(0, weight=5)
            pin_config_frame.rowconfigure(1, weight=1)

            # Bottom Buttons
            bottom_button_frame = ttk.Frame(pin_config_frame)
            bottom_button_frame.grid(row=2, column=1, padx=5, pady=5)
            save_button = ttk.Button(bottom_button_frame, text='Save', command=save_configuration)
            save_button.pack(side=tkinter.LEFT)
            cancel_button = ttk.Button(bottom_button_frame, text='Cancel', command=quit_window)
            cancel_button.pack(side=tkinter.RIGHT)

            # Treeview
            treeview_frame = ttk.Frame(pin_config_frame)
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
            tree_view.heading('bounce', text='Debounce')
            tree_view.column('id', width=100)
            tree_view.column('name', width=200)
            tree_view.column('pin', width=60, anchor=tkinter.E)
            tree_view.column('bounce', width=70, anchor=tkinter.E)

            # Populate Treeview
            for _id, (_name, _pin, _bounce) in self.pinDataManager.get_sensorDict_items():
                tree_view.insert('', tkinter.END, values=(_id, _name, _pin, _bounce))

            # Scroll for Treeview
            treeview_vscroll = ttk.Scrollbar(treeview_frame, orient='vertical', command=tree_view.yview)
            treeview_vscroll.grid(row=0, column=1, sticky='nsw')
            tree_view.configure(yscrollcommand=treeview_vscroll.set)

            # Add & Delete buttons
            top_button_frame = ttk.Frame(pin_config_frame)
            top_button_frame.grid(row=0, column=1, padx=5, pady=5)
            add_button = ttk.Button(top_button_frame, text='Add', command=launch_item_window)
            add_button.pack()
            edit_button = ttk.Button(top_button_frame, text='Edit', command=launch_edit)
            edit_button.pack()
            delete_button = ttk.Button(top_button_frame, text='Delete', command=delete_item)
            delete_button.pack()

            # Move up & down buttons
            middle_button_frame = ttk.Frame(pin_config_frame)
            middle_button_frame.grid(row=1, column=1, padx=5, pady=5)
            up_button = ttk.Button(middle_button_frame, text=u'\u25B2', command=lambda: move_item(-1))
            up_button.pack(side=tkinter.RIGHT)
            down_button = ttk.Button(middle_button_frame, text=u'\u25BC', command=lambda: move_item(1))
            down_button.pack(side=tkinter.LEFT)

            self.pinConfigWindow.grab_set()

    def launch_network_settings(self):  # TODO test on RPi
        def quit_window():
            self.networkSettWindow.destroy()
            self.networkSettWindow = None

        def save_configurations():
            transfer_time = transfer_option.get().rsplit(sep=' ', maxsplit=1)[0]
            save_time = save_option.get().rsplit(sep=' ', maxsplit=1)[0]
            self.rPiController.networkDataManager.set_transfer_time(transfer_time)
            self.rPiController.networkDataManager.set_save_time(save_time)
            quit_window()

        if self.networkSettWindow is not None:
            self.networkSettWindow.lift()
        else:
            self.networkSettWindow = tkinter.Toplevel(self.mainWindow)
            self.networkSettWindow.title('Network Settings')
            self.networkSettWindow.geometry('-200-200')
            self.networkSettWindow.columnconfigure(0, weight=1)
            self.networkSettWindow.rowconfigure(0, weight=1)
            self.networkSettWindow.protocol('WM_DELETE_WINDOW', quit_window)
            network_sett_frame = ttk.Frame(self.networkSettWindow)
            network_sett_frame.grid(sticky='nsew')
            network_sett_frame.columnconfigure(0, weight=1)
            network_sett_frame.rowconfigure(0, weight=1)
            network_sett_frame.rowconfigure(1, weight=1)

            # Buttons
            button_frame = ttk.Frame(network_sett_frame)
            button_frame.grid(row=1, column=0, padx=5, pady=5)
            save_button = ttk.Button(button_frame, text='Save', command=save_configurations)
            save_button.pack(side=tkinter.LEFT)
            cancel_button = ttk.Button(button_frame, text='Cancel', command=quit_window)
            cancel_button.pack(side=tkinter.RIGHT)

            # Options
            option_frame = ttk.Frame(network_sett_frame)
            option_frame.grid(row=0, column=0, padx=5, pady=5)
            option_frame.rowconfigure(0, weight=1)
            option_frame.rowconfigure(1, weight=1)
            option_frame.columnconfigure(0, weight=1)
            option_frame.columnconfigure(1, weight=1)
            transfer_label = ttk.Label(option_frame, text='Timestamp frequency: ', width=20)
            transfer_label.grid(row=0, column=0, sticky='w')
            transfer_option_list = ('5 minutes', '15 minutes', '30 minutes', '60 minutes')
            transfer_option = tkinter.StringVar()
            transfer_option.set(transfer_option_list[0])
            transfer_option_menu = ttk.OptionMenu(option_frame, transfer_option, transfer_option_list[0],
                                                  *transfer_option_list)
            transfer_option_menu.config(width=10)
            transfer_option_menu.grid(row=0, column=1, sticky='ew')
            save_label = ttk.Label(option_frame, text='Save frequency: ', width=20)
            save_label.grid(row=1, column=0, sticky='w')
            save_option_list = ('5 minutes', '15 minutes', '30 minutes', '60 minutes')
            save_option = tkinter.StringVar()
            save_option.set(save_option_list[0])
            save_option_menu = ttk.OptionMenu(option_frame, save_option, save_option_list[0], *save_option_list)
            save_option_menu.config(width=10)
            save_option_menu.grid(row=1, column=1, sticky='ew')


if __name__ == '__main__':
    rPi = sensorGlobal.TempClass()
    mainWindow = tkinter.Tk()
    MainGUI(mainWindow, rPi).start_gui()
