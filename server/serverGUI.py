import os
import json
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

class Settings(ttk.Frame):
	def __init__(self, master):
		super(Settings, self).__init__()
		self.master = master
		self.tabControl = ttk.Notebook(self.master)
		self.master.title("Settings")
		# self.master.minsize(640, 600)
		self.add_tab()

	def add_tab(self):
		#tabControl = ttk.Notebook(seself)
		self.tab1 = Network(self.tabControl)
		self.tabControl.add(self.tab1, text="Network")
		self.tab2 = Extra(self.tabControl)
		self.tabControl.add(self.tab2, text="Extra")
		self.tab3 = Employee(self.tabControl)
		self.tabControl.add(self.tab3, text="Employee")

		self.tabControl.pack(expand=True, fill="both")

class Network(ttk.Frame):
	def __init__(self, master, filename='machineSetting.json'):
		ttk.Frame.__init__(self)
		self.filename = filename
		self.setting_dict = {}
		self.treeview_frame()
		self.button_frame()
		self.details_frame()
		self.populate_treeview()

	def treeview_frame(self):
		self.topFrame = ttk.Frame(self)
		self.topFrame.pack(side=tk.TOP, fill=tk.BOTH, anchor=tk.N)

		# scroll bar for the terminal outputs
		terminal_scrollbar = ttk.Scrollbar(self.topFrame)
		terminal_scrollbar.grid(row=0, column=5, sticky=tk.NS)

		# terminal treeview output
		self.terminal_tree = ttk.Treeview(self.topFrame)
		self.terminal_tree.grid(row=0, column=0, columnspan=5, sticky=tk.NSEW)
		self.terminal_tree.configure(yscrollcommand=terminal_scrollbar.set)
		self.topFrame.columnconfigure(2, weight=1)
		self.topFrame.rowconfigure(2, weight=1)
		self.terminal_tree["columns"] = ("1", "2", "3")
		self.terminal_tree['show'] = 'headings'
		self.terminal_tree.column("1", width=200, anchor='c')
		self.terminal_tree.column("2", width=200, anchor='c')
		self.terminal_tree.column("3", width=200, anchor='c')
		self.terminal_tree.heading("1", text="Machine")
		self.terminal_tree.heading("2", text="IP")
		self.terminal_tree.heading("3", text="Mac")

	def button_frame(self):
		self.midFrame = ttk.Frame(self)
		self.midFrame.pack(side=tk.TOP, fill=tk.BOTH, anchor=tk.N)
		# buttons
		add_button = ttk.Button(self.midFrame, text="Add", command=self.get_entry_dict)
		add_button.grid(row=0, column=0, padx=10, pady=5, sticky=tk.EW)

		edit_button = ttk.Button(self.midFrame, text="Edit")
		edit_button.grid(row=0, column=1, padx=10, pady=5, sticky=tk.EW)

		delete_button = ttk.Button(self.midFrame, text="Delete", command=self.delete_machine)
		delete_button.grid(row=0, column=2, padx=10, pady=5, sticky=tk.EW)

		save_button = ttk.Button(self.midFrame, text="Save", command=self.save_settings)
		save_button.grid(row=0, column=3, padx=10, pady=5, sticky=tk.EW)

		for rows in range(3):
			self.midFrame.columnconfigure(rows, weight=1)

	def details_frame(self):
		self.bottomFrame = ttk.Frame(self)
		self.bottomFrame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

		self.bottomFrame.columnconfigure(0, weight=1)
		self.bottomFrame.columnconfigure(1, weight=1)
		self.bottomFrame.columnconfigure(3, weight=1)
		self.bottomFrame.columnconfigure(4, weight=1)

		for rows in range(13):
			self.bottomFrame.rowconfigure(rows, weight=1)

		# terminal input label and entry
		Machine_label = ttk.Label(self.bottomFrame, text="Machine")
		Machine_label.grid(row=0, column=0, padx=(40,0), pady=5, sticky=tk.E)

		self.Machine_entry = ttk.Entry(self.bottomFrame, text="machine")
		self.Machine_entry.grid(row=0, column=1, padx=(0,50), pady=5, sticky=tk.W)

		IP_label = ttk.Label(self.bottomFrame, text="IP")
		IP_label.grid(row=0, column=3, pady=5, sticky=tk.E)

		self.IP_entry = ttk.Entry(self.bottomFrame, text="ip")
		self.IP_entry.grid(row=0, column=4, padx=(0,50), pady=5, sticky=tk.W)

		Mac_label = ttk.Label(self.bottomFrame, text="Mac")
		Mac_label.grid(row=1, column=0, pady=5, sticky=tk.E)

		self.Mac_entry = ttk.Entry(self.bottomFrame, text="mac")
		self.Mac_entry.grid(row=1, column=1, pady=5, sticky=tk.W)

		Separator = ttk.Separator(self.bottomFrame, orient='horizontal')
		Separator.grid(row=2, columnspan=5, pady=5, sticky=tk.EW)

		sensorOddList = ["S01", "S02", "S03", "S04", "SO5", "S06", "S07", "S08", "S09", "S10"]
		sensorEvenList = ["S11", "S12", "S13", "S14", "S15", "E01", "E02", "E03", "E04", "E05"]
		self.sensorEntry = []
		sensorLabel = []
		rowOdd = 3
		rowEven = 3

		for sensor in range(0, len(sensorOddList)):
			rowOdd = rowOdd + 1
			sensorLabel.append(ttk.Label(self.bottomFrame, text=sensorOddList[sensor]))
			self.sensorEntry.append(ttk.Entry(self.bottomFrame, text=sensorOddList[sensor]))
			sensorLabel[-1].grid(row=rowOdd, column=0, pady=5, sticky=tk.E)
			self.sensorEntry[-1].grid(row=rowOdd, column=1, pady=5, sticky=tk.W)

		for sensor in range(0, len(sensorEvenList)):
			rowEven = rowEven + 1
			sensorLabel.append(ttk.Label(self.bottomFrame, text=sensorEvenList[sensor]))
			self.sensorEntry.append(ttk.Entry(self.bottomFrame, text=sensorEvenList[sensor]))
			sensorLabel[-1].grid(row=rowEven, column=3, pady=5, sticky=tk.E)
			self.sensorEntry[-1].grid(row=rowEven, column=4, pady=5, sticky=tk.W)

	def get_entry_dict(self):
		sensor_dict = {}
		merge_dict = {}
		if (self.IP_entry.get() and self.Machine_entry.get() and self.Mac_entry.get()):
			sensor_dict.update({self.Machine_entry.cget("text"): self.Machine_entry.get()})
			sensor_dict.update({self.Mac_entry.cget("text"): self.Mac_entry.get()})

			for sensor in range(len(self.sensorEntry)):
				sensor_dict.update({self.sensorEntry[sensor].cget("text"): self.sensorEntry[sensor].get() or None})

			merge_dict[self.IP_entry.get()] = sensor_dict

			self.terminal_tree.insert('', tk.END, values=(self.Machine_entry.get(), self.IP_entry.get(), self.Mac_entry.get()))

			print(self.setting_dict)

			self.setting_dict.update(merge_dict)

			print(self.setting_dict)

		else:
			messagebox.showerror("Error", "Please input the mandatory fields: \nMachine, IP and Mac")

	def save_settings(self):
		settings = self.setting_dict
		print(settings)
		# settings = {**self.treeview_insert,**self.setting_dict}
		#print(self.get_entry_dict())
		with open(self.filename, 'w+') as outfile:
			json.dump(settings, outfile)

	def populate_treeview(self):
		if os.stat(self.filename).st_size == 0:
			pass
		else:
			with open(self.filename) as infile:
				self.setting_dict = json.load(infile)

			for ip, details in self.setting_dict.items():
				self.terminal_tree.insert('', tk.END, values=(details.get('machine'), ip, details.get('mac')))

		print(self.setting_dict)

	def delete_machine(self):
		try:
			iid = self.terminal_tree.focus()
			machine, ip, mac = self.terminal_tree.item(iid)['values']
			del self.setting_dict[ip]

			selected_machine = self.terminal_tree.selection()[0]  # <-- get selected item
			self.terminal_tree.delete(selected_machine)
		except ValueError as error:
			pass

class Extra(ttk.Frame):
	def __init__(self, master):
		ttk.Frame.__init__(self)
		label = ttk.Label(self, text="Hi, this is extra")
		label.grid(row=1,column=0,padx=10,pady=10)

class Employee(ttk.Frame):
	def __init__(self, master):
		ttk.Frame.__init__(self)
		label = ttk.Label(self, text="Hi, this is employee")
		label.grid(row=1,column=0,padx=10,pady=10)

if __name__ == '__main__':
	root = tk.Tk()
	main_app = Settings(root)
	root.mainloop()