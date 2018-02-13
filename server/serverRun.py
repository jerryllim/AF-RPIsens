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
        self.main = serverGUI.MainWindow(self.root, self.settings, self)
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
        self.main.populate_live_table()

    def reset_request_interval(self):
        self.communication.set_jobs()
        self.main.schedule_refresh_table()


if __name__ == '__main__':
    server = ServerRun()
    server.start_program()
