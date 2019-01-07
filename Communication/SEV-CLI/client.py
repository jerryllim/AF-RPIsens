import zmq
import tkinter as tk
from tkinter import ttk
import time
import random
import json
import threading

class MainApplication(tk.Frame):

	def __init__(self, master):
		self.master = master
		tk.Frame.__init__(self, self.master)
		self.configure_gui()
		self.create_widgets()
		self.port_number = '9999'
		self.pack(fill='both', expand=True)

	def respondent_routine(self):
		self.context = zmq.Context()
		self.respondent = self.context.socket(zmq.REP)
		self.respondent.setsockopt(zmq.LINGER, 0)
		self.respondent.bind("tcp://*:%s" % self.port_number)
		print("Successfully binded to port %s for respondent" % self.port_number)

		while True:
			#  Wait for next request from client
			_message = str(self.respondent.recv(), "utf-8")
			print('Received request ({})'.format(_message))
			time.sleep(1)
			msgDict = {
				'sensor': "6",
				'data': "123456789",
				'client': "9876",
			}
			msg_json = json.dumps(msgDict)
			self.respondent.send_string(msg_json)

	def publisher_routine(self):
		self.context = zmq.Context()
		self.subscriber = "127.0.0.1:56789"

		# publish
		self.publisher = self.context.socket(zmq.PUB)
		self.publisher.connect("tcp://%s" % self.subscriber)
		print("Successfully connected to server %s for subscriber" % self.subscriber)

		"""data = input("Type a message to publish\n") # user input
		topic = "Server"
		messagedata = random.randrange(1,215) - 80 # random messagedata
		print("%s %d %s" % (topic, messagedata, data))
		self.publisher.send_string("%s %d %s" % (topic, messagedata, data))
		time.sleep(1)"""

		data_content = self.retrieve_output()
		print(data_content)
		try:
			content_json = json.dumps(data_content)
			self.publisher.send_string(content_json)
		except:
			print("Unable to send")
			return

	def run_thread(self):
		respondent_thread = threading.Thread(target=self.respondent_routine)
		respondent_thread.start()

	# retrieve data from treeview
	def retrieve_output(self):
		treeview_content = []
		try:
			for child in self.terminal_tree.get_children():
				print(self.terminal_tree.item(child)["values"])
				treeview_content.append(self.terminal_tree.item(child)["values"])
				print(treeview_content)

		except:
			return

	def insert_data_window(self):
		self.insertData = tk.Toplevel(self.master)
		self.insertData.title("Insert Data")

		# add Timestamp
		self.addTimestamp_label = ttk.Label(self.insertData, text="Timestamp: ")
		self.addTimestamp_label.grid(row=0, column=0)

		self.addTimestamp_entry = ttk.Entry(self.insertData, text="Timestamp")
		self.addTimestamp_entry.grid(row=0, column=1)

		# add Data
		self.addData_label = ttk.Label(self.insertData, text="Data: ")
		self.addData_label.grid(row=1, column=0)

		self.addData_entry = ttk.Entry(self.insertData, text="Data")
		self.addData_entry.grid(row=1, column=1)

		# add Client
		self.addClient_label = ttk.Label(self.insertData, text="Client: ")
		self.addClient_label.grid(row=2, column=0)

		self.addClient_entry = ttk.Entry(self.insertData, text="Client")
		self.addClient_entry.grid(row=2, column=1)

		# add Sensor
		self.addSensor_label = ttk.Label(self.insertData, text="Sensor: ")
		self.addSensor_label.grid(row=3, column=0)

		self.addSensor_entry = ttk.Entry(self.insertData, text="Sensor")
		self.addSensor_entry.grid(row=3, column=1)

		# insert Button
		self.insertData_button = ttk.Button(self.insertData, text="Insert", command=self.add_data)
		self.insertData_button.grid(row=4, column=1)


	def graceful_exit(self):
		try:
			self.respondent.setsockopt(zmq.LINGER, 0)
			self.respondent.close()
			self.context.term()
			self.master.destroy()
		except AttributeError:
			self.master.destroy()

	def configure_gui(self):
		# set the gui window title
		self.master.title("CLIENT TEST")

	def create_widgets(self):
		# button to add data
		self.setting_button = ttk.Button(self, text="Add", command=self.insert_data_window)
		self.setting_button.grid(row=0, column=1, rowspan=2, sticky=tk.EW)
		# rep data
		self.repData_button = ttk.Button(self, text="Reply", command=self.run_thread)
		self.repData_button.grid(row=0, column=2, rowspan=2, sticky=tk.EW)

		# publish
		self.publish_button = ttk.Button(self, text="Publish", command=self.publisher_routine)
		self.publish_button.grid(row=0, column=3, rowspan=2, sticky=tk.EW)

		# button to exit
		self.exit_button = ttk.Button(self, text="Exit", command=self.graceful_exit)
		self.exit_button.grid(row=0, column=4, rowspan=2, sticky=tk.EW)

		# scroll bar for the terminal outputs
		self.terminal_scrollbar = ttk.Scrollbar(self)
		self.terminal_scrollbar.grid(row=2, column=5, sticky=tk.NS)

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

	def add_data(self):
		self.terminal_tree.insert('', tk.END, values=(self.addTimestamp_entry.get(), self.addData_entry.get(), self.addClient_entry.get(), self.addSensor_entry.get()))
		self.addTimestamp_entry.delete(0, tk.END)
		self.addData_entry.delete(0, tk.END)
		self.addClient_entry.delete(0, tk.END)
		self.addSensor_entry.delete(0, tk.END)

if __name__ == '__main__':
	root = tk.Tk()
	main_app = MainApplication(root)
	root.mainloop()
