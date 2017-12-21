import tkinter
from tkinter import ttk
import sensorGlobal


class MainWindow:
    GREYCOLOUR = '#c1c1c1'

    def __init__(self, data_handler):
        self.dataHandler = data_handler
        self.advancedWindow = None
        self.mainWindow = tkinter.Tk()
        self.mainWindow.title('Sensor Reading')
        self.mainWindow.geometry('-8-200')
        self.mainWindow.minsize(width=500, height=200)
        self.mainWindow.columnconfigure(0, weight=1)
        self.mainWindow.rowconfigure(0, weight=1)
        self.main_window_frame = ttk.Frame(self.mainWindow)

        # Store the information here as need tkinter package TODO alternative or add tkinter to other package?
        self.count = []
        for i in range(15):
            _temp = tkinter.IntVar()
            self.count.append(_temp)

        self.draw_main_window()

    def draw_main_window(self):
        def readings_row_setup(parent, row):
            row_frame = ttk.Frame(parent)
            row_frame.grid(row=row, column=0, sticky='nsew')
            row_frame.columnconfigure(0, weight=1, uniform='equalColumn')
            row_frame.columnconfigure(1, weight=1, uniform='equalColumn')
            row_frame.columnconfigure(2, weight=1, uniform='equalColumn')
            row_frame.columnconfigure(3, weight=1, uniform='equalColumn')
            row_frame.columnconfigure(4, weight=1, uniform='equalColumn')
            row_frame.rowconfigure(0, weight=1, minsize=50)

            _keys = self.dataHandler.get_keys()
            for index in range(5):
                temp_frame = ttk.Frame(row_frame, relief=tkinter.RIDGE, borderwidth=2)
                temp_frame.grid(row=0, column=index, sticky='nsew')
                loc = index + row*5
                if loc < len(_keys):
                    name_label = ttk.Label(temp_frame, text=_keys[loc])
                    name_label.pack()
                    value_label = ttk.Label(temp_frame, textvariable=self.count[loc])
                    value_label.pack()

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
        quit_button = ttk.Button(button_frame, text='Quit', command=self.mainWindow.quit)
        quit_button.pack(side=tkinter.LEFT)

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
            self.draw_main_window()

        def delete_item():
            for item in tree_view.selection():
                tree_view.delete(item)

        # Launch window to add new item to Treeview (Add new sensor)
        def launch_add_window():
            def quit_add_window():
                new_item_window.destroy()
                advanced_window_frame.grab_set()

            def add_item():
                tree_view.insert('', tkinter.END, values=(name_entry.get(), pin_entry.get()))
                quit_add_window()

            new_item_window = tkinter.Toplevel(self.advancedWindow)
            new_item_window.title('New Item')
            new_item_window.geometry('-8-200')
            new_item_window.columnconfigure(0, weight=1)
            new_item_window.rowconfigure(0, weight=1)
            newitem_window_frame = ttk.Frame(new_item_window)
            newitem_window_frame.grid(sticky='nsew')
            newitem_window_frame.rowconfigure(0, weight=1)
            newitem_window_frame.rowconfigure(1, weight=1)
            newitem_window_frame.columnconfigure(0, weight=1)

            entry_frame = ttk.Frame(newitem_window_frame)
            entry_frame.grid(row=0, sticky='nsew', padx=5, pady=5)
            entry_frame.rowconfigure(0, weight=1)
            entry_frame.columnconfigure(0, weight=5)
            entry_frame.columnconfigure(1, weight=1)
            name_entry = ttk.Entry(entry_frame, width=30)
            name_entry.grid(row=0, column=0, sticky='nsew', pady=5)
            pin_entry = ttk.Entry(entry_frame, width=2, justify=tkinter.RIGHT)
            pin_entry.grid(row=0, column=1, sticky='nsew', pady=5)

            button_frame = ttk.Frame(newitem_window_frame)
            button_frame.grid(row=1)
            _add_button = ttk.Button(button_frame, text='Add', command=add_item)
            _add_button.pack(side=tkinter.LEFT)
            _cancel_button = ttk.Button(button_frame, text='Cancel', command=quit_add_window)
            _cancel_button.pack(side=tkinter.LEFT)

            new_item_window.grab_set()

        def save_configuration():
            _temp_dict = {}
            for iid in tree_view.get_children():
                name, pin = tree_view.item(iid)['values']
                _temp_dict[name] = pin
            self.dataHandler.sensorArray.clear()
            self.dataHandler.sensorArray.update(_temp_dict)
            self.dataHandler.save_data()
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
        bottom_button_frame.grid(row=1, column=1, padx=5, pady=5)
        save_button = ttk.Button(bottom_button_frame, text='Save', command=save_configuration)  # TODO add command
        save_button.pack(side=tkinter.LEFT)
        cancel_button = ttk.Button(bottom_button_frame, text='Cancel', command=self.advancedWindow.destroy)
        cancel_button.pack(side=tkinter.LEFT)

        # Treeview
        treeview_frame = ttk.Frame(advanced_window_frame)
        treeview_frame.grid(row=0, column=0, rowspan=2, sticky='nsew', padx=5, pady=5)
        treeview_frame.rowconfigure(0, weight=1)
        treeview_frame.columnconfigure(0, weight=10)
        treeview_frame.columnconfigure(1, weight=0)
        tree_view = ttk.Treeview(treeview_frame)
        tree_view.grid(row=0, column=0, sticky='nsew')
        tree_view['show'] = 'headings'
        tree_view['column'] = ('name', 'pin')
        tree_view.heading('name', text='Name')
        tree_view.heading('pin', text='Pin')
        tree_view.column('pin', width=100, anchor=tkinter.E)

        # Populate Treeview
        for key, value in self.dataHandler.sensorArray.items():
            tree_view.insert('', tkinter.END, values=(key, value))

        # Scroll for Treeview
        treeview_vscroll = ttk.Scrollbar(treeview_frame, orient='vertical', command=tree_view.yview)
        treeview_vscroll.grid(row=0, column=1, sticky='nsw')
        tree_view.configure(yscrollcommand=treeview_vscroll.set)

        # Add & Delete buttons TODO add an edit button?
        top_button_frame = ttk.Frame(advanced_window_frame)
        top_button_frame.grid(row=0, column=1, padx=5, pady=5)
        add_button = ttk.Button(top_button_frame, text='Add', command=launch_add_window)
        add_button.pack()
        delete_button = ttk.Button(top_button_frame, text='Delete', command=delete_item)
        delete_button.pack()

        self.advancedWindow.grab_set()


if __name__ == '__main__':
    dataHandler = sensorGlobal.DataHandler()
    MainWindow(dataHandler).start_gui()
