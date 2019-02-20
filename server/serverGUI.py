import tkinter as tk
from tkinter import ttk

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
	def __init__(self, master):
		ttk.Frame.__init__(self)
		self.treeview_frame()
		self.button_frame()
		self.details_frame()

	def treeview_frame(self):
		# label = ttk.Label(self, text="Hi, this is network")
		# label.grid(row=1,column=0,padx=10,pady=10)

		self.topFrame = tk.Frame(self, background='red')
		self.topFrame.pack(side=tk.TOP, fill=tk.BOTH, anchor=tk.N)

		# scroll bar for the terminal outputs
		terminal_scrollbar = ttk.Scrollbar(self.topFrame)
		terminal_scrollbar.grid(row=0, column=5, sticky=tk.NS)

		# terminal treeview output
		terminal_tree = ttk.Treeview(self.topFrame)
		terminal_tree.grid(row=0, column=0, columnspan=5, sticky=tk.NSEW)
		terminal_tree.configure(yscrollcommand=terminal_scrollbar.set)
		self.topFrame.columnconfigure(2, weight=1)
		self.topFrame.rowconfigure(2, weight=1)
		terminal_tree["columns"] = ("1", "2", "3")
		terminal_tree['show'] = 'headings'
		terminal_tree.column("1", width=200, anchor='c')
		terminal_tree.column("2", width=200, anchor='c')
		terminal_tree.column("3", width=200, anchor='c')
		terminal_tree.heading("1", text="Machine")
		terminal_tree.heading("2", text="IP")
		terminal_tree.heading("3", text="Date Modified")

	def button_frame(self):
		self.midFrame = tk.Frame(self, background='green')
		self.midFrame.pack(side=tk.TOP, fill=tk.BOTH, anchor=tk.N)
		# buttons
		add_button = ttk.Button(self.midFrame, text="Add")
		add_button.grid(row=0, column=0, padx=10, pady=5, sticky=tk.EW)

		edit_button = ttk.Button(self.midFrame, text="Edit")
		edit_button.grid(row=0, column=1, padx=10, pady=5, sticky=tk.EW)

		delete_button = ttk.Button(self.midFrame, text="Delete")
		delete_button.grid(row=0, column=2, padx=10, pady=5, sticky=tk.EW)

		for rows in range(3):
			self.midFrame.columnconfigure(rows, weight=1)

	def details_frame(self):
		self.bottomFrame = tk.Frame(self, background='blue')
		self.bottomFrame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

		self.bottomFrame.columnconfigure(0, weight=1)
		self.bottomFrame.columnconfigure(1, weight=1)
		self.bottomFrame.columnconfigure(3, weight=1)
		self.bottomFrame.columnconfigure(4, weight=1)

		for rows in range(13):
			self.bottomFrame.rowconfigure(rows, weight=1)

		# terminal input label and entry
		Machine_label = ttk.Label(self.bottomFrame, text="Machine: ")
		Machine_label.grid(row=0, column=0, padx=(40,0), pady=5, sticky=tk.E)

		Machine_entry = ttk.Entry(self.bottomFrame, text="Machine")
		Machine_entry.grid(row=0, column=1, padx=(0,50), pady=5, sticky=tk.W)

		IP_label = ttk.Label(self.bottomFrame, text="IP: ")
		IP_label.grid(row=0, column=3, pady=5, sticky=tk.E)

		IP_entry = ttk.Entry(self.bottomFrame, text="IP")
		IP_entry.grid(row=0, column=4, padx=(0,50), pady=5, sticky=tk.W)

		Mac_label = ttk.Label(self.bottomFrame, text="Mac: ")
		Mac_label.grid(row=1, column=0, pady=5, sticky=tk.E)

		Mac_entry = ttk.Entry(self.bottomFrame, text="Mac")
		Mac_entry.grid(row=1, column=1, pady=5, sticky=tk.W)

		Separator = ttk.Separator(self.bottomFrame, orient='horizontal')
		Separator.grid(row=2, columnspan=5, pady=5, sticky=tk.EW)

		sensorOddList = ["S01", "S03", "S05", "S07", "SO9", "S11", "S13", "S15", "E02", "E04"]
		sensorEvenList = ["S02", "S04", "S06", "S08", "S10", "S12", "S14", "E01", "E03", "E05"]

		rowOdd = 3
		rowEven = 3

		for sensor in range(len(sensorOddList)):
			rowOdd = rowOdd + 1
			columnLabel = 0
			columnEntry = 1
			sensorLabel = sensorOddList[sensor] + "_label"
			sensorLabel = ttk.Label(self.bottomFrame, text="%s: " % sensorOddList[sensor])
			sensorLabel.grid(row=rowOdd, column=columnLabel, pady=5, sticky=tk.E)

			sensorEntry = sensorOddList[sensor] + "_entry"
			sensorEntry = ttk.Entry(self.bottomFrame, text=sensorOddList[sensor])
			sensorEntry.grid(row=rowOdd, column=columnEntry, pady=5, sticky=tk.W)

		for sensor in range(len(sensorEvenList)):
			rowEven = rowEven + 1
			columnLabel = 3
			columnEntry = 4
			sensorLabel = sensorEvenList[sensor] + "_label"
			sensorLabel = ttk.Label(self.bottomFrame, text="%s: " % sensorEvenList[sensor])
			sensorLabel.grid(row=rowEven, column=columnLabel, pady=5, sticky=tk.E)

			sensorEntry = sensorEvenList[sensor] + "_entry"
			sensorEntry = ttk.Entry(self.bottomFrame, text=sensorEvenList[sensor])
			sensorEntry.grid(row=rowEven, column=columnEntry, pady=5, sticky=tk.W)

		# S01_label = ttk.Label(self.bottomFrame, text="S01: ")
		# S01_label.grid(row=3, column=0, sticky=tk.E)

		# S01_entry = ttk.Entry(self.bottomFrame, text="S01")
		# S01_entry.grid(row=3, column=1, sticky=tk.W)

		# S02_label = ttk.Label(self.bottomFrame, text="S02: ")
		# S02_label.grid(row=4, column=0, sticky=tk.E)

		# S02_entry = ttk.Entry(self.bottomFrame, text="S02")
		# S02_entry.grid(row=4, column=1, sticky=tk.W)

		# S03_label = ttk.Label(self.bottomFrame, text="S03: ")
		# S03_label.grid(row=5, column=0, sticky=tk.E)

		# S03_entry = ttk.Entry(self.bottomFrame, text="S03")
		# S03_entry.grid(row=5, column=1, sticky=tk.W)

		# S04_label = ttk.Label(self.bottomFrame, text="S04: ")
		# S04_label.grid(row=6, column=0, sticky=tk.E)

		# S04_entry = ttk.Entry(self.bottomFrame, text="S04")
		# S04_entry.grid(row=6, column=1, sticky=tk.W)

		# S05_label = ttk.Label(self.bottomFrame, text="S05: ")
		# S05_label.grid(row=7, column=0, sticky=tk.E)

		# S05_entry = ttk.Entry(self.bottomFrame, text="S05")
		# S05_entry.grid(row=7, column=1, sticky=tk.W)

		# S06_label = ttk.Label(self.bottomFrame, text="S06: ")
		# S06_label.grid(row=8, column=0, sticky=tk.E)

		# S06_entry = ttk.Entry(self.bottomFrame, text="S06")
		# S06_entry.grid(row=8, column=1, sticky=tk.W)

		# S07_label = ttk.Label(self.bottomFrame, text="S07: ")
		# S07_label.grid(row=9, column=0, sticky=tk.E)

		# S07_entry = ttk.Entry(self.bottomFrame, text="S07")
		# S07_entry.grid(row=9, column=1, sticky=tk.W)

		# S08_label = ttk.Label(self.bottomFrame, text="S08: ")
		# S08_label.grid(row=10, column=0, sticky=tk.E)

		# S08_entry = ttk.Entry(self.bottomFrame, text="S08")
		# S08_entry.grid(row=10, column=1, sticky=tk.W)

		# S09_label = ttk.Label(self.bottomFrame, text="S09: ")
		# S09_label.grid(row=11, column=0, sticky=tk.E)

		# S09_entry = ttk.Entry(self.bottomFrame, text="S09")
		# S09_entry.grid(row=11, column=1, sticky=tk.W)

		# S10_label = ttk.Label(self.bottomFrame, text="S10: ")
		# S10_label.grid(row=12, column=0, sticky=tk.E)

		# S10_entry = ttk.Entry(self.bottomFrame, text="S10")
		# S10_entry.grid(row=12, column=1, sticky=tk.W)

		# S11_label = ttk.Label(self.bottomFrame, text="S11: ")
		# S11_label.grid(row=3, column=3, sticky=tk.E)

		# S11_entry = ttk.Entry(self.bottomFrame, text="S11")
		# S11_entry.grid(row=3, column=4, sticky=tk.W)

		# S12_label = ttk.Label(self.bottomFrame, text="S12: ")
		# S12_label.grid(row=4, column=3, sticky=tk.E)

		# S12_entry = ttk.Entry(self.bottomFrame, text="S12")
		# S12_entry.grid(row=4, column=4, sticky=tk.W)

		# S13_label = ttk.Label(self.bottomFrame, text="S13: ")
		# S13_label.grid(row=5, column=3, sticky=tk.E)

		# S13_entry = ttk.Entry(self.bottomFrame, text="S13")
		# S13_entry.grid(row=5, column=4, sticky=tk.W)

		# S14_label = ttk.Label(self.bottomFrame, text="S14: ")
		# S14_label.grid(row=6, column=3, sticky=tk.E)

		# S14_entry = ttk.Entry(self.bottomFrame, text="S14")
		# S14_entry.grid(row=6, column=4, sticky=tk.W)

		# S15_label = ttk.Label(self.bottomFrame, text="S15: ")
		# S15_label.grid(row=7, column=3, sticky=tk.E)

		# S15_entry = ttk.Entry(self.bottomFrame, text="S15")
		# S15_entry.grid(row=7, column=4, sticky=tk.W)

		# E01_label = ttk.Label(self.bottomFrame, text="E01: ")
		# E01_label.grid(row=8, column=3, sticky=tk.E)

		# E01_entry = ttk.Entry(self.bottomFrame, text="E01")
		# E01_entry.grid(row=8, column=4, sticky=tk.W)

		# E02_label = ttk.Label(self.bottomFrame, text="E02: ")
		# E02_label.grid(row=9, column=3, sticky=tk.E)

		# E02_entry = ttk.Entry(self.bottomFrame, text="E02")
		# E02_entry.grid(row=9, column=4, sticky=tk.W)

		# E03_label = ttk.Label(self.bottomFrame, text="E03: ")
		# E03_label.grid(row=10, column=3, sticky=tk.E)

		# E03_entry = ttk.Entry(self.bottomFrame, text="E03")
		# E03_entry.grid(row=10, column=4, sticky=tk.W)

		# E04_label = ttk.Label(self.bottomFrame, text="E04: ")
		# E04_label.grid(row=11, column=3, sticky=tk.E)

		# E04_entry = ttk.Entry(self.bottomFrame, text="E04")
		# E04_entry.grid(row=11, column=4, sticky=tk.W)

		# E05_label = ttk.Label(self.bottomFrame, text="E05: ")
		# E05_label.grid(row=12, column=3, sticky=tk.E)

		# E05_entry = ttk.Entry(self.bottomFrame, text="E05")
		# E05_entry.grid(row=12, column=4, sticky=tk.W)

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