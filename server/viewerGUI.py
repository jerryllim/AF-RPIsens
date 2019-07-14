import serverGUI
from PySide2 import QtWidgets

if __name__ == '__main__':
    # TODO use sys argv to get is_server
    app = QtWidgets.QApplication([])
    window = serverGUI.JamMainWindow(None, is_server=False)
    window.setWindowTitle('JAM')
    app.exec_()
