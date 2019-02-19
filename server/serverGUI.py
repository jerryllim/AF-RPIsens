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

		self.tabControl.pack(expand=1, fill="both")

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
		self.terminal_scrollbar = ttk.Scrollbar(self.topFrame)
		self.terminal_scrollbar.grid(row=2, column=5, sticky=tk.NS)

		# terminal treeview output
		self.terminal_tree = ttk.Treeview(self.topFrame)
		self.terminal_tree.grid(row=2, column=0, columnspan=5, sticky=tk.NSEW)
		self.terminal_tree.configure(yscrollcommand=self.terminal_scrollbar.set)
		self.columnconfigure(2, weight=1)
		self.rowconfigure(2, weight=1)
		self.terminal_tree["columns"] = ("1", "2", "3")
		self.terminal_tree['show'] = 'headings'
		self.terminal_tree.column("1", width=200, anchor='c')
		self.terminal_tree.column("2", width=200, anchor='c')
		self.terminal_tree.column("3", width=200, anchor='c')
		self.terminal_tree.heading("1", text="Name")
		self.terminal_tree.heading("2", text="IP")
		self.terminal_tree.heading("3", text="Date Modified")

	def details_frame(self):
		self.bottomFrame = ttk.Frame(self)
		self.bottomFrame.pack(side=tk.TOP, fill=tk.BOTH, anchor=tk.N)

		# terminal input label and entry
		self.Machine_label = ttk.Label(self.bottomFrame, text="Machine: ")
		self.Machine_label.grid(row=0, column=0)

		self.Machine_entry = ttk.Entry(self.bottomFrame, text="Machine")
		self.Machine_entry.grid(row=0, column=1)

		self.IP_label = ttk.Label(self.bottomFrame, text="IP: ")
		self.IP_label.grid(row=0, column=3)

		self.IP_entry = ttk.Entry(self.bottomFrame, text="IP")
		self.IP_entry.grid(row=0, column=4)

		self.Mac_label = ttk.Label(self.bottomFrame, text="Mac: ")
		self.Mac_label.grid(row=1, column=0)

		self.Mac_entry = ttk.Entry(self.bottomFrame, text="Mac")
		self.Mac_entry.grid(row=1, column=1)

		self.S01_label = ttk.Label(self.bottomFrame, text="S01: ")
		self.S01_label.grid(row=3, column=0)

		self.S01_entry = ttk.Entry(self.bottomFrame, text="S01")
		self.S01_entry.grid(row=3, column=1)

		self.S02_label = ttk.Label(self.bottomFrame, text="S02: ")
		self.S02_label.grid(row=4, column=0)

		self.S02_entry = ttk.Entry(self.bottomFrame, text="S02")
		self.S02_entry.grid(row=4, column=1)

		self.S03_label = ttk.Label(self.bottomFrame, text="S03: ")
		self.S03_label.grid(row=5, column=0)

		self.S03_entry = ttk.Entry(self.bottomFrame, text="S03")
		self.S03_entry.grid(row=5, column=1)

		self.S04_label = ttk.Label(self.bottomFrame, text="S04: ")
		self.S04_label.grid(row=6, column=0)

		self.S04_entry = ttk.Entry(self.bottomFrame, text="S04")
		self.S04_entry.grid(row=6, column=1)

		self.S05_label = ttk.Label(self.bottomFrame, text="S05: ")
		self.S05_label.grid(row=7, column=0)

		self.S05_entry = ttk.Entry(self.bottomFrame, text="S05")
		self.S05_entry.grid(row=7, column=1)

		self.S06_label = ttk.Label(self.bottomFrame, text="S06: ")
		self.S06_label.grid(row=8, column=0)

		self.S06_entry = ttk.Entry(self.bottomFrame, text="S06")
		self.S06_entry.grid(row=8, column=1)

		self.S07_label = ttk.Label(self.bottomFrame, text="S07: ")
		self.S07_label.grid(row=9, column=0)

		self.S07_entry = ttk.Entry(self.bottomFrame, text="S07")
		self.S07_entry.grid(row=9, column=1)

		self.S08_label = ttk.Label(self.bottomFrame, text="S08: ")
		self.S08_label.grid(row=10, column=0)

		self.S08_entry = ttk.Entry(self.bottomFrame, text="S08")
		self.S08_entry.grid(row=10, column=1)

		self.S09_label = ttk.Label(self.bottomFrame, text="S09: ")
		self.S09_label.grid(row=11, column=0)

		self.S09_entry = ttk.Entry(self.bottomFrame, text="S09")
		self.S09_entry.grid(row=11, column=1)

		self.S10_label = ttk.Label(self.bottomFrame, text="S10: ")
		self.S10_label.grid(row=12, column=0)

		self.S10_entry = ttk.Entry(self.bottomFrame, text="S10")
		self.S10_entry.grid(row=12, column=1)

		self.S11_label = ttk.Label(self.bottomFrame, text="S11: ")
		self.S11_label.grid(row=3, column=3)

		self.S11_entry = ttk.Entry(self.bottomFrame, text="S11")
		self.S11_entry.grid(row=3, column=4)

		self.S12_label = ttk.Label(self.bottomFrame, text="S12: ")
		self.S12_label.grid(row=4, column=3)

		self.S12_entry = ttk.Entry(self.bottomFrame, text="S12")
		self.S12_entry.grid(row=4, column=4)

		self.S13_label = ttk.Label(self.bottomFrame, text="S13: ")
		self.S13_label.grid(row=5, column=3)

		self.S13_entry = ttk.Entry(self.bottomFrame, text="S13")
		self.S13_entry.grid(row=5, column=4)

		self.S14_label = ttk.Label(self.bottomFrame, text="S14: ")
		self.S14_label.grid(row=6, column=3)

		self.S14_entry = ttk.Entry(self.bottomFrame, text="S14")
		self.S14_entry.grid(row=6, column=4)

		self.S15_label = ttk.Label(self.bottomFrame, text="S15: ")
		self.S15_label.grid(row=7, column=3)

		self.S15_entry = ttk.Entry(self.bottomFrame, text="S15")
		self.S15_entry.grid(row=7, column=4)

		self.E01_label = ttk.Label(self.bottomFrame, text="E01: ")
		self.E01_label.grid(row=8, column=3)

		self.E01_entry = ttk.Entry(self.bottomFrame, text="E01")
		self.E01_entry.grid(row=8, column=4)

		self.E02_label = ttk.Label(self.bottomFrame, text="E02: ")
		self.E02_label.grid(row=9, column=3)

		self.E02_entry = ttk.Entry(self.bottomFrame, text="E02")
		self.E02_entry.grid(row=9, column=4)

		self.E03_label = ttk.Label(self.bottomFrame, text="E03: ")
		self.E03_label.grid(row=10, column=3)

		self.E03_entry = ttk.Entry(self.bottomFrame, text="E03")
		self.E03_entry.grid(row=10, column=4)

		self.E04_label = ttk.Label(self.bottomFrame, text="E04: ")
		self.E04_label.grid(row=11, column=3)

		self.E04_entry = ttk.Entry(self.bottomFrame, text="E04")
		self.E04_entry.grid(row=11, column=4)

		self.E05_label = ttk.Label(self.bottomFrame, text="E05: ")
		self.E05_label.grid(row=12, column=3)

		self.E05_entry = ttk.Entry(self.bottomFrame, text="E05")
		self.E05_entry.grid(row=12, column=4)

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