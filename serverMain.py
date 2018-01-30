import server.serverDB as serverDB
import server.serverGUI as serverGUI
import tkinter

root = tkinter.Tk()
root.title('Test')
root.minsize(width=1000, height=100)
main_frame = serverGUI.MainWindow(root)
main_frame.pack(fill=tkinter.BOTH, expand=tkinter.TRUE)
while True:
    try:
        root.mainloop()
    except UnicodeDecodeError:
        continue
    else:
        break