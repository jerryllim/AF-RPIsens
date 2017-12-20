import tkinter

mainWindow = tkinter.Tk()
mainWindow.title("Sensor Reading")
mainWindow.geometry('640x480-8-200')
mainWindow.grid_columnconfigure(0, weight=1)  # TODO add minsize
mainWindow.grid_rowconfigure(0, weight=10)
mainWindow.grid_rowconfigure(1, weight=1)

buttonFrame = tkinter.Frame(mainWindow)
buttonFrame.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)
advancedButton = tkinter.Button(buttonFrame, text='Advanced')  # TODO add command
advancedButton.pack(side=tkinter.LEFT)
quitButton = tkinter.Button(buttonFrame, text='Quit', command=mainWindow.quit)
quitButton.pack(side=tkinter.LEFT)

readingsFrame = tkinter.Frame(mainWindow)

mainWindow.mainloop()




