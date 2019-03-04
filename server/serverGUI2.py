import sqlite3
from PySide2 import QtCore, QtWidgets, QtGui


class ServerGUI(QtWidgets.QWidget):
    sensor_list = ['S01', 'S02', 'S03', 'S04', 'S05', 'S06', 'S07', 'S08', 'S09', 'S10', 'S11', 'S12', 'S13', 'S14',
                   'S15', 'E01', 'E02', 'E03', 'E04', 'E05']

    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.setWindowTitle('JAM Server')
        self.setGeometry(60, 60, 800, 500)

        # Connect to save
        self.conn = sqlite3.connect('serverTest.sqlite')
        self.conn.row_factory = self.dict_factory
        self.cursor = self.conn.cursor()

        # Tree View for the networks
        self.pis_treeview = QtWidgets.QTreeView(self)
        self.pis_model = QtGui.QStandardItemModel(0, 3, self)
        self.pis_treeview.setAlternatingRowColors(True)
        self.pis_treeview.setRootIsDecorated(False)

        # Button box for New, Edit, Delete
        button_box = QtWidgets.QVBoxLayout()
        new_btn = QtWidgets.QPushButton('New', self)
        new_btn.clicked.connect(self.new_item)
        button_box.addWidget(new_btn)
        edit_btn = QtWidgets.QPushButton('Edit', self)
        edit_btn.clicked.connect(self.edit_item)
        button_box.addWidget(edit_btn)
        del_btn = QtWidgets.QPushButton('Delete', self)
        del_btn.clicked.connect(self.delete_item)
        button_box.addWidget(del_btn)
        button_box.addStretch()

        # Last box
        vbox_layout = QtWidgets.QVBoxLayout()

        # Top form layout for Nick, IP & Mac
        self.main_lineedits = {}
        form_layout = QtWidgets.QFormLayout()
        nick_edit = QtWidgets.QLineEdit()
        self.main_lineedits['nick'] = nick_edit
        form_layout.addRow('Nickname:', nick_edit)
        ip_edit = QtWidgets.QLineEdit()
        self.main_lineedits['ip'] = ip_edit
        form_layout.addRow('IP:', ip_edit)
        mac_edit = QtWidgets.QLineEdit()
        self.main_lineedits['mac'] = mac_edit
        form_layout.addRow('Mac:', mac_edit)

        # Details scroll area with GridLayout
        details = QtWidgets.QScrollArea()
        details.setWidgetResizable(True)
        detail_widget = QtWidgets.QWidget()
        detail_grid = QtWidgets.QGridLayout(detail_widget)
        detail_grid.setColumnStretch(1, 1)
        detail_grid.setColumnStretch(2, 1)

        # TODO set this to be dynamic temp list
        machines = ['-', 'Exia', 'Kyrios', 'Dynames', 'Virtue', 'Nadleeh']
        columns = ['-', 'output', 'col1', 'col2', 'col3', 'col4', 'col5', 'col6', 'col7', 'col8', 'col9', 'col10']
        self.machine_comboboxes = {}
        self.col_comboboxes = {}
        for row, id_ in enumerate(self.sensor_list):
            label = QtWidgets.QLabel(id_)
            machine_combo = QtWidgets.QComboBox()
            machine_combo.addItems(machines)
            self.machine_comboboxes[id_] = machine_combo
            col_combo = QtWidgets.QComboBox()
            col_combo.insertItems(0, columns)
            self.col_comboboxes[id_] = col_combo
            detail_grid.addWidget(label, row, 0)
            detail_grid.addWidget(machine_combo, row, 1)
            detail_grid.addWidget(col_combo, row, 2)

        # Button box for the details
        detail_btn_box = QtWidgets.QHBoxLayout()
        save_btn = QtWidgets.QPushButton('Save', self)
        save_btn.clicked.connect(self.save_item)
        clear_btn = QtWidgets.QPushButton('Clear', self)
        clear_btn.clicked.connect(self.clear_all)
        detail_btn_box.addStretch()
        detail_btn_box.addWidget(save_btn)
        detail_btn_box.addWidget(clear_btn)

        vbox_layout.addLayout(form_layout)
        details.setWidget(detail_widget)
        vbox_layout.addWidget(details)
        vbox_layout.addLayout(detail_btn_box)

        self.hbox_layout = QtWidgets.QHBoxLayout()
        self.hbox_layout.addWidget(self.pis_treeview)
        self.hbox_layout.addLayout(button_box)
        self.hbox_layout.addLayout(vbox_layout)

        self.populate_network_view()

        self.setLayout(self.hbox_layout)

        self.set_all_enabled(False, False)
        self.show()

    def populate_network_view(self):
        self.pis_model.clear()
        self.pis_model.setHorizontalHeaderLabels(['Nickname', 'IP Address', 'Mac'])

        self.cursor.execute("SELECT nickname, ip, mac FROM pis;")

        for row in self.cursor:
            nick_item = QtGui.QStandardItem(row['nickname'])
            ip_item = QtGui.QStandardItem(row['ip'])
            mac_item = QtGui.QStandardItem(row['mac'])
            index = self.pis_model.rowCount()
            self.pis_model.setItem(index, 0, nick_item)
            self.pis_model.setItem(index, 1, ip_item)
            self.pis_model.setItem(index, 2, mac_item)

        self.pis_treeview.setModel(self.pis_model)
        header = self.pis_treeview.header()
        header.setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        for i in range(3):
            self.pis_treeview.resizeColumnToContents(i)

        self.pis_treeview.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.pis_treeview.setSortingEnabled(True)
        self.pis_treeview.activated.connect(self.set_fields)

    @staticmethod
    def dict_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    def set_fields(self, index):
        row = index.row()

        for col, id_ in enumerate(['nick', 'ip', 'mac']):
            item = self.pis_model.item(row, col)
            self.main_lineedits[id_].setText(item.text())

        self.set_all_enabled(False, False)

        ip = self.pis_model.item(row, 1).text()
        self.cursor.execute("SELECT * FROM pis WHERE ip = ? LIMIT 1", (ip,))
        ip_dict = self.cursor.fetchone()
        for key in self.sensor_list:
            if ip_dict.get('machine{}'.format(key)):
                self.machine_comboboxes[key].setCurrentText(ip_dict['machine{}'.format(key)])
            else:
                self.machine_comboboxes[key].setCurrentText('-')

            if ip_dict.get('colnum{}'.format(key)):
                self.col_comboboxes[key].setCurrentText(ip_dict['colnum{}'.format(key)])
            else:
                self.col_comboboxes[key].setCurrentText('-')

    def new_item(self):
        self.clear_all(edits=True)

        self.main_lineedits['nick'].setFocus()
        self.set_all_enabled(True, True)

    def edit_item(self):
        if len(self.main_lineedits['nick'].text()) > 0 and not self.main_lineedits['nick'].isEnabled():
            self.set_all_enabled(True, False)

    def delete_item(self):
        index = self.pis_treeview.selectedIndexes()[0]
        row = index.row()
        ip = self.pis_model.item(row, 1).text()

        try:
            self.cursor.execute("DELETE FROM pis WHERE ip = ? LIMIT 1", (ip, ))
            self.conn.commit()
        except sqlite3.Error as error:
            msgbox = QtWidgets.QMessageBox()
            msgbox.setText(str(error))
            msgbox.exec_()
        finally:
            self.populate_network_view()

    def save_item(self):
        ip = self.main_lineedits['ip'].text()
        nick = self.main_lineedits['nick'].text()
        mac = self.main_lineedits['mac'].text()

        try:
            if not self.main_lineedits['ip'].isEnabled():
                query = "UPDATE pis SET nickname = ?, mac = ? WHERE ip = ?"
            else:
                query = "INSERT INTO pis (nickname, mac, ip) VALUES (?, ?, ?)"

            self.cursor.execute(query, (nick, mac, ip))

            for key in self.sensor_list:
                machine = self.machine_comboboxes.get(key).currentText()
                colnum = self.col_comboboxes.get(key).currentText()

                self.cursor.execute("UPDATE pis SET machine{0} = ?, colnum{0} = ? WHERE ip = ?".format(key), (machine, colnum, ip))

                # TODO to continue
            self.conn.commit()
            self.new_item()
            self.populate_network_view()

        except sqlite3.Error as error:
            self.conn.rollback()
            print(error)  # TODO log error
            msgbox = QtWidgets.QMessageBox()
            msgbox.setText(str(error))
            msgbox.exec_()

    def set_all_enabled(self, enable, ip):
        for key, edit in self.main_lineedits.items():
            if key == 'ip':
                edit.setEnabled(ip)
            else:
                edit.setEnabled(enable)

        for combo in self.machine_comboboxes.values():
            combo.setEnabled(enable)

        for combo in self.col_comboboxes.values():
            combo.setEnabled(enable)

    def clear_all(self, edits=False):
        if edits:
            for edit in self.main_lineedits.values():
                edit.clear()
                edit.setText('')

        for combo in self.machine_comboboxes.values():
            combo.setCurrentIndex(0)

        for combo in self.col_comboboxes.values():
            combo.setCurrentIndex(0)


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    window = ServerGUI()
    app.exec_()
