import csv
import datetime
import configparser
from server import databaseServer
from PySide2 import QtCore, QtWidgets, QtGui


class MachinesTab(QtWidgets.QWidget):
    def __init__(self, parent):
        QtWidgets.QWidget.__init__(self, parent)
        self.database_manager = self.parent().database_manager

        # Tree View & Models for Machines
        self.machine_model = QtGui.QStandardItemModel(0, 3, self)
        self.machine_table = QtWidgets.QTableView(self)
        self.machine_table.setModel(self.machine_model)
        self.machine_table.setAlternatingRowColors(True)
        self.machine_table.setSortingEnabled(True)
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
        save_btn = QtWidgets.QPushButton('Save', self)
        save_btn.clicked.connect(self.save_table)
        btn_box.addWidget(save_btn)
        btn_box.addStretch()

        box_layout = QtWidgets.QHBoxLayout()
        box_layout.addWidget(self.machine_table)
        box_layout.addLayout(btn_box)
        self.setLayout(box_layout)
        self.show()

    def populate_machines(self):
        self.machine_model.clear()
        # Set horizontal headers
        headers_list = self.database_manager.get_machines_headers()
        self.machine_model.setHorizontalHeaderLabels(headers_list)

        # Insert machines
        machines_list = self.database_manager.get_machines()
        for idx, row in enumerate(machines_list):
            for col, value in enumerate(row):
                if value:
                    item = QtGui.QStandardItem()
                    item.setData(value, QtCore.Qt.EditRole)
                    if col == 0:
                        item.setFlags(QtCore.Qt.ItemIsEnabled)
                    self.machine_model.setItem(idx, col, item)

    def add_row(self):
        self.machine_model.insertRow(self.machine_model.rowCount())

    def delete_rows(self):
        rows = set()
        for idx in self.machine_table.selectedIndexes():
            rows.add(idx.row())
        row = min(rows)
        count = len(rows)
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


class PisTab(QtWidgets.QWidget):
    sensor_list = ['S01', 'S02', 'S03', 'S04', 'S05', 'S06', 'S07', 'S08', 'S09', 'S10', 'S11', 'S12', 'S13', 'S14',
                   'S15', 'E01', 'E02', 'E03', 'E04', 'E05']

    def __init__(self, parent):
        QtWidgets.QWidget.__init__(self, parent)
        self.database_manager = self.parent().database_manager
        self.pis_dict = {}

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
        header.setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)

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

        # Top form layout for Nick, IP & Mac
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
        mac_edit = QtWidgets.QLineEdit(self)
        mac_edit.setValidator(validator)
        self.main_lineedits['mac'] = mac_edit
        form_layout.addRow('Mac:', mac_edit)

        # Details scroll area with GridLayout
        details = QtWidgets.QScrollArea()
        details.setWidgetResizable(True)
        detail_widget = QtWidgets.QWidget(self)
        detail_grid = QtWidgets.QGridLayout(detail_widget)
        detail_grid.setColumnStretch(1, 1)
        detail_grid.setColumnStretch(2, 1)

        machines = [None] + self.database_manager.get_machine_names()
        self.machines_model = QtCore.QStringListModel(machines, self)

        columns = [None]
        for row in self.database_manager.custom_query("SHOW COLUMNS FROM jam_current_table WHERE field LIKE 'col%' "
                                                     "OR field LIKE 'output%';"):
            columns.append(row[0])
        self.machine_comboboxes = {}
        self.col_comboboxes = {}
        for row, id_ in enumerate(self.sensor_list):
            label = QtWidgets.QLabel(id_, detail_widget)
            machine_combo = QtWidgets.QComboBox(detail_widget)
            machine_combo.setModel(self.machines_model)
            self.machine_comboboxes[id_] = machine_combo
            col_combo = QtWidgets.QComboBox(detail_widget)
            col_combo.insertItems(0, columns)
            self.col_comboboxes[id_] = col_combo
            detail_grid.addWidget(label, row, 0)
            detail_grid.addWidget(machine_combo, row, 1)
            detail_grid.addWidget(col_combo, row, 2)

        # Button box for details
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

        hbox_layout = QtWidgets.QHBoxLayout()
        hbox_layout.addWidget(self.pis_treeview)
        hbox_layout.addLayout(button_box)
        hbox_layout.addLayout(vbox_layout)
        self.setLayout(hbox_layout)

        self.set_all_enabled(False, False)
        self.show()

    def populate_pis(self):
        self.pis_model.clear()
        self.pis_model.setHorizontalHeaderLabels(['Nickname', 'IP Address', 'Mac'])

        self.pis_dict = self.database_manager.get_pis()

        for ip in self.pis_dict.keys():
            nick_item = QtGui.QStandardItem(self.pis_dict[ip].get('nick'))
            ip_item = QtGui.QStandardItem(ip)
            mac_item = QtGui.QStandardItem(self.pis_dict[ip].get('mac'))
            index = self.pis_model.rowCount()
            self.pis_model.setItem(index, 0, nick_item)
            self.pis_model.setItem(index, 1, ip_item)
            self.pis_model.setItem(index, 2, mac_item)

    def update_machines_list(self):
        machines = [None] + self.database_manager.get_machine_names()
        self.machines_model.setStringList(machines)

    def set_fields(self, index):
        row = index.row()

        self.set_all_enabled(False, False)

        ip = self.pis_model.item(row, 1).text()
        self.main_lineedits['ip'].setText(ip)
        for id_ in ['nick', 'mac']:
            self.main_lineedits[id_].setText(self.pis_dict[ip][id_])

        for key in self.sensor_list:
            self.machine_comboboxes[key].setCurrentText(self.pis_dict[ip].get('machine{}'.format(key)))
            self.col_comboboxes[key].setCurrentText(self.pis_dict[ip].get('colnum{}'.format(key)))

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
        ip = self.pis_model.item(row, 1).text()

        self.database_manager.delete_pi(ip)
        self.populate_pis()

    def save_item(self):
        pi_row = []
        for key in ['ip', 'nick', 'mac']:
            pi_row.append(self.main_lineedits[key].text())

        for key in self.sensor_list:
            pi_row.append(self.machine_comboboxes[key].currentText())
            pi_row.append(self.col_comboboxes[key].currentText())

        self.database_manager.replace_pi(pi_row)

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


class EmployeesTab(QtWidgets.QWidget):
    def __init__(self, parent):
        QtWidgets.QWidget.__init__(self, parent)
        self.database_manager = self.parent().database_manager

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
        del_btn.clicked.connect(self.delete_emp)
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

            self.database_manager.insert_emp(id_, name)

        self.populate_employees()

    def delete_emp(self):
        rows = set()
        for idx in self.emp_treeview.selectedIndexes():
            rows.add(idx.row())
        emp_list = [self.emp_model.item(row, 0).text() for row in rows]

        self.database_manager.mark_to_delete_emp(rows, emp_list)
        self.populate_employees()

    def import_csv(self):
        path = QtWidgets.QFileDialog.getOpenFileName(self, 'Open CSV', '', 'CSV(*.csv)')
        if path[0] != '':
            with open(path[0], 'r') as csv_file:
                csv_reader = csv.reader(csv_file)
                csv_list = list(csv_reader)
                self.database_manager.insert_emps(csv_list)

            self.populate_employees()


class MiscTab(QtWidgets.QWidget):
    def __init__(self, parent):
        QtWidgets.QWidget.__init__(self, parent)
        self.database_manager = self.parent().database_manager
        self.config = configparser.ConfigParser()
        self.config.read('jam.ini')

        # Request group
        req_box = QtWidgets.QGroupBox('Request polling', self)
        req_layout = QtWidgets.QGridLayout()
        req_layout.setColumnMinimumWidth(0, 100)
        dur_label = QtWidgets.QLabel('Polling Interval: ', req_box)
        self.poll_spinbox = QtWidgets.QSpinBox(req_box)
        self.poll_spinbox.setMinimum(1)
        self.poll_spinbox.setMaximum(90)
        self.poll_spinbox.setValue(self.config.getint('Request', 'interval'))
        dur_label2 = QtWidgets.QLabel('minutes', req_box)
        req_layout.addWidget(dur_label, 0, 0, QtCore.Qt.AlignRight)
        req_layout.addWidget(self.poll_spinbox, 0, 1)
        req_layout.addWidget(dur_label2, 0, 2)
        req_btn = QtWidgets.QPushButton('Request now', req_box)
        req_layout.setAlignment(QtCore.Qt.AlignLeft)
        req_layout.addWidget(req_btn, 0, 3)
        req_box.setLayout(req_layout)

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

        # Set data management configs
        self.data_fields = {}
        data_box = QtWidgets.QGroupBox('Data')
        data_layout = QtWidgets.QGridLayout()
        data_box.setLayout(data_layout)
        data_start_label = QtWidgets.QLabel('Start week on', data_box)
        data_start_day = QtWidgets.QComboBox(data_box)
        data_start_day.addItems(['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'])
        data_start_day.setCurrentText(self.config.get('Data', 'day'))
        data_start_time = QtWidgets.QTimeEdit(QtCore.QTime.fromString(self.config.get('Data', 'time')), data_box)
        data_start_time.setDisplayFormat('hh:mm')
        self.data_fields['day'] = data_start_day
        self.data_fields['time'] = data_start_time
        data_layout.addWidget(data_start_label, 0, 0)
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
        data_layout.addWidget(data_archive_label, 1, 0)
        data_layout.addWidget(data_archive_spin, 1, 1)
        data_layout.addWidget(data_archive_label2, 1, 2)
        data_delete_label = QtWidgets.QLabel('Delete archive after ', data_box)
        data_delete_spin = QtWidgets.QSpinBox(data_box)
        data_delete_spin.setMaximum(12)
        data_delete_spin.setMinimum(2)
        data_delete_spin.setValue(self.config.getint('Data', 'delete'))
        data_delete_label2 = QtWidgets.QLabel(' months', data_box)
        self.data_fields['delete'] = data_delete_spin
        data_layout.addWidget(data_delete_label, 2, 0)
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

        # Save button at bottom right
        save_box = QtWidgets.QHBoxLayout()
        save_btn = QtWidgets.QPushButton('Save', self)
        save_btn.clicked.connect(self.save_misc)
        save_box.addStretch()
        save_box.addWidget(save_btn)

        vbox_layout = QtWidgets.QVBoxLayout()
        vbox_layout.addWidget(req_box)
        vbox_layout.addWidget(db_box)
        vbox_layout.addWidget(data_box)
        vbox_layout.addWidget(shift_box)
        vbox_layout.addStretch()
        vbox_layout.addLayout(save_box)
        self.setLayout(vbox_layout)
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

    def save_misc(self):
        for key in self.db_edits.keys():
            self.config.set('Database', key, self.db_edits[key].text())

        self.config.set('Data', 'day', self.data_fields['day'].currentText())
        for key in ['time', 'archive', 'delete']:
            self.config.set('Data', key, str(self.data_fields[key].text()))

        for col in range(1, 5):
            self.config.set('Shift', 'shift{}_enable'.format(col), str(self.shift_checks[col].isChecked()))
            self.config.set('Shift', 'shift{}_start'.format(col), str(self.shift_starts[col].text()))
            self.config.set('Shift', 'shift{}_end'.format(col), str(self.shift_ends[col].text()))

        self.config.set('Request', 'interval', str(self.poll_spinbox.text()))

        # TODO trigger reset all
        with open('jam.ini', 'w') as configfile:
            self.config.write(configfile)


class ConfigurationWidget(QtWidgets.QWidget):
    def __init__(self, parent):
        QtWidgets.QWidget.__init__(self, parent)
        config = configparser.ConfigParser()
        config.read('jam.ini')
        self.database_manager = databaseServer.DatabaseManager(None, host=config.get('Database', 'host'),
                                                               port=config.get('Database', 'port'),
                                                               user=config.get('Database', 'user'),
                                                               password=config.get('Database', 'password'),
                                                               db=config.get('Database', 'db'))

        self.setWindowTitle('Configurations')
        self.setMinimumWidth(800)

        self.tab_widget = QtWidgets.QTabWidget()
        self.machines_tab = MachinesTab(self)
        self.pis_tab = PisTab(self)
        self.emp_tab = EmployeesTab(self)
        self.misc_tab = MiscTab(self)
        self.tab_widget.addTab(self.machines_tab, 'Machines')
        self.tab_widget.addTab(self.pis_tab, 'Pis')
        self.tab_widget.addTab(self.emp_tab, 'Employees')
        self.tab_widget.addTab(self.misc_tab, 'Miscellaneous')
        self.tab_widget.currentChanged.connect(self.changed_tabs)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)
        # self.show()

    def changed_tabs(self):
        if self.tab_widget.currentWidget() == self.pis_tab:
            self.pis_tab.update_machines_list()


class DisplayTable(QtWidgets.QWidget):
    def __init__(self, parent):
        QtWidgets.QWidget.__init__(self, parent)
        config = configparser.ConfigParser()
        config.read('jam.ini')
        self.database_manager = databaseServer.DatabaseManager(None, host=config.get('Database', 'host'),
                                                               port=config.get('Database', 'port'),
                                                               user=config.get('Database', 'user'),
                                                               password=config.get('Database', 'password'),
                                                               db=config.get('Database', 'db'))

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
        self.display_table = DisplayTable(self)
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

        self.show()

    def launch_configuration(self):
        dialog = QtWidgets.QDialog(self)
        configurations = ConfigurationWidget(dialog)
        configurations.show()
        dialog.exec_()


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    window = JamMainWindow(None)
    # window = ConfigurationWidget(None)
    app.exec_()
