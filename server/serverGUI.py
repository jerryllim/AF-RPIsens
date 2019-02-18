import tkinter as tk
from tkinter import ttk

class MainApplication(tk.Frame):
	def __init__(self, master):
		self.master = master
		tk.Frame.__init__(self, self.master)
		self.configure_gui()
		self.create_widgets()
		self.pack(fill='both', expand=True)

	def configure_gui(self):
		self.master.title("SERVER")

	def create_widgets(self):
		self.settings_label = ttk.Label(self, text="Settings: ")
		self.settings_label.grid(row=0, column=0)

		self.settings_button = ttk.Button(self, text="Settings", command=self.settings)
		self.settings_button.grid(row=0, column=1)

	def settings(self):
		self.setting = tk.Toplevel(self.master)
		try:
			self.main_app = Settings(self.setting)
		except FileNotFoundError:
			pass

class Settings(tk.Frame):
	def __init__(self, master):
		super(Settings, self).__init__()
		self.master = master
		self.tabControl = ttk.Notebook(self.master)
		self.master.title("Settings")
		self.master.minsize(640, 400)

		#tabControl = ttk.Notebook(self)
		self.tab1 = ttk.Frame(self.tabControl)
		self.tabControl.add(self.tab1, text="Network")
		self.tab2 = ttk.Frame(self.tabControl)
		self.tabControl.add(self.tab2, text="Extra")
		self.tab3 = ttk.Frame(self.tabControl)
		self.tabControl.add(self.tab3, text="Employee")

		self.tabControl.pack(expand=1, fill="both")

# TODO Network class tab

if __name__ == '__main__':
	root = tk.Tk()
	main_app = MainApplication(root)
	root.mainloop()