import zmq
import json
import csv
import datetime
import tkinter as tk
from tkinter import ttk
from queue import Queue
import apscheduler.schedulers.background


class MainApplication(tk.Frame):

    def __init__(self, master):
        self.master = master
        tk.Frame.__init__(self, self.master)
        self.configure_gui()
        self.create_widgets()
        self.job = None
        self.pack(fill='both', expand=True)

    def req_client(self):

        self.ports = ["9999"]

        self.context = zmq.Context()
        print("Connecting to port...")
        self.socket = self.context.socket(zmq.REQ)
        self.socket.setsockopt(zmq.LINGER, 0)
        for port in self.ports:
            self.socket.bind("tcp://*:%s" % port)
            print("Successfully connected to port %s" % port)

        for request in range(len(self.ports)):
            print("Sending request ", request, "...")
            # use poll for timeouts:
            poller = zmq.Poller()
            poller.register(self.socket, zmq.POLLOUT)
            if poller.poll(10 * 1000):  # 10s timeout in milliseconds
                self.socket.send_string("Sensor Data")
            else:
                self.popup = tk.Toplevel(self.master)
                self.popup.title("Error")

                # error label
                self.error_label = ttk.Label(self.popup, text="Server was not able to detect port %s" % port)
                self.error_label.grid(row=0)

                # OK button
                self.ok_button = ttk.Button(self.popup, text="Okay", command=self.popup.destroy)
                self.ok_button.grid(row=1)
                raise IOError("Timeout processing auth request")

            # use poll for timeouts:
            poller.register(self.socket, zmq.POLLIN)
            if poller.poll(30 * 1000):  # 30s timeout in milliseconds
                # Get the reply.
                msg_json = self.socket.recv()
                sens = json.loads(msg_json)
            else:
                raise IOError("Timeout processing auth request")

            # sens_data = sens['machine_details']
            '''
            for timestamp, values in sens.items():
                for uniqID, count in values.items():
                    response = "Sensor: %s :: Data: %s :: Client: %s" % (uniqID, count, port, timestamp)
                    print("Received reply ", request, "[", response, "]")'''

            currentDT = datetime.datetime.now()

            # open the file for writing and creates it, if it doesn't exist
            f = open("sensorDataLog.txt", "a+")

            # write the data into the file
            f.write("Requested on %s. \n %s \n" % (currentDT, sens))

            # close the file when done
            f.close()

            '''
            # open the file for writing and creates it if it doesn't exist
            sensor_data = open("sensorData.cs", "a+")

            # create the csv writer object
            csvwriter = csv.writer(sensor_data)

            count = 0

            for sen in sens_data:

                  if count == 0:

                         header = sen.keys()

                         csvwriter.writerow(header)

                         count += 1

                  csvwriter.writerow(sen.values())

            sensor_data.close()'''

            # label['text'] = response # <-- update label
            # terminal.insert(tk.END, str(response))

            terminal = self.terminal_tree

            for timestamp, values in sens.items():
                for uniqID, count in values.items():
                    terminal.insert('', tk.END, values=(uniqID, count, port, timestamp))
            print("Done")

                    #tree_view.insert('', tkinter.END, values=(_id, sensor, _count))
            #terminal.insert('', tk.END, values=(sens['sensor'], sens['data'], sens['client'], str(currentDT.strftime("%H:%M:%S"))))
            root.update()  # <-- run mainloop once

            # time.sleep(1)

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
            self.job = scheduler.add_job(self.req_client, 'cron', minute=minutes, id='option_timer')
            scheduler.start()

    def graceful_exit(self):
        try:
            self.socket.setsockopt(zmq.LINGER, 0)
            self.socket.close()
            self.context.term()
            self.master.destroy()
        except AttributeError:
            self.master.destroy()

    def port_settings(self):
        self.portSettings = tk.Toplevel(self.master)
        self.main_app = PortSettings(self.portSettings)

    def configure_gui(self):
        # set the gui window title
        self.master.title("Server")

    def create_widgets(self):
        # button to request data
        self.request_button = ttk.Button(self, text="Request", command=self.req_client)
        self.request_button.grid(row=0, column=2, rowspan=2)

        # button for port settings
        self.setting_button = ttk.Button(self, text="Settings", command=self.port_settings)
        self.setting_button.grid(row=0, column=1, rowspan=2)

        # button to exit
        self.exit_button = ttk.Button(self, text="Exit", command=self.graceful_exit)
        self.exit_button.grid(row=0, column=3, rowspan=2)

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
        self.terminal_tree.column("1", width=100, anchor='c')
        self.terminal_tree.column("2", width=100, anchor='c')
        self.terminal_tree.column("3", width=100, anchor='c')
        self.terminal_tree.column("4", width=100, anchor='c')
        self.terminal_tree.heading("1", text="Sensor")
        self.terminal_tree.heading("2", text="Data")
        self.terminal_tree.heading("3", text="Client")
        self.terminal_tree.heading("4", text="Timestamp")

        # LabelRep = Label(root)
        # LabelRep.pack(pady=10, padx=10)


class PortSettings(tk.Frame):
    def __init__(self, master):
        self.master = master
        tk.Frame.__init__(self, self.master)
        self.configure_gui()
        self.create_widgets()
        self.pack(fill='both', expand=True)

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

        # exit button
        '''
        self.exitAdd_button = ttk.Button(self.add_window, text="Cancel", command=self.add_window.destroy)
        self.exitAdd_button.grid(row=3, column=2)'''

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
        machine_ports = self.terminal_tree.get_children(item)
        for child in self.terminal_tree.get_children():
            print(self.terminal_tree.item(child)["values"])

    def delete_port(self):
        selected_port = self.terminal_tree.selection()[0]  # <-- get selected item
        self.terminal_tree.delete(selected_port)

    def delete_current(self, terminal_tree):
        curr = self.terminal_tree.focus()

        self.terminal_tree.delete(curr)

    def create_widgets(self):
        # scroll bar for the terminal outputs
        self.terminal_scrollbar = ttk.Scrollbar(self)
        self.terminal_scrollbar.grid(row=0, column=4, sticky=tk.NS)

        # terminal treeview output
        self.terminal_tree = ttk.Treeview(self)
        self.terminal_tree.grid(row=0, column=0, columnspan=5, sticky=tk.NSEW)
        self.terminal_tree.configure(yscrollcommand=self.terminal_scrollbar.set)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(2, weight=1)
        self.terminal_tree["columns"] = ("1", "2")
        self.terminal_tree['show'] = 'headings'
        self.terminal_tree.column("1", width=100, anchor='c')
        self.terminal_tree.column("2", width=100, anchor='c')
        self.terminal_tree.heading("1", text="Machine")
        self.terminal_tree.heading("2", text="Port")

        self.add_button = ttk.Button(self, text="Add", command=self.addPort_window)
        self.add_button.grid(row=1, column=0)

        self.remove_button = ttk.Button(self, text="Remove", command=self.delete_port)
        self.remove_button.grid(row=1, column=1)

        self.edit_button = ttk.Button(self, text="Edit", command=self.editPort_window)
        self.edit_button.grid(row=1, column=2)

        self.save_button = ttk.Button(self, text="Save", command=self.save_settings)
        self.save_button.grid(row=1, column=3)

        self.exit_button = ttk.Button(self, text="Exit", command=self.close_settings)
        self.exit_button.grid(row=1, column=4)


if __name__ == '__main__':
    root = tk.Tk()
    main_app = MainApplication(root)
    root.mainloop()
