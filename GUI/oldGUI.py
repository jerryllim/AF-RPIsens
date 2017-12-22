import tkinter
import checkBar
import sensorGlobal


def checkbox_values():
    return checkBoxBar1.state() + checkBoxBar2.state()


def clear_readings():
    global sums
    for i in range(10):
        sums[i].set(0)


def advanced_options():
    def save_settings():
        for i in range(10):
            sensorGlobal.sensorNameArray[i] = name_entry_array[i].get()
            sensorGlobal.pinArray[i] = pin_entry_array[i].get()
        advanced_window.destroy()

    advanced_window = tkinter.Tk()
    advanced_window.title("Advanced Options")
    advanced_window.geometry('-200-200')
    advanced_window.grid_rowconfigure(0, weight=2)
    advanced_window.grid_rowconfigure(1, weight=1)
    advanced_window.grid_columnconfigure(0, weight=1)

    entry_frame = tkinter.LabelFrame(advanced_window, text='Sensor pins')
    entry_frame.grid(row=0, column=0, padx=5, pady=5)
    name_entry_array = []
    pin_entry_array = []
    for i in range(10):
        if i < 5:
            cRow = i
            cCol = 0
        else:
            cRow = i - 5
            cCol = 2

        name = tkinter.Entry(entry_frame)
        name.grid(row=cRow, column=cCol)
        name.delete(0, tkinter.END)
        name.insert(0,sensorGlobal.sensorNameArray[i])
        name_entry_array.append(name)
        pin = tkinter.Entry(entry_frame, width=2, justify=tkinter.RIGHT)
        pin.grid(row=cRow, column=cCol+1)
        pin.delete(0, tkinter.END)
        pin.insert(0, sensorGlobal.pinArray[i])
        pin_entry_array.append(pin)

    button_frame = tkinter.Frame(advanced_window)
    button_frame.grid(row=1, column=0, padx=5, pady=5)
    save_button = tkinter.Button(button_frame, text='Save', command=save_settings)
    save_button.pack(side=tkinter.LEFT)
    cancel_button = tkinter.Button(button_frame, text='Cancel', command=advanced_window.destroy)
    cancel_button.pack(side=tkinter.LEFT)


def new_reading():
    desired_readings = checkbox_values()
    global readingsFrame
    readingsFrame.destroy()
    readingsFrame = tkinter.Frame(mainWindow)
    readingsFrame.grid(row=1,column=0,columnspan=2,sticky='nsew',padx=5, pady=5)
    readingsFrame.grid_columnconfigure(0,weight=1)
    readingsFrame.grid_columnconfigure(1,weight=1)
    readingsFrame.grid_columnconfigure(2,weight=1)
    readingsFrame.grid_columnconfigure(3,weight=1)
    readingsFrame.grid_columnconfigure(4,weight=1)
    readingsFrame.grid_rowconfigure(0,weight=1)
    readingsFrame.grid_rowconfigure(1,weight=1)
    readingsFrame.grid_rowconfigure(2,weight=1)
    readingsFrame.grid_rowconfigure(3,weight=1)
    readingsFrame.grid_rowconfigure(4,weight=1)
    clear_readings()

    for i in range(10):
        if i < 5:
            _row = 0
            _Col = i
        else:
            _row = 1
            _Col = i - 5

        temp_frame = tkinter.Frame(readingsFrame, relief=tkinter.RIDGE, borderwidth=2)
        temp_frame.grid(row=_row, column=_Col, sticky='nsew')
        name_label = tkinter.Label(temp_frame, text=sensorGlobal.sensorNameArray[i])
        name_label.pack()
        value_label = tkinter.Label(temp_frame)
        value_label.pack()
        if desired_readings[i] == 1:
            value_label.config(textvariable=sums[i])
        else:
            value_label.config(text='None',foreground='red')


def start_gui():
    new_reading()
    mainWindow.mainloop()


# GUI starts here
mainWindow = tkinter.Tk()
mainWindow.title("Sample Sensor Reading")
mainWindow.geometry('-8-200')
mainWindow.grid_columnconfigure(0,weight=5)
mainWindow.grid_columnconfigure(1,weight=1)
mainWindow.grid_rowconfigure(0,weight=1)
mainWindow.grid_rowconfigure(1,weight=5)

# frame for sensor options
optionFrame = tkinter.LabelFrame(mainWindow, text='Sensor Options')
optionFrame.grid(row=0, column=0, sticky='ew', padx=5, pady=5)


checkBoxBar1 = checkBar.Checkbar(optionFrame, sensorGlobal.sensorNameArray[:5], button_width=10)
checkBoxBar1.pack(fill=tkinter.X)
checkBoxBar2 = checkBar.Checkbar(optionFrame, sensorGlobal.sensorNameArray[5:], button_width=10)
checkBoxBar2.pack(fill=tkinter.X)

buttonsFrame = tkinter.Frame(mainWindow)
buttonsFrame.grid(row=0, column=1, sticky='nsew', padx=5)
buttonsFrame.grid_rowconfigure(0, weight=1)
buttonsFrame.grid_rowconfigure(1, weight=1)
buttonsFrame.grid_rowconfigure(2, weight=1)
buttonsFrame.grid_rowconfigure(3, weight=1)
buttonsFrame.grid_columnconfigure(0, weight=1)
setButton = tkinter.Button(buttonsFrame, text='Set', command=new_reading)
setButton.grid(row=0, column=0, sticky='ew')
clearButton = tkinter.Button(buttonsFrame, text='Clear', command=clear_readings)
clearButton.grid(row=1, column=0, sticky='ew')
advancedButton = tkinter.Button(buttonsFrame, text='Advanced', command=advanced_options)
advancedButton.grid(row=2, column=0, sticky='ew')
quitButton = tkinter.Button(buttonsFrame, text='Quit', command=mainWindow.quit)
quitButton.grid(row=3, column=0, sticky='ew')

readingsFrame = tkinter.Frame(mainWindow)

# Sensor reading values
sums = []
for i in range(10):
    temp = tkinter.IntVar()
    sums.append(temp)

if __name__ == '__main__':
    start_gui()
