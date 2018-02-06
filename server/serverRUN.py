import server.serverDB as serverDB
import server.serverGUI as serverGUI
import server.serverCommunication as serverCommunication
import tkinter

if __name__ == '__main__':
    settings = serverDB.ServerSettings()
    database = serverDB.DatabaseManager()
    communication = serverCommunication.CommunicationManager()
    root = tkinter.Tk()
    root.title('afRPIsens Server')
    root.minsize(width=1000, height=400)
    main = serverGUI.MainWindow(root, settings)
    main.pack(fill=tkinter.BOTH, expand=tkinter.TRUE)
    while True:
        try:
            root.mainloop()
        except UnicodeDecodeError:
            continue
        else:
            break
