import zmq
import time
import json
from datetime import datetime
import tkinter as tk
from tkinter import ttk
import apscheduler.schedulers.background

class MainApplication(tk.Frame):

    def __init__(self, master):
        self.master = master
        tk.Frame.__init__(self, self.master)
        self.configure_gui()
        self.create_widgets()
        self.job = None

    def req_client(self):

        ports = ["9998", "9999"]

        context = zmq.Context()
        print("Connecting to port...")
        socket = context.socket(zmq.REQ)
        for port in ports:
            socket.connect("tcp://localhost:%s" % port)
            print("Successfully connected to port %s" % port)

        for request in range(1, 3):
            print("Sending request ", request, "...")
            socket.send_string("Sensor Data")
            #  Get the reply.
            msg_json = socket.recv()
            ds = json.loads(msg_json)
            response = "Sensor: %s :: Data: %s :: Client: %s" % (ds['sensor'], ds['data'], ds['client'])
            print("Received reply ", request, "[", response, "]")

            # open the file for writing and creates it, if it doesn't exist
            f = open("sensorDataLog.txt", "a+")

            # write the data into the file
            f.write("Requested on %s. \n %s \n" % (datetime.now(), response))

            # close the file when done
            f.close()

            # label['text'] = response # <-- update label
            terminal = self.terminal_listbox
            terminal.insert(tk.END, str(response))
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
            self.job = scheduler.add_job(self.req_client, 'cron', second=minutes, id='option_timer')
            scheduler.start()

    def configure_gui(self):
        # set the gui window title
        self.master.title("Server")

    def create_widgets(self):
        # button to request data
        self.request_button = tk.Button(root, text="Request", command=self.req_client)
        self.request_button.grid(row=0, column=0, rowspan=2, columnspan=3)

        # timer label
        self.timer_label = tk.Label(root, text="Timer Settings")
        self.timer_label.grid(row=0, column=3, columnspan=2, pady=3)

        # create tk variable
        self.timervar = tk.StringVar(root)

        # dropdown dictionary
        self.timerDict = {"-", "5 minutes", "10 minutes", "15 minutes"}
        self.timervar.set("-")  # <-- set the default value

        # timer dropdown menu
        self.timer_option = tk.OptionMenu(root, self.timervar, *self.timerDict, command=self.req_timer)
        self.timer_option.grid(row=1, column=3, columnspan=2, padx=3, pady=3)

        # scroll bar for the terminal outputs
        self.terminal_scrollbar = tk.Scrollbar(root)
        self.terminal_scrollbar.grid(row=2, column=5, sticky=tk.NS)

        # Terminal output. Auto scrolls to the bottom but also has the scroll bar incase you want to go back up
        '''self.terminal_listbox = tk.Listbox(root, yscrollcommand=self.terminal_scrollbar.set, width=100, height=13)
        self.terminal_listbox.grid(row=2, column=0, columnspan=5, sticky=tk.NSEW)
        self.terminal_listbox.see(tk.END)
        self.terminal_scrollbar.config(command=self.terminal_listbox.yview)'''

        self.terminal_tree = ttk.Treeview(root)
        self.terminal_tree.grid(row=2, column=0, columnspan=5, sticky=tk.NSEW)
        self.terminal_tree.configure(yscrollcommand=self.terminal_scrollbar.set)
        self.terminal_tree["columns"] = ("1", "2", "3")
        self.terminal_tree['show'] = 'headings'
        self.terminal_tree.column("1", width=100, anchor='c')
        self.terminal_tree.column("2", width=100, anchor='c')
        self.terminal_tree.column("3", width=100, anchor='c')
        self.terminal_tree.heading("1", text="Sensor")
        self.terminal_tree.heading("2", text="Data")
        self.terminal_tree.heading("3", text="Client")

       # for i in range 


        # LabelRep = Label(root)
        # LabelRep.pack(pady=10, padx=10)

if __name__ == '__main__':
    root = tk.Tk()
    main_app = MainApplication(root)
    root.mainloop()