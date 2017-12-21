import tkinter
from tkinter import ttk
import sensorGlobal


class MainWindow:
    GREYCOLOUR = '#c1c1c1'

    def __init__(self):
        def readings_row_setup(parent, row, name_array=()):
            row_frame = ttk.Frame(parent)
            row_frame.grid(row=row, column=0, sticky='nsew')
            row_frame.columnconfigure(0, weight=1, uniform='equalColumn')
            row_frame.columnconfigure(1, weight=1, uniform='equalColumn')
            row_frame.columnconfigure(2, weight=1, uniform='equalColumn')
            row_frame.columnconfigure(3, weight=1, uniform='equalColumn')
            row_frame.columnconfigure(4, weight=1, uniform='equalColumn')
            row_frame.rowconfigure(0, weight=1, minsize=50)

            for index in range(5):
                temp_frame = ttk.Frame(row_frame, relief=tkinter.RIDGE, borderwidth=2)
                temp_frame.grid(row=0, column=index, sticky='nsew')
                if index < len(name_array):
                    name_label = ttk.Label(temp_frame, text=name_array[index])
                    name_label.pack()
                    value_label = ttk.Label(temp_frame, textvariable=count[(row*5+index)])
                    value_label.pack()

        self.advancedWindow = None
        self.mainWindow = tkinter.Tk()
        self.mainWindow.title('Sensor Reading')
        self.mainWindow.geometry('-8-200')
        self.mainWindow.minsize(width=500, height=200)
        self.mainWindow.columnconfigure(0, weight=1)
        self.mainWindow.rowconfigure(0, weight=1)
        main_window_frame = ttk.Frame(self.mainWindow)
        main_window_frame.grid(sticky='nsew')
        main_window_frame.grid_columnconfigure(0, weight=1, minsize=500)
        main_window_frame.grid_rowconfigure(0, weight=10, minsize=150)
        main_window_frame.grid_rowconfigure(1, weight=1)

        style = ttk.Style()
        style.map('TEntry', background=[('disabled', self.GREYCOLOUR)])

        button_frame = ttk.Frame(main_window_frame)
        button_frame.grid(row=1, column=0, padx=5, pady=5)
        advanced_button = ttk.Button(button_frame, text='Advanced', command=self.launch_advanced_window)
        advanced_button.pack(side=tkinter.LEFT)
        quit_button = ttk.Button(button_frame, text='Quit', command=self.mainWindow.quit)
        quit_button.pack(side=tkinter.LEFT)

        readings_frame = ttk.Frame(main_window_frame)
        readings_frame.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        readings_frame.rowconfigure(0, weight=1)
        readings_frame.rowconfigure(1, weight=1)
        readings_frame.rowconfigure(2, weight=1)
        readings_frame.columnconfigure(0, weight=1)

        # Store the information here as need tkinter package TODO alternative or add tkinter to other package?
        count = []
        for i in range(15):
            _temp = tkinter.IntVar()
            count.append(_temp)

        readings_row_setup(readings_frame, 0, sensorGlobal.sensorNameArray[0:5])
        readings_row_setup(readings_frame, 1, sensorGlobal.sensorNameArray[5:10])
        readings_row_setup(readings_frame, 2, sensorGlobal.sensorNameArray[10:15])

        self.mainWindow.mainloop()

    # Advanced Window Setup and Launch
    def launch_advanced_window(self):
        def delete_item():
            for item in tree_view.selection():
                tree_view.delete(item)

        # Launch window to add new item to Treeview
        def launch_add_window():
            def add_item():
                tree_view.insert('', tkinter.END, values=(name_entry.get(),pin_entry.get()))
                new_item_window.destroy()

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
            _cancel_button = ttk.Button(button_frame, text='Cancel', command=new_item_window.destroy)
            _cancel_button.pack(side=tkinter.LEFT)

            new_item_window.grab_set()

        def save_configuration():

            print('-' * 50)

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
        for key, value in sensorGlobal.sensorsArray.items():
            tree_view.insert('', tkinter.END, values=(key,value))
        tree_view.focus(tree_view.get_children()[0])
        tree_view.selection_set(tree_view.get_children()[0])

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
    MainWindow()
