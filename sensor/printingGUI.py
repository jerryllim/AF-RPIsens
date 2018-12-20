import tkinter
from tkinter import ttk
from tkinter import messagebox
import json
import cv2
import time
from pyzbar import pyzbar


class PrintingGUI(tkinter.Tk):
    def __init__(self):
        tkinter.Tk.__init__(self)
        self.title('Printing GUI')
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.current_job = None

        self.select_page = SelectJobPage(self)
        self.select_page.pack(fill=tkinter.BOTH, expand=tkinter.TRUE)

    def open_job_page(self, job_dict):
        job_page = JobPage(self.master, job_dict)
        job_page.pack(fill=tkinter.BOTH, expand=tkinter.TRUE)
        job_page.tkraise()


class SelectJobPage(ttk.Frame):
    def __init__(self, parent, **kwargs):
        ttk.Frame.__init__(self, parent, **kwargs)
        self.configure(padding=5)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)
        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=100)
        self.columnconfigure(1, weight=1)

        job_label = ttk.Label(self, text='JO number:')
        job_label.grid(row=0, column=0, sticky='sw')
        self.job_var = tkinter.StringVar()
        job_entry = ttk.Entry(self, textvariable=self.job_var, state="readonly")
        job_entry.grid(row=1, column=0, stick='ew')
        scan_button = ttk.Button(self, text='Scan', command=self.scan_barcode)
        scan_button.grid(row=1, column=1, sticky='w')
        button_frame = ttk.Frame(self)
        button_frame.grid(row=2, column=0, columnspan=2, sticky='n')
        start_button = ttk.Button(button_frame, text='Start', command=self.start_job)
        start_button.pack()

    def scan_barcode(self):
        cam = cv2.VideoCapture(0)
        timeout = time.time() + 10

        while True:
            _, frame = cam.read()

            barcodes = pyzbar.decode(frame)

            if barcodes:
                barcode = barcodes[0]
                barcodeData = barcode.data.decode("utf-8")
                self.job_var.set(barcodeData)
                break
            elif time.time() > timeout:
                break

        cam.release()

    def start_job(self, job_num):
        try:
            with open('{}.json'.format(job_num), 'r') as infile:
                job_dict = json.load(infile)

            self.master.open_job_page(job_dict)
        except FileNotFoundError:
            messagebox.showerror('Job Not Found', 'JO No.: {} not found.'.format(job_num))


class JobPage(ttk.Frame):
    def __init__(self, parent, job, **kwargs):
        ttk.Frame.__init__(self, parent, **kwargs)
        self.job = job
        self.configure(padding=5)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        self.top_frame = ttk.Frame(self)
        self.top_frame.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')
        self.top_frame_init()

        self.adjust_view = False
        self.current_entry = None

        # Job info page
        self.info_frame = ttk.Frame(self)
        self.info_frame.grid(row=1, column=0, sticky="nsew")
        self.info_frame_init()

        # Adjustments page
        self.adjust_frame = ttk.Frame(self)
        self.adjust_frame.grid(row=1, column=0, sticky="nsew")
        self.adjust_frame_init()

        self.set_frame()

    def set_frame(self):
        if self.adjust_view:
            self.adjust_frame.tkraise()
        else:
            self.info_frame.tkraise()

    def top_frame_init(self):
        job_label = ttk.Label(self.top_frame, text='JO number:')
        job_label.pack(side=tkinter.LEFT, padx=5)
        number_label = ttk.Label(self.top_frame, text=self.job['JO No.'])
        number_label.pack(side=tkinter.LEFT, padx=5)

        stop_button = tkinter.Button(self.top_frame, text='Stop', bg='red', fg='white', height=4, width=15,
                                     command=self.stop_job)
        stop_button.pack(side=tkinter.RIGHT, padx=5)
        adjust_icon = tkinter.PhotoImage(file='adjust_icon.png')
        adjust_button = tkinter.Button(self.top_frame, image=adjust_icon, command=self.toggle_adjustments)
        adjust_button.image = adjust_icon
        adjust_button.pack(side=tkinter.RIGHT, padx=5)

    def info_frame_init(self):
        vscroll_frame = VerticalScrollFrame(self.info_frame, tk=True)
        vscroll_frame.pack(fill=tkinter.BOTH, expand=True)
        vscroll_inner = vscroll_frame.get_interior_frame()
        vscroll_inner.rowconfigure(0, weight=1)
        vscroll_inner.columnconfigure(0, weight=1)

        # Set up To do, current count, ...
        count_frame = tkinter.Frame(vscroll_inner)
        count_frame.grid(row=0, column=0, sticky='w')
        todo_label = FramedFrame(count_frame, self.job, 'To do')
        todo_label.pack(side=tkinter.LEFT, fill=tkinter.X, expand=True)
        counter_frame = tkinter.Frame(count_frame, highlightcolor='Blue', highlightbackground='Blue',
                                      highlightthickness=1, padx=5, pady=5)
        counter_frame.pack(side=tkinter.LEFT, fill=tkinter.X, expand=True)
        counter_label = tkinter.Label(counter_frame, text='Counter:', fg='Blue')
        counter_label.pack(side=tkinter.LEFT, fill=tkinter.X, anchor='e')
        counter_var = tkinter.StringVar()
        counter_var.set(0)
        counter_val = tkinter.Label(counter_frame, textvariable=counter_var)
        counter_val.pack(side=tkinter.LEFT, fill=tkinter.X, expand=True, anchor='w')

        # Row 1
        temp_frame = tkinter.Frame(vscroll_inner)
        temp_frame.grid(row=1, column=0, sticky='w')
        code_label = FramedFrame(temp_frame, self.job, 'Code')
        code_label.pack(side=tkinter.LEFT, fill=tkinter.X, expand=True)
        desc_label = FramedFrame(temp_frame, self.job, 'Desc')
        desc_label.pack(side=tkinter.LEFT, fill=tkinter.X, expand=True)

        # Row 2
        temp_frame = tkinter.Frame(vscroll_inner)
        temp_frame.grid(row=2, column=0, sticky='w')
        sono_label = FramedFrame(temp_frame, self.job, 'So No')
        sono_label.pack(side=tkinter.LEFT, fill=tkinter.X, expand=True)
        edd_label = FramedFrame(temp_frame, self.job, 'EDD')
        edd_label.pack(side=tkinter.LEFT, fill=tkinter.X, expand=True)
        soqty_label = FramedFrame(temp_frame, self.job, 'So Qty')
        soqty_label.pack(side=tkinter.LEFT, fill=tkinter.X, expand=True)
        sorem_label = FramedFrame(temp_frame, self.job, 'So Rem')
        sorem_label.pack(side=tkinter.LEFT, fill=tkinter.X, expand=True)

        # Materials
        treeview_frame = tkinter.Frame(vscroll_inner, highlightcolor='Blue', highlightbackground='Blue',
                                   highlightthickness=1, padx=5, pady=5)
        treeview_frame.grid(row=3, column=0, sticky='w')
        treeview_frame.rowconfigure(0, weight=1)
        treeview_frame.columnconfigure(0, weight=1)
        material_treeview = ttk.Treeview(treeview_frame, height=len(self.job['Materials']))
        material_treeview.pack(fill=tkinter.BOTH, expand=False)
        material_treeview['show'] = 'headings'
        material_treeview['column'] = ('code', 'desc', 'qty', 'uom')
        material_treeview.heading('code', text='Material Code')
        material_treeview.heading('desc', text='Material Description')
        material_treeview.heading('qty', text='QTY')
        material_treeview.heading('uom', text='UOM')
        material_treeview.column('code', width=200)
        material_treeview.column('desc', width=500)
        material_treeview.column('qty', width=50, anchor=tkinter.E)
        material_treeview.column('uom', width=50)

        for key in sorted(self.job['Materials'].keys()):
            material = self.job['Materials'][key]
            material_treeview.insert('', tkinter.END, values=(material['Material Code'],
                                                              material['Material Description'],
                                                              material['Qty'], material['UOM']))

        # Instructions
        instruction_frame = tkinter.Frame(vscroll_inner, highlightcolor='Blue', highlightbackground='Blue',
                                          highlightthickness=1, padx=5, pady=5)
        instruction_frame.grid(row=4, column=0, sticky='w')
        instruction_label = tkinter.Label(instruction_frame, fg='Blue', text='{}: '.format('Instruction'))
        instruction_label.pack(side=tkinter.TOP, anchor=tkinter.W)
        instruction_text = tkinter.Label(instruction_frame, text=self.job['Instruction'], justify=tkinter.LEFT)
        instruction_text.pack(side=tkinter.TOP, anchor=tkinter.W)

    def adjust_frame_init(self):
        self.adjust_frame.rowconfigure(0, weight=1)
        self.adjust_frame.columnconfigure(0, weight=1)
        self.adjust_frame.columnconfigure(1, weight=1)

        # TODO create stringVar for entries or something
        left_frame = VerticalScrollFrame(self.adjust_frame)
        left_frame.grid(row=0, column=0, sticky='nsew')
        left_inner=left_frame.get_interior_frame()
        size_label = ttk.Label(left_inner, text='Size')
        size_label.grid(row=0, column=0, sticky='e')
        size_entry = ttk.Entry(left_inner)
        size_entry.grid(row=0, column=1, sticky='w')

        ink_label = ttk.Label(left_inner, text='Ink')
        ink_label.grid(row=1, column=0, sticky='e')
        ink_entry = ttk.Entry(left_inner)
        ink_entry.grid(row=1, column=1, sticky='w')

        plate_label = ttk.Label(left_inner, text='Plate')
        plate_label.grid(row=2, column=0, sticky='e')
        plate_entry = ttk.Entry(left_inner)
        plate_entry.grid(row=2, column=1, sticky='w')

        load_label = ttk.Label(left_inner, text='Load')
        load_label.grid(row=3, column=0, sticky='e')
        load_entry = ttk.Entry(left_inner)
        load_entry.grid(row=3, column=1, sticky='w')

        unload_label = ttk.Label(left_inner, text='Unload')
        unload_label.grid(row=4, column=0, sticky='e')
        unload_entry = ttk.Entry(left_inner)
        unload_entry.grid(row=4, column=1, sticky='w')

        blanket_label = ttk.Label(left_inner, text='Blanket/Packing')
        blanket_label.grid(row=5, column=0, sticky='e')
        blanket_entry = ttk.Entry(left_inner)
        blanket_entry.grid(row=5, column=1, sticky='w')


        size_entry.bind("<FocusIn>", self.set_entry)
        ink_entry.bind("<FocusIn>", self.set_entry)
        plate_entry.bind("<FocusIn>", self.set_entry)
        load_entry.bind("<FocusIn>", self.set_entry)
        unload_entry.bind("<FocusIn>", self.set_entry)
        blanket_entry.bind("<FocusIn>", self.set_entry)
        self.numpad_init()

    def stop_job(self):
        self.destroy()

    def toggle_adjustments(self):
        self.adjust_view = not self.adjust_view
        self.set_frame()

    def numpad_init(self):
        numpad_frame = ttk.Frame(self.adjust_frame)
        numpad_frame.grid(row=0, column=1, padx=5, pady=5)
        numpad_frame.rowconfigure(0, weight=1)
        numpad_frame.rowconfigure(1, weight=1)
        numpad_frame.rowconfigure(2, weight=1)
        numpad_frame.rowconfigure(3, weight=1)
        numpad_frame.columnconfigure(0, weight=1)
        numpad_frame.columnconfigure(1, weight=1)
        numpad_frame.columnconfigure(2, weight=1)

        buttons = []

        button = ttk.Button(numpad_frame, text='0', command=lambda: self.button_pressed(0))
        button.grid(row=3, column=1)
        buttons.append(button)

        for i in range(1,10):
            button = ttk.Button(numpad_frame, text=i, command=lambda val=i: self.button_pressed(val))
            row = 2 - (i - 1)//3
            col = (i + 2)%3
            button.grid(row=row, column=col)
            buttons.append(button)

        del_button = ttk.Button(numpad_frame, text='Del', command=lambda: self.button_pressed('del'))
        del_button.grid(row=3, column=0)

        enter_button = ttk.Button(numpad_frame, text='Enter', command=lambda: self.button_pressed('enter'))
        enter_button.grid(row=3, column=2)

    def button_pressed(self, val):
        if self.current_entry is None:
            return

        if val == 'del':
            self.current_entry.delete(len(self.current_entry.get()) - 1)
        elif val == 'enter':
            self.current_entry = None
        else:
            self.current_entry.insert(tkinter.END, val)

    def set_entry(self, _event):
        self.current_entry = self.master.focus_get()


class VerticalScrollFrame(ttk.Frame):
    def __init__(self, parent, tk=False, **kwargs):
        ttk.Frame.__init__(self, parent, **kwargs)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.canvas = tkinter.Canvas(self)
        self.canvas.grid(row=0, column=0, sticky='nsew')
        v_scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        v_scrollbar.grid(row=0, column=1, sticky='nsw')
        self.canvas.config(yscrollcommand=v_scrollbar.set, scrollregion=self.canvas.bbox('all'))

        if tk:
            self.interior_frame = tkinter.Frame(self.canvas)
        else:
            self.interior_frame = ttk.Frame(self.canvas)
        self.interior_frame_id = self.canvas.create_window((0, 0), window=self.interior_frame, anchor=tkinter.NW)

        self.interior_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind('<Configure>', self._on_canvas_configure)

    def _on_canvas_configure(self, event):
        canvas_width = event.width
        self.canvas.itemconfig(self.interior_frame_id, width=canvas_width)

    def _on_frame_configure(self, _event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def get_interior_frame(self):
        return self.interior_frame

class FramedFrame(tkinter.Frame):
    def __init__(self, parent, job_dict, key):
        tkinter.Frame.__init__(self, parent, highlightcolor='White', highlightbackground='Blue', highlightthickness=1,
                               padx=5, pady=5)
        label = tkinter.Label(self, fg='Blue', text='{}: '.format(key))
        label.pack(side=tkinter.LEFT, anchor='e', fill=tkinter.X)
        value = tkinter.Label(self, text=job_dict[key])
        value.pack(side=tkinter.LEFT, anchor='w', expand=True, fill=tkinter.X)


if __name__ == '__main__':
    if False:
        with open('Z000461580003.json', 'r') as infile:
            job_dict = json.load(infile)

        root = tkinter.Tk()
        app = JobPage(root, job_dict)
        app.pack(fill=tkinter.BOTH, expand=tkinter.TRUE)
        root.mainloop()

    root = PrintingGUI()
    root.mainloop()
