import tkinter as tk
from tkinter import ttk

class Settings(ttk.Frame):
	def __init__(self, master):
		super(Settings, self).__init__()
		self.master = master
		self.tabControl = ttk.Notebook(self.master)
		self.master.title("Settings")
		self.master.minsize(640, 600)
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
		self.details_frame()

	def treeview_frame(self):
		# label = ttk.Label(self, text="Hi, this is network")
		# label.grid(row=1,column=0,padx=10,pady=10)

		self.topFrame = ttk.Frame(self)
		self.topFrame.pack(side=tk.TOP, fill=tk.BOTH, anchor=tk.N)

		# scroll bar for the terminal outputs
		terminal_scrollbar = ttk.Scrollbar(self.topFrame)
		terminal_scrollbar.grid(row=2, column=5, sticky=tk.NS)

		# terminal treeview output
		terminal_tree = ttk.Treeview(self.topFrame)
		terminal_tree.grid(row=2, column=0, columnspan=5, sticky=tk.NSEW)
		terminal_tree.configure(yscrollcommand=terminal_scrollbar.set)
		self.columnconfigure(2, weight=1)
		self.rowconfigure(2, weight=1)
		terminal_tree["columns"] = ("1", "2", "3")
		terminal_tree['show'] = 'headings'
		terminal_tree.column("1", width=200, anchor='c')
		terminal_tree.column("2", width=200, anchor='c')
		terminal_tree.column("3", width=200, anchor='c')
		terminal_tree.heading("1", text="Name")
		terminal_tree.heading("2", text="IP")
		terminal_tree.heading("3", text="Date Modified")

	def details_frame(self):
		self.bottomFrame = ttk.Frame(self)
		self.bottomFrame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

		# terminal scroll bar
		terminal_scrollbar = ttk.Scrollbar(self.bottomFrame)
		terminal_scrollbar.grid(row=0, column=1, sticky=tk.NS)

		# terminal treeview output
		terminal_tree = ttk.Treeview(self.bottomFrame)
		terminal_tree.grid(row=0, column=0, columnspan=1, sticky=tk.NSEW)
		terminal_tree.configure(yscrollcommand=terminal_scrollbar.set)
		self.columnconfigure(0, weight=1)
		self.rowconfigure(0, weight=1)
		terminal_tree["columns"] = ("1", "2", "3")
		terminal_tree['show'] = 'headings'
		terminal_tree.column("1", width=200, anchor='c')
		terminal_tree.column("2", width=200, anchor='c')
		terminal_tree.column("3", width=200, anchor='c')
		terminal_tree.heading("1", text="Name")
		terminal_tree.heading("2", text="Value")
		terminal_tree.heading("3", text="Date Modified")

	def addMachine_window(self):
		self.add_window = tk.Toplevel(self.master)
		self.add_window.title("Add Machine")

		# terminal input label and entry
		Machine_label = ttk.Label(self.bottomFrame, text="Machine: ")
		Machine_label.grid(row=0, column=0, padx=(40,0))

		Machine_entry = ttk.Entry(self.bottomFrame, text="Machine")
		Machine_entry.grid(row=0, column=1, padx=(0,50))

		IP_label = ttk.Label(self.bottomFrame, text="IP: ")
		IP_label.grid(row=0, column=3,)

		IP_entry = ttk.Entry(self.bottomFrame, text="IP")
		IP_entry.grid(row=0, column=4, padx=(0,50))

		Mac_label = ttk.Label(self.bottomFrame, text="Mac: ")
		Mac_label.grid(row=1, column=0)

		Mac_entry = ttk.Entry(self.bottomFrame, text="Mac")
		Mac_entry.grid(row=1, column=1)

		Separator = ttk.Separator(self.bottomFrame, orient='horizontal')
		Separator.grid(row=2, columnspan=5, sticky=tk.EW)

		S01_label = ttk.Label(self.bottomFrame, text="S01: ")
		S01_label.grid(row=3, column=0)

		S01_entry = ttk.Entry(self.bottomFrame, text="S01")
		S01_entry.grid(row=3, column=1)

		S02_label = ttk.Label(self.bottomFrame, text="S02: ")
		S02_label.grid(row=4, column=0)

		S02_entry = ttk.Entry(self.bottomFrame, text="S02")
		S02_entry.grid(row=4, column=1)

		S03_label = ttk.Label(self.bottomFrame, text="S03: ")
		S03_label.grid(row=5, column=0)

		S03_entry = ttk.Entry(self.bottomFrame, text="S03")
		S03_entry.grid(row=5, column=1)

		S04_label = ttk.Label(self.bottomFrame, text="S04: ")
		S04_label.grid(row=6, column=0)

		S04_entry = ttk.Entry(self.bottomFrame, text="S04")
		S04_entry.grid(row=6, column=1)

		S05_label = ttk.Label(self.bottomFrame, text="S05: ")
		S05_label.grid(row=7, column=0)

		S05_entry = ttk.Entry(self.bottomFrame, text="S05")
		S05_entry.grid(row=7, column=1)

		S06_label = ttk.Label(self.bottomFrame, text="S06: ")
		S06_label.grid(row=8, column=0)

		S06_entry = ttk.Entry(self.bottomFrame, text="S06")
		S06_entry.grid(row=8, column=1)

		S07_label = ttk.Label(self.bottomFrame, text="S07: ")
		S07_label.grid(row=9, column=0)

		S07_entry = ttk.Entry(self.bottomFrame, text="S07")
		S07_entry.grid(row=9, column=1)

		S08_label = ttk.Label(self.bottomFrame, text="S08: ")
		S08_label.grid(row=10, column=0)

		S08_entry = ttk.Entry(self.bottomFrame, text="S08")
		S08_entry.grid(row=10, column=1)

		S09_label = ttk.Label(self.bottomFrame, text="S09: ")
		S09_label.grid(row=11, column=0)

		S09_entry = ttk.Entry(self.bottomFrame, text="S09")
		S09_entry.grid(row=11, column=1)

		S10_label = ttk.Label(self.bottomFrame, text="S10: ")
		S10_label.grid(row=12, column=0)

		S10_entry = ttk.Entry(self.bottomFrame, text="S10")
		S10_entry.grid(row=12, column=1)

		S11_label = ttk.Label(self.bottomFrame, text="S11: ")
		S11_label.grid(row=3, column=3)

		S11_entry = ttk.Entry(self.bottomFrame, text="S11")
		S11_entry.grid(row=3, column=4)

		S12_label = ttk.Label(self.bottomFrame, text="S12: ")
		S12_label.grid(row=4, column=3)

		S12_entry = ttk.Entry(self.bottomFrame, text="S12")
		S12_entry.grid(row=4, column=4)

		S13_label = ttk.Label(self.bottomFrame, text="S13: ")
		S13_label.grid(row=5, column=3)

		S13_entry = ttk.Entry(self.bottomFrame, text="S13")
		S13_entry.grid(row=5, column=4)

		S14_label = ttk.Label(self.bottomFrame, text="S14: ")
		S14_label.grid(row=6, column=3)

		S14_entry = ttk.Entry(self.bottomFrame, text="S14")
		S14_entry.grid(row=6, column=4)

		S15_label = ttk.Label(self.bottomFrame, text="S15: ")
		S15_label.grid(row=7, column=3)

		S15_entry = ttk.Entry(self.bottomFrame, text="S15")
		S15_entry.grid(row=7, column=4)

		E01_label = ttk.Label(self.bottomFrame, text="E01: ")
		E01_label.grid(row=8, column=3)

		E01_entry = ttk.Entry(self.bottomFrame, text="E01")
		E01_entry.grid(row=8, column=4)

		E02_label = ttk.Label(self.bottomFrame, text="E02: ")
		E02_label.grid(row=9, column=3)

		E02_entry = ttk.Entry(self.bottomFrame, text="E02")
		E02_entry.grid(row=9, column=4)

		E03_label = ttk.Label(self.bottomFrame, text="E03: ")
		E03_label.grid(row=10, column=3)

		E03_entry = ttk.Entry(self.bottomFrame, text="E03")
		E03_entry.grid(row=10, column=4)

		E04_label = ttk.Label(self.bottomFrame, text="E04: ")
		E04_label.grid(row=11, column=3)

		E04_entry = ttk.Entry(self.bottomFrame, text="E04")
		E04_entry.grid(row=11, column=4)

		E05_label = ttk.Label(self.bottomFrame, text="E05: ")
		E05_label.grid(row=12, column=3)

		E05_entry = ttk.Entry(self.bottomFrame, text="E05")
		E05_entry.grid(row=12, column=4)

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