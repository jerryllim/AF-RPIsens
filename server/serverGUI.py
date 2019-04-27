import csv
import logging
import datetime
import configparser
import serverDatabase, serverNetwork
from PySide2 import QtCore, QtWidgets, QtGui


class MachinesTab(QtWidgets.QWidget):
    def __init__(self, parent):
        QtWidgets.QWidget.__init__(self, parent)
        self.database_manager = self.parent().database_manager

        # Add Top box for insert
        self.insert_fields = {}
        self.hheaders = self.database_manager.get_machines_headers()
        insert_box = QtWidgets.QGridLayout()
        for col, head in enumerate(self.hheaders):
            label = QtWidgets.QLabel(head, self)
            edit = QtWidgets.QLineEdit(self)
            edit.setValidator(QtGui.QIntValidator())
            self.insert_fields[head] = edit
            insert_box.addWidget(label, 0, col)
            insert_box.setAlignment(label, QtCore.Qt.AlignCenter)
            insert_box.addWidget(edit, 1, col)
        self.insert_fields[self.hheaders[0]].setValidator(None)

        # Tree View & Models for Machines
        self.machine_model = QtGui.QStandardItemModel(0, 3, self)
        self.machine_table = QtWidgets.QTableView(self)
        self.machine_table.setModel(self.machine_model)
        self.machine_table.setAlternatingRowColors(True)
        self.machine_table.setSortingEnabled(True)
        self.machine_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        # v_header = self.machine_table.verticalHeader()
        # v_header.hide()
        # v_header.setSectionsMovable(True)
        self.populate_machines()

        # Add, Delete, Save button on right
        btn_box = QtWidgets.QVBoxLayout()
        add_btn = QtWidgets.QPushButton('Add', self)
        add_btn.clicked.connect(self.add_row)
        btn_box.addWidget(add_btn)
        del_btn = QtWidgets.QPushButton('Delete', self)
        del_btn.clicked.connect(self.delete_rows)
        btn_box.addWidget(del_btn)
        btn_box.addStretch()

        vbox_layout = QtWidgets.QVBoxLayout()
        vbox_layout.addLayout(insert_box)
        hbox_layout = QtWidgets.QHBoxLayout()
        hbox_layout.addWidget(self.machine_table)
        hbox_layout.addLayout(btn_box)
        vbox_layout.addLayout(hbox_layout)
        self.setLayout(vbox_layout)
        self.show()

    def populate_machines(self):
        self.machine_model.clear()
        # Set horizontal headers
        self.machine_model.setHorizontalHeaderLabels(self.hheaders)

        # Insert machines
        machines_list = self.database_manager.get_machines()
        item = QtGui.QStandardItem(None)
        self.machine_model.setItem(0, 0, item)
        self.machine_table.hideRow(0)

        for id_, row in enumerate(machines_list):
            idx = id_ + 1
            for col, value in enumerate(row):
                if value:
                    item = QtGui.QStandardItem()
                    item.setData(value, QtCore.Qt.EditRole)
                    if col == 0:
                        pass
                    self.machine_model.setItem(idx, col, item)

    def add_row(self):
        row = self.machine_model.rowCount()
        if self.insert_fields[self.hheaders[0]]:
            for col, key in enumerate(self.hheaders):
                value = self.insert_fields[key].text()
                if value:
                    item = QtGui.QStandardItem()
                    item.setData(value, QtCore.Qt.EditRole)
                    self.machine_model.setItem(row, col, item)
                self.insert_fields[key].clear()

    def delete_rows(self):
        rows = set()
        for idx in self.machine_table.selectedIndexes():
            rows.add(idx.row())
        if not rows:
            return

        row = min(rows)
        count = len(rows)
        choice = QtWidgets.QMessageBox.question(self, 'Delete', 'Delete {} rows?'.format(count),
                                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if choice == QtWidgets.QMessageBox.Yes:
            self.machine_model.removeRows(row, count)

    def save_table(self):
        machines_list = []

        for row in range(self.machine_model.rowCount()):
            machine_name = self.machine_model.item(row, 0).data(QtCore.Qt.EditRole)
            if not machine_name:
                continue
            items = [machine_name]
            for col in range(1, self.machine_model.columnCount()):
                item = self.machine_model.item(row, col)
                if item:
                    try:
                        text = int(item.data(QtCore.Qt.EditRole))
                    except ValueError:
                        text = None
                else:
                    text = None
                items.append(text)

            machines_list.append(items)

        self.database_manager.reinsert_machines(machines_list)
        self.populate_machines()

    def get_machines_model(self):
        return self.machine_model


class PiMachineDetails(QtWidgets.QWidget):
    def __init__(self, parent):
        QtWidgets.QWidget.__init__(self, parent)
        self.details = {}
        self.machines_model = self.parent().machines_model
        self.colnum_model = self.parent().colnum_model
        form_layout = QtWidgets.QFormLayout()

        # Machine
        machine_field = QtWidgets.QComboBox(self)
        machine_field.setModel(self.machines_model)
        self.details['machine'] = machine_field
        form_layout.addRow('Machine: ', machine_field)
        mac_field = QtWidgets.QLineEdit(self)
        self.details['mac'] = mac_field
        form_layout.addRow('Mac: ', mac_field)

        # Sensors
        for key in ['A1', 'A2', 'A3', 'A4', 'A5']:
            combo = QtWidgets.QComboBox(self)
            combo.setModel(self.colnum_model)
            self.details[key] = combo
            form_layout.addRow('{}: '.format(key), combo)

        # Sensors 2
        for key in ['B1', 'B2', 'B3', 'B4', 'B5']:
            combo = QtWidgets.QComboBox(self)
            combo.setModel(self.colnum_model)
            self.details[key] = combo
            form_layout.addRow('{}: '.format(key), combo)

        self.setLayout(form_layout)
        self.show()

    def enable_combos(self, enable):
        for combo in self.details.values():
            combo.setEnabled(enable)

    def set_fields(self, idx, values):
        for key in self.details:
            if key == 'mac':
                self.details[key].setText(values.get('{0}{1}'.format(key, idx)))
            else:
                self.details[key].setCurrentText(values.get('{0}{1}'.format(key, idx)))

    def get_values(self, idx):
        values = {}
        for key, value in self.details.items():
            newk = '{0}{1}'.format(key, idx)

            if type(value) is QtWidgets.QLineEdit:
                if value.text() == '':
                    values[newk] = None
                else:
                    values[newk] = value.text()
            else:
                if value.currentText() == '':
                    values[newk] = None
                else:
                    values[newk] = value.currentText()

        return values

    def clear_fields(self):
        if self.details['machine'].isEnabled():
            for field in self.details.values():
                if type(field) is QtWidgets.QLineEdit:
                    field.setText('')
                else:
                    field.setCurrentIndex(0)


class PisTab(QtWidgets.QWidget):
    sensor_list = ['machine', 'mac', 'A1', 'A2', 'A3', 'A4', 'A5', 'B1', 'B2', 'B3', 'B4', 'B5']

    def __init__(self, parent, machines_model):
        QtWidgets.QWidget.__init__(self, parent)
        self.database_manager = self.parent().database_manager
        self.pis_dict = self.database_manager.get_pis()

        # Tree View for the Pis
        self.pis_model = QtGui.QStandardItemModel(0, 3, self)
        self.pis_treeview = QtWidgets.QTreeView(self)
        self.pis_treeview.setModel(self.pis_model)
        self.pis_treeview.setAlternatingRowColors(True)
        self.pis_treeview.setRootIsDecorated(False)
        self.pis_treeview.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.pis_treeview.setSortingEnabled(True)
        self.pis_treeview.activated.connect(self.set_fields)
        self.populate_pis()
        header = self.pis_treeview.header()
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QtWidgets.QHeaderView.ResizeToContents)

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

        # Right box with details
        vbox_layout = QtWidgets.QVBoxLayout()

        # Top form layout for Nick, IP & Port
        self.main_lineedits = {}
        form_layout = QtWidgets.QFormLayout()
        nick_edit = QtWidgets.QLineEdit(self)
        rx = QtCore.QRegExp('([A-Za-z0-9_]){1,15}')
        validator = QtGui.QRegExpValidator(rx)
        nick_edit.setValidator(validator)
        self.main_lineedits['nick'] = nick_edit
        form_layout.addRow('Nickname:', nick_edit)
        ip_edit = QtWidgets.QLineEdit(self)
        ip_rx = QtCore.QRegExp('((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(\.|$)){4}')
        ip_validator = QtGui.QRegExpValidator(ip_rx)
        ip_edit.setValidator(ip_validator)
        self.main_lineedits['ip'] = ip_edit
        form_layout.addRow('IP:', ip_edit)
        port_edit = QtWidgets.QLineEdit(self)
        self.main_lineedits['port'] = port_edit
        form_layout.addRow('Port:', port_edit)

        # Details tab
        self.machines_model = machines_model
        self.colnum_model = QtCore.QStringListModel(self)
        column = [None]
        for row in self.database_manager.custom_query("SHOW COLUMNS FROM jam_current_table WHERE field LIKE 'col%' "
                                                      "OR field LIKE 'output%';"):
            column.append(row[0])

        self.colnum_model.setStringList(column)
        self.machine_tabs = {}
        tab_widget = QtWidgets.QTabWidget(self)
        for idx in range(1, 4):
            tab = PiMachineDetails(self)
            self.machine_tabs[idx] = tab
            tab_widget.addTab(tab, '{}'.format(idx))

        # Button box for details
        detail_btn_box = QtWidgets.QHBoxLayout()
        set_btn = QtWidgets.QPushButton('Set', self)
        set_btn.clicked.connect(self.set_item)
        clear_btn = QtWidgets.QPushButton('Clear', self)
        clear_btn.clicked.connect(self.clear_all)
        detail_btn_box.addStretch()
        detail_btn_box.addWidget(clear_btn)
        detail_btn_box.addWidget(set_btn)

        vbox_layout.addLayout(form_layout)
        vbox_layout.addWidget(tab_widget)
        vbox_layout.addLayout(detail_btn_box)
        v_widget = QtWidgets.QWidget()
        v_widget.setLayout(vbox_layout)
        v_widget.setMaximumWidth(300)

        hbox_layout = QtWidgets.QHBoxLayout()
        hbox_layout.addWidget(self.pis_treeview)
        hbox_layout.addLayout(button_box)
        hbox_layout.addWidget(v_widget)
        self.setLayout(hbox_layout)

        self.set_all_enabled(False, False)
        self.show()

    def populate_pis(self):
        self.pis_model.clear()
        self.pis_model.setHorizontalHeaderLabels(['Nickname', 'IP Address', 'Port', 'Machine1', 'Machine2', 'Machine3',
                                                  'last updated'])

        for ip in self.pis_dict.keys():
            nick_item = QtGui.QStandardItem(self.pis_dict[ip].get('nick'))
            ip_item = QtGui.QStandardItem(ip)
            port_item = QtGui.QStandardItem(self.pis_dict[ip].get('port'))
            machine1_item = QtGui.QStandardItem(self.pis_dict[ip].get('machine1'))
            machine2_item = QtGui.QStandardItem(self.pis_dict[ip].get('machine2'))
            machine3_item = QtGui.QStandardItem(self.pis_dict[ip].get('machine3'))
            last_update_time = self.parent().database_manager.get_last_updates(ip)[0]
            if last_update_time:
                last_update_item = QtGui.QStandardItem(last_update_time.strftime("%d/%m/%y %H:%M"))
            else:
                last_update_item = QtGui.QStandardItem('-')
            index = self.pis_model.rowCount()
            self.pis_model.setItem(index, 0, nick_item)
            self.pis_model.setItem(index, 1, ip_item)
            self.pis_model.setItem(index, 2, port_item)
            self.pis_model.setItem(index, 3, machine1_item)
            self.pis_model.setItem(index, 4, machine2_item)
            self.pis_model.setItem(index, 5, machine3_item)
            self.pis_model.setItem(index, 6, last_update_item)

    def set_fields(self, index):
        row = index.row()

        self.set_all_enabled(False, False)

        ip = self.pis_model.item(row, 1).text()
        self.main_lineedits['ip'].setText(ip)
        self.main_lineedits['nick'].setText(self.pis_dict[ip]['nick'])
        self.main_lineedits['port'].setText(self.pis_dict[ip]['port'])

        for key in self.machine_tabs:
            self.machine_tabs[key].set_fields(key, self.pis_dict[ip])

    def new_item(self):
        self.clear_all(edits=True)
        self.main_lineedits['nick'].setFocus()
        self.set_all_enabled(True, True)

    def edit_item(self):
        if len(self.main_lineedits['ip'].text()) > 0 and not self.main_lineedits['nick'].isEnabled():
            self.set_all_enabled(True, False)

    def delete_item(self):
        index = self.pis_treeview.selectedIndexes()[0]
        row = index.row()
        nick = self.pis_model.item(row, 0).text()
        ip = self.pis_model.item(row, 1).text()

        choice = QtWidgets.QMessageBox.question(self, 'Delete', 'Delete {0} ({1})?'.format(nick, ip))
        if choice == QtWidgets.QMessageBox.Yes:
            self.pis_dict.pop(ip, None)
            self.populate_pis()

    def set_item(self):
        ip = self.main_lineedits['ip'].text()
        self.pis_dict[ip] = {}
        for key in ['nick', 'port']:
            self.pis_dict[ip][key] = self.main_lineedits[key].text()

        for idx in self.machine_tabs.keys():
            self.pis_dict[ip].update(self.machine_tabs[idx].get_values(idx))

        self.populate_pis()
        self.clear_all(True)
        self.set_all_enabled(False, False)

    def save_items(self):
        pis_row = []

        for ip, values in self.pis_dict.items():
            pi_row = [ip, int(values['port']), values['nick']]

            for i in range(1, 4):
                for key in self.sensor_list:
                    pi_row.append(values['{0}{1}'.format(key, i)])

            pis_row.append(pi_row)

        self.database_manager.saved_all_pis(pis_row)

    def set_all_enabled(self, enable, ip):
        for key, edit in self.main_lineedits.items():
            if key == 'ip':
                edit.setEnabled(ip)
            else:
                edit.setEnabled(enable)

        for tab in self.machine_tabs.values():
            tab.enable_combos(enable)

    def clear_all(self, edits=False):
        if edits:
            for edit in self.main_lineedits.values():
                edit.clear()
                edit.setText('')

        for tab in self.machine_tabs.values():
            tab.clear_fields()


class EmployeesTab(QtWidgets.QWidget):
    def __init__(self, parent):
        QtWidgets.QWidget.__init__(self, parent)
        self.database_manager = self.parent().database_manager
        self.deleted_emps = set()

        # Insertion fields
        insert_grid = QtWidgets.QGridLayout()
        self.insert_edits = {}
        id_label = QtWidgets.QLabel('ID: ', self)
        id_edit = QtWidgets.QLineEdit(self)
        rx = QtCore.QRegExp('([A-Za-z0-9]){1,6}')
        validator = QtGui.QRegExpValidator(rx)
        id_edit.setMaximumWidth(70)
        id_edit.setValidator(validator)
        self.insert_edits['id'] = id_edit
        name_label = QtWidgets.QLabel('Name: ', self)
        name_edit = QtWidgets.QLineEdit(self)
        name_edit.setMaxLength(20)
        self.insert_edits['name'] = name_edit
        insert_grid.addWidget(id_label, 0, 0)
        insert_grid.addWidget(id_edit, 0, 1)
        insert_grid.addWidget(name_label, 0, 2)
        insert_grid.addWidget(name_edit, 0, 3)

        # Tree View
        self.emp_model = QtGui.QStandardItemModel(0, 3, self)
        self.emp_treeview = QtWidgets.QTreeView(self)
        self.emp_treeview.setModel(self.emp_model)
        self.emp_treeview.setAlternatingRowColors(True)
        self.emp_treeview.setRootIsDecorated(False)
        self.emp_treeview.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.emp_treeview.setSortingEnabled(True)
        self.emp_treeview.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        header = self.emp_treeview.header()
        header.setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        for i in range(3):
            self.emp_treeview.resizeColumnToContents(i)
        self.populate_employees()

        vbox_layout = QtWidgets.QVBoxLayout()
        vbox_layout.addLayout(insert_grid)
        vbox_layout.addWidget(self.emp_treeview)

        # Buttons
        buttons_box = QtWidgets.QVBoxLayout()
        add_btn = QtWidgets.QPushButton('Add', self)
        add_btn.clicked.connect(self.add_emp)
        buttons_box.addWidget(add_btn)
        del_btn = QtWidgets.QPushButton('Delete', self)
        del_btn.clicked.connect(self.delete_emps)
        buttons_box.addWidget(del_btn)
        import_btn = QtWidgets.QPushButton('Import', self)
        import_btn.clicked.connect(self.import_csv)
        buttons_box.addWidget(import_btn)
        buttons_box.addStretch()

        hbox_layout = QtWidgets.QHBoxLayout()
        hbox_layout.addLayout(vbox_layout)
        hbox_layout.addLayout(buttons_box)

        self.setLayout(hbox_layout)
        self.show()

    def populate_employees(self):
        self.emp_model.clear()
        self.emp_model.setHorizontalHeaderLabels(['ID', 'Name', 'last modified'])

        for row in self.database_manager.get_emps():
            id_item = QtGui.QStandardItem(row[0])
            name_item = QtGui.QStandardItem(row[1])
            date_item = QtGui.QStandardItem(str(row[2]))
            index = self.emp_model.rowCount()
            self.emp_model.setItem(index, 0, id_item)
            self.emp_model.setItem(index, 1, name_item)
            self.emp_model.setItem(index, 2, date_item)

    def add_emp(self):
        if len(self.insert_edits['id'].text()) > 0:
            id_ = self.insert_edits['id'].text()
            name = self.insert_edits['name'].text()

            self.deleted_emps.discard(id_)
            index = self.emp_model.rowCount()
            self.emp_model.setItem(index, 0, QtGui.QStandardItem(id_))
            self.emp_model.setItem(index, 1, QtGui.QStandardItem(name))
            self.emp_model.setItem(index, 2, QtGui.QStandardItem('Now'))
            self.emp_treeview.scrollToBottom()

            self.insert_edits['id'].clear()
            self.insert_edits['name'].clear()

    def delete_emps(self):
        rows = set()
        for idx in self.emp_treeview.selectedIndexes():
            rows.add(idx.row())
            self.deleted_emps.add(self.emp_model.item(idx.row(), 0).text())
        if not rows:
            return

        row = min(rows)
        count = len(rows)
        choice = QtWidgets.QMessageBox.question(self, 'Delete', 'Delete {} rows?'.format(count),
                                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if choice == QtWidgets.QMessageBox.Yes:
            self.emp_model.removeRows(row, count)

    def import_csv(self):
        path = QtWidgets.QFileDialog.getOpenFileName(self, 'Open CSV', '', 'CSV(*.csv)')
        if path[0] != '':
            with open(path[0], 'r') as csv_file:
                csv_reader = csv.reader(csv_file)

                for row in csv_reader:
                    self.deleted_emps.discard(row[0])
                    idx = self.emp_model.rowCount()
                    self.emp_model.setItem(idx, 0, QtGui.QStandardItem(row[0]))
                    self.emp_model.setItem(idx, 1, QtGui.QStandardItem(row[1]))
                    self.emp_model.setItem(idx, 2, QtGui.QStandardItem('Now'))

            self.emp_treeview.scrollToBottom()

    def save_emp(self):
        emp_rows = []

        for row in range(self.emp_model.rowCount()):
            emp_row = []
            if self.emp_model.item(row, 2).text() == 'Now':
                emp_row.append(self.emp_model.item(row, 0).text())
                emp_row.append(self.emp_model.item(row, 1).text())
                emp_rows.append(emp_row)

        self.database_manager.insert_emps(emp_rows)
        if self.deleted_emps:
            self.database_manager.mark_to_delete_emp(self.deleted_emps)


class MiscTab(QtWidgets.QWidget):
    def __init__(self, parent):
        QtWidgets.QWidget.__init__(self, parent)
        self.database_manager = self.parent().database_manager
        self.config = configparser.ConfigParser()
        self.config.read('jam.ini')

        # Network group
        self.network_fields = {}
        network_box = QtWidgets.QGroupBox('Network', self)
        network_layout = QtWidgets.QGridLayout()
        network_layout.setColumnMinimumWidth(0, 100)
        network_box.setLayout(network_layout)
        ip_label = QtWidgets.QLineEdit(network_box)
        ip_label.setReadOnly(True)
        ip_label.setText(serverNetwork.NetworkManager.get_ip_add())
        network_layout.addWidget(QtWidgets.QLabel('Server IP: ', network_box), 0, 0, QtCore.Qt.AlignRight)
        network_layout.addWidget(ip_label, 0, 1)
        port_label = QtWidgets.QLabel('Port: ', network_box)
        port_edit = QtWidgets.QLineEdit(network_box)
        port_edit.setText(self.config.get('Network', 'port'))
        self.network_fields['port'] = port_edit
        network_layout.addWidget(port_label, 1, 0, QtCore.Qt.AlignRight)
        network_layout.addWidget(port_edit, 1, 1)
        dur_label = QtWidgets.QLabel('Polling Interval: ', network_box)
        poll_spinbox = QtWidgets.QSpinBox(network_box)
        poll_spinbox.setMinimum(1)
        poll_spinbox.setMaximum(90)
        self.network_fields['interval'] = poll_spinbox
        poll_spinbox.setValue(self.config.getint('Network', 'interval'))
        dur_label2 = QtWidgets.QLabel('minutes', network_box)
        network_layout.addWidget(dur_label, 2, 0, QtCore.Qt.AlignRight)
        network_layout.addWidget(poll_spinbox, 2, 1)
        network_layout.addWidget(dur_label2, 2, 2)
        req_btn = QtWidgets.QPushButton('Request now', network_box)
        req_btn.clicked.connect(self.parent().parent().network_manager.request_jam)
        network_layout.setAlignment(QtCore.Qt.AlignLeft)
        network_layout.addWidget(req_btn, 2, 3)

        # Database group
        self.db_edits = {}
        db_box = QtWidgets.QGroupBox('Database', self)
        db_layout = QtWidgets.QGridLayout()
        db_layout.setColumnMinimumWidth(0, 100)
        db_box.setLayout(db_layout)
        host_label = QtWidgets.QLabel('TCP/IP Server: ', db_box)
        host_edit = QtWidgets.QLineEdit(db_box)
        self.db_edits['host'] = host_edit
        host_edit.setText(self.config.get('Database', 'host'))
        port_label = QtWidgets.QLabel('Port: ', db_box)
        port_edit = QtWidgets.QLineEdit(db_box)
        self.db_edits['port'] = port_edit
        port_edit.setText(self.config.get('Database', 'port'))
        port_edit.setMaximumWidth(100)
        db_layout.addWidget(host_label, 0, 0, QtCore.Qt.AlignRight)
        db_layout.addWidget(host_edit, 0, 1)
        db_layout.addWidget(port_label, 0, 2, QtCore.Qt.AlignRight)
        db_layout.addWidget(port_edit, 0, 3)
        user_label = QtWidgets.QLabel('User: ', db_box)
        user_edit = QtWidgets.QLineEdit(db_box)
        self.db_edits['user'] = user_edit
        user_edit.setText(self.config.get('Database', 'user'))
        db_layout.addWidget(user_label, 1, 0, QtCore.Qt.AlignRight)
        db_layout.addWidget(user_edit, 1 ,1)
        pass_label = QtWidgets.QLabel('Password: ', db_box)
        pass_edit = QtWidgets.QLineEdit(db_box)
        self.db_edits['password'] = pass_edit
        pass_edit.setText(self.config.get('Database', 'password'))
        db_layout.addWidget(pass_label, 2, 0, QtCore.Qt.AlignRight)
        db_layout.addWidget(pass_edit, 2, 1)
        db_label = QtWidgets.QLabel('Database: ', db_box)
        db_edit = QtWidgets.QLineEdit(db_box)
        self.db_edits['db'] = db_edit
        db_edit.setText(self.config.get('Database', 'db'))
        db_layout.addWidget(db_label, 3, 0, QtCore.Qt.AlignRight)
        db_layout.addWidget(db_edit, 3, 1)
        db_test_btn = QtWidgets.QPushButton('Test', db_box)
        db_test_btn.clicked.connect(self.test_db)
        db_layout.addWidget(db_test_btn, 3, 3)

        # Import Export group
        import_box = QtWidgets.QGroupBox('Import', self)
        import_layout = QtWidgets.QGridLayout()
        import_box.setLayout(import_layout)
        self.import_fields = {}
        import_time = QtWidgets.QTimeEdit(import_box)
        import_time.setDisplayFormat('hh:mm')
        import_t = QtCore.QTime.fromString(self.config.get('Import', 'time'))
        import_time.setTime(import_t)
        self.import_fields['time'] = import_time
        import_layout.addWidget(QtWidgets.QLabel('Start time: '), 0, 0, QtCore.Qt.AlignRight)
        import_layout.addWidget(import_time, 0, 1)
        import_hour = QtWidgets.QSpinBox(import_box)
        import_hour.setMinimum(0)
        import_hour.setMaximum(23)
        self.import_fields['hour'] = import_hour
        import_hour.setValue(self.config.getint('Import', 'hour'))
        import_minute = QtWidgets.QSpinBox(import_box)
        import_minute.setMinimum(0)
        import_minute.setMaximum(59)
        self.import_fields['minute'] = import_minute
        import_minute.setValue(self.config.getint('Import', 'minute'))
        import_layout.addWidget(QtWidgets.QLabel('Repeat every: '), 1, 0, QtCore.Qt.AlignRight)
        import_layout.addWidget(import_hour, 1, 1)
        import_layout.addWidget(QtWidgets.QLabel('hours'), 1, 2)
        import_layout.addWidget(import_minute, 1, 3)
        import_layout.addWidget(QtWidgets.QLabel('minutes'), 1, 4)
        import_layout.addWidget(QtWidgets.QLabel('Import path: '), 2, 0, QtCore.Qt.AlignRight)
        import_edit = QtWidgets.QLineEdit(self)
        self.import_fields['path'] = import_edit
        import_edit.setText(self.config.get('Import', 'path'))
        import_edit.setReadOnly(True)
        import_layout.addWidget(import_edit, 2, 1, 1, 3)
        import_button = QtWidgets.QPushButton('...', self)
        import_button.clicked.connect(self.import_from)
        import_layout.addWidget(import_button, 2, 4)

        export_box = QtWidgets.QGroupBox('Export', self)
        export_layout = QtWidgets.QGridLayout()
        export_box.setLayout(export_layout)
        self.export_fields = {}
        export_time = QtWidgets.QTimeEdit(export_box)
        export_time.setDisplayFormat('hh:mm')
        export_t = QtCore.QTime.fromString(self.config.get('Export', 'time'))
        export_time.setTime(export_t)
        self.export_fields['time'] = export_time
        export_layout.addWidget(QtWidgets.QLabel('Start time: '), 0, 0, QtCore.Qt.AlignRight)
        export_layout.addWidget(export_time, 0, 1)
        export_hour = QtWidgets.QSpinBox(export_box)
        export_hour.setMinimum(0)
        export_hour.setMaximum(23)
        export_hour.setValue(self.config.getint('Export', 'hour'))
        self.export_fields['hour'] = export_hour
        export_minute = QtWidgets.QSpinBox(export_box)
        export_minute.setMinimum(0)
        export_minute.setMaximum(59)
        export_minute.setValue(self.config.getint('Export', 'minute'))
        self.export_fields['minute'] = export_minute
        export_layout.addWidget(QtWidgets.QLabel('Repeat every: '), 1, 0, QtCore.Qt.AlignRight)
        export_layout.addWidget(export_hour, 1, 1)
        export_layout.addWidget(QtWidgets.QLabel('hours'), 1, 2)
        export_layout.addWidget(export_minute, 1, 3)
        export_layout.addWidget(QtWidgets.QLabel('minutes'), 1, 4)
        export_layout.addWidget(QtWidgets.QLabel('Export path: '), 2, 0, QtCore.Qt.AlignRight)
        export_edit = QtWidgets.QLineEdit(self)
        self.export_fields['path'] = export_edit
        export_edit.setText(self.config.get('Export', 'path'))
        export_edit.setReadOnly(True)
        export_layout.addWidget(export_edit, 2, 1, 1, 3)
        export_button = QtWidgets.QPushButton('...', self)
        export_button.clicked.connect(self.export_to)
        export_layout.addWidget(export_button, 2, 4)

        # Set data management configs
        self.data_fields = {}
        data_box = QtWidgets.QGroupBox('Data')
        data_layout = QtWidgets.QGridLayout()
        data_box.setLayout(data_layout)
        data_start_label = QtWidgets.QLabel('Start week on', data_box)
        data_start_day = QtWidgets.QComboBox(data_box)
        data_start_day.addItems(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])
        data_start_day.setCurrentIndex(self.config.getint('Data', 'day'))
        data_start_time = QtWidgets.QTimeEdit(QtCore.QTime.fromString(self.config.get('Data', 'time')), data_box)
        data_start_time.setDisplayFormat('hh:mm')
        self.data_fields['day'] = data_start_day
        self.data_fields['time'] = data_start_time
        data_layout.addWidget(data_start_label, 0, 0, QtCore.Qt.AlignRight)
        data_layout.addWidget(data_start_day, 0, 1)
        data_layout.addWidget(data_start_time, 0, 2)
        data_archive_label = QtWidgets.QLabel('Archive after ', data_box)
        data_archive_spin = QtWidgets.QSpinBox(data_box)
        data_archive_spin.setMaximum(6)
        data_archive_spin.setMinimum(1)
        data_archive_spin.setValue(self.config.getint('Data', 'archive'))
        data_archive_spin.valueChanged.connect(self.set_delete_spin_min)
        data_archive_label2 = QtWidgets.QLabel(' months', data_box)
        self.data_fields['archive'] = data_archive_spin
        data_layout.addWidget(data_archive_label, 1, 0, QtCore.Qt.AlignRight)
        data_layout.addWidget(data_archive_spin, 1, 1)
        data_layout.addWidget(data_archive_label2, 1, 2)
        data_delete_label = QtWidgets.QLabel('Delete archive after ', data_box)
        data_delete_spin = QtWidgets.QSpinBox(data_box)
        data_delete_spin.setMaximum(12)
        data_delete_spin.setMinimum(2)
        data_delete_spin.setMinimum(2)
        data_delete_spin.setValue(self.config.getint('Data', 'delete'))
        data_delete_label2 = QtWidgets.QLabel(' months', data_box)
        self.data_fields['delete'] = data_delete_spin
        data_layout.addWidget(data_delete_label, 2, 0, QtCore.Qt.AlignRight)
        data_layout.addWidget(data_delete_spin, 2, 1)
        data_layout.addWidget(data_delete_label2, 2, 2)

        # Shift group
        shift_box = QtWidgets.QGroupBox('Shifts', self)
        shift_layout = QtWidgets.QGridLayout()
        shift_box.setLayout(shift_layout)
        shift_layout.addWidget(QtWidgets.QLabel('Shift'), 0, 0)
        shift_layout.addWidget(QtWidgets.QLabel('Start time'), 0, 1)
        shift_layout.addWidget(QtWidgets.QLabel('End time'), 0, 2)
        self.shift_checks = {}
        self.shift_starts = {}
        self.shift_ends = {}
        for col in range(1, 5):
            check = QtWidgets.QCheckBox('Shift {}'.format(col), shift_box)
            check.setChecked(self.config.getboolean('Shift', 'shift{}_enable'.format(col)))
            check.stateChanged.connect(lambda state, idx=col: self.shift_check_state(state, idx))
            self.shift_checks[col] = check
            start = QtWidgets.QTimeEdit(shift_box)
            start.setDisplayFormat('hh:mm')
            start_time = QtCore.QTime.fromString(self.config.get('Shift', 'shift{}_start'.format(col)))
            start.setTime(start_time)
            self.shift_starts[col] = start
            end = QtWidgets.QTimeEdit(shift_box)
            end.setDisplayFormat('hh:mm')
            end_time = QtCore.QTime.fromString(self.config.get('Shift', 'shift{}_end'.format(col)))
            end.setTime(end_time)
            self.shift_ends[col] = end
            shift_layout.addWidget(check, col, 0)
            shift_layout.addWidget(start, col, 1)
            shift_layout.addWidget(end, col, 2)
            self.shift_check_state(check.checkState(), col)

        # Log group
        # TODO add log group - log level & file name

        vbox_layout = QtWidgets.QVBoxLayout()
        vbox_layout.addWidget(network_box)
        vbox_layout.addWidget(db_box)
        vbox_layout.addWidget(import_box)
        vbox_layout.addWidget(export_box)
        vbox_layout.addWidget(data_box)
        vbox_layout.addWidget(shift_box)
        vbox_layout.addStretch()

        widget = QtWidgets.QWidget(self)
        widget.setLayout(vbox_layout)
        scroll_area = QtWidgets.QScrollArea(self)
        scroll_area.setWidget(widget)
        scroll_area.setWidgetResizable(True)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(scroll_area)
        self.setLayout(layout)
        self.show()

    def set_delete_spin_min(self, value):
        self.data_fields['delete'].setMinimum(value)

    def shift_check_state(self, state, idx):
        state = bool(state)
        self.shift_starts[idx].setEnabled(state)
        self.shift_ends[idx].setEnabled(state)

    def test_db(self):
        success = self.database_manager.test_db_connection(self.db_edits['host'].text(), self.db_edits['port'].text(),
                                                           self.db_edits['user'].text(),
                                                           self.db_edits['password'].text(), self.db_edits['db'].text())
        msgbox = QtWidgets.QMessageBox()
        msgbox.setMinimumWidth(500)
        if success:
            msgbox.setText('Connection Successful')
        else:
            msgbox.setText('Connection Failed')
        msgbox.exec_()

    def import_from(self):
        path = QtWidgets.QFileDialog.getOpenFileName(self, 'Select file to import', '', 'CSV(*.csv)')
        if path[0] != '':
            self.import_fields['import'].setText(path[0])

    def export_to(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(self, 'Set export location', '')
        if path != '':
            self.import_fields['export'].setText(path)

    def save_misc(self):
        for key in self.db_edits.keys():
            self.config.set('Database', key, self.db_edits[key].text())

        self.config.set('Data', 'day', str(self.data_fields['day'].currentIndex()))
        for key in ['time', 'archive', 'delete']:
            self.config.set('Data', key, str(self.data_fields[key].text()))

        for col in range(1, 5):
            self.config.set('Shift', 'shift{}_enable'.format(col), str(self.shift_checks[col].isChecked()))
            self.config.set('Shift', 'shift{}_start'.format(col), str(self.shift_starts[col].text()))
            self.config.set('Shift', 'shift{}_end'.format(col), str(self.shift_ends[col].text()))

        self.config.set('Network', 'port', self.network_fields['port'].text())
        self.config.set('Network', 'interval', str(self.network_fields['interval'].text()))

        for key, line_edit in self.import_fields.items():
            self.config.set('Import', key, line_edit.text())

        for key, line_edit in self.export_fields.items():
            self.config.set('Export', key, line_edit.text())

        with open('jam.ini', 'w') as configfile:
            self.config.write(configfile)


class ConfigurationWidget(QtWidgets.QWidget):
    def __init__(self, parent, database_manager):
        QtWidgets.QWidget.__init__(self, parent)
        config = configparser.ConfigParser()
        config.read('jam.ini')
        self.database_manager = database_manager

        self.setWindowTitle('Configurations')
        self.setMinimumWidth(800)

        self.tab_widget = QtWidgets.QTabWidget()
        self.machines_tab = MachinesTab(self)
        machines = self.machines_tab.get_machines_model()
        self.pis_tab = PisTab(self, machines)
        self.emp_tab = EmployeesTab(self)
        self.misc_tab = MiscTab(self)
        self.tab_widget.addTab(self.machines_tab, 'Machines')
        self.tab_widget.addTab(self.pis_tab, 'Pis')
        self.tab_widget.addTab(self.emp_tab, 'Employees')
        self.tab_widget.addTab(self.misc_tab, 'Miscellaneous')

        btn_box = QtWidgets.QHBoxLayout()
        save_btn = QtWidgets.QPushButton('Save', self)
        save_btn.setAutoDefault(False)
        save_btn.clicked.connect(self.save_all)
        cancel_btn = QtWidgets.QPushButton('Cancel', self)
        cancel_btn.setAutoDefault(False)
        cancel_btn.clicked.connect(self.cancel_changes)
        btn_box.addStretch()
        btn_box.addWidget(cancel_btn)
        btn_box.addWidget(save_btn)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.tab_widget)
        layout.addLayout(btn_box)
        self.setLayout(layout)
        # self.show()

    def save_all(self):
        self.pis_tab.save_items()
        self.emp_tab.save_emp()
        self.machines_tab.save_table()
        self.misc_tab.save_misc()
        self.parent().done(0)
        self.parent().parent().settings.update()

    def cancel_changes(self):
        self.parent().done(0)


class DisplayTable(QtWidgets.QWidget):
    def __init__(self, parent, database_manager):
        QtWidgets.QWidget.__init__(self, parent)
        config = configparser.ConfigParser()
        config.read('jam.ini')
        self.database_manager = database_manager

        self.table_model = QtGui.QStandardItemModel(3, 10)

        self.table_view = QtWidgets.QTableView()
        self.table_view.setModel(self.table_model)
        self.table_view.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table_view.setAlternatingRowColors(True)
        v_header = self.table_view.verticalHeader()
        v_header.hide()

        hbox = QtWidgets.QHBoxLayout()
        date_label = QtWidgets.QLabel('Date: ')
        self.date_spin = QtWidgets.QDateEdit()
        self.date_spin.setDate(QtCore.QDate.currentDate())
        start_label = QtWidgets.QLabel('Start: ')
        self.start_spin = QtWidgets.QTimeEdit(QtCore.QTime(7, 0))
        self.start_spin.setDisplayFormat('HH:mm')
        hour_label = QtWidgets.QLabel('Hours: ')
        self.hour_spin = QtWidgets.QSpinBox()
        self.hour_spin.setMinimum(1)
        self.hour_spin.setMaximum(24)
        populate_btn = QtWidgets.QPushButton('Refresh')
        populate_btn.clicked.connect(self.populate_table)
        hbox.addWidget(date_label)
        hbox.addWidget(self.date_spin)
        hbox.addWidget(start_label)
        hbox.addWidget(self.start_spin)
        hbox.addWidget(hour_label)
        hbox.addWidget(self.hour_spin)
        hbox.addWidget(populate_btn)

        box_layout = QtWidgets.QVBoxLayout()
        box_layout.addLayout(hbox)
        box_layout.addWidget(self.table_view)
        self.setLayout(box_layout)
        self.show()

    def populate_table(self):
        self.table_model.clear()

        table_hheaders = ['Machine', 'Sum']
        date = self.date_spin.date().toPython()
        start_time = self.start_spin.time().toPython()
        start = datetime.datetime.combine(date, start_time)
        end = start + datetime.timedelta(hours=int(self.hour_spin.text()))
        if start.hour >= end.hour:
            for i in range(start.hour, 24):
                table_hheaders.append('{:02d}'.format(i))
            for i in range(end.hour):
                table_hheaders.append('{:02d}'.format(i))
        else:
            for i in range(start.hour, end.hour):
                table_hheaders.append('{:02d}'.format(i))
        self.table_model.setHorizontalHeaderLabels(table_hheaders)

        output_list = []
        table_vheaders = self.database_manager.get_machine_names()
        for row, machine in enumerate(table_vheaders):
            output_list.append([0] * len(table_hheaders))
            self.table_model.setItem(row, 0, QtGui.QStandardItem(machine))

        outputs = self.database_manager.get_output(start.isoformat(timespec='minutes'),
                                                   end.isoformat(timespec='minutes'))
        for row in outputs:
            col = table_hheaders.index('{:02d}'.format(row[2]))
            idx = table_vheaders.index(row[0])
            output_list[idx][col] = row[3]

        targets_dict = self.database_manager.get_machine_targets('output')

        for idx, row in enumerate(output_list):
            target = targets_dict[table_vheaders[idx]]
            for col, value in enumerate(row):
                if col < 2:
                    continue
                item = QtGui.QStandardItem(str(value))
                if target and value <= target:
                    font = QtGui.QFont()
                    font.setBold(True)
                    item.setForeground(QtGui.QBrush(QtGui.QColor(255, 0, 0)))
                    item.setFont(font)
                self.table_model.setItem(idx, col, item)
            self.table_model.setItem(idx, 1, QtGui.QStandardItem(str(sum(row))))


class JamMainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent):
        QtWidgets.QMainWindow.__init__(self, parent)
        self.logger = logging.getLogger('jamSERVER')

        config = configparser.ConfigParser()
        config.read('jam.ini')
        self.settings = serverDatabase.Settings()
        self.database_manager = serverDatabase.DatabaseManager(self.settings, host=config.get('Database', 'host'),
                                                               port=config.get('Database', 'port'),
                                                               user=config.get('Database', 'user'),
                                                               password=config.get('Database', 'password'),
                                                               db=config.get('Database', 'db'))
        self.network_manager = serverNetwork.NetworkManager(self.settings, self.database_manager)
        self.scheduler = serverDatabase.AutomateSchedulers(self.settings, self.database_manager)
        self.scheduler.schedule_export()
        self.scheduler.schedule_import()

        self.display_table = DisplayTable(self, self.database_manager)
        self.setCentralWidget(self.display_table)

        config_action = QtWidgets.QAction('&Configuration', self)
        config_action.setShortcut(QtGui.QKeySequence('Ctrl+,'))
        config_action.setStatusTip('Configurations Window')
        config_action.triggered.connect(self.launch_configuration)
        quit_action = QtWidgets.QAction('&Quit', self)
        quit_action.setShortcut(QtGui.QKeySequence('Ctrl+q'))
        quit_action.setStatusTip('Quit')
        quit_action.triggered.connect(exit)

        self.statusBar()

        main_menu = self.menuBar()
        file_menu = main_menu.addMenu(' &File')
        file_menu.addAction(config_action)
        file_menu.addAction(quit_action)

        self.logger.info('Completed JamMainWindow __init__')
        self.show()

    def launch_configuration(self):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle('Configurations')
        configurations = ConfigurationWidget(self, self.database_manager)
        configurations.show()
        dialog_layout = QtWidgets.QVBoxLayout()
        dialog_layout.addWidget(configurations)
        dialog.setLayout(dialog_layout)
        dialog.exec_()


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    window = JamMainWindow(None)
    window.setWindowTitle('JAM')
    # window = ConfigurationWidget(None)
    app.exec_()
