import zmq
import json
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import apscheduler.schedulers.background
import threading


class MainApplication(tk.Frame):

    def __init__(self, master, filename='portSetting.json'):
        self.master = master
        tk.Frame.__init__(self, self.master)
        self.configure_gui()
        self.create_widgets()
        self.job = None
        self.filename = filename
        self.ports = []
        self.pack(fill='both', expand=True)

    def requester_routine(self):

        with open(self.filename, 'r') as infile:
            machines_port = json.load(infile)

        try:
            machines, self.ports = map(list, zip(*machines_port))
        except ValueError:
            messagebox.showerror("Error", "None available")
            return

        self.context = zmq.Context()
        print("Connecting to machine...")
        self.requester = self.context.socket(zmq.DEALER)
        self.requester.setsockopt(zmq.LINGER, 0)
        for port in self.ports:
            self.requester.connect("tcp://%s" % port)
            print("Successfully connected to machine %s" % port)

        for request in range(len(self.ports)):
            print("Sending request ", request, "...")
            self.requester.send_string("", zmq.SNDMORE)
            self.requester.send_string("Sensor Data")

            # use poll for timeouts:
            poller = zmq.Poller()
            poller.register(self.requester, zmq.POLLIN)

            socks = dict(poller.poll(5 * 1000))

            if self.requester in socks:
                try:
                    self.requester.recv()
                    msg_json = self.requester.recv()
                    print(msg_json)
                    sens = json.loads(msg_json)
                    #response = "Sensor: %s :: Data: %s :: Client: %s" % (sens['sensor'], sens['data'], sens['client'])
                    #print("Received reply ", request, "[", response, "]")

                    """for timestamp, values in sens.items():
                        for uniqID, count in values.items():
                            response = "Time: %s :: Data: %s :: Client: %s :: Sensor: %s" % (uniqID, count, port, timestamp)
                            print("Received reply ", request, "[", response, "]")"""
                except IOError:
                    print("Could not connect to machine")

            else:
                print("Machine did not respond")
                self.popup = tk.Toplevel(self.master)
                self.popup.title("Error")
                # error label
                self.error_label = ttk.Label(self.popup, text="Machine did not respond %s" % port)
                self.error_label.grid(row=0)
                # OK button
                self.ok_button = ttk.Button(self.popup, text="Okay", command=self.popup.destroy)
                self.ok_button.grid(row=1, pady=10)

    def req_timer(self, option):

        minutes_map = {
            "15 minutes": "*/15",
            "10 minutes": "*/10",
            "5 minutes": "*/5",
            "-": None,
        }

        scheduler = apscheduler.schedulers.background.BackgroundScheduler()

        if self.job is not None:
            self.job.remove()
            self.job = None
        minutes = minutes_map.get(option, None)

        if minutes is not None:
            self.job = scheduler.add_job(self.requester_routine, 'cron', minute=minutes, id='option_timer')
            scheduler.start()

    def subscriber_routine(self):
        self.publisher = "127.0.0.1:56789"

        # Socket to talk to server
        self.context = zmq.Context()
        self.subscriber = self.context.socket(zmq.SUB)
        self.subscriber.setsockopt_string(zmq.SUBSCRIBE, "Server")

        print("Connecting to machine...")
        self.subscriber.bind("tcp://%s" % self.publisher)
        print("Successfully connected to machine %s" % self.publisher)

        while True:
            # wait for messages from publishers
            print("Waiting for progression updates...")
            rev_msg = str(self.subscriber.recv(), "utf-8")
            #received_json = json.loads(rev_msg)
            print("Received message: %s" % rev_msg)

    def run_thread(self):
        subscriber_thread = threading.Thread(target=self.subscriber_routine)
        subscriber_thread.start()

    def graceful_exit(self):
        try:
            self.subscriber.setsockopt(zmq.LINGER, 0)
            self.subscriber.close()
            self.context.term()
            self.master.destroy()
        except AttributeError:
            self.master.destroy()

    def port_settings(self):
        self.portSettings = tk.Toplevel(self.master)
        try:
            self.main_app = PortSettings(self.portSettings)
        except FileNotFoundError:
            pass

    def configure_gui(self):
        # set the gui window title
        self.master.title("TEST SERVER")

    def create_widgets(self):
        # button to request data
        self.request_button = ttk.Button(self, text="Request", command=self.requester_routine)
        self.request_button.grid(row=0, column=2, rowspan=2, sticky=tk.EW)

        # button to run subscriber
        self.subscriber_button = ttk.Button(self, text="Subscribe", command=self.run_thread)
        self.subscriber_button.grid(row=0, column=3, rowspan=2, sticky=tk.EW)

        # button for port settings
        self.setting_button = ttk.Button(self, text="Settings", command=self.port_settings)
        self.setting_button.grid(row=0, column=1, rowspan=2, sticky=tk.EW)
        # button to exit
        self.exit_button = ttk.Button(self, text="Exit", command=self.graceful_exit)
        self.exit_button.grid(row=0, column=4, rowspan=2, sticky=tk.EW)

        """
        # timer label
        self.timer_label = ttk.Label(self, text="Timer Settings")
        self.timer_label.grid(row=0, column=0, padx=10, pady=3, sticky=tk.NSEW)

        # create tk variable
        self.timervar = tk.StringVar(self)

        # dropdown dictionary
        self.timerDict = {"-", "5 minutes", "10 minutes", "15 minutes"}

        # timer dropdown menu
        self.timer_option = ttk.OptionMenu(self, self.timervar, "-", *self.timerDict, command=self.req_timer)
        self.timer_option.grid(row=1, column=0, padx=3, pady=3, sticky=tk.NSEW)
        """
        
        # scroll bar for the terminal outputs
        self.terminal_scrollbar = ttk.Scrollbar(self)
        self.terminal_scrollbar.grid(row=2, column=5, sticky=tk.NS)

        # terminal listbox output. Auto scrolls to the bottom but also has the scroll bar incase you want to go back up
        '''self.terminal_listbox = tk.Listbox(root, yscrollcommand=self.terminal_scrollbar.set, width=100, height=13)
        self.terminal_listbox.grid(row=2, column=0, columnspan=5, sticky=tk.NSEW)
        self.terminal_listbox.see(tk.END)
        self.terminal_scrollbar.config(command=self.terminal_listbox.yview)'''

        # terminal treeview output
        self.terminal_tree = ttk.Treeview(self)
        self.terminal_tree.grid(row=2, column=0, columnspan=5, sticky=tk.NSEW)
        self.terminal_tree.configure(yscrollcommand=self.terminal_scrollbar.set)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(2, weight=1)
        self.terminal_tree["columns"] = ("1", "2", "3", "4")
        self.terminal_tree['show'] = 'headings'
        self.terminal_tree.column("1", width=200, anchor='c')
        self.terminal_tree.column("2", width=100, anchor='c')
        self.terminal_tree.column("3", width=200, anchor='c')
        self.terminal_tree.column("4", width=100, anchor='c')
        self.terminal_tree.heading("1", text="Timestamp")
        self.terminal_tree.heading("2", text="Data")
        self.terminal_tree.heading("3", text="Client")
        self.terminal_tree.heading("4", text="Sensor")


class PortSettings(tk.Frame):
    def __init__(self, master, filename='portSetting.json'):
        super(PortSettings, self).__init__()
        self.master = master
        self.settingTab()
        self.configure_gui()
        self.create_portWidgets()
        self.create_userWidgets()
        self.tabControl.pack(fill='both', expand=True)
        self.filename = filename
        self.machine_ports = []
        self.populate_treeview()

    def settingTab(self):
        self.tabControl = ttk.Notebook(self.master)
        self.portTab1 = ttk.Frame(self.tabControl)
        self.tabControl.add(self.portTab1, text="Port Settings")
        self.userTab2 = ttk.Frame(self.tabControl)
        self.tabControl.add(self.userTab2, text="User Settings")
        self.extraTab3 = ttk.Frame(self.tabControl)
        self.tabControl.add(self.extraTab3, text="Extra Settings")

    def close_settings(self):
        self.master.destroy()

    def configure_gui(self):
        # set the gui window title
        self.master.title("Settings")

    def addPort_window(self):
        self.add_window = tk.Toplevel(self.master)
        self.add_window.title("Add Port")

        # add label
        self.addMachine_label = ttk.Label(self.add_window, text="Machine: ")
        self.addMachine_label.grid(row=0, column=0)

        self.addPort_label = ttk.Label(self.add_window, text="Port: ")
        self.addPort_label.grid(row=1, column=0)

        # add entry
        self.addMachine_entry = ttk.Entry(self.add_window, text="Machine")
        self.addMachine_entry.grid(row=0, column=1)

        self.addPort_entry = ttk.Entry(self.add_window, text="Port")
        self.addPort_entry.grid(row=1, column=1)

        # add button
        self.addMachine_button = ttk.Button(self.add_window, text="Insert", command=self.add_port)
        self.addMachine_button.grid(row=3, column=1)

    def editPort_window(self):
        editable_port = self.terminal_tree.selection()[0]
        for child in self.terminal_tree.get_children():
            if child == editable_port:
                values = self.terminal_tree.item(child)["values"]
                break

        self.edit_window = tk.Toplevel(self.master)
        self.edit_window.title("Edit Port")

        # edit label
        editMachine_label = ttk.Label(self.edit_window, text="Machine: ")
        editMachine_label.grid(row=0, column=0)

        editPort_label = ttk.Label(self.edit_window, text="Port: ")
        editPort_label.grid(row=1, column=0)

        # edit entry
        editMachine_entry = ttk.Entry(self.edit_window)
        editMachine_entry.insert(0, values[0])  # <-- Default is entry's current value
        editMachine_entry.grid(row=0, column=1)

        editPort_entry = ttk.Entry(self.edit_window)
        editPort_entry.insert(0, values[1])
        editPort_entry.grid(row=1, column=1)

        def update_destroy():
            if self.edit_port(self.terminal_tree, editMachine_entry.get(), editPort_entry.get()):
                self.edit_window.destroy()

        edit_Button = ttk.Button(self.edit_window, text="Edit", command=lambda: update_destroy())
        edit_Button.grid(row=2, columnspan=2)

    def edit_port(self, terminal_tree, machine, port):
        # grab the current index in the tree
        currInd = self.terminal_tree.index(self.terminal_tree.focus())
        # remove from treeview
        self.delete_current(self.terminal_tree)
        # insert it back in with the upated values
        self.terminal_tree.insert('', currInd, values=(machine, port))

        return True

    def add_port(self):
        self.terminal_tree.insert('', tk.END, values=(self.addMachine_entry.get(), self.addPort_entry.get()))
        self.addMachine_entry.delete(0, tk.END)
        self.addPort_entry.delete(0, tk.END)

    def save_settings(self, item=""):
        self.machine_ports = []

        for child in self.terminal_tree.get_children():
            print(self.terminal_tree.item(child)["values"])

            self.machine_ports.append(self.terminal_tree.item(child)["values"])
            print(self.machine_ports)

        with open(self.filename, 'w+') as outfile:
            json.dump(self.machine_ports, outfile)

        return self.machine_ports

    def delete_port(self):
        selected_port = self.terminal_tree.selection()[0]  # <-- get selected item
        self.terminal_tree.delete(selected_port)

    def delete_current(self, terminal_tree):
        curr = self.terminal_tree.focus()

        self.terminal_tree.delete(curr)

    def create_portWidgets(self):
        # scroll bar for the terminal outputs
        self.terminal_scrollbar = ttk.Scrollbar(self)
        self.terminal_scrollbar.grid(row=0, column=4, sticky=tk.NS)

        # terminal treeview output
        self.terminal_tree = ttk.Treeview(self.portTab1)
        self.terminal_tree.grid(row=0, column=0, columnspan=5, sticky=tk.NSEW)
        self.terminal_tree.configure(yscrollcommand=self.terminal_scrollbar.set)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(0, weight=1)
        self.terminal_tree["columns"] = ("1", "2")
        self.terminal_tree['show'] = 'headings'
        self.terminal_tree.column("1", width=100, anchor='c')
        self.terminal_tree.column("2", width=100, anchor='c')
        self.terminal_tree.heading("1", text="Machine")
        self.terminal_tree.heading("2", text="Port")

        self.add_button = ttk.Button(self.portTab1, text="Add", command=self.addPort_window)
        self.add_button.grid(row=1, column=0)

        self.remove_button = ttk.Button(self.portTab1, text="Remove", command=self.delete_port)
        self.remove_button.grid(row=1, column=1)

        self.edit_button = ttk.Button(self.portTab1, text="Edit", command=self.editPort_window)
        self.edit_button.grid(row=1, column=2)

        self.save_button = ttk.Button(self.portTab1, text="Save", command=self.save_settings)
        self.save_button.grid(row=1, column=3)

        self.exit_button = ttk.Button(self.portTab1, text="Exit", command=self.close_settings)
        self.exit_button.grid(row=1, column=4)

    def create_userWidgets(self):
        self.employee_button = ttk.Button(self.userTab2, text="Employee", command=self.addEmp_window)
        self.employee_button.grid(row=1, column=2)

        self.qc_button = ttk.Button(self.userTab2, text="QC")
        self.qc_button.grid(row=1, column=3)

    def addEmp_window(self):
        self.add_window = tk.Toplevel(self.master)
        self.add_window.title("Employee")

        # employee label
        self.addEmp_label = ttk.Label(self.userTab2, text="Employees")
        self.addEmp_label.grid(row=0, column=1)

        # terminal treeview output
        self.terminal_tree = ttk.Treeview(self.add_window)
        self.terminal_tree.grid(row=0, column=0, columnspan=5, sticky=tk.NSEW)
        self.terminal_tree.configure(yscrollcommand=self.terminal_scrollbar.set)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(0, weight=1)
        self.terminal_tree["columns"] = ("1", "2")
        self.terminal_tree['show'] = 'headings'
        self.terminal_tree.column("1", width=100, anchor='c')
        self.terminal_tree.column("2", width=100, anchor='c')
        self.terminal_tree.heading("1", text="ID")
        self.terminal_tree.heading("2", text="Name")

    def populate_treeview(self):
        with open(self.filename, 'r') as infile:
            self.machine_ports = json.load(infile)

        for items in self.machine_ports:
            self.terminal_tree.insert('', tk.END, values=items)


if __name__ == '__main__':
    root = tk.Tk()
    main_app = MainApplication(root)
    root.mainloop()