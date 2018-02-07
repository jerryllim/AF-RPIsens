import server.serverDB as serverDB
import server.serverGUI as serverGUI
import server.serverCommunication as serverCommunication
import tkinter


class ServerRun:
    def __init__(self):
        self.settings = serverDB.ServerSettings()
        self.database = serverDB.DatabaseManager(self.settings)
        self.communication = serverCommunication.CommunicationManager(self.settings, self.database)
        self.root = tkinter.Tk()
        self.root.title('afRPIsens Server')
        self.root.minsize(width=1000, height=400)
        self.main = serverGUI.MainWindow(self.root, self.settings)
        self.main.pack(fill=tkinter.BOTH, expand=tkinter.TRUE)

    def start_program(self):
        while True:
            try:
                self.root.mainloop()
            except UnicodeDecodeError:
                continue
            else:
                break

    def request_from_communication(self):
        self.communication.req_client()

    def reset_request_interval(self):
        self.communication.set_jobs()


if __name__ == '__main__':
    server = ServerRun()
    server.start_program()
